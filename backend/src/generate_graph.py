import copy
import netaddr
import ipcalc
import logging
from graphs import Graph
from database import get_mongodb
import services
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PIL import Image
import time


class Neighbor:
    def __init__(self, interface, neighbor_ip):
        self.neighbor_ip = neighbor_ip
        self.interface = interface


def create_networkx_graph(devices):
    """ Create graph than using NetworkX libraly
    """
    num_device = devices.count()
    networkx = nx.Graph()

    cdp_service = services.CdpService()
    device_service = services.DeviceService()

    for src_device in devices:
        cdp = cdp_service.get_by_management_ip(src_device['management_ip'])
        # logging.debug(cdp)
        if cdp is not None:
            cdp_neighbor = cdp.get('neighbor')
            current_device = device_service.get_device(src_device['management_ip'])
            for neighbor in cdp_neighbor:
                # check device is exist in topology
                # If not continue to next cdp device
                neighbor_device = device_service.find_by_if_ip(neighbor.get('ip_addr'))
                if neighbor_device is None:
                    logging.debug('1: none')
                    continue

                if_index = -1
                neighbor_if_speed = 0
                for neighbor_interface in neighbor_device.get('interfaces'):
                    # Default is -1, -2 because if no IP is not match
                    if neighbor_interface.get('ipv4_address', -1) == neighbor.get('ip_addr', -2):
                        if_index = neighbor_interface['index']
                        neighbor_if_speed = neighbor_interface['speed']
                        break

                # Don't have neighbor
                if if_index == -1:
                    logging.debug('2: none')
                    continue

                if_speed = 0
                current_if_speed = 0
                can_find_interface = False
                for interface in current_device['interfaces']:
                    if interface.get('index') == neighbor['local_ifindex']:
                        current_ip = interface.get('ipv4_address')
                        current_port = interface.get('description')
                        if_speed = min(neighbor_if_speed, interface.get('speed'))
                        current_if_speed = interface.get('speed')
                        can_find_interface = True
                        break

                if not can_find_interface:
                    raise ValueError("Can't find current device interface ip %s" % src_device['management_ip'])

                if netaddr.IPAddress(current_ip) < netaddr.IPAddress(neighbor['ip_addr']):
                    src_ip = current_ip
                    src_port = current_port
                    dst_ip = neighbor['ip_addr']
                    dst_port = neighbor['port']
                else:
                    dst_ip = current_ip
                    dst_port = current_port
                    src_ip = neighbor['ip_addr']
                    src_port = neighbor['port']

                logging.debug("Added edge: " + src_device['management_ip'] + " - " + neighbor_device[
                    'management_ip'] + " nb speed: " + str(neighbor_if_speed) + " my speed: " + str(
                    current_if_speed) + " src_ip: " + src_ip + " src_port: " + src_port)
                networkx.add_edge(
                    src_device['management_ip'],
                    neighbor_device['management_ip'],
                    src_ip=src_ip,
                    src_port=src_port,
                    dst_ip=dst_ip,
                    dst_port=dst_port,
                    link_min_speed=if_speed
                )
        else:
            # TODO
            pass
    # logging.debug(networkx.edges)
    return networkx


def create_graph(devices):
    """
    """
    num_device = len(devices)

    matrix = []
    graph = {}
    conn = get_mongodb()
    for n1 in range(num_device):
        # Resetting neighbor
        devices[n1].neighbor = []
        device_1_name = devices[n1].get_name()
        _matrix = {
            'name': device_1_name,
            'connected': []
        }
        graph[devices[n1]] = []

        # Check CDP Enable
        cdp = devices[n1].get_cdp()
        if cdp.get('neighbor'):
            for neighbor in cdp.get('neighbor'):
                neighbor_device = conn.device.find_one({
                    'interfaces.ipv4_address': neighbor.get('ip_addr')
                })
                if neighbor_device is None:
                    continue
                if_index = -1
                for neighbor_interface in neighbor_device.get('interfaces'):
                    # Default is -1, -2 because if no IP is not match
                    if neighbor_interface.get('ipv4_address', -1) == neighbor.get('ip_addr', -2):
                        if_index = neighbor_interface['index']
                        break
                neighbor_info = {
                    "neighbor_ip": neighbor['ip_addr'],
                    # "neighbor_if_index": n4,
                    "neighbor_obj": neighbor_device,
                    "ip": devices[n1].ip,
                    "if_index": if_index,
                    "port": neighbor['port']
                }
                devices[n1].neighbor.append(neighbor_info)
                for device in devices:
                    if device.ip == neighbor_device.get('device_ip'):
                        graph[devices[n1]].append(device)
                        break
            continue
        # If CDP Not enable use SNMP
        for n2 in range(num_device):
            device_2_name = devices[n2].get_name()
            # device_2_info = devices[n1].get_info()
            # _d2_matrix = {
            #     'name': device_2_name,
            #     'connected': False
            # }
            if n1 == n2:
                # _d2_matrix['connected'] = True
                # _matrix['connected'].append(_d2_matrix)
                continue

            device_1_if = devices[n1].get_interfaces()
            device_2_if = devices[n2].get_interfaces()
            for n3 in range(len(device_1_if)):
                stop_flag = False
                d1_ip = device_1_if[n3].get('ipv4_address')
                d1_subnet = device_1_if[n3].get('subnet')
                if not d1_ip:
                    continue
                d1_ip_network = ipcalc.Network(d1_ip, d1_subnet)

                ### TEST
                # if d1_ip in ipcalc.Network('192.168.106.0', '255.255.255.0'):
                #     continue
                ### END TEST

                for n4 in range(len(device_2_if)):
                    d2_ip = device_2_if[n4].get('ipv4_address')
                    d2_subnet = device_2_if[n4].get('subnet')
                    if not d2_ip:
                        continue
                    if d2_ip in d1_ip_network:
                        graph[devices[n1]].append(devices[n2])
                        # Add neighbor to Device object
                        neighbor_info = {
                            "neighbor_ip": d2_ip,
                            # "neighbor_if_index": n4,
                            "neighbor_obj": devices[n2],
                            "ip": d1_ip,
                            "if_index": n3
                        }
                        devices[n1].neighbor.append(neighbor_info)
                        stop_flag = True
                        break
                # if stop_flag:
                #     _d2_matrix['connected'] = True
                #     break
        #     _matrix['connected'].append(_d2_matrix)
        # matrix.append(_matrix)
    logging.debug(graph)
    topo_graph = Graph(graph)
    # print(matrix)
    return topo_graph


def print_matrix(devices, use_cdp=False):
    """
    Print matrix
    :param devices:
    :return string:
    """
    # Todo matrix
    graph = create_graph(devices)
    edges = graph.edges()
    # print(edges)
    # logging.debug(graph.edges())
    width = 0
    for device in devices:
        if len(device.get_name()) > width:
            width = len(device.get_name())
    width += 2
    print('{:{width}s}'.format('', width=width), end='')
    for device in devices:
        print("{:^{width}s}".format(device.get_name(), width=width), end='')
    print('')
    for device_row in devices:
        print('{:{width}s}'.format(device_row.get_name(), width=width), end='')
        for device_col in devices:
            if {device_row, device_col} in edges or {device_col, device_row} in edges \
                    or device_col == device_row:
                print('{:^{width}s}'.format(str(1), width=width), end='')
            else:
                print('{:^{width}s}'.format(str(0), width=width), end='')
        print()

# if __name__ == '__main__':
#     run(exclude_ips=[('192.168.106.0', '255.255.255.0')])