import logging
import time
import ipaddress
from .sdn_cmd import SDNCommand
from .topology_command import TopologyCommand
from .device_command import DeviceCommand
from .show_command import ShowCommand
from .config_mode.config_command import ConfigCommand
from database import get_connection

class CLIController(SDNCommand):

    _COMPLETE_SHOW = ('device', 'flow', 'topology', 'graph', 'version', 'route')

    def init(self, topology, logbug, version):
        self.topology = topology
        self.logbug = logbug
        self.version = version
        self.topology_command = TopologyCommand(topology)
        self.device_command = DeviceCommand(topology, logbug)
        self.show_command = ShowCommand(topology)
        self.config_command = ConfigCommand(topology, logbug)
        self.prompt = 'SDN Handmade (0.0.1)# '
        self.logbug.prompt = self.prompt

    def do_show(self, args):
        """ Show detail of topology, device and more.
        Show [topology, device]
        """
        args = args.split(" ")
        if args[0] == '':
            print("Incorrect command.")
            return
        elif args[0] == 'device':
            if len(args) < 2:
                if len(self.topology.devices) == 0:
                    print("No device in this topology.")
                    return
                for index, device in enumerate(self.topology.devices):
                    print("[{}] {}".format(index, device.infomation_text()))
                return
            device_ip = args[1]
            device = self.topology.get_device_by_ip(device_ip)
            if device is None:
                print("Not found device IP {}".format(device_ip))
                return
            if len(args) < 3:
                # Todo show device info
                print(device.infomation_text())
                return
            if args[2] == 'route':
                routes = device.get_routes()
                self.print_pretty_routes(routes, device.get_interfaces())
                return
            if 'interface'.startswith(args[2]):
                interfaces = device.get_interfaces()
                self.print_interfaces(interfaces)
                return
        elif args[0] == 'flow':
            # print(len(self.topology.get_flows()))
            for flow in self.topology.get_flows():
                print(flow)
            return
        elif args[0] == 'route':
            return self.show_route(args[1:])
        elif args[0] == 'graph':
            print(self.topology.create_graph())
        elif args[0] == 'topology':
            self.topology.print_matrix()
        elif args[0] == 'version':
            print("SDN Handmade: 0.0.1")

    def complete_show(self, text, line, begidx, endidx):
        # logging.debug("text: {}, line: {}, begidx: {}, endidx: {}".format(text, line, begidx, endidx))
        _text = line.split(' ')
        if _text[1] == 'device':
            # logging.debug('Enter device')
            if len(_text) < 3:
                # print("")
                return []
            else:
                device_ip = _text[2]
            device_list = [i.ip for i in self.topology.devices if i.ip.startswith(device_ip)]
            if device_ip in device_list:
                return [i for i in ('route', 'interface') if i.startswith(_text[3])]
            logging.debug(device_list)
            return device_list
        return [i for i in self._COMPLETE_SHOW if i.startswith(text)]

    def show_route(self, args):
        """ Display route information
        """
        # Check argument
        # args = args.split(' ')
        if len(args) != 4:
            print("Usage: show route {host <source addr> | <source network> <source mask>} {host <destination addr> | <destination network> <destination mask>}")
            return

        # Todo implement find by host
        if args[0] == 'host' or args[2] == 'host':
            pass

        src_network, src_mask, dst_network, dst_mask = args
        mongo = get_connection()
        # src_device = mongo.device.find_one({'interfaces.'})
        src_route = mongo.route.find_one({
                                    'ipCidrRouteType': 3,
                                    'ipCidrRouteDest': src_network,
                                    'ipCidrRouteMask': src_mask
                                    })
        if src_route is None:
            print("Can't find source network {} {}".format(src_network, src_mask))
            return
        path = []
        dest = mongo.route.find({
            'ipCidrRouteDest': dst_network,
            'ipCidrRouteMask': dst_mask
        })
        start_device_ip = src_route.get('device_ip')

        stop_flag = False
        for _ in range(dest.count()):
            for route in dest:
                logging.info("%s :: %s", route.get('device_ip'), start_device_ip)
                if route.get('device_ip') == start_device_ip:
                    path.append(route.get('device_ip'))
                    start_device = mongo.device.find_one({
                        'interfaces.ipv4_address': route.get('ipCidrRouteNextHop')
                    })
                    start_device_ip = start_device.get('device_ip')
                    logging.info(start_device_ip)
                    # Stop
                    if route.get('ipCidrRouteType') == 3:
                        stop_flag = True
                    break
            if stop_flag:
                break
        logging.info(path)

    def print_interfaces(self, interfaces):
        """ Print pretty interfaces
        """
        for interface in interfaces:
            print("{:30} {:18} BW in {:.3f}% out {:.3f}%".format(
                interface.get('description', 'No name'),
                interface.get('ipv4_address', 'No IP address'),
                interface.get('bw_in_usage_percent', 0.0),
                interface.get('bw_out_usage_percent', 0.0)
            ))

    def print_pretty_routes(self, routes, interfaces):
        """ Print pretty route
        """
        interfaces = list(interfaces)
        for i, route in enumerate(routes):
            type = route.get('ipCidrRouteType')
            dest = route.get('ipCidrRouteDest')
            mask = route.get('ipCidrRouteMask')
            next_hop = route.get('ipCidrRouteNextHop')

            # -1 because in programming index start at 0
            if_index = route.get('ipCidrRouteIfIndex') - 1

            if_name = interfaces[if_index]['description']
            ip_addr = ipaddress.ip_network("{}/{}".format(dest, mask))

            print("[R]({}) {:21} -> {:21}(IF - {})".format(type, str(ip_addr), next_hop, if_name))

    def do_device(self, args):
        """
        Enter to device mode
        :param args:
        :return:
        """
        self.device_command.cmdloop("Enter to device mode")

    def do_config(self, args):
        """
        Enter to config mode
        :param args:
        :return:
        """
        self.config_command.cmdloop("Enter to config mode")


    def do_exit(self, args):
        self.logbug.pre_shutdown()
        logging.debug("Shutdown...")
        self.topology.shutdown()
        time.sleep(0.5)
        self.logbug.post_shutdown()
        time.sleep(0.5)
        return True

    def handle_input(self):
        """ Handle user input
        """
        inp = self.logbug.read_input("SDN Handmade (0.0.1)# ")
        if inp is None or inp in ('exit', 'shutdown'):
            return 'shutdown'
        # Split input
        inp_split = inp.split(' ')

        # Topology
        if inp_split[0] == 'show':
            self.show_command.handle_command(inp_split[1:])
        elif inp_split[0] == 'topology':
            self.topology_command.handle_command(inp_split[1:])
        elif inp_split[0] in ('device',):
            self.device_command.handle_command(inp_split[1:])
