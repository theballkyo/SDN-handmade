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

    def __init__(self, ip, snmp_community='public', snmp_port=161):
        self.ip = ip
        self.snmp_community = snmp_community
        self.snmp_port = snmp_port

        # Default status
        self.status = self.STATUS_OFFLINE

        self.info = {}

        self.neighbor = []
        self.route = []
        self.subnets = {}

    def init_device(self):
        """ Initialize device
        """
        mongo = MongoDB()
        info = mongo.device.find_one({
            'device_ip': self.ip
        })

        self.info = info

    def get_name(self):
        """ Get device name
        """
        return self.info.get('name', 'Unknow')

    def get_interfaces(self):
        """ Get interfaces of device
        """
        return self.info.get('interfaces', [])

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
        self.route = mongo.route.find({'device_ip': self.ip})

        return self.route

    def infomation_text(self):
        """ Display device infomation
        """
        return "{} ({}) uptime - {}".format(self.get_name(),
                                            self.ip,
                                            self.info.get('uptime', 'Down'))

    def __repr__(self):
        return "{}".format(self.get_name())

    def __str__(self):
        return "{}".format(self.get_name())


class Router(Device):
    """ Device is a Router
    """
    def __init__(self, ip, snmp_community='public'):
        super(Router, self).__init__(ip, snmp_community)
        self.type = 'router'


class CiscoRouter(Router):
    """ Device is a Cisco Router
    """
    def __init__(self, ip, ssh_info, snmp_community='public'):
        super(CiscoRouter, self).__init__(ip, snmp_community)

        self.ssh_info = {
            'device_type': 'cisco_ios',
            'ip':   ip,
            'username': ssh_info.get('username'),
            'password': ssh_info.get('password'),
            'port' : ssh_info.get('port'),
            'secret': ssh_info.get('secret'),
            'verbose': ssh_info.get('verbose', False),
        }
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


class Topoloygy:
    """ Topoloy class
    """
    def __init__(self, netflow_ip='127.0.0.1', netflow_port=23456):
        self.__create_time = time.time()
        self.devices = []
        self.subnets = []

        self._snmp_worker = SNMPWorker()

        self._netflow_worker = NetflowWorker(
            netflow_ip,
            netflow_port
        )

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

    def get_device(self, name):
        """ Get device object by name
        """
        for device in self.devices:
            if device.get_name() == name:
                return devices
        return None

    def add_device(self, devices):
        """ Add device(s) to topoloygy
        """
        if isinstance(devices, list):
            for device in devices:
                self.__add_device(device)
        else:
            self.__add_device(devices)

    def uptime(self):
        """ Topoloygy uptime
        """
        return time.time() - self.__create_time

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
        # Add to snmp worker
        self._snmp_worker.add_device(device.ip, device.snmp_community)
