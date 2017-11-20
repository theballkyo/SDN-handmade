""" SDN Handmade start class
"""
import logging
import time
from functools import reduce

import gen_nb
import gen_subnet
import logbug
from database import MongoDB
from netflow import NetflowWorker
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoTimeoutException
from snmp_worker import SNMPWorker
import sdn_utils


class Route:
    def __init__(self):
        pass


class Device:
    """ Device object
    """

    STATUS_OFFLINE = 0
    STATUS_ONLINE = 1
    STATUS_MARK_OFFLINE = 2
    STATUS_SNMP_WORKING = 3

    DEVICE_STATUS = (
        (STATUS_OFFLINE, 'Offline'),
        (STATUS_ONLINE, 'Online'),
        (STATUS_MARK_OFFLINE, 'Mark offline'),
        (STATUS_SNMP_WORKING, 'SNMP Working'),
    )

    def __init__(self, device_info, ssh_info, snmp_info):
        self.ip = device_info['ip']
        self.ssh_info = ssh_info
        self.ssh_info['ip'] = self.ip
        self.snmp_info = snmp_info
        self.snmp_community = snmp_info['community']
        self.snmp_port = snmp_info['port']
        self.type = 'device'

        # Default status
        self.status = self.STATUS_OFFLINE

        self.info = {}

        self.neighbor = []
        self.route = []
        self.subnets = {}

        self.mongo = MongoDB()

    def fork(self):
        self.mongo = MongoDB()

    def update_info(self):
        self.mongo.device.update_one({
            'device_ip': self.ip
        }, {
            '$set': self.info
        })

    def set_status(self, status):
        """ Set device status """
        verify = False
        for _status in self.DEVICE_STATUS:
            if _status[0] == status:
                verify = True
                break

        if not verify:
            logging.info("Can't find device status ID {}", status)
            return

        self.init_device()
        self.info['status'] = status
        # Reset mark offline count
        if status == self.STATUS_ONLINE:
            self.info['mark_offline_count'] = 0
        self.update_info()

    def mark_offline(self):
        self.init_device()
        if self.info['mark_offline_count'] > 3:
            pass
        self.mongo.device.update_one({'device_ip': self.ip}, {'$inc', {'mark_offline_count': 1}})


    def get_status(self):
        self.init_device()
        return self.info['status']

    def init_device(self):
        """ Initialize device
        """
        info = self.mongo.device.find_one({
            'device_ip': self.ip
        })

        if info is None:
            self.mongo.device.insert_one({
                'device_ip': self.ip,
                'status': self.STATUS_OFFLINE,
                'mark_offline_count': 0
            })

            info = self.mongo.device.find_one({
                'device_ip': self.ip
            })

        self.info = info

    def query(self, field):
        self.init_device()
        return self.info.get(field, [])

    def get_name(self):
        """ Get device name
        """
        self.init_device()
        return self.info.get('name', 'Unknow')

    def get_interfaces(self):
        """ Get interfaces of device
        """
        # self.init_device()
        # return self.info.get('interfaces', [])
        return self.query('interfaces')

    def find_neighbor_by_name(self, name):
        """ Find neighbor by device name
            and return Device object
        """
        for device in self.neighbor:
            # logbug.debug(device.get_name() + ":" + name)
            if device.get_name() == name:
                return device
        return None

    def find_neighbor(self, other_device):
        """ Find neighbor by device name
            and return Device object
        """
        for link_info in self.neighbor:
            if other_device == link_info['neighbor_obj']:
                return link_info
        return None

    def get_routes(self):
        """ Get routes
        """
        mongo = MongoDB()
        self.route = mongo.route.find({'device_ip': self.ip}).sort([
            ('ipCidrRouteDest', mongo.pymongo.ASCENDING),
            ('ipCidrRouteMask', mongo.pymongo.DESCENDING)
        ])

        return self.route

    def uptime(self):
        self.init_device()
        _time = self.info.get('uptime')
        if not _time:
            return "Down"
        return sdn_utils.millis_to_datetime(_time*10)

    def infomation_text(self):
        """ Display device infomation
        """
        self.init_device()
        return "{} ({}) uptime - {}".format(self.get_name(),
                                            self.ip,
                                            self.uptime())

    def __repr__(self):
        self.init_device()
        return "{}".format(self.get_name())

    def __str__(self):
        self.init_device()
        return "{}".format(self.get_name())


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

        self.net_connect = None


    def remote_command(self, command):
        """ Connect SSH to device
        """
        if self.net_connect:
            try:
                # Try to reconnect
                self.net_connect.establish_connection()
            except NetMikoTimeoutException:
                self.net_connect = None
        # If can't establish connection, Create new connection
        try:
            self.net_connect = ConnectHandler(**self.ssh_info)
        except NetMikoTimeoutException:
            self.net_connect = None
            logging.info("Error: Can't SSH to device ip {}".format(self.ip))
            return None

        output = self.net_connect.send_command(command)
        return output

    def send_config_set(self, config_command):
        if self.net_connect:
            try:
                # Try to reconnect
                self.net_connect.establish_connection()
            except NetMikoTimeoutException:
                self.net_connect = None
        # If can't establish connection, Create new connection
        try:
            self.net_connect = ConnectHandler(**self.ssh_info)
        except NetMikoTimeoutException:
            self.net_connect = None
            logging.info("Error: Can't SSH to device ip {}".format(self.ip))
            return None

        output = self.net_connect.send_config_set(config_command)
        return output

    def map_action(self, flow, action):
        acl_command1 = "ip access-list extend SDN-{}".format(flow['name'])
        acl_command2 = "remark Generate by SDN Handmade for flow name".format(flow['name'])
        # For debugging
        acl_command3 = "permit udp "
        if flow['src_ip'] == 'any':
            acl_command3 += ' any'
        elif flow['src_wildcard'] is None:
            acl_command3 += ' host {}'.format(flow['src_ip'])
        else:
            acl_command3 += ' {} {}'.format(flow['src_ip'], flow['src_wildcard'])
        if flow['src_port'] is not None:
            if '-' in flow['src_port']:
                port = flow['src_port'].split('-')
                start_port = port[0]
                end_port = port[1]
                acl_command3 += ' range {} {}'.format(start_port, end_port)
            else:
                acl_command3 += ' eq {}'.format(flow['src_port'])

        if flow['dst_ip'] == 'any':
            acl_command3 += ' any'
        elif flow['dst_wildcard'] is None:
            acl_command3 += ' host {}'.format(flow['dst_ip'])
        else:
            acl_command3 += ' {} {}'.format(flow['dst_ip'], flow['dst_wildcard'])
        if flow['dst_port'] is not None:
            if '-' in flow['dst_port']:
                port = flow['dst_port'].split('-')
                start_port = port[0]
                end_port = port[1]
                acl_command3 += ' range {} {}'.format(start_port, end_port)
            else:
                acl_command3 += ' eq {}'.format(flow['dst_port'])

        command = [acl_command1, acl_command2, acl_command3]
        logging.debug(command)
        self.send_config_set(command)

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

        self._snmp_worker = SNMPWorker()

        self._netflow_worker = NetflowWorker(
            netflow_ip,
            netflow_port
        )

        self.mongo = MongoDB()

        # self.graph, self.matrix = self.create_graph()
        logging.debug("Create topology")

    def run(self):
        """ Start topoloygy loop
        """
        self._netflow_worker.start()
        self._snmp_worker.run()

    def shutdown(self):
        """ Shutdown topology
        """
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
                    neighbor = device.find_neighbor(path[i+1])
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
                neighbor = device.find_neighbor(paths[i+1])
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

    def create_graph(self):
        """ Create graph
        """
        return gen_nb.create_graph(self.devices)
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
        for device in self.devices:
            if device.ip == device_ip:
                self._snmp_worker.remove_device(device)
                self.devices.remove(device)
                return True
        return False

    def add_flow(self, flow):
        """ Add flow
        """
        self.mongo.flow_table.update_one({
            'name': flow['name']
        }, {
            '$set': flow
        }, upsert=True)
        #
        # _flow = self.mongo.flow_table.find_one({
        #     'name': flow['name']
        # })
        # # logging.debug("Query flow result is {}", _flow)
        # if _flow is None:
        #     self.mongo.flow_table.insert_one(flow)
        # else:

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
        gen_nb.print_matrix(self.devices)

    def print_status(self):
        """ Print status of topoloygy
        """
        print("Uptime: {:.2f} seconds".format(self.uptime()))
        print("Number of device(s): {}".format(len(self.devices)))
        for device in self.devices:
            print("\t > {}".format(device))


    def __add_device(self, device):
        if not isinstance(device, Device):
            print("device argument is not instance of Device")
            return
        self.devices.append(device)
        self.mongo.device_config.update_one({
            'ip': device.ip,
        }, {
            '$set': {
                'ip': device.ip,
                'type': device.type,
                'ssh_info': device.ssh_info,
                'snmp_info': device.snmp_info
            }
        }, upsert=True)
        # Add to snmp worker
        self._snmp_worker.add_device(device, run=True)
