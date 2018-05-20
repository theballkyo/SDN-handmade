import logging
import time

import matplotlib.pyplot as plt
import netaddr
import networkx as nx

import generate_graph
import repository
import sdn_utils
import traceback

from enum import Enum, unique


class PathFinder:
    @unique
    class SelectBy(Enum):
        LOWEST = 0
        HIGHEST = 1

    @unique
    class LinkSide(Enum):
        IN = 0
        OUT = 1
        LOWEST = 2
        HIGHEST = 3

    def __init__(self, auto_update_graph=True):
        # If true.
        # It automatically update graph when get a path
        self.auto_update_graph = auto_update_graph

        # Cache Simple path
        self._all_simple_paths = {}
        # Cache link information
        self.link_cache = {}

        self.device_repository = repository.get("device")
        self.copied_route_repository = repository.get('copied_route')

        # Create NetworkX graph
        self.graph = None
        self.update_graph()

    def update_graph(self):
        """ Use for update NetworkX graph object
        """
        devices = self.device_repository.get_all()
        # print(services.device_service.get_active().count())
        try:
            self.graph = generate_graph.create_networkx_graph(devices)
            self._all_simple_paths = {}
            self.link_cache = {}
        except (ValueError, KeyError) as e:
            # Create empty graph
            logging.error(traceback.format_exc())
            self.graph = nx.Graph()

    def active_by_subnet(self, src_subnet, dst_subnet):
        if self.auto_update_graph:
            self.update_graph()

        raise NotImplementedError()

    # def get_management_ip(self, ip):
    #
    #     management_ip = ''
    #     return management_ip

    def active_by_manage_ip(self, src_ip, dst_ip, prev_path=None, path=None):
        # if self.auto_update_graph:
        #     self.update_graph()
        if prev_path is None:
            prev_path = []
        if path is None:
            path = set()
        dst_ip = netaddr.IPAddress(dst_ip)
        start_device_ip = src_ip
        _device_id = self.device_repository.get_device_by_mgmt_ip(start_device_ip)

        # Todo Check route from route-map
        """
        other    (1), -- not specified by this MIB
        reject   (2), -- route which discards traffic
        local    (3), -- local interface
        remote   (4)  -- remote destination
        """
        routes = self.copied_route_repository.model.find({
            'type': 4,
            # 'type': {
            #     '$ne':
            # }
            'device_id': _device_id['_id'],
            'start_ip': {
                '$lte': dst_ip.value  # Using IP integer format
            },
            'end_ip': {
                '$gte': dst_ip.value  # Using IP integer format
            }
        })

        if routes.count() == 0:
            # print('END 1', end='')
            final_path = prev_path + [start_device_ip]
            if start_device_ip != str(dst_ip):
                final_path.append(str(dst_ip))
            path.add(tuple(final_path))
            if len(prev_path) == 0:
                return path
            return
        bbb = start_device_ip
        for route in routes:
            next_hop = route['next_hop']
            if next_hop == '0.0.0.0':
                # print(">>>", prev_path + [start_device_ip])
                final_path = prev_path + [start_device_ip]
                if start_device_ip != str(dst_ip):
                    final_path.append(str(dst_ip))
                if len(prev_path) == 0:
                    path.add(tuple([src_ip, str(dst_ip)]))
                    return path
                path.add(tuple(final_path))
                return
            next_hop_device = self.device_repository.model.find_one({
                'interfaces.ipv4_address': next_hop
            })
            if next_hop_device is None:
                # TODO not find device
                return ''
            start_device_ip = next_hop_device['management_ip']
            prev_path.append(bbb)
            self.active_by_manage_ip(start_device_ip, str(dst_ip), prev_path, path)
            # Reset prev path
            prev_path = []
        return path

    def shortest_by_manage_ip(self, src_ip, dst_ip):
        if self.auto_update_graph:
            self.update_graph()

        path = nx.shortest_path(self.graph, src_ip, dst_ip)
        return path

    def _by_speed(self, src_ip, dst_ip, select_by):
        """
        Find path(s) is interface speed by selector lowest or highest
        :param src_ip:
        :param dst_ip:
        :return:
        """
        if select_by not in self.SelectBy:
            logging.warning("select_by arg not in choices")
            return []
        all_paths = self.all_by_manage_ip(src_ip, dst_ip)
        paths = []
        last_bandwidth = None
        for path in all_paths:
            path_bandwidth = None
            for i in range(len(path) - 1):
                try:
                    edge = self.graph.edges[(path[i], path[i + 1])]
                    for _, link in edge['links'].items():
                        if path_bandwidth is None:
                            path_bandwidth = link['link_min_speed']
                        path_bandwidth = min(path_bandwidth, link['link_min_speed'])
                except ValueError:
                    pass
            if last_bandwidth is None:
                last_bandwidth = path_bandwidth
            logging.debug("Path bandwidth: [%d], Last bandwidth: [%d]", path_bandwidth, last_bandwidth)

            if path_bandwidth > last_bandwidth:
                # Find new higher bandwidth. Clear old paths
                if select_by == self.SelectBy.HIGHEST:
                    paths = list()
                    paths.append(path)
                    last_bandwidth = path_bandwidth
            elif path_bandwidth < last_bandwidth:
                if select_by == self.SelectBy.LOWEST:
                    paths = list()
                    paths.append(path)
                    last_bandwidth = path_bandwidth
            else:
                paths.append(path)

        return paths

    def highest_speed(self, src_ip, dst_ip):
        return self._by_speed(src_ip, dst_ip, self.SelectBy.LOWEST)

    def lowest_speed(self, src_ip, dst_ip):
        return self._by_speed(src_ip, dst_ip, self.SelectBy.HIGHEST)

    def all_by_manage_ip(self, src_ip, dst_ip):
        """
        Find best path by management IP
        :param src_ip:
        :param dst_ip:
        :return:
        """
        if self.auto_update_graph:
            self.update_graph()
        # print(self._all_simple_paths)
        if not self._all_simple_paths.get(src_ip + dst_ip, False):
            self._all_simple_paths[src_ip + dst_ip] = list(nx.all_simple_paths(self.graph, src_ip, dst_ip))
        # print(self._all_simple_paths[src_ip + dst_ip])
        return self._all_simple_paths[src_ip + dst_ip][:]
        # print(list(nx.all_simple_paths(self.graph, src_ip, dst_ip)))
        # return nx.all_simple_paths(self.graph, src_ip, dst_ip)

    def find_by_available_bandwidth(self, src_ip, dst_ip, select_by, min_available_bw=None):
        """
        Find path(s) is interface speed by selector lowest or highest
        :param src_ip:
        :param dst_ip:
        :param select_by:
        :param min_available_bw: Minimum bandwidth in bit
        :return:
        """
        if select_by not in self.SelectBy:
            logging.error("select_by arg not in choices")
            return []

        src_ip = self.get_management_ip(src_ip)
        dst_ip = self.get_management_ip(dst_ip)

        all_paths = self.all_by_manage_ip(src_ip, dst_ip)
        paths = []
        last_bandwidth = None
        for path in all_paths:
            path_available_bandwidth = None
            path_link = []
            for i in range(len(path) - 1):
                try:
                    edge = self.graph.edges[(path[i], path[i + 1])]
                    # Check is exist in link_cache
                    for link_id, link_data in edge['links'].items():
                        link = self.get_link(link_id, link_data)

                        # IN  link == Interface is receive a packet
                        # OUT link == Interface is send a packet

                        if link['src']['management_ip'] == path[i]:
                            out_if = link['src']['interfaces'][0]
                            in_if = link['dst']['interfaces'][0]
                        else:
                            out_if = link['dst']['interfaces'][0]
                            in_if = link['src']['interfaces'][0]

                        l_src_if = link['src']['interfaces'][0]
                        l_dsr_if = link['dst']['interfaces'][0]

                        link_speed = min(l_src_if['speed'], l_dsr_if['speed'])
                        out_usage = max(l_src_if['bw_out_usage_percent'], l_dsr_if['bw_in_usage_percent'])
                        in_usage = max(l_src_if['bw_in_usage_percent'], l_dsr_if['bw_out_usage_percent'])

                        out_available = link_speed - (out_usage / 100 * link_speed)
                        in_available = link_speed - (in_usage / 100 * in_usage)

                        bw_available = link_speed - ((out_usage + in_usage) / 100 * link_speed)

                        # out_available = min(out_if['speed'], ou) - (out_if['bw_out_usage_percent'] / 100 * out_if['speed'])
                        # in_available = in_if['speed'] - (in_if['bw_in_usage_percent'] / 100 * in_if['speed'])
                        # logging.debug("%.2f, %.2f, %.2f, %.2f, %.2f, %.2f",
                        #               out_if['bw_in_usage_percent'],
                        #               out_if['bw_out_usage_percent'],
                        #               in_if['bw_in_usage_percent'],
                        #               in_if['bw_out_usage_percent'],
                        #               in_available,
                        #               out_available)
                        # this_path_bandwidth = min(in_available, out_available)

                        this_path_bandwidth = bw_available

                        if path_available_bandwidth is None:
                            path_available_bandwidth = this_path_bandwidth
                        else:
                            path_available_bandwidth = min(path_available_bandwidth, this_path_bandwidth)

                        # Path is [node1, node2, node3, ...]
                        path_link.append({
                            'out': out_if,  # Left node <node1>, <node2>
                            'in': in_if  # Right node <node2>, <node3>
                        })

                except ValueError:
                    pass
            if last_bandwidth is None:
                last_bandwidth = path_available_bandwidth
            logging.debug(
                "Path {} available bandwidth is {:.2f}, {:.2f}".format(path, path_available_bandwidth, last_bandwidth))

            if min_available_bw:
                # Check Path bandwidth is higher than min available bandwidth is user request
                if path_available_bandwidth < min_available_bw:
                    last_bandwidth = None
                    continue

            if path_available_bandwidth > last_bandwidth:
                # Find new higher bandwidth. Clear old paths
                if select_by == self.SelectBy.HIGHEST:
                    paths = list()
                    paths.append({
                        'path': path,
                        'path_link': path_link,
                        'available_bandwidth': path_available_bandwidth
                    })
                    last_bandwidth = path_available_bandwidth
            elif path_available_bandwidth < last_bandwidth:
                if select_by == self.SelectBy.LOWEST:
                    paths = list()
                    paths.append({
                        'path': path,
                        'path_link': path_link,
                        'available_bandwidth': path_available_bandwidth
                    })
                    last_bandwidth = path_available_bandwidth
            else:
                paths.append({
                    'path': path,
                    'path_link': path_link,
                    'available_bandwidth': path_available_bandwidth
                })

        return paths

    def get_link_by_ip(self, ip1, ip2, force_update=False):
        ip1 = netaddr.IPAddress(ip1)
        ip2 = netaddr.IPAddress(ip2)
        edge = self.graph

    def get_link(self, link_id, link_data, force_update=False):
        link = self.link_cache.get(link_id)
        if not link or force_update:
            links = self.device_repository.model.find({
                'interfaces.ipv4_address': {
                    '$in': [
                        link_data['src_ip'], link_data['dst_ip']
                    ]
                }
            }, {
                'management_ip': 1,
                'interfaces.$1': 1
            })

            for _link in links:
                if _link['interfaces'][0]['ipv4_address'] == link_data['src_ip']:
                    src_link = _link
                else:
                    dst_link = _link

            # Cache link
            link = {
                'src': src_link,
                'dst': dst_link
            }
            self.link_cache[link_id] = link

        return link

    def get_links(self):
        _links = []
        for u, v, links in self.graph.edges.data('links'):
            if links is not None:
                for link_id, link_data in links.items():
                    link = self.get_link(link_id, link_data, True)
                    _links.append(link)

        return _links

    def get_management_ip(self, ip):
        device = self.device_repository.find_by_if_ip(ip)
        if device is None:
            return None
        return device['management_ip']

    def simulate_route(self, include_pending=False):
        """
        Step 1 Find in policy
             1.1 if include pending, find in policy pending first
             1.2 if not in policy pending, find in policy
        Step 2 if not in policy, find in route table
        Step 3 if not in route, return
        :param include_pending:
        :return:
        """
        raise NotImplementedError

    def plot(self):
        if self.auto_update_graph:
            self.update_graph()
        # plt.rcParams["figure.figsize"] = [30, 30]
        nx.draw_networkx_edge_labels(self.graph, pos=nx.spring_layout(self.graph))
        nx.draw_circular(self.graph, with_labels=True)
        # plt.plot()
        plt.show()

    def save_graph_img(self, filename=None, figsize=(15, 15), labels=False, layout='kamada_kawai'):
        if not filename:
            filename = "imgs/topo-{}.png".format(time.time())

        layouts = {
            'kamada_kawai': nx.kamada_kawai_layout,
            'circular': nx.circular_layout,
            'spectral': nx.spectral_layout,
            'spring': nx.spring_layout
        }

        if layout not in layouts.keys():
            print("Can't not find layout name: {}".format(layout))
            return

        # Set fig size
        plt.rcParams["figure.figsize"] = figsize
        # Include edge labels
        if labels:
            nx.draw_networkx_edge_labels(self.graph, pos=layouts[layout](self.graph))

        # nx.draw_circular(self.graph, with_labels=True)
        nx.draw(self.graph, pos=layouts[layout](self.graph), with_labels=True)
        plt.savefig(filename)
        print("Saved file to: {}".format(filename))
