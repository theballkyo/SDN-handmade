import logging

import netaddr
import networkx as nx

import service
import sdn_utils

def create_networkx_graph(devices, add_link=True):
    """ Create graph than using NetworkX library
    """
    networkx = nx.Graph()

    cdp_service = service.get_service('cdp')
    device_service = service.get_service('device')
    link_service = service.get_service('link')

    link_list = []

    for src_device in devices:
        cdp = cdp_service.get_by_management_ip(src_device['management_ip'])

        if cdp is not None:
            cdp_neighbor = cdp.get('neighbor')
            # current_device = src_device
            # current_device = device_service.get_device(src_device['management_ip'])
            for neighbor in cdp_neighbor:
                # check device is exist in topology
                # If not continue to next cdp device
                neighbor_device = device_service.find_by_if_ip(neighbor.get('ip_addr'))
                if neighbor_device is None:
                    continue

                if_index = -1
                neighbor_if_speed = 0
                for neighbor_interface in neighbor_device.get('interfaces'):
                    # Default is -1, -2 because if no IP is not match
                    if neighbor_interface.get('ipv4_address', -1) == neighbor.get('ip_addr', -2):
                        if_index = neighbor_interface['index']
                        neighbor_if_speed = neighbor_interface['speed']
                        break

                # not have a neighbor
                if if_index == -1:
                    continue

                if_speed = 0
                current_if_speed = 0
                can_find_interface = False
                for interface in src_device['interfaces']:
                    if interface.get('index') == neighbor['local_ifindex']:
                        current = interface
                        if_speed = min(neighbor_if_speed, interface.get('speed'))
                        current_if_speed = interface.get('speed')
                        can_find_interface = True
                        break

                if not can_find_interface:
                    raise ValueError("Can't find current device interface ip %s" % src_device['management_ip'])

                if netaddr.IPAddress(current['ipv4_address']) < netaddr.IPAddress(neighbor['ip_addr']):
                    src_if_ip = current['ipv4_address']
                    src_port = current['description']
                    src_if_index = current['index']
                    # src_usage = current['bw_in_usage_octets']
                    dst_if_ip = neighbor['ip_addr']
                    dst_port = neighbor['port']
                    dst_if_index = neighbor_interface['index']
                else:
                    dst_if_ip = current['ipv4_address']
                    dst_port = current['description']
                    dst_if_index = current['index']
                    src_if_ip = neighbor['ip_addr']
                    src_port = neighbor['port']
                    src_if_index = neighbor_interface['index']
                    # src_usage = current['bw_in_usage_octets']

                logging.debug("Added edge: " + src_device['management_ip'] + " - " + neighbor_device[
                    'management_ip'] + " nb speed: " + str(neighbor_if_speed) + " my speed: " + str(
                    current_if_speed) + " src_ip: " + src_if_ip + " src_port: " + src_port)

                # TODO implement multiple edges between nodes
                try:
                    edge = networkx.edges[(src_device['management_ip'], neighbor_device['management_ip'])]
                except KeyError:
                    edge = None

                if edge:
                    links = edge['links']
                else:
                    links = {}

                if netaddr.IPAddress(src_device['management_ip']) < netaddr.IPAddress(neighbor_device['management_ip']):
                    src_node_ip = src_device['management_ip']
                    dst_node_ip = neighbor_device['management_ip']
                else:
                    dst_node_ip = src_device['management_ip']
                    src_node_ip = neighbor_device['management_ip']

                link_info = {
                    'src_node_ip': src_node_ip,
                    'src_ip': src_if_ip,
                    'src_if_ip': src_if_ip,
                    'src_port': src_port,
                    'src_if_index': src_if_index,
                    # 'src_usage': src_usage,
                    'dst_node_ip': dst_node_ip,
                    'dst_ip': dst_if_ip,
                    'dst_if_ip': dst_if_ip,
                    'dst_port': dst_port,
                    'dst_if_index': dst_if_index,
                    'link_min_speed': if_speed
                }

                link_id = sdn_utils.generate_link_id(src_if_ip, dst_if_ip)
                links[link_id] = link_info

                networkx.add_edge(
                    src_device['management_ip'],
                    neighbor_device['management_ip'],
                    links=links
                )

                if add_link:
                    link_list.append(link_info)

        else:
            # TODO
            raise NotImplementedError("SNMP currently is not support")

    if add_link:
        link_service.add_links(link_list)

    return networkx

# def add_link_to_db():
