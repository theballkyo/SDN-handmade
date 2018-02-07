""" SDN Handmade start class
"""
import logging
import threading
import time

from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoTimeoutException

import sdn_utils
import services
from database import get_mongodb
from device import Device
from netflow import NetflowWorker
from snmp_worker import SNMPWorker


class Router(Device):
    """ Device is a Router
    """

    def __init__(self, device_info, ssh_info, snmp_info):
        super(Router, self).__init__(device_info, ssh_info, snmp_info)
        self.type = 'router'


class CiscoRouter(Router):
    """ Device is a Cisco Router
    """

    def __init__(self, device_info, ssh_info, snmp_info):
        super(CiscoRouter, self).__init__(device_info, ssh_info, snmp_info)
        self.ssh_info['device_type'] = 'cisco_ios'

        self.net_connect = ConnectHandler(**ssh_info)

    def remote_command(self, command):
        """ Connect SSH to device
        """
        if not self.test_ssh_connect():
            return False
        self.net_connect.enable()
        output = self.net_connect.send_command(command)
        return output

    def test_ssh_connect(self):
        if self.net_connect is None or not self.net_connect.is_alive():
            try:
                logging.debug("ConnectHandler")
                self.net_connect = ConnectHandler(**self.ssh_info)
            except NetMikoTimeoutException:
                self.net_connect = None
                logging.info("Error: Can't SSH to device ip {}".format(self.ip))
                return False
        # TEST
        retry = 0
        max_retry = 3
        while retry < max_retry:
            try:
                if retry > 0:
                    self.net_connect = ConnectHandler(**self.ssh_info)
                self.net_connect.enable()
                return True
            except (NetMikoTimeoutException, EOFError):
                retry += 1
        return False

    def send_config_set(self, config_command):
        if not self.test_ssh_connect():
            return False
        try:
            self.net_connect.enable()
            output = self.net_connect.send_config_set(config_command)
            return output
        except (NetMikoTimeoutException, EOFError):
            return False

    def update_flow(self, flow):
        """ apply action to device
        """
        my_action = None
        current_action = None
        for action in flow['action_pending']:
            if action['device_ip'] == self.ip:
                # is_in_flow_pending = True
                my_action = action
                break

        if my_action is None:
            if not flow['is_pending']:
                return True
        else:
            if my_action.get('rule') == 'remove':
                command = sdn_utils.generate_flow_remove_command(flow)
                logging.debug(command)
                if not self.send_config_set(command):
                    return False
                return True
            else:
                for action in flow['action']:
                    if action['device_ip'] == self.ip:
                        current_action = action
                        break

        # Apply interface policy
        # Todo

        # Grouping commands
        command = sdn_utils.generate_flow_command(flow, my_action, current_action)
        logging.info(command)
        if not self.send_config_set(command):
            return False
        return True

    def get_serial_number(self):
        """ Get device serial Number
        """
        return self.remote_command("show version | inc Processor board ID")

    def get_route_map(self):
        """ Get current route map on device
        """
        # Todo Create function for this
        pass

    def get_acl_list(self):
        """ Get current access list on device
        """
        # Todo Create function for this
        pass


class CiscoIosRouter(Router):
    def __init__(self, device_info, ssh_info, snmp_info):
        super(CiscoIosRouter, self).__init__(device_info, ssh_info, snmp_info)
        self.type = 'cisco_ios'


class Topology:
    """ Topology class
    """

    accept_device = (
        ('cisco_ios', CiscoRouter),
    )

    def __init__(self, netflow_ip='127.0.0.1', netflow_port=23456):
        self.__create_time = time.time()
        self.devices = []
        self.subnets = []
        self.app_service = services.AppService()

        self._snmp_worker = SNMPWorker()

        self._netflow_worker = NetflowWorker(
            netflow_ip,
            netflow_port
        )

        self.mongo = get_mongodb()

        self.init()

        self.device_service = services.DeviceService()
        logging.info("Create topology")

    def init(self):
        if self.mongo.flow_seq.find_one() is None:
            for i in range(0, 65535):
                self.mongo.flow_seq.insert_one({
                    'number': i,
                    'in_use': False
                })

    def run(self):
        """ Start topology loop
        """
        if not self.app_service.is_running():
            # Resetting snmp status
            devices = self.device_service.get_all()
            for device in devices:
                self.device_service.set_snmp_running(device['management_ip'], False)

            self._netflow_worker.start()
            threading.Thread(target=self._snmp_worker.run).start()
            self.app_service.set_running(True)

    def shutdown(self):
        """ Shutdown topology
        """
        self.app_service.set_running(False)
        self._snmp_worker.shutdown()
        self._netflow_worker.shutdown()
        self._netflow_worker.join()
        logging.debug("Shutdown Netflow server complete")

    def get_device_by_ip(self, ip):
        """ Get device object by IP address
        """
        for device in self.devices:
            if device.ip == ip:
                return device
        return None

    def get_device(self, name):
        """ Get device object by name
        """
        for device in self.devices:
            if device.get_name() == name:
                return device
        return None

    def add_device(self, devices):
        """ Add device(s) to topology
        """
        if isinstance(devices, list):
            for device in devices:
                self._add_device(device)
        else:
            self._add_device(devices)

    def remove_device(self, device_ip):
        # Todo fix
        raise NotImplementedError()

    def add_flow(self, flow):
        """ Add flow
        """

        if flow.get('seq') is None:
            seq = self.mongo.flow_seq.find_one({'in_use': False})
            if seq is None:
                return None
            flow['seq'] = seq['number']

            seq['in_use'] = True
            self.mongo.flow_seq.update_one({
                'number': seq['number']
            }, {
                '$set': seq
            })

        self.mongo.flow_table.update_one({
            'name': flow['name']
        }, {
            '$set': flow
        }, upsert=True)

        return flow

    def get_flow(self, name):
        return self.mongo.flow_table.find_one({'name': name})

    def get_flows(self):
        """ Get flow """
        return self.mongo.flow_table.find()

    def create_device_object(self, device_info, ssh_info, snmp_info):
        for accept in self.accept_device:
            if accept[0] == device_info['type']:
                device_obj = accept[1](device_info, ssh_info, snmp_info)
                return device_obj

    def uptime(self):
        """ topology uptime
        """
        return time.time() - self.__create_time

    def print_status(self):
        """ Print status of topology
        """
        print("Uptime: {:.2f} seconds".format(self.uptime()))
        print("Number of device(s): {}".format(len(self.devices)))
        for device in self.devices:
            print("\t > {}".format(device))

    def _add_device(self, device):
        if not isinstance(device, Device):
            logging.info("device argument is not instance of Device")
            return
        self.devices.append(device)

        self.device_service.add_device({
            'management_ip': device.ip,
            'status': Device.STATUS_OFFLINE,
            'type': device.type,
            'ssh_info': device.ssh_info,
            'snmp_info': device.snmp_info,
            # Todo
            'netflow_src': {
                'ip': '0.0.0.0'
            }
        })
