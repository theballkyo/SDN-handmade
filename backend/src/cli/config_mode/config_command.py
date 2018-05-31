import ipaddress
import logging

import logbug
import repository
import sdn_utils
from cli.sdn_cmd import SDNCommand
from repository import DeviceRepository
import netaddr


# from services.device_service import DeviceService


class AddDeviceCommand:
    SNMP_VERSION = (
        '2c',
    )
    ACCEPT_DEVICE = (
        'cisco_ios',
    )

    def __init__(self):
        self.logbug = logbug.get()

    def _input(self, msg):
        inp = self.logbug.read_input(msg)
        if inp == 'exit':
            raise KeyboardInterrupt
        return inp

    def _get_device_type(self):
        while 1:
            inp = self._input("Device type: ")
            accept_device = [device for device in self.ACCEPT_DEVICE]
            if inp.lower() in accept_device:
                return inp
            print("Device is not in list ({})".format(",".join(accept_device)))

    def _get_ip(self):
        while 1:
            inp = self._input("Device management ip(v4): ")
            try:
                ip = ipaddress.ip_address(inp)
                if ip.version != 4:
                    print("Ip not IPv4 format")
                else:
                    return inp
            except ValueError:
                print("IP format not correct")

    def _get_snmp_version(self):
        while True:
            inp = self._input("SNMP Version [2c]: ")
            if inp == '':
                inp = '2c'
            if inp not in self.SNMP_VERSION:
                print("SNMP Version can be only {}".format(self.SNMP_VERSION))
                continue
            return inp

    def _get_snmp_community(self):
        inp = self._input("SNMP Community string [public]: ")
        if inp == '':
            return 'public'
        return inp

    def _get_ssh_username(self):
        inp = self._input("SSH username: ")
        return inp

    def _get_ssh_password(self):
        inp = self._input("SSH password: ")
        return inp

    def _get_snmp_port(self):
        while True:
            inp = self._input("SNMP Port [161]: ")
            if inp == '':
                return 161
            if not inp.isdigit():
                print("Port number must be Integer only")
                continue
            try:
                port = int(inp)
                if port > 65535:
                    print("Port number must be between 0 - 65535")
                else:
                    return port
            except ValueError:
                print("Port number must be Integer only")

    def _get_ssh_port(self):
        while 1:
            inp = self._input("SSH Port [22]: ")
            if inp == '':
                return 22
            if not inp.isdigit():
                print("Port number must be Integer only")
                continue
            try:
                port = int(inp)
                if port > 65535:
                    print("Port number must be between 0 - 65535")
                else:
                    return port
            except ValueError:
                print("Port number must be Integer only")

    def _get_ssh_secret(self):
        inp = self._input("SSH secret (enable password): ")
        return inp

    def add_handle(self):
        """

        :return:
        """
        print("Add device to topology")
        print("If you want to cancel this task. Please enter `exit`")
        device_info = {}
        ssh_info = {}
        snmp_info = {}
        try:
            device_info['type'] = self._get_device_type()
            device_info['ip'] = self._get_ip()

            ssh_info['username'] = self._get_ssh_username()
            ssh_info['password'] = self._get_ssh_password()
            ssh_info['secret'] = self._get_ssh_secret()
            ssh_info['port'] = self._get_ssh_port()

            snmp_info['version'] = self._get_snmp_version()
            snmp_info['community'] = self._get_snmp_community()
            snmp_info['port'] = self._get_snmp_port()

            logging.debug("Device info %s", device_info)
            logging.debug("SSH info %s", ssh_info)
            logging.debug("SNMP info %s", snmp_info)

            device_repository = repository.get('device')
            device_repository.add_device({
                'management_ip': device_info['ip'],
                'status': DeviceRepository.STATUS_WAIT_UPDATE,
                'type': device_info['type'],
                'ssh_info': ssh_info,
                'snmp_info': snmp_info,
            })

            # Clear prompt
        except KeyboardInterrupt:
            print("Interrupt add device.")


class FlowCommand(SDNCommand):

    def __init__(self, version, name):
        super(FlowCommand, self).__init__()
        self.name = name
        self.prompt = 'SDN Handmade ({:s})(config-flow)# '.format(version)
        self.device_repository = repository.get('device')
        self.flow_routing_repository = repository.get('flow_routing')
        # self.used_flow_id_repository = repository.get('')
        self.new_flow = {
            'name': name,
            'actions': []
        }
        self.flow = {
            'info': {
                'submit_from': {
                    "type": 1,
                    "user": "CLI"
                },
                'status': 0
            },
            'new_flow': {}
        }

    def do_match(self, args):
        if args == '':
            print('Incomplete command.')
            return
        args = args.split(' ')
        if len(args) != 3:
            print("match <src/dst> <IP>/<Prefixlen> <Port>")
            return

        side = args[0]
        if side not in ('src', 'dst'):
            print("Side must be src, dst")
            return

        try:
            ip_obj = netaddr.IPNetwork(args[1])
        except ValueError:
            print("IP Address not is network address")
            return
        port = args[2]
        if port != 'any' and not port.isdigit():
            print("Port error")
            return

        self.new_flow[side + '_ip'] = str(ip_obj.network)
        self.new_flow[side + '_port'] = port
        self.new_flow[side + '_wildcard'] = str(ip_obj.hostmask)

        print(self.new_flow)

    def do_set(self, args):
        args = args.split(' ')
        if len(args) < 3:
            print('Incomplete command')
            return

        # Check device is exist
        device_ip = args[1]
        device = self.device_repository.get_device_by_mgmt_ip(device_ip)
        # device = self.topology.get_device_by_ip(device_ip)
        if device is None:
            print("Can't find device IP {}".format(device_ip))
            return
        action = args[2]
        if action not in ('next-hop', 'exit-if', 'drop'):
            print("Action must be {}".format(('next-hop', 'exit-if', 'drop')))
            return
        if action == 'next-hop':
            action_n = repository.PolicyRoute.ACTION_NEXT_HOP_IP
        elif action == 'exit-if':
            action_n = repository.PolicyRoute.ACTION_EXIT_IF
        else:
            action_n = repository.PolicyRoute.ACTION_DROP

        try:
            data = args[3]
        except (ValueError, IndexError, KeyError):
            data = ""

        actions = self.new_flow['actions']
        for action in actions:
            if action['device_id'] == device['_id']:
                action['action'] = action_n
                action['data'] = data
                return

        actions.append({
            'device_id': device['_id'],
            'action': action_n,
            'data': data
        })
        print(self.new_flow)

    def do_no(self, args):
        try:
            args = args.split()
            if args[0] == '':
                return
            if args[0] == 'set':
                if args[1] == 'device':
                    ip = args[2]
                    device = self.device_repository.get_device_by_mgmt_ip(ip)
                    actions = self.new_flow['actions']
                    i = 0
                    for action in actions:
                        if action['device_id'] == device['_id']:
                            del self.new_flow['actions'][i]
                            print(self.new_flow)
                            return
                        i += 1

        except (IndexError, ValueError):
            print('Incorrect command')

    def do_apply(self, args):
        self.flow['new_flow'] = self.new_flow
        self.flow_routing_repository.add_or_update_flow_routing(self.flow)
        print("Apply flow to queue success.")

    def do_detail(self, args):
        print('================== Flow name: {} =================='.format(self.name))
        print("MATCH: ", end='')
        src_ip = netaddr.IPNetwork(self.new_flow['src_ip'] + "/" + self.new_flow['src_wildcard'])
        print("SRC {host}/{prefix} {port}".format(
            host=str(src_ip.ip),
            prefix=str(src_ip.prefixlen),
            port=self.new_flow['src_port']
        ))
        dst_ip = netaddr.IPNetwork(self.new_flow['dst_ip'] + "/" + self.new_flow['dst_wildcard'])
        print("       DST {host}/{prefix} {port}".format(
            host=str(dst_ip.ip),
            prefix=str(dst_ip.prefixlen),
            port=self.new_flow['src_port']
        ))

        print("Actions")
        i = 1
        for action in self.new_flow['actions']:
            device = self.device_repository.get_device_by_id(action['device_id'])
            action_text = 'None'
            if action['action'] == repository.PolicyRoute.ACTION_DROP:
                action_text = 'drop'
            elif action['action'] == repository.PolicyRoute.ACTION_NEXT_HOP_IP:
                action_text = 'next-hop'
            elif action['action'] == repository.PolicyRoute.ACTION_EXIT_IF:
                action_text = 'exit-if'

            print("Device: {device_ip:22} -> {action:10} {data}".format(
                device_ip=device['management_ip'],
                action=action_text,
                data=action['data']
            ))
            i += 1


class ConfigCommand(SDNCommand):
    _AVAILABLE_ADD = ('device', 'flow')

    def __init__(self, version):
        super(ConfigCommand, self).__init__()
        self.version = version
        self.prompt = 'SDN Handmade ({:s})(config)# '.format(version)
        self.add_device_cmd = AddDeviceCommand()
        self.device_repository = repository.get("device")
        self.logbug = logbug.get()

    def do_remove(self, args):
        args = args.split(' ')
        if args[0] == 'device':
            if len(args) < 2:
                print("Usage remove device {Management ip}")
            else:
                try:
                    ip = ipaddress.ip_address(args[1])
                    if ip.version != 4:
                        print("Device IP must be IPv4")
                        return
                    self.device_repository.remove(args[1])
                    # if self.topology.remove_device(args[1]):
                    print("Removed device IP {}".format(args[1]))
                    # else:
                    #     print('Can\'t find device IP {}'.format(args[1]))
                except ValueError:
                    print("Device IP format not correct")

    def complete_remove(self, text, line, begidx, endidx):
        return ['device']

    def do_flow(self, args):
        if args == '':
            print("Usage flow <name>")
            return
        FlowCommand(self.version, args.split(' ')[0]).cmdloop()

    def complete_flow(self, text, line, begidx, endidx):
        flows = self.topology.get_flows()
        # logging.info(flows)
        return [i['name'] for i in flows if i['name'].startswith(text)]

    def do_debug(self, args):
        try:
            level = int(args)
            self.logbug.log_level = level
        except ValueError:
            return

    def do_add(self, args):
        """ Using to add something
        """
        args = args.split(' ')
        if args[0] == 'device':
            self.add_device_cmd.add_handle()
            print("Added device to topology")
            self.prompt = 'SDN Handmade (1.0.0)(config)# '
        elif args[0] == 'flow':
            if len(args) < 2:
                print("Flow must be name")
                return
            flow_name = args[1]
            if len(args[2:]) < 2:
                print("Flow must be source and destination IP")
                return
            self._add_flow(flow_name, args[2:])
        elif args[0] == 'action':
            if len(args) < 2:
                print("Incomplete command")
                return
            action = {
                'action': None,
            }
            if args[1] == 'drop':
                action['action'] = 'drop'

        else:
            print("Incomplete command. Usage: add [command]")

    def _add_flow(self, name, args):
        """ Checking and add flow"""
        flow = {
            'name': name,
            'src_ip': None,
            'src_port': None,
            'src_wildcard': None,
            'dst_ip': None,
            'dst_port': None,
            'dst_wildcard': None,
        }
        if len(args) == 2:
            flow['src_ip'] = args[0]
            flow['dst_ip'] = args[1]
            self.topology.add_flow(flow)
        elif len(args) == 3:
            print("Not implement yet.")
        elif len(args) == 4:
            flow['src_ip'] = args[0]
            if sdn_utils.is_int(args[1]):
                flow['src_port'] = int(args[1])
            else:
                flow['src_wildcard'] = args[1]

            flow['dst_ip'] = args[2]
            if sdn_utils.is_int(args[3]):
                flow['dst_port'] = int(args[3])
            else:
                flow['dst_wildcard'] = args[3]

            print(flow)
            self.topology.add_flow(flow)

        else:
            print("Incorrect command.")

    def complete_add(self, text, line, begidx, endidx):
        args = line.split(" ")
        if len(args) > 1:
            if args[1] == 'flow':
                pass
        return [i for i in self._AVAILABLE_ADD if i.startswith(text)]
