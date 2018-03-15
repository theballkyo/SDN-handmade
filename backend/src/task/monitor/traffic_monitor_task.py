import datetime
import logging
import time

from service import get_service, PolicyRoute
from tools import PathFinder


class TrafficMonitorTask:
    def __init__(self):
        self.device_service = get_service('device')
        self.netflow_service = get_service('netflow')
        self.route_service = get_service('route')
        self.link_service = get_service('link')
        self.policy_service = get_service('policy')
        self.last_run = 0
        self.delay = 15
        self.path_finder = PathFinder(auto_update_graph=False)
        self.use_port = False
        self.active_paths = []

        self.current_flow = None

    def check_before_run(self):
        if time.time() > self.last_run + self.delay:
            return True
        return False

    def run(self):
        print("Running...")
        if not self.check_before_run():
            return

        # Update graph in path finder
        # self.path_finder.update_graph()

        # for link in self.path_finder.get_links():
        #     src = link['src']
        #     a1 = sdn_utils.bandwidth_usage_percent_to_bit(src['interfaces'][0]['speed'],
        #                                                   src['interfaces'][0]['bw_in_usage_percent'])
        #     b1 = sdn_utils.bandwidth_usage_percent_to_bit(src['interfaces'][0]['speed'],
        #                                                   src['interfaces'][0]['bw_out_usage_percent'])
        #     dst = link['dst']
        #     a2 = sdn_utils.bandwidth_usage_percent_to_bit(dst['interfaces'][0]['speed'],
        #                                                   dst['interfaces'][0]['bw_in_usage_percent'])
        #     b2 = sdn_utils.bandwidth_usage_percent_to_bit(dst['interfaces'][0]['speed'],
        #                                                   dst['interfaces'][0]['bw_out_usage_percent'])
        #     link_speed = min(src['interfaces'][0]['speed'], dst['interfaces'][0]['speed'])
        #
        #     utilize = max(a1 + b1, a2 + b2)
        #
        #     free_utilize = link_speed - utilize
        #     print(link_speed, utilize, free_utilize)
        #     if free_utilize < link_speed * (85 / 100):
        #         print("...")

        devices = self.device_service.get_by_if_utilization(85, 'in')
        # print(list(devices))
        # if not devices:
        #     return

        for device in devices:
            for interface in device['interfaces']:
                # Todo add support multiple link
                src_if_ip = interface['ipv4_address']
                src_if_index = interface['index']
                src_node_ip = device['management_ip']

                # Todo Getting flow
                if not self.use_port:
                    group_by = ('ipv4_src_addr', 'ipv4_dst_addr', 'input_snmp')
                else:
                    group_by = ()

                extra_match = {
                    'device_ip': device['management_ip'],
                    'direction': 0,  # Ingress
                    'input_snmp': src_if_index
                    # 'input_snmp': interface['index']
                }

                flows = self.netflow_service.get_ingress_flow(
                    datetime.datetime(2018, 2, 27, 11, 20) - datetime.timedelta(minutes=5),
                    datetime.datetime(2018, 2, 27, 11, 20),
                    limit=10,  # Top 10 flows
                    group_by=group_by,
                    extra_match=extra_match
                )

                for flow in flows:
                    src_flow = flow['data'][0]['_id']['ipv4_src_addr']
                    dst_flow = flow['data'][0]['_id']['ipv4_dst_addr']

                    # TODO Check in policy route

                    src_node_ips = self.route_service.get_management_ip_from_host_ip(src_flow)
                    dst_node_ips = self.route_service.get_management_ip_from_host_ip(dst_flow)
                    self.active_paths = []
                    for _src_node_ip in src_node_ips:
                        for dst_node_ip in dst_node_ips:
                            active_path = self.path_finder.active_by_manage_ip(_src_node_ip, dst_node_ip)
                            # logging.debug("%s", active_path)
                            self.active_paths.append(active_path)
                    print(self.active_paths)
                    self.current_flow = flow
                    new_path = self.find_available_path(src_node_ip, dst_node_ips, None, first=True)
                    if not new_path:
                        logging.debug("No new path")
                        continue
                    else:
                        logging.debug("New path is: %s", new_path['path'])

                    # Update path
                    # Create a new policy
                    policy_route = PolicyRoute()
                    policy_route.set_policy(src_network=src_flow, dst_network=dst_flow)
                    for hop in range(len(new_path['path_link'])):
                        logging.debug("Node: %s <=> Exit-IF: %s, Next-hop: %s",
                                      new_path['path'][hop],
                                      new_path['path_link'][hop]['out']['index'],
                                      new_path['path_link'][hop]['in']['ipv4_address'])
                        policy_route.add_action(
                            new_path['path'][hop],
                            'next-hop',
                            new_path['path_link'][hop]['in']['ipv4_address'])
                    policy = policy_route.get_policy()
                    self.policy_service.add_new_pending_policy(policy)

        #         # Todo Select path
        #         for path in paths:
        #             pass
        #
        #         # Todo Update path

        self.last_run = time.time()

    def find_available_path(self, src_node_ip, dst_node_ips, src_if_ip=None, first=False):
        # Todo Getting available paths
        src_flow = self.current_flow['data'][0]['_id']['ipv4_src_addr']
        dst_flow = self.current_flow['data'][0]['_id']['ipv4_dst_addr']

        # Finding path
        if not first:
            from_flows = self.netflow_service.netflow.find_one({
                'ipv4_src_addr': src_flow,
                'ipv4_dst_addr': dst_flow,
                # 'output_snmp': output_index
            })
            logging.debug("%s", from_flows)
            for dst_node_ip in dst_node_ips:
                paths = self.path_finder.find_by_available_bandwidth(
                    src_node_ip,
                    dst_node_ip,
                    PathFinder.SelectBy.HIGHEST,
                    self.current_flow['data'][0]['total_in_bytes']
                )
                for path in paths:
                    # Source is R3
                    #  Active => [R1, R2, R3, R4, R5]
                    #  New    => [R3, R2, R1, ...] X
                    #  New2   => [R3, R6, ...] Y
                    #
                    #  Check loop
                    for active_path in self.active_paths:
                        for _active_path in active_path:
                            before_node = _active_path[list(_active_path).index(src_node_ip) - 1]
                            logging.debug("before_node: %s", before_node)
                            # logging.debug("Path: %s", path)
                            logging.debug("src node ip: %s <=> Active path is %s", src_node_ip, _active_path)
                            if path['path'][1] == before_node:
                                continue
                            else:
                                logging.debug("Found path: %s", path['path'])
                                return path
                        pass
                    # TODO Return path
                    # return None

        # If can't find a new path
        # Find neighbor link device
        if src_if_ip is None:
            node_ips = self.find_neighbor(src_node_ip, src_flow, dst_flow)
            # logging.debug(node_ips)
        else:
            node_ips = (node_ip for node_ip in src_if_ip)

        for node_ip in node_ips:
            # Find path from prevent path of active flow
            new_path = self.find_available_path(node_ip, dst_node_ips)
            # If found new path
            if new_path:
                return new_path
        return None

    def find_neighbor(self, src_node_ip, src_ip, dst_ip):
        logging.debug("Find neighbor: %s %s %s", src_node_ip, src_ip, dst_ip)
        # Find interfaces than receive this flow
        flow_from = self.netflow_service.netflow.aggregate([{
            '$match': {
                'ipv4_src_addr': src_ip,
                'ipv4_dst_addr': dst_ip,
                'device_ip': src_node_ip
            }
        }, {
            '$group': {
                '_id': {
                    'input_snmp': '$input_snmp'
                },
                'total_in_bytes': {'$sum': '$in_bytes'}
            }
        }])

        node_ips = []

        for _flow in flow_from:
            # TODO Improve performance
            # Get interface index
            src_if_index = _flow['_id']['input_snmp']
            # src_if_ip = self.device_service.get_if_ip_by_if_index(src_node_ip, src_if_index)
            # my_links = self.link_service.find_by_if_ip(src_if_ip)
            # Find links than connected
            my_links = self.link_service.find_by_if_index(src_node_ip, src_if_index)
            # Loop all links
            for link in my_links:
                # print(link)
                if link['src_node_ip'] == src_node_ip:
                    src_node_ip = link['dst_node_ip']
                else:
                    src_node_ip = link['src_node_ip']
                node_ips.append(src_node_ip)
        return node_ips
