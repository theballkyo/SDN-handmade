import logging

import netaddr
import networkx as nx

import services


def create_networkx_graph(devices):
    """ Create graph than using NetworkX library
    """
    networkx = nx.Graph()

    cdp_service = services.CdpService()
    device_service = services.DeviceService()

    for src_device in devices:
        cdp = cdp_service.get_by_management_ip(src_device['management_ip'])

        if cdp is not None:
            cdp_neighbor = cdp.get('neighbor')
            current_device = device_service.get_device(src_device['management_ip'])
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
            raise NotImplementedError("Using SNMP to Find neighbor")
    return networkx
