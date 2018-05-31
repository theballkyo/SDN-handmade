import repository
from cli.config_mode.config_command import ConfigCommand
from cli.sdn_cmd import SDNCommand
import datetime
from repository import CopiedRouteRepository
import ipaddress


class CLIController(SDNCommand):
    _COMPLETE_SHOW = ('device', 'topology'
                      , 'version')

    def __init__(self, version):
        super(CLIController, self).__init__()
        self.version = version
        self.config_command = ConfigCommand(version)
        self.prompt = 'SDN Handmade ({:s})# '.format(version)
        self.logbug.prompt = self.prompt
        self.device_repository = repository.get('device')
        self.link_utilization_repository = repository.get('link_utilization')
        self.copied_route_repository = repository.get('copied_route')

    def do_show(self, args):
        """ Show detail of topology, device and more.
        Show [topology, device]
        """
        args = args.split(" ")
        if args[0] == '':
            print("Incorrect command.")
            return
        elif args[0] == 'device':
            return self._show_device(args[1:])
        elif args[0] == 'flow':
            # print(len(self.topology.get_flows()))
            for flow in self.topology.get_flows():
                print(flow)
            return
        elif args[0] == 'route':
            return self.show_route(args[1:])
        elif args[0] == 'topology':
            self._show_topology()
        # self.topology.print_matrix()
        elif args[0] == 'version':
            print(self.version)

    def complete_show(self, text, line, begidx, endidx):
        # logging.debug("text: {}, line: {}, begidx: {}, endidx: {}".format(text, line, begidx, endidx))
        _text = line.split(' ')
        if _text[1] == 'device':
            if len(_text) < 3:
                return []
            else:
                device_ip = _text[2]
            devices = self.device_repository.get_all()

            device_list = [
                i['management_ip'] for i in devices if i['management_ip'].startswith(device_ip)]
            if device_ip in device_list:
                return [i for i in ('route', 'interface') if i.startswith(_text[3])]
            # logging.debug(device_list)
            return device_list
        return [i for i in self._COMPLETE_SHOW if i.startswith(text)]

    def show_route(self, args):
        """ Display route information
        """
        # Check argument
        # args = args.split(' ')
        if len(args) != 4:
            print(
                "Usage: show route {host <source addr> | <source network> <source mask>} {host <destination addr> | <destination network> <destination mask>}")
            return

        # Todo implement find by host
        if args[0] == 'host' or args[2] == 'host':
            pass

        src_network, src_mask, dst_network, dst_mask = args

        path = self.topology.get_path_by_subnet(
            src_network, src_mask, dst_network, dst_mask)

        print(" -> ".join(path))

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

            print("[R]({}) {:21} -> {:21}(IF - {})".format(type,
                                                           str(ip_addr), next_hop, if_name))

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
        # self.logbug.pre_shutdown()
        # logging.debug("Shutdown...")
        # self.topology.shutdown()
        # time.sleep(0.5)
        # self.logbug.post_shutdown()
        # time.sleep(0.5)
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

    def _show_topology(self):
        links = self.link_utilization_repository.get_all()
        device_set = set()
        device_connect = set()
        margin = 0
        for link in links:
            device_set.add(link['src_node_hostname'])
            device_set.add(link['dst_node_hostname'])
            device_connect.add(link['src_node_hostname'] + link['dst_node_hostname'])
            margin = max(margin, len(link['src_node_hostname']))
            margin = max(margin, len(link['dst_node_hostname']))
        device_set = sorted(device_set)
        margin += 2
        print(" " * margin, end="")
        for device in device_set:
            print("{:^{margin}}".format(device, margin=margin), end="")
        print("")
        for device in device_set:
            print("{:^{margin}}".format(device, margin=margin), end="")
            for device2 in device_set:
                if device == device2:
                    print("{:^{margin}}".format("1", margin=margin), end="")
                elif device + device2 in device_connect:
                    print("{:^{margin}}".format("1", margin=margin), end="")
                else:
                    print("{:^{margin}}".format("0", margin=margin), end="")
                # print(device, device2, end="\t")
            print("")
        # logging.info(device_set)
        # logging.info(device_connect)

    def _show_device(self, args):
        if not args:
            devices = self.device_repository.get_all()
            margin = 0
            i = 1
            for device in devices:
                uptime = str(datetime.timedelta(seconds=device['uptime'] // 100))
                print("[{i}] {name} ({ip}) uptime - {uptime}".format(
                    i=i,
                    name=device['name'],
                    ip=device['management_ip'],
                    uptime=uptime
                ))
                i += 1
            return
        if len(args) == 1:
            print("Incomplete command.")
            return
        elif args[1] == 'interface':
            device = self.device_repository.get_device_by_mgmt_ip(args[0])
            margin = 0
            if not device:
                print("Can't find device IP {ip}".format(ip=args[0]))
                return
            for interface in device['interfaces']:
                margin = max(margin, len(interface.get('description')))
            margin += 2
            if margin < 16:
                margin = 16
            # Print header
            print("{name:{margin}} {ip:16} [Bandwidth usage]".format(
                name="Interface name",
                ip="IP Address",
                margin=margin
            ))

            for interface in device['interfaces']:
                if_ip = interface.get('ipv4_address')
                if not if_ip:
                    if_ip = 'No IP Address'
                print("{if_name:{margin}} {ip:16} IN: {bw_in:.2f}%, OUT: {bw_out:.2f}%".format(
                    margin=margin,
                    if_name=interface['description'],
                    ip=if_ip,
                    bw_in=interface.get('bw_in_usage_percent', 0.00),
                    bw_out=interface.get('bw_out_usage_percent', 0.00),
                ))
        elif args[1] == 'route':
            device = self.device_repository.get_device_by_mgmt_ip(args[0])
            if not device:
                print("Exit")
                return
            routes = self.copied_route_repository.get_by_device_id(device['_id'])
            print("{proto:14} {dst:22}    Next-hop".format(
                proto="Protocol",
                dst="Destination"
            ))
            for route in routes:
                dst = ipaddress.IPv4Network(route['dst'] + '/' + route['mask'])
                # print(dst)
                print("[{proto:12}] {dst:22} -> {nexthop}".format(
                    proto=CopiedRouteRepository.route_proto_reverse[route['proto']],
                    dst=str(dst),
                    nexthop=route['next_hop']
                ))
        else:
            print("Unknown command {}".format(args[1]))
            return
