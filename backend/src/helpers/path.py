import gen_nb
import services
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PIL import Image
import time


class FindPath:
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
        devices = services.device_service.get_active()
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

        raise NotImplementedError()

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

        print(self.graph)
