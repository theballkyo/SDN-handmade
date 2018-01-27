import matplotlib
import networkx as nx

matplotlib.use('Agg')


def main():
    from helpers.path_finder import PathFinder
    import pprint
    import services

    device_service = services.get_service("device")
    device_service.get_active()

    device_service.device.find({})

    route_service = services.get_service("route")
    route_service.route.find()

    path_finder = PathFinder(auto_update_graph=False)

    print(path_finder.graph.edges["192.168.1.2", "192.168.1.1"])
    # pprint.pprint(path_finder.graph)
    path1 = path_finder.all_by_manage_ip("192.168.1.1", "192.168.1.10")
    print("List 1")
    pprint.pprint(list(path1))

    print("=" * 100)
    path2 = path_finder.shortest_by_manage_ip("192.168.1.1", "192.168.1.10")
    print("List 2")
    pprint.pprint(list(path2))

    # path_finder.plot()
    # path_finder.save_graph_img()

    print("=" * 100)
    print("Active path: 192.168.1.1 to 10.0.1.2")
    path3 = path_finder.active_by_manage_ip('192.168.1.1', '10.0.1.2')
    pprint.pprint(path3)
    for path in map(nx.utils.pairwise, path3):
        for pp in path:
            try:
                edge = path_finder.graph.edges[pp]
                print(edge)
            except KeyError:
                continue

    print("=" * 100)
    print("Active path: 192.168.1.1 to 192.168.1.10")
    path4 = path_finder.active_by_manage_ip('192.168.1.1', '192.168.1.10')
    pprint.pprint(path4)

    for path in map(nx.utils.pairwise, path4):
        for pp in path:
            print(path_finder.graph.edges[pp])


if __name__ == '__main__':
    import logging
    import timeit

    logging.basicConfig(level=logging.INFO)
    usage_time = timeit.timeit(main, number=1)
    print("Usage time: {:.3f}".format(usage_time))
