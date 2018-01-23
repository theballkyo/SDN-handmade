from helpers.path import PathFinder
import pprint
import logging
import timeit


def main():
    path_finder = PathFinder(auto_update_graph=True)
    # pprint.pprint(path_finder.graph)
    path1 = path_finder.all_by_manage_ip("192.168.1.1", "192.168.1.10")
    pprint.pprint(list(path1))
    path2 = path_finder.shortest_by_manage_ip("192.168.1.1", "192.168.1.10")
    pprint.pprint(list(path2))
    # path_finder.plot()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    usage_time = timeit.timeit(main, number=1)
    print(usage_time)
