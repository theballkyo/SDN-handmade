import copy
import ipcalc

from graphs import Graph
from database import MongoDB

def run(exclude_ips=None):
    """
    """
    mongo = MongoDB()
    device_db = mongo.device

    devices = device_db.find()

    num_device = devices.count()

    matrix = []

    graph = {}

    # print(num_device)
    nnn = 0
    for n1 in range(num_device):
        _matrix = {
            'name': devices[n1]['name'],
            'connected': []
        }
        graph[devices[n1]['name']] = []
        for n2 in range(num_device):
            _d2_matrix = {
                'name': devices[n2]['name'],
                'connected': False
            }
            if n1 == n2:
                _d2_matrix['connected'] = True
                _matrix['connected'].append(_d2_matrix)
                continue
            device_1_if = devices[n1]['interfaces']
            device_2_if = devices[n2]['interfaces']
            for n3 in range(len(device_1_if)):
                stop_flag = False
                d1_ip = device_1_if[n3].get('ipv4_address')
                d1_subnet = device_1_if[n3].get('subnet')
                if not d1_ip:
                    nnn += 1
                    continue
                d1_ip_network = ipcalc.Network(d1_ip, d1_subnet)


                ### TEST
                if d1_ip in ipcalc.Network('192.168.106.0', '255.255.255.0'):
                    # print(d1_ip)
                    continue
                # print(devices[n1]['name'], d1_ip)
                for n4 in range(len(device_2_if)):
                    nnn += 1
                    d2_ip = device_2_if[n4].get('ipv4_address')
                    d2_subnet = device_2_if[n4].get('subnet')
                    if not d2_ip:
                        continue
                    # print(d2_ip, d1_ip_network)
                    if d2_ip in d1_ip_network:
                        graph[devices[n1]['name']].append(devices[n2]['name'])
                        stop_flag = True
                        break
                if stop_flag:
                    _d2_matrix['connected'] = True
                    break
            _matrix['connected'].append(_d2_matrix)
        matrix.append(_matrix)
    # print(nnn)
    # print(matrix)
    print(' ' * 10, end='')
    for m in matrix:
        print("[{:^10}]".format(m['name']), end='')
    print('')
    for m in matrix:
        print("{:10}".format(m['name']), end='')
        for conn in m['connected']:
            print("{:^12}".format(conn['connected']), end='')
        print('')
    # print(graph)
    topo_graph = Graph(graph)
    # print(topo_graph)
    # print(topo_graph.vertices())
    # print(topo_graph.edges())
    # path = topo_graph.find_all_paths("R4", "R1")
    # print(path)
    # path = topo_graph.find_path("R4", "R1")
    # print(path)
    return topo_graph

def get_neighbor():
    return run()

if __name__ == '__main__':
    run(exclude_ips=[('192.168.106.0', '255.255.255.0')])
