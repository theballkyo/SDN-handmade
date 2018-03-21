import pprint

import logbug
from generate_graph import get_all_subnet
from tools import PathFinder
from repository import get_service
import netaddr


def main():
    tsv = get_service('topology')
    topo_path_sv = get_service('topology_path')
    subnets = get_all_subnet()
    # pprint.pprint(subnets)
    path_finder = PathFinder(auto_update_graph=False)
    all_paths = set()
    subnet_list = list(subnets.values())
    i = 1
    print(len(subnet_list))
    subnets_info = []

    for subnet in range(len(subnets.values()) - 1):
        for subnet2 in range(1, len(subnets.values())):
            # If same IP Address. Skip
            if subnet_list[subnet]['node'] == subnet_list[subnet2]['node']:
                continue

            # Create IPAddress object
            subnet_1 = netaddr.IPAddress(subnet_list[subnet]['node'])
            subnet_2 = netaddr.IPAddress(subnet_list[subnet2]['node'])

            # Sort, From subnet must be less than To subnet
            if subnet_1 > subnet_2:
                subnet_1, subnet_2 = subnet_2, subnet_1

            # Find all paths
            paths = path_finder.all_by_manage_ip(subnet_list[subnet]['node'], subnet_list[subnet2]['node'])

            # Create subnet info for add to DB
            subnet_info = {
                'from_subnet': str(subnet_1),
                'to_subnet': str(subnet_2),
                'paths': paths
            }
            # Add to subnets_info list
            subnets_info.append(subnet_info)

            # Todo ...
            for path in paths:
                path_tuple = tuple(path)
                # print("From {} to {} <=> {}".format(subnet['node'], subnet2['node'], path_tuple))
                all_paths.add(path_tuple)

            i += 1

    # Insert into DB
    # tsv.add_subnet_to_subnet_bulk(subnets_info)
    #
    # topo_path_sv.insert_new_paths(all_paths)
    # _path = ['192.168.1.1', '192.168.1.2', '192.168.1.6', '192.168.1.10', '192.168.1.13']

    paths = path_finder.all_by_manage_ip('192.168.1.1', '192.168.1.13')
    path__ = {}
    for _path in paths:
        _all_path = []
        for i in range(len(_path) - 1):
            edge = path_finder.graph.edges[(_path[i], _path[i + 1])]

            # Initial first hop
            if len(_all_path) == 0:
                for link_id, link_data in edge['links'].items():
                    _all_path.append([{
                        'src_node_ip': link_data['src_node_ip'],
                        'src_ip': link_data['src_ip'],
                        'dst_node_ip': link_data['dst_node_ip'],
                        'dst_ip': link_data['dst_ip']
                    }])
                continue

            index = 0
            for p in _all_path.copy():
                _p = p.copy()
                n = 0
                for link_id, link_data in edge['links'].items():
                    if n > 0:
                        _all_path.append(_p + [{
                            'src_node_ip': link_data['src_node_ip'],
                            'src_ip': link_data['src_ip'],
                            'dst_node_ip': link_data['dst_node_ip'],
                            'dst_ip': link_data['dst_ip']
                        }])
                    else:
                        _all_path[index] += [{
                            'src_node_ip': link_data['src_node_ip'],
                            'src_ip': link_data['src_ip'],
                            'dst_node_ip': link_data['dst_node_ip'],
                            'dst_ip': link_data['dst_ip']
                        }]
                    n += 1
                index += 1

        print(_all_path)
        path_key = "{},{}".format(_path[0].replace('.', '-'), _path[-1].replace('.', '-'))
        if path__.get(path_key) is not None:
            path__[path_key] += _all_path
        else:
            path__[path_key] = _all_path

    pprint.pprint(path__, width=200)
    print("Total paths: {}, {}".format(len(all_paths), i))


if __name__ == '__main__':
    logbug.init()
    main()
