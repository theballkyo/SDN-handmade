import gen_nb
import services
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PIL import Image
import time


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

    def active_by_manage_ip(self, src_ip, dst_ip):
        if self.auto_update_graph:
            self.update_graph()

        raise NotImplementedError()

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
