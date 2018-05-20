import datetime
import logging
import socket
import struct
import settings
import os
import netaddr


def get_snmp_num_worker():
    num_worker = settings.snmp_worker.get('pool')
    try:
        num_worker = int(num_worker)
    except ValueError:
        num_worker = os.cpu_count()
    return num_worker


def hex_to_string(str_hex):
    if str_hex.startswith('0x'):
        str_hex = str_hex[2::]
        return ''.join(chr(int(str_hex[i:i + 2], 16)) for i in range(0, len(str_hex), 2))
    return str_hex


def hex_to_ip(ip_hex):
    """
    """
    try:
        return socket.inet_ntoa(struct.pack(">L", int(ip_hex, 16)))
    except ValueError:
        return None


def millis_to_datetime(millis):
    return datetime.timedelta(seconds=millis // 1000)


def seconds_to_datetime(seconds):
    return datetime.timedelta(seconds=seconds)


def unix_to_datetime(unix_time):
    if not isinstance(unix_time, int) and not isinstance(unix_time, float):
        raise ValueError('Unix time must be int or float only.')
    # return datetime.datetime.fromtimestamp(unix_time)
    date = datetime.datetime.utcfromtimestamp(unix_time)
    return date


def datetime_now():
    return datetime.datetime.utcnow()


def fraction_to_percent(numerator, denominator):
    return numerator / denominator * 100


def cal_bw_usage_percent(octets, if_speed, in_time):
    """ Calculate bandwidth usage
    """
    # logging.info("%s <--> %s :: %s", octets, if_speed, in_time)
    # return ((if_speed / ((octets * 8) / (in_time / 100))) * 100)
    in_time = in_time
    return ((octets * 8 * 100) / (in_time * if_speed)) * 100


def bandwidth_usage_percent_to_bit(speed, percent):
    return percent / 100 * speed


def subnet_mask_to_wildcard_mask(subnet_mask):
    """ Convert subnet mask to wildcard mask
    """
    subnet = subnet_mask.split('.')
    return ".".join([~x & 0xff for x in subnet])


def is_int(val):
    try:
        int(val)
        return True
    except ValueError:
        return False


def generate_link_id(src_ip, dst_ip):
    """

    :param src_ip:
    :param dst_ip:
    :return: @String link_id
    """
    src_ip = netaddr.IPAddress(src_ip)
    dst_ip = netaddr.IPAddress(dst_ip)
    if src_ip < dst_ip:
        return "{},{}".format(str(src_ip), str(dst_ip))
    return "{},{}".format(str(dst_ip), str(src_ip))


# def calculate_bw_usage_byte(octets, if_speed, in_time):
#     """Calculate bandwidth usage
#     """
#     return (octets * 8)

def generate_flow_remove_command(flow):
    remove_acl = "no ip access-list extended SDN-{}".format(flow['name'])
    remove_route_map = "no route-map SDN-topo permit {}".format(flow['seq'])
    return [remove_acl, remove_route_map]


def generate_flow_command(flow, action, current_action):
    acl_command1 = "ip access-list extended SDN-{}".format(flow['name'])
    acl_command0 = "no " + acl_command1
    acl_command2 = "remark Generate by SDN Handmade for flow name {}".format(flow['name'])
    # For debugging
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

    acl_command4 = acl_command3.replace('10 permit udp', '20 permit tcp')
    acl_command5 = acl_command3.replace('10 permit udp', '30 permit icmp')

    if action is None:
        return [acl_command0, acl_command1, acl_command2, acl_command3, acl_command4, acl_command5]

    map_seq = flow.get('seq')

    # Route Map
    rmap_1 = "route-map SDN-topo permit {}".format(map_seq)
    rmap_2 = "match ip address SDN-{}".format(flow['name'])

    rmap_21 = ''
    if current_action is not None:
        if current_action['rule'] == 'drop':
            rmap_21 = 'no set interface Null0'
        elif current_action['rule'] == 'next-hop':
            rmap_21 = 'no set ip next-hop {}'.format(current_action['data'])
        elif current_action['rule'] == 'exit-if':
            rmap_21 = 'no set interface {}'.format(current_action['data'])

    if action['rule'] == 'drop':
        rmap_3 = 'set interface Null0'
    elif action['rule'] == 'next-hop':
        rmap_3 = 'set ip next-hop {}'.format(action['data'])
    elif action['rule'] == 'exit-if':
        rmap_3 = 'set interface {}'.format(action['data'])
    else:
        rmap_3 = ''

    return [acl_command0, acl_command1, acl_command2, acl_command3, acl_command4, acl_command5, rmap_1, rmap_2, rmap_21,
            rmap_3]
