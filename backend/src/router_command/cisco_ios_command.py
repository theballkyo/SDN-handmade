import netaddr

from repository import PolicyRoute

ACCEPT_PROTOCOL = ('tcp', 'udp')


def generate_cmd(flow, flow_id, flow_name, action):
    policy = generate_policy_command(flow)
    action = generate_action_command(flow_id, flow_name, action)
    return policy + action


def _generate_match(ip, wildcard, port):
    # ACL match
    # Validate IP
    src_ip = netaddr.IPAddress(ip)
    src_wildcard = netaddr.IPAddress(wildcard)

    if (not src_wildcard.is_hostmask()) and (not src_wildcard.is_netmask()):
        raise ValueError("Wildcard: %s format error", str(src_wildcard))

    if str(src_ip) == '0.0.0.0' and str(src_wildcard) == '255.255.255.255':
        acl_cmd = 'any'
    elif str(src_wildcard) == '0.0.0.0':
        acl_cmd = 'host {}'.format(str(src_ip))
    else:
        acl_cmd = '{} {}'.format(str(src_ip), str(src_wildcard))

    if isinstance(port, str):
        if port == 'any':
            acl_cmd += ""
        elif port.find("-") >= 0:
            start_port, end_port = port.split('-')
            acl_cmd += " range {} {}".format(start_port, end_port)

        elif port.isdigit():
            acl_cmd += " eq {}".format(port)

    if isinstance(port, int):
        acl_cmd += " eq {}".format(port)

    return acl_cmd


def generate_acl_name(policy_id):
    return "SDN-handmade-policy-{}".format(policy_id)


def generate_policy_command(policy):
    name = policy.get('name')
    policy_id = policy.get('flow_id')

    acl_name = "ip access-list extended {}".format(generate_acl_name(policy_id))
    clear_acl = "no {}".format(acl_name)
    acl_remark = "remark Generate by SDN handmade for flow name {}".format(name)

    acl_src_cmd = _generate_match(policy['src_ip'], policy['src_wildcard'], policy['src_port'])
    acl_dst_cmd = _generate_match(policy['dst_ip'], policy['dst_wildcard'], policy['dst_port'])

    acl_cmd = []
    if policy.get('protocol') in ACCEPT_PROTOCOL:
        _acl_cmd = "10 permit {}".format(policy.get('protocol'))
        _acl_cmd += " {} {}".format(acl_src_cmd, acl_dst_cmd)
        acl_cmd.append(_acl_cmd)
    else:
        i = 1
        for protocol in ACCEPT_PROTOCOL:
            _acl_cmd = "{} permit {}".format(i * 10, protocol)
            _acl_cmd += " {} {}".format(acl_src_cmd, acl_dst_cmd)
            acl_cmd.append(_acl_cmd)
            i += 1

    return [clear_acl, acl_name, acl_remark] + acl_cmd


def _generate_policy_command(flow):
    flow_name = flow['name']
    acl_command1 = "ip access-list extended SDN-handmade-flow-{}".format(flow_name)
    # Add this to clear old ACL
    acl_command0 = "no " + acl_command1
    # Set remark
    acl_command2 = "remark Generate by SDN Handmade for flow name {}".format(flow_name)

    # Set ACL rule
    acl_command3 = "10 permit udp"
    if flow['pending']['src_ip'] == 'any':
        acl_command3 += ' any'
    elif flow['pending']['src_wildcard'] is None:
        acl_command3 += ' host {}'.format(flow['pending']['src_ip'])
    else:
        acl_command3 += ' {} {}'.format(flow['pending']['src_ip'], flow['pending']['src_wildcard'])
    if flow['pending']['src_port'] is not None:
        if '-' in flow['pending']['src_port']:
            port = flow['pending']['src_port'].split('-')
            start_port = port[0]
            end_port = port[1]
            acl_command3 += ' range {} {}'.format(start_port, end_port)
        else:
            acl_command3 += ' eq {}'.format(flow['pending']['src_port'])

    if flow['pending']['dst_ip'] == 'any':
        acl_command3 += ' any'
    elif flow['pending']['dst_wildcard'] is None:
        acl_command3 += ' host {}'.format(flow['pending']['dst_ip'])
    else:
        acl_command3 += ' {} {}'.format(flow['pending']['dst_ip'], flow['pending']['dst_wildcard'])
    if flow['pending']['dst_port'] is not None:
        if '-' in flow['pending']['dst_port']:
            port = flow['pending']['dst_port'].split('-')
            start_port = port[0]
            end_port = port[1]
            acl_command3 += ' range {} {}'.format(start_port, end_port)
        else:
            acl_command3 += ' eq {}'.format(flow['pending']['dst_port'])

    # Add ACL protocols (tcp, udp, icmp)
    acl_command4 = acl_command3.replace('10 permit udp', '20 permit tcp')
    acl_command5 = acl_command3.replace('10 permit udp', '30 permit icmp')

    return [acl_command0, acl_command1, acl_command2, acl_command3, acl_command4, acl_command5]


def generate_action_command(policy_id, policy_name, action):
    """
    Using route-map
    :return:
    """
    # flow_id = flow.get('flow_id')

    # Clear old action
    route_map00 = "no route-map SDN-handmade permit {}".format(policy_id)

    # Route Map
    route_map01 = "route-map SDN-handmade permit {}".format(policy_id)
    route_map02 = "match ip address {}".format(generate_acl_name(policy_id))

    # Clear old action
    # route_map03 = ''
    # if current_action is not None:
    #     if current_action['rule'] == 'drop':
    #         route_map03 = 'no set interface Null0'
    #     elif current_action['rule'] == 'next-hop':
    #         route_map03 = 'no set ip next-hop {}'.format(current_action['data'])
    #     elif current_action['rule'] == 'exit-if':
    #         route_map03 = 'no set interface {}'.format(current_action['data'])

    # Set route-map action
    if action['action'] == PolicyRoute.ACTION_DROP:
        route_map04 = 'set interface Null0'
    elif action['action'] == PolicyRoute.ACTION_NEXT_HOP_IP:
        route_map04 = 'set ip next-hop {}'.format(action['data'])
    elif action['action'] == PolicyRoute.ACTION_EXIT_IF:
        route_map04 = 'set interface {}'.format(action['data'])
    else:
        route_map04 = ''

    return [route_map00, route_map01, route_map02, route_map04]


def generate_remove_command(policy):
    policy_id = policy['flow_id']

    acl = "no ip access-list extended {}".format(generate_acl_name(policy_id))
    route_map = "no route-map SDN-handmade permit {}".format(policy_id)
    return [route_map, acl]
