import gen_nb
import services
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PIL import Image
import time
import netaddr


class PathFinder:
    def __init__(self, auto_update_graph=True):
        # Create NetworkX graph
        self.graph = None
        self.update_graph()

        # If true.
        # It automatically update graph when get a path
        self.auto_update_graph = auto_update_graph

    def update_graph(self):
        """ Use for update NetworkX graph object
        """
        devices = services.device_service.get_all()
        # print(services.device_service.get_active().count())
        self.graph = gen_nb.create_networkx_graph(devices)

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

    def all_by_manage_ip(self, src_ip, dst_ip):
        """
        Find best path by management IP
        :param src_ip:
        :param dst_ip:
        :return:
        """
        if self.auto_update_graph:
            self.update_graph()

        return nx.all_simple_paths(self.graph, src_ip, dst_ip)

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
            nx.draw_networkx_edge_labels(self.graph)

        # nx.draw_circular(self.graph, with_labels=True)
        nx.draw(self.graph, pos=layouts[layout](self.graph), with_labels=True)
        plt.savefig(filename)
        print("Saved file to: {}".format(filename))
