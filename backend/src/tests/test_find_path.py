import matplotlib
import networkx as nx

matplotlib.use('Agg')


def main():
    path_finder = PathFinder(auto_update_graph=False)

    print(path_finder.graph.edges["192.168.1.2", "192.168.1.1"])
    # pprint.pprint(path_finder.graph)
    path1 = path_finder.all_by_manage_ip("192.168.1.1", "192.168.1.13")
    print("all_by_manage_ip 192.168.1.1 to 192.168.1.13")
    pprint.pprint(list(path1))

    print("=" * 100)
    path2 = path_finder.shortest_by_manage_ip("192.168.1.1", "192.168.1.13")
    print("shortest_by_manage_ip 192.168.1.1 to 192.168.1.13")
    pprint.pprint(list(path2))

    # path_finder.plot()
    # path_finder.save_graph_img()

    print("=" * 100)
    print("Active path: 192.168.1.1 to 192.168.1.13")
    path3 = path_finder.active_by_manage_ip('192.168.1.1', '192.168.1.13')
    pprint.pprint(path3)
    for path in map(nx.utils.pairwise, path3):
        for pp in path:
            try:
                edge = path_finder.graph.edges[pp]
                print(edge)
            except KeyError:
                continue

    print("=" * 100)
    print("Active path: 192.168.1.13 to 192.168.2.1")
    path4 = path_finder.active_by_manage_ip('192.168.1.13', '192.168.2.1')
    pprint.pprint(path4)

    for path in map(nx.utils.pairwise, path4):
        for pp in path:
            print(path_finder.graph.edges[pp])

    print("=" * 100)
    print("Active path: 192.168.1.1 to 192.168.2.3")
    path4 = path_finder.active_by_manage_ip('192.168.1.1', '192.168.2.3')
    pprint.pprint(path4)

    for path in map(nx.utils.pairwise, path4):
        for pp in path:
            print(path_finder.graph.edges[pp])

    print("=" * 100)
    print("highest speed path: 192.168.1.1 to 192.168.1.13")
    path5 = path_finder.highest_speed('192.168.1.1', '192.168.1.13')
    pprint.pprint(path5)

    print("=" * 100)
    print("lowest speed path: 192.168.1.1 to 192.168.1.13")
    path6 = path_finder.lowest_speed('192.168.1.1', '192.168.1.13')
    pprint.pprint(path6)

    print("=" * 100)
    print("find_by_available_bandwidth (highest, in): 192.168.1.1 to 192.168.1.13")
    path7 = path_finder.find_by_available_bandwidth(
        '192.168.1.1',
        '192.168.1.13',
        PathFinder.SelectBy.HIGHEST,
        PathFinder.LinkSide.IN
    )
    pprint.pprint(path7)

    print("=" * 100)
    print("find_by_available_bandwidth (highest, out): 192.168.1.1 to 192.168.1.13")
    path8 = path_finder.find_by_available_bandwidth(
        '192.168.1.1',
        '192.168.1.13',
        PathFinder.SelectBy.HIGHEST,
        PathFinder.LinkSide.OUT
    )
    pprint.pprint(path8)

    print("=" * 100)
    print("find_by_available_bandwidth (lowest, in): 192.168.1.1 to 192.168.1.13")
    path9 = path_finder.find_by_available_bandwidth(
        '192.168.1.1',
        '192.168.1.13',
        PathFinder.SelectBy.LOWEST,
        PathFinder.LinkSide.IN
    )
    pprint.pprint(path9)

    print("=" * 100)
    print("find_by_available_bandwidth (lowest, out): 192.168.1.1 to 192.168.1.13")
    path10 = path_finder.find_by_available_bandwidth(
        '192.168.1.1',
        '192.168.1.13',
        PathFinder.SelectBy.LOWEST,
        PathFinder.LinkSide.OUT
    )
    pprint.pprint(path10)

    print("=" * 100)
    print("find_by_available_bandwidth (lowest, lowest): 192.168.1.1 to 192.168.1.13")
    path11 = path_finder.find_by_available_bandwidth(
        '192.168.1.1',
        '192.168.1.13',
        PathFinder.SelectBy.LOWEST,
        PathFinder.LinkSide.LOWEST
    )
    pprint.pprint(path11)

    print("=" * 100)
    print("find_by_available_bandwidth (lowest, highest): 192.168.1.1 to 192.168.1.13")
    path12 = path_finder.find_by_available_bandwidth(
        '192.168.1.1',
        '192.168.1.13',
        PathFinder.SelectBy.LOWEST,
        PathFinder.LinkSide.HIGHEST
    )
    pprint.pprint(path12)

    # TODO highest bandwidth, lowest bandwidth [Ava, link]


if __name__ == '__main__':
    import logging
    import timeit
    from tools import PathFinder
    import pprint

    logging.basicConfig(level=logging.INFO)
    usage_time = timeit.timeit(main, number=1)
    print("Usage time: {:.3f}".format(usage_time))
