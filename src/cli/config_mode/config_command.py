from cli.sdn_cmd import SDNCommand
import logging
import ipaddress
import sdn_utils


class AddDeviceCommand():
    def __init__(self, topology, logbug):
        self.topology = topology
        self.logbug = logbug

    def __input(self, prompt):
        inp = self.logbug.read_input(prompt)
        if inp == 'exit':
            raise KeyboardInterrupt
        return inp

    def __get_device_type(self):
        while 1:
            inp = self.__input("Device type: ")
            accept_device = [device[0] for device in self.topology.accept_device]
            if inp.lower() in accept_device:
                return inp
            print("Device is not in list ({})".format(",".join((accept_device))))

    def __get_ip(self):
        while 1:
            inp = self.__input("Device management ip(v4): ")
            try:
                ip = ipaddress.ip_address(inp)
                if ip.version != 4:
                    print("Ip not IPv4 format")
                else:
                    return inp
            except ValueError:
                print("IP format not correct")

    def __get_snmp_community(self):
        inp = self.__input("SNMP Community string (default `public`): ")
        if inp == '':
            return 'public'
        return inp

    def __get_ssh_username(self):
        inp = self.__input("SSH username: ")
        return inp

    def __get_ssh_password(self):
        inp = self.__input("SSH password: ")
        return inp

    def __get_snmp_port(self):
        while 1:
            inp = self.__input("SNMP Port (default `161`): ")
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

    def __get_ssh_port(self):
        while 1:
            inp = self.__input("SSH Port (default `22`): ")
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

    def __get_ssh_secret(self):
        inp = self.__input("SSH secret (enable password): ")
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
            device_info['type'] = self.__get_device_type()
            device_info['ip'] = self.__get_ip()

            ssh_info['username'] = self.__get_ssh_username()
            ssh_info['password'] = self.__get_ssh_password()
            ssh_info['secret'] = self.__get_ssh_secret()
            ssh_info['port'] = self.__get_ssh_port()

            snmp_info['community'] = self.__get_snmp_community()
            snmp_info['port'] = self.__get_snmp_port()

            logging.debug("Device info %s", device_info)
            logging.debug("SSH info %s", ssh_info)
            logging.debug("SNMP info %s", snmp_info)

            device = self.topology.create_device_object(device_info, ssh_info, snmp_info)
            self.topology.add_device(device)

            # Clear prompt
            self.logbug.prompt = ''
        except KeyboardInterrupt:
            print("Interrupt add device.")

class FlowCommand(SDNCommand):

    def __init__(self, topology, logbug, name):
        super(FlowCommand, self).__init__()
        self.topology = topology
        self.logbug = logbug
        self.name = name
        self.prompt = 'SDN Handmade (0.0.1)(config-flow)# '

        self.flow = self.topology.get_flow(name)

        if self.flow is None:
            self.topology.add_flow({
                'name': name,
                'src_ip': None,
                'src_port': None,
                'src_wildcard': None,
                'dst_ip': None,
                'dst_port': None,
                'dst_wildcard': None,
                'action': [],
                'action_pending': []
            })
            self.flow = self.topology.get_flow(self.name)

    def do_match(self, args):
        if args == '':
            print('Incomplete command.')
            return
        args = args.split(' ')

        if args[0] == 'src':
            if len(args[1:]) == 0:
                print('Incomplete command.')
            elif len(args[1:]) == 1:
                # { any }
                self.flow['src_ip'] = 'any'
                self.flow['src_port'] = None
                self.flow['src_wildcard'] = None
            elif len(args[1:]) == 2:
                # { host 192.168.1.1 | 192.168.1.0 0.0.0.255 }
                if args[1] == 'host':
                    self.flow['src_ip'] = args[2]
                    self.flow['src_port'] = None
                    self.flow['src_wildcard'] = None
                else:
                    self.flow['src_ip'] = args[1]
                    self.flow['src_port'] = None
                    self.flow['src_wildcard'] = args[2]
            elif len(args[1:]) == 3:
                # { any port 80 | any port-range 80-8000 }
                # host = args[1]
                port = args[3]
                self.flow['src_ip'] = 'any'
                self.flow['src_port'] = port
                self.flow['src_wildcard'] = None
            elif len(args[1:]) == 4:
                # { host 192.168.1.1 port 80 | host 192.168.1.1 port-range 80-8000 }
                # { 192.168.1.0 0.0.0.255 port 80 | 192.168.1.0 0.0.0.255 port-range 80-8000 }
                if args[1] == 'host':
                    host = args[2]
                    wildcard = None
                else:
                    host = args[1]
                    wildcard = args[2]
                port = args[4]
                self.flow['src_ip'] = host
                self.flow['src_wildcard'] = wildcard
                self.flow['src_port'] = port
        elif args[0] == 'dest':
            if len(args[1:]) == 0:
                print('Incomplete command.')
            elif len(args[1:]) == 1:
                # { any }
                self.flow['dst_ip'] = 'any'
                self.flow['dst_port'] = None
                self.flow['dst_wildcard'] = None
            elif len(args[1:]) == 2:
                # { host 192.168.1.1 | 192.168.1.0 0.0.0.255 }
                if args[1] == 'host':
                    self.flow['dst_ip'] = args[2]
                    self.flow['dst_port'] = None
                    self.flow['dst_wildcard'] = None
                else:
                    self.flow['dst_ip'] = args[1]
                    self.flow['dst_port'] = None
                    self.flow['dst_wildcard'] = args[2]
            elif len(args[1:]) == 3:
                # { any port 80 | any port-range 80-8000 }
                # host = args[1]
                port = args[3]
                self.flow['dst_ip'] = 'any'
                self.flow['dst_port'] = port
                self.flow['dst_wildcard'] = None
            elif len(args[1:]) == 4:
                # { host 192.168.1.1 port 80 | host 192.168.1.1 port-range 80-8000 }
                # { 192.168.1.0 0.0.0.255 port 80 | 192.168.1.0 0.0.0.255 port-range 80-8000 }
                if args[1] == 'host':
                    host = args[2]
                    wildcard = None
                else:
                    host = args[1]
                    wildcard = args[2]
                port = args[4]
                self.flow['dst_ip'] = host
                self.flow['dst_wildcard'] = wildcard
                self.flow['dst_port'] = port

        self.topology.add_flow(self.flow)

    def do_set(self, args):
        args = args.split(' ')
        if len(args) < 3:
            print('Incomplete command')
            return

        # Check device is exist
        device_ip = args[1]
        device = self.topology.get_device_by_ip(device_ip)
        if device is None:
            print("Can't find device IP {}".format(device_ip))
            return

        # Get action
        # Now, { drop | next-hop | exit-if-index }
        action = args[2]
        if action in ('next-hop', 'exit-if-index') and len(args) < 4:
            print('Incomplete command.')
            return

        # Drop action
        if action == 'drop':
            _action = {
                'device_ip': device_ip,
                'rule': 'drop',
                'data': ''
            }
        elif action == 'next-hop':
            _action = {
                'device_ip': device_ip,
                'rule': 'next-hop',
                'data': args[3]
            }
        elif action == 'exit-if-index':
            _action = {
                'device_ip': device_ip,
                'rule': 'exit-if-index',
                'data': args[3]
            }

        for i, action in enumerate(self.flow['action_pending']):
            if action.get('device_ip') == device_ip:
                self.flow['action_pending'][i] = _action
                break
        else:
            self.flow['action_pending'].append(_action)
        self.topology.add_flow(self.flow)

    def do_no(self, args):
        try:
            args = args.split()
            if args[0] == '':
                return
            if args[0] == 'set':
                if args[1] == 'device':
                    ip = args[2]
                    for i, action in enumerate(self.flow['action']):
                        if action['device_ip'] == ip:
                            in_pending = False
                            for i2, action_pending in enumerate(self.flow['action_pending']):
                                if action_pending['device_ip'] == ip:
                                    self.flow['action_pending'][i] = {
                                        'rule': 'remove',
                                        'device_ip': ip
                                    }
                                    in_pending = True
                                    break
                            if not in_pending:
                                self.flow['action_pending'].append({
                                    'rule': 'remove',
                                    'device_ip': ip
                                })
                            self.topology.add_flow(self.flow)
                            return
                    for i, action in enumerate(self.flow['action_pending']):
                        if action['device_ip'] == ip:
                            del self.flow['action_pending'][i]
                            self.topology.add_flow(self.flow)
                            return

        except (IndexError, ValueError):
                print('Incorrect command')

    def do_apply(self, args):
        if len(self.flow['action_pending']) < 1:
            return

        for device in self.topology.devices:
            if not device.test_ssh_connect():
                print("Some device can't SSH, Stopped operations")
                return
        for device in self.topology.devices:
            device.update_flow(self.flow)

        # Remove
        # del_count = 0
        for i, action_pending in enumerate(self.flow['action_pending']):
            in_action = False
            del_count = 0
            for i2, action in enumerate(self.flow['action']):
                if action_pending['device_ip'] == action['device_ip']:
                    in_action = True
                    if action_pending['rule'] == 'remove':
                        del self.flow['action'][i2-del_count]
                        del_count += 1
                    else:
                        self.flow['action'][i2-del_count] = action_pending
                    break
            if not in_action:
                self.flow['action'].append(action_pending)

        logging.debug(self.flow['action'])
        # self.flow['action'] = new_action
        self.flow['action_pending'] = []
        self.topology.add_flow(self.flow)

        print("Apply flow success.")

    def do_detail(self, args):
        print('================== Flow name: {} =================='.format(self.flow['name']))

        print("Match: src ", end='')
        if self.flow['src_wildcard'] is None:
            print("host {}".format(self.flow['src_ip']), end='')
        else:
            print("{} {}".format(self.flow['src_ip'], self.flow['src_wildcard']), end='')
        if self.flow['src_port'] is not None:
            print(" port {}".format(self.flow['src_port']))
        else:
            print("")
        print("       dst ", end='')
        if self.flow['dst_wildcard'] is None:
            print("host {}".format(self.flow['dst_ip']), end='')
        else:
            print("{} {}".format(self.flow['dst_ip'], self.flow['dst_wildcard']), end='')
        if self.flow['dst_port'] is not None:
            print(" port {}".format(self.flow['dst_port']))
        else:
            print("")

        print("Current actions:", end='')
        for i, action in enumerate(self.flow['action']):
            if i == 0:
                margin = 1
            else:
                margin = 17
            print((" " * margin) + "Device: {:15} -> {} {}".format(
                action['device_ip'],
                action['rule'],
                action.get('data') or ''
            ))
        print('')
        print("Pending actions:", end='')
        for i, action in enumerate(self.flow['action_pending']):
            if i == 0:
                margin = 1
            else:
                margin = 17
            print((" " * margin) + "Device: {:15} -> {} {}".format(
                action['device_ip'],
                action['rule'],
                action.get('data') or ''
            ))
        print('')

class ConfigCommand(SDNCommand):
    _AVAILABLE_ADD = ('device',)

    def __init__(self, topology, logbug):
        super(ConfigCommand, self).__init__()
        self.topology = topology
        self.logbug = logbug
        self.prompt = 'SDN Handmade (0.0.1)(config)# '
        self.add_device = AddDeviceCommand(topology, logbug)

    def do_remove(self, args):
        args = args.split(' ')
        if args[0] == 'device':
            if len(args) < 2:
                print("Usage remove device {device ip}")
            else:
                try:
                    ip = ipaddress.ip_address(args[1])
                    if ip.version != 4:
                        print("Device IP must be IPv4")
                        return
                    if self.topology.remove_device(args[1]):
                        print("Removed device IP {}".format(args[1]))
                    else:
                        print('Can\'t find device IP {}'.format(args[1]))
                except ValueError:
                    print("Device IP format not correct")

    def do_flow(self, args):
        if args == '':
            print("Usage flow <name>")
            return
        FlowCommand(self.topology, self.logbug, args.split(' ')[0]).cmdloop()


    def do_add(self, args):
        """ Using to add something
        """
        args = args.split(' ')
        if args[0] == 'device':
            self.add_device.add_handle()
            print("Added device to topology")
            self.prompt = 'SDN Handmade (0.0.1)(config)# '
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
        # if len(args) < 1:
        #     print("Usage add [command]")
        # else:
        #     if args[1] ==

    # def do_flow(self, args):
    #     """ Add flow
    #     """
    #

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
        return [i for i in self._AVAILABLE_ADD if i.startswith(text)]