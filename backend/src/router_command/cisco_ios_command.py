import logging


def generate_flow_command(flow):
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


def generate_action_command(flow, action):
    """
    Using route-map
    :return:
    """
    flow_id = flow.get('flow_id')

    # Clear old action
    route_map00 = "no route-map SDN-handmade permit {}".format(flow_id)

    # Route Map
    route_map01 = "route-map SDN-handmade permit {}".format(flow_id)
    route_map02 = "match ip address SDN-{}".format(flow['name'])

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
    if action['rule'] == 'drop':
        route_map04 = 'set interface Null0'
    elif action['rule'] == 'next-hop':
        route_map04 = 'set ip next-hop {}'.format(action['data'])
    elif action['rule'] == 'exit-if':
        route_map04 = 'set interface {}'.format(action['data'])
    else:
        route_map04 = ''

    return [route_map00, route_map01, route_map02, route_map04]
