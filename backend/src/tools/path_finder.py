import generate_graph
import services
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PIL import Image
import time
import netaddr
import logging
import pprint


class PathFinder:
    LOWEST = 'lo'
    HIGHEST = 'hi'

    SELECT_BY_CHOICES = (
        LOWEST,
        HIGHEST
    )

    BW_TYPE_IN = 'bw_in'
    BW_TYPE_OUT = 'bw_out'
    BW_TYPE_LOWEST = 'bw_lowest'  # Select type is lower
    BW_TYPE_HIGHEST = 'bw_highest'  # Select type is higher
    BW_TYPE_CHOICES = (
        BW_TYPE_IN,
        BW_TYPE_OUT,
        BW_TYPE_LOWEST,
        BW_TYPE_HIGHEST
    )

    def __init__(self, auto_update_graph=True):
        # Create NetworkX graph
        self.graph = None
        self.update_graph()

        # If true.
        # It automatically update graph when get a path
        self.auto_update_graph = auto_update_graph

        # Cache Simple path
        self._all_simple_paths = {}
        # Cache link information
        self.link_cache = {}

    def update_graph(self):
        """ Use for update NetworkX graph object
        """
        devices = services.device_service.get_all()
        # print(services.device_service.get_active().count())
        try:
            self.graph = generate_graph.create_networkx_graph(devices)
            self._all_simple_paths = {}
            self.link_cache = {}
        except ValueError as e:
            # Create empty graph
            print(e)
            self.graph = nx.Graph()

    def active_by_subnet(self, src_subnet, dst_subnet):
        if self.auto_update_graph:
            self.update_graph()

        raise NotImplementedError()

    def active_by_manage_ip(self, src_ip, dst_ip, prev_path=None, path=None):
        # if self.auto_update_graph:
        #     self.update_graph()
        if prev_path is None:
            prev_path = []
        if path is None:
            path = set()
        dst_ip = netaddr.IPAddress(dst_ip)
        start_device_ip = src_ip

        routes = services.get_service('route').route.find({
            # 'type': 4,
            'device_ip': start_device_ip,
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
            return
        bbb = start_device_ip
        for route in routes:
            next_hop = route['next_hop']
            if next_hop == '0.0.0.0':
                # print(">>>", prev_path + [start_device_ip])
                final_path = prev_path + [start_device_ip]
                if start_device_ip != str(dst_ip):
                    final_path.append(str(dst_ip))
                path.add(tuple(final_path))
                return
            next_hop_device = services.get_service('device').device.find_one({
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
        if select_by not in self.SELECT_BY_CHOICES:
            logging.warning("select_by arg can be only {}".format(self.SELECT_BY_CHOICES))
            return []
        all_paths = self.all_by_manage_ip(src_ip, dst_ip)
        paths = []
        last_bandwidth = None
        for path in all_paths:
            path_bandwidth = None
            for i in range(len(path) - 1):
                try:
                    edge = self.graph.edges[(path[i], path[i + 1])]
                    if path_bandwidth is None:
                        path_bandwidth = edge['link_min_speed']
                    path_bandwidth = min(path_bandwidth, edge['link_min_speed'])
                except ValueError:
                    pass
            if last_bandwidth is None:
                last_bandwidth = path_bandwidth
            print(path_bandwidth, last_bandwidth)

            if path_bandwidth > last_bandwidth:
                # Find new higher bandwidth. Clear old paths
                if select_by == self.HIGHEST:
                    paths = list()
                    paths.append(path)
            elif path_bandwidth < last_bandwidth:
                if select_by == self.LOWEST:
                    paths = list()
                    paths.append(path)
            else:
                paths.append(path)

            last_bandwidth = path_bandwidth
        return paths

    def highest_speed(self, src_ip, dst_ip):
        return self._by_speed(src_ip, dst_ip, self.LOWEST)

    def lowest_speed(self, src_ip, dst_ip):
        return self._by_speed(src_ip, dst_ip, self.HIGHEST)

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

    def find_by_available_bandwidth(self, src_ip, dst_ip, select_by, bw_type):
        """
        Find path(s) is interface speed by selector lowest or highest
        :param src_ip:
        :param dst_ip:
        :return:
        """
        if select_by not in self.SELECT_BY_CHOICES:
            logging.warning("select_by arg can be only {}".format(self.SELECT_BY_CHOICES))
            return []

        if bw_type not in self.BW_TYPE_CHOICES:
            logging.warning("bw_type arg can be only {}".format(self.SELECT_BY_CHOICES))
            return []

        device_service = services.get_service("device")
        all_paths = self.all_by_manage_ip(src_ip, dst_ip)
        paths = []
        last_bandwidth = None
        for path in all_paths:
            path_bandwidth = None
            for i in range(len(path) - 1):
                try:
                    edge = self.graph.edges[(path[i], path[i + 1])]
                    # Check is exist in link_cache
                    link = self.link_cache.get(edge['src_ip'])
                    if not link:
                        link = device_service.device.aggregate([
                            {
                                '$match': {
                                    "interfaces.ipv4_address": edge['src_ip']
                                }
                            },
                            {
                                '$project': {
                                    'interfaces': {
                                        '$filter': {
                                            'input': "$interfaces",
                                            'as': 'interface',
                                            'cond': {
                                                '$or': [
                                                    {'$eq': ["$$interface.ipv4_address", edge['src_ip']]}
                                                ]
                                            }
                                        }
                                    }
                                }
                            }
                        ])

                        link = list(link)
                        # Cache link
                        self.link_cache[edge['src_ip']] = link

                    # Clone list object before use
                    link = link[:]
                    # pprint.pprint(link)
                    link_if = link[0]['interfaces'][0]
                    in_bw = link_if['bw_in_usage_percent'] * link_if['speed']
                    out_bw = link_if['bw_out_usage_percent'] * link_if['speed']

                    if path_bandwidth is None:
                        path_bandwidth = link_if['speed'] - in_bw

                    if bw_type == self.BW_TYPE_IN:
                        bw = in_bw
                    elif bw_type == self.BW_TYPE_OUT:
                        bw = out_bw
                    elif bw_type == self.BW_TYPE_HIGHEST:
                        # Select type is available is higher
                        bw = min(in_bw, out_bw)
                    elif bw_type == self.BW_TYPE_LOWEST:
                        # Select type is available is lower
                        bw = max(in_bw, out_bw)

                    logging.debug((link_if['speed'] - in_bw, link_if['speed'] - out_bw, link_if['speed'] - bw))
                    path_bandwidth = min(path_bandwidth, link_if['speed'] - bw)
                except ValueError:
                    pass
            if last_bandwidth is None:
                last_bandwidth = path_bandwidth

            if path_bandwidth > last_bandwidth:
                # Find new higher bandwidth. Clear old paths
                if select_by == self.HIGHEST:
                    paths = list()
                    paths.append(path)
            elif path_bandwidth < last_bandwidth:
                if select_by == self.LOWEST:
                    paths = list()
                    paths.append(path)
            else:
                paths.append(path)

            last_bandwidth = path_bandwidth
        return paths

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
