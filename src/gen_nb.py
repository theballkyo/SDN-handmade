import copy
import ipcalc
import logging
from graphs import Graph
from database import MongoDB


class Link:
    def __init__(self):
        self.device1_ip = ''
        self.device1_name = ''
        self.device2_ip = ''
        self.device2_name = ''


class Neighbor:
    def __init__(self, interface, neighbor_ip):
        self.neighbor_ip = neighbor_ip
        self.interface = interface


def create_graph(devices):
    """
    """
    num_device = len(devices)

    matrix = []
    graph = {}
    for n1 in range(num_device):
        # Resetting neighbor
        devices[n1].neighbor = []

        device_1_name = devices[n1].get_name()
        _matrix = {
            'name': device_1_name,
            'connected': []
        }
        graph[devices[n1]] = []
        for n2 in range(num_device):
            device_2_name = devices[n2].get_name()
            _d2_matrix = {
                'name': device_2_name,
                'connected': False
            }
            if n1 == n2:
                _d2_matrix['connected'] = True
                _matrix['connected'].append(_d2_matrix)
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
                if d1_ip in ipcalc.Network('192.168.106.0', '255.255.255.0'):
                    # print(d1_ip)
                    continue
                # print(devices[n1]['name'], d1_ip)
                for n4 in range(len(device_2_if)):
                    d2_ip = device_2_if[n4].get('ipv4_address')
                    d2_subnet = device_2_if[n4].get('subnet')
                    if not d2_ip:
                        continue
                    # print(d2_ip, d1_ip_network)
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
                if stop_flag:
                    _d2_matrix['connected'] = True
                    break
            _matrix['connected'].append(_d2_matrix)
        matrix.append(_matrix)
    # logging.debug(graph)
    topo_graph = Graph(graph)
    # print(matrix)
    return topo_graph

# if __name__ == '__main__':
#     run(exclude_ips=[('192.168.106.0', '255.255.255.0')])
