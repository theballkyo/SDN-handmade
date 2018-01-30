""" SDN Handmade start class
"""
import logging
import threading
import time
from functools import reduce
import multiprocessing

from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoTimeoutException

import generate_graph
import gen_subnet
import sdn_utils
import services
from database import get_mongodb
from device import Device
from netflow import NetflowWorker
from snmp_worker import SNMPWorker


class Route:
    def __init__(self):
        pass


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

        # self.ssh_info = {
        #     'device_type': 'cisco_ios',
        #     'ip':   ip,
        #     'username': ssh_info.get('username'),
        #     'password': ssh_info.get('password'),
        #     'port' : ssh_info.get('port'),
        #     'secret': ssh_info.get('secret'),
        #     'verbose': ssh_info.get('verbose', False),
        # }
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

        # is_in_flow = False
        # for action in flow['action']:
        #     if action['device_ip'] == self.ip:
        #         is_in_flow = True

        # is_in_flow_pending = False
        my_action = None
        current_action = None
        for action in flow['action_pending']:
            if action['device_ip'] == self.ip:
                # is_in_flow_pending = True
                my_action = action
                break

        if my_action is None:
            if flow['is_pending'] == False:
                return True
        else:
            if my_action.get('rule') == 'remove':
                command = sdn_utils.generate_flow_remove_command(flow)
                logging.debug(command)
                if self.send_config_set(command) == False:
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
        if self.send_config_set(command) == False:
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

        # self.path = FindPath()

        self.mongo = get_mongodb()

        self.init()

        self.device_service = services.DeviceService()
        # self.graph, self.matrix = self.create_graph()
        logging.info("Create topology")

    def init(self):
        if self.mongo.flow_seq.find_one() is None:
            # self.mongo.flow_seq.insert_one({
            #     'seq': [{'number': i, 'in_use': False} for i in range(0, 65535)]
            # })
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

    def find_link(self, from_device, to_device):
        """ Find link between 2 devices
            if not found link return None
        """
        pass

    def find_path_by_device(self, from_device, to_device, shortest=False):
        """ Find a path between 2 devices
        """
        if not isinstance(from_device, Device) or \
                not isinstance(to_device, Device):
            print("Error: from_device or to_device is not instance of Device")
            return None

        graph = self.create_graph()
        paths = graph.find_all_paths(from_device, to_device)

        if shortest:
            f = lambda a, b: a if (len(a) < len(b)) else b
            paths = reduce(f, paths)

        new_path = []

        if paths is None or len(paths) == 0:
            return []

        if isinstance(paths[0], list):
            for path in paths:
                path__ = []
                for i in range(len(path) - 1):
                    device = path[i]
                    neighbor = device.find_neighbor(path[i + 1])
                    path__.append({
                        "from_device": device,
                        "to_device": neighbor['neighbor_obj'],
                        "next_hop_ip": neighbor['neighbor_ip'],
                        "if_index": neighbor['if_index'],
                        # "next_hop_obj": neighbor['neighbor_obj']
                    })
                new_path.append(path__)
        else:
            for i in range(len(paths) - 1):
                device = paths[i]
                neighbor = device.find_neighbor(paths[i + 1])
                new_path.append({
                    "from_device": device,
                    "to_device": neighbor['neighbor_obj'],
                    "next_hop_ip": neighbor['neighbor_ip'],
                    "if_index": neighbor['if_index'],
                    # "next_hop_obj": neighbor['neighbor_obj']
                })
        return new_path

    def find_path_by_subnet(self, subnet1, subnet2, shortest=False):
        """ Find path by subnet
        """
        # Todo.
        subnets = self.create_subnet()
        subnet1_devices = subnets.get(subnet1)
        subnet2_devices = subnets.get(subnet2)

        if subnet1_devices is None or subnet2_devices is None:
            return None

        graph = self.create_graph()
        paths = []

        for subnet1_device in subnet1_devices:
            # print(subnet1_device)
            for subnet2_device in subnet2_devices:
                # print(subnet2_device)
                path_ = graph.find_all_paths(
                    subnet1_device['device_name'],
                    subnet2_device['device_name']
                )

                path = {
                    'from': subnet1_device['device_name'],
                    'from_ip': subnet1_device['ip'],
                    'to': subnet2_device['device_name'],
                    'to_ip': subnet2_device['ip'],
                    'paths': path_
                }
                paths.append(path)
        # logbug.debug(subnets)
        if shortest:
            f = lambda a, b: a if (len(a) < len(b)) else b
            return reduce(f, paths)
        return paths

    def get_path_by_subnet(self, src_network, src_mask, dst_network, dst_mask):
        src_route = self.mongo.route.find_one({
            'ipCidrRouteType': 3,
            'ipCidrRouteDest': src_network,
            'ipCidrRouteMask': src_mask
        })
        if src_route is None:
            print("Can't find source network {} {}".format(src_network, src_mask))
            return
        path = []
        dst_route = self.mongo.route.find({
            'ipCidrRouteDest': dst_network,
            'ipCidrRouteMask': dst_mask
        })
        start_device_ip = src_route.get('device_ip')

        src_wildcard = sdn_utils.subnet_mask_to_wildcard_mask(src_mask)
        dst_wildcard = sdn_utils.subnet_mask_to_wildcard_mask(dst_mask)

        stop_flag = False
        for _ in range(dst_route.count()):
            for route in dst_route.clone():
                logging.debug("%s :: %s", route.get('device_ip'), start_device_ip)
                if route.get('device_ip') == start_device_ip:
                    # Find route-map in flow_table
                    route_map = self.mongo.find_one({
                        "$or": [
                            {
                                'src_wildcard': src_wildcard,
                            }
                        ],
                        '$or': [
                            {
                                'dst_wildcard': dst_wildcard,
                            }
                        ],
                        'src_ip': src_network,
                        'dst_ip': dst_network,
                        'action.device_ip': ''
                    })

                    # TODO Check is in flow_table
                    if route_map is not None:
                        action = None
                        for _action in route_map.action:
                            if _action.device_ip == start_device_ip:
                                action = _action

                        if action.rule == 'exit-if':
                            device = self.mongo.device.find_one({
                                'device_ip': start_device_ip
                            })
                        elif action.rule == 'drop':
                            path.append('DROP')
                            stop_flag = True
                            break

                    path.append(route.get('device_ip'))
                    # Stop
                    if route.get('ipCidrRouteType') == 3:
                        stop_flag = True
                        break

                    start_device = self.mongo.device.find_one({
                        'interfaces.ipv4_address': route.get('ipCidrRouteNextHop')
                    })
                    start_device_ip = start_device.get('device_ip')
                    # logging.info(start_device_ip)
                    break

            if stop_flag:
                break
        return path

    def update_graph(self):
        self.path.update_graph(self.create_graph())

    def create_graph(self):
        """ Create graph
        """
        devices = self.device_service.get_active()
        return generate_graph.create_networkx_graph(devices)
        # return get_neighbor()

    def create_subnet(self):
        """ Create a subnet of topoloygy
        """
        return gen_subnet.create_subnet(self.devices)

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
        """ Add device(s) to topoloygy
        """
        if isinstance(devices, list):
            for device in devices:
                self.__add_device(device)
        else:
            self.__add_device(devices)

    def remove_device(self, device_ip):
        # Todo fix
        pass
        # for device in self.devices:
        #     if device.ip == device_ip:
        #         self._snmp_worker.remove_device(device)
        #         self.devices.remove(device)
        #         return True
        # return False

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

    def apply_flow(self, flow_name):
        flow = self.get_flow(flow_name)
        if flow is None:
            return
        device_action = []

        # Generate Access list command
        command = sdn_utils.generate_acl(flow)

        for action in flow['action']:
            in_pending = False
            for action_pending in flow['action_pending']:
                if action['device_ip'] == action_pending['device_ip']:
                    in_pending = True
                    break
            if not in_pending:
                # remove flow
                pass

    def get_flow(self, name):
        return self.mongo.flow_table.find_one({'name': name})

    def get_flows(self):
        """ Get flow """
        return self.mongo.flow_table.find()

    def create_device_object(self, device_info, ssh_info, snmp_info):
        for accept in self.accept_device:
            if accept[0] == device_info['type']:
                device_obj = accept[1](device_info, ssh_info, snmp_info)
                # device_obj = accept[1](ip, ssh_username, ssh_password, ssh_port, enable_password,
                #                        snmp_community, snmp_port)
                return device_obj

    def uptime(self):
        """ topology uptime
        """
        return time.time() - self.__create_time

    def print_matrix(self):
        """ Print matrix of devices
        """
        generate_graph.print_matrix(self.devices)

    def print_status(self):
        """ Print status of topoloygy
        """
        print("Uptime: {:.2f} seconds".format(self.uptime()))
        print("Number of device(s): {}".format(len(self.devices)))
        for device in self.devices:
            print("\t > {}".format(device))

    def __add_device(self, device):
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


class Flow:
    def __init__(self, flow_name):
        mongo = get_mongodb()
        flow = mongo.flow_table.find_one({'name': flow_name})
