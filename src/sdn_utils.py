import datetime
import struct
import socket

def hex_to_string(str_hex):
    if str_hex.startswith('0x'):
        str_hex = str_hex[2::]
    return ''.join(chr(int(str_hex[i:i+2], 16)) for i in range(0, len(str_hex), 2))


def hex_to_ip(ip_hex):
    """
    """
    return socket.inet_ntoa(struct.pack(">L", int(ip_hex, 16)))

def unix_to_datetime(unix_time):
    # if not isinstance(unix_time, int):
    #     raise ValueError('Unix time must be integer only.')
    return datetime.datetime.fromtimestamp(unix_time)

def cal_bw_usage_percent(octets, if_speed, in_time):
    """Calculate bandwidth usage
    """
    return (octets * 8 * 100) / ((in_time) * if_speed)

# def calculate_bw_usage_byte(octets, if_speed, in_time):
#     """Calculate bandwidth usage
#     """
#     return (octets * 8)
