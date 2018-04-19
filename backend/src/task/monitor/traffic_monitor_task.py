import datetime
import logging
import time

import sdn_utils
from repository import get_service, PolicyRoute
from tools import PathFinder
from snmp.snmp_force_process import force_update_interface

class TrafficMonitorTask:
    def __init__(self):
        self.device_service = get_service('device')
        self.netflow_service = get_service('netflow')
        self.route_service = get_service('route')
        self.link_service = get_service('link')
        self.policy_service = get_service('policy')
        self.last_run = 0
        self.delay = 1
        self.path_finder = PathFinder(auto_update_graph=False)
        self.use_port = False
        self.active_paths = []
        self.utilize = 85

        self.reverse_path = []
        self.reverse_path_link = []

        self.current_flow = None

        self.explorer_neighbor = []

    def check_before_run(self):
        if time.time() > self.last_run + self.delay:
            return True
        return False

    def run(self, ssh_connection=None):
        if not self.check_before_run():
            return

        logging.debug("Traffic monitor task is running...")
        # Update path
        self.path_finder.update_graph()

        datetime_now = datetime.datetime.now()

        devices = self.device_service.get_by_if_utilization(self.utilize, 'in')

        for device in devices:
            for interface in device['interfaces']:
                if not interface.get('ipv4_address') or interface.get('bw_in_usage_percent') <= self.utilize:
                    continue
                # Todo add support multiple link
                src_if_ip = interface['ipv4_address']
                src_if_index = interface['index']
                src_node_ip = device['management_ip']

                # Todo checking policy pending
                pending_policy_set = self.policy_service.sum_bytes_pending_has_pass_interface(src_if_ip)
                pending_policy_set = list(pending_policy_set)
                if pending_policy_set:
                    logging.debug("Found Pending policy: %s", pending_policy_set)
                    if pending_policy_set:
                        total = pending_policy_set[0]
                        new_utilize = interface['bw_in_usage_persec'] - total['total']
                        new_utilize_percent = sdn_utils.fraction_to_percent(new_utilize, interface['speed'])
                        if new_utilize_percent < self.utilize:
                            continue

                # Not used this
                # Get last update flow time
                # last_policy = self.policy_service.get_last_policy_apply(device['management_ip'], projection={
                #     'created_at': 1
                # })
                # if last_policy and last_policy['created_at'] + datetime.timedelta(
                #         seconds=self.delay) > datetime.datetime.now():
                #     continue

                # Use this inside
                # currently interface utilize - In policy flow utilize
                in_use_policy = self.policy_service.policy.aggregate([
                    {
                        '$match': {
                            "info.submit_from.device_ip": device['management_ip'],
                            "info.old_path_link.in": src_if_ip
                        }
                    },
                    {
                        '$group': {
                            '_id': None,
                            'total_in_bytes': {
                                '$sum': '$info.in_bytes_per_sec'
                            }
                        }
                    },
                    {
                        '$project': {
                            '_id': 0,
                            'total_in_bytes': 1
                        }
                    }
                ])

                in_use_policy = list(in_use_policy)

                # if len(in_use_policy) > 0:
                #
                #     in_use_policy = in_use_policy[0]
                #
                #     in_policy_utilize = sdn_utils.fraction_to_percent(in_use_policy['total_in_bytes'], interface['speed'])
                #
                #     if interface['bw_in_usage_percent'] - in_policy_utilize < self.utilize:
                #         continue

                # Getting flows
                # Todo Change query to new calculation
                in_policies = self.policy_service.policy.find({
                    "info.old_path": device['management_ip']
                }, {
                    'src_ip': 1,
                    'dst_ip': 1
                })
                not_in = {'src_ip': [], 'dst_ip': []}
                for in_policy in in_policies:
                    not_in['src_ip'].append(in_policy['src_ip'])
                    not_in['dst_ip'].append(in_policy['dst_ip'])

                # Todo support port, protocol
                flows = self.netflow_service.summary_flow_v2(
                    device['management_ip'],
                    not_in=not_in  # Exclude flow is already change route
                )

                for flow in flows:
                    # src_flow = flow['data'][0]['_id']['ipv4_src_addr']
                    # dst_flow = flow['data'][0]['_id']['ipv4_dst_addr']

                    src_flow = flow['_id']['ipv4_src_addr']
                    dst_flow = flow['_id']['ipv4_dst_addr']

                    if dst_flow == '255.255.255.255':
                        continue

                    # TODO Check in policy route

                    flow_src_node_ips = self.route_service.get_management_ip_from_host_ip(src_flow)
                    flow_dst_node_ips = self.route_service.get_management_ip_from_host_ip(dst_flow)

                    # Getting all active path
                    self.active_paths = []
                    for flow_src_node_ip in flow_src_node_ips:
                        for flow_dst_node_ip in flow_dst_node_ips:
                            active_path = self.path_finder.active_by_manage_ip(flow_src_node_ip, flow_dst_node_ip)
                            # logging.debug("%s", active_path)
                            self.active_paths.append(active_path)
                    logging.debug("Active paths: %s", self.active_paths)

                    # Setting current flow
                    self.current_flow = flow

                    # Getting new path
                    self.reverse_path = []
                    self.reverse_path_link = []
                    self.explorer_neighbor = []
                    logging.debug("Find available path for flow: {} <=> {} || {}".format(src_flow, dst_flow, src_node_ip))
                    new_path = self.find_available_path(src_node_ip, flow_dst_node_ips, initial=True)

                    # If not have a new path
                    if not new_path:
                        logging.debug("No new path")
                        continue

                    logging.debug("New path is: %s", new_path['path'])
                    if new_path['path'] == self.reverse_path[:-(len(new_path['path']) + 1):-1]:
                        continue

                    # Update path
                    # Create a new policy
                    policy_route = PolicyRoute()

                    new_path_link = []

                    policy_route.set_policy(src_network=src_flow, dst_network=dst_flow)
                    for hop_index in range(len(new_path['path_link'])):
                        logging.debug(
                            "Node: %s <=> Exit-IF: %s, Next-hop: %s",
                            new_path['path'][hop_index],
                            new_path['path_link'][hop_index]['out']['index'],
                            new_path['path_link'][hop_index]['in']['ipv4_address']
                        )

                        new_path_link.append({
                            'out': new_path['path_link'][hop_index]['out']['ipv4_address'],
                            'in': new_path['path_link'][hop_index]['in']['ipv4_address']
                        })
                        policy_route.add_action(
                            new_path['path'][hop_index],  # Node IP
                            'next-hop',  # Action
                            new_path['path_link'][hop_index]['in']['ipv4_address']  # Data
                        )

                    policy_route.info['old_path'] = self.reverse_path
                    policy_route.info['old_path_link'] = self.reverse_path_link
                    policy_route.info['new_path'] = new_path['path']
                    policy_route.info['new_path_link'] = new_path_link

                    # Todo implement in_byte_per_sec
                    policy_route.info['in_bytes_per_sec'] = flow['in_bytes_per_sec']
                    policy_route.info['in_pkts_per_sec'] = flow['in_pkts_per_sec']
                    policy_route.info['in_bytes'] = flow['in_bytes']
                    policy_route.info['in_pkts'] = flow['in_pkts']
                    policy_route.info['submit_from'] = {
                        'type': 'automate',
                        'device_ip': device['management_ip']
                    }

                    policy = policy_route.get_policy()
                    self.policy_service.add_new_pending_policy(policy)

                    # Force update SNMP interfaces
                    force_update_interface(device['management_ip'],
                                           device['snmp_info']['community'],
                                           device['snmp_info']['port']
                                           )
                    break

        self.last_run = time.time()
        logging.debug("Traffic monitor task is run success...")

    def find_available_path(self, src_node_ip, dst_node_ips, initial=False):
        # Todo Getting available paths
        src_flow = self.current_flow['_id']['ipv4_src_addr']
        dst_flow = self.current_flow['_id']['ipv4_dst_addr']

        # first_switched = self.current_flow['_id']

        # Finding path
        if not initial:
            for dst_node_ip in dst_node_ips:
                paths = self.path_finder.find_by_available_bandwidth(
                    src_node_ip,
                    dst_node_ip,
                    PathFinder.SelectBy.HIGHEST,
                    self.current_flow['in_bytes_per_sec']  # Minimum free bandwidth
                )
                for path in paths:
                    # Source is R3
                    #  Active => [R1, R2, R3, R4, R5]
                    #  Case 1   => [R3, R2, R1, ...] X because R2 is reverse path -> looping
                    #  Case 2   => [R3, R6, ...] Y
                    #  Case 3   => [R3, R6, R2, R3, ...] Todo Checking
                    #
                    #  Check loop
                    for active_path in self.active_paths:  # many src_node -> many dst_node
                        if active_path is None:
                            continue
                        for _active_path in active_path:  # some path have multiple paths
                            try:
                                node_active_path_index = list(_active_path).index(src_node_ip)
                            except ValueError:
                                continue
                            before_node = _active_path[node_active_path_index - 1]
                            logging.debug("before_node: %s", before_node)
                            logging.debug("src node ip: %s, dst node ip: %s <=> Active path is %s", src_node_ip,
                                          dst_node_ip, _active_path)

                            # Case 1
                            #  path['path'][1] mean next node ip
                            if path['path'][1] == before_node:  # Detect loop, skip
                                continue
                            # Case 3
                            elif src_node_ip in path['path'][1:]:
                                continue
                            # Case 2
                            else:
                                logging.debug("Found path: %s", path['path'])
                                return path
        else:
            self.reverse_path.append(src_node_ip)

        # If can't find a new path
        # Find neighbor link device
        if src_node_ip in self.explorer_neighbor:
            logging.debug("Explorer neighbor %s, next explore %s", self.explorer_neighbor, src_node_ip)
            return
        node_ips = self.find_neighbor_link(src_node_ip, src_flow, dst_flow)
        self.explorer_neighbor.append(src_node_ip)
        for node_ip in node_ips:
            # logging.debug(node_ip)
            # if initial:
            self.reverse_path.append(node_ip['src_node_ip'])
            self.reverse_path_link.append({
                # 'out': node_ip['src_if_ip'],
                # 'in': node_ip['dst_if_ip']
                'out': node_ip['dst_if_ip'],
                'in': node_ip['src_if_ip']
            })

            # Find path from prevent path of active flow
            new_path = self.find_available_path(node_ip['src_node_ip'], dst_node_ips)
            # If found new path
            if new_path:
                # self.reverse_path.append(node_ip['src_if_ip'])
                return new_path

            # Remove not used path.
            self.reverse_path = self.reverse_path[:-1]
            self.reverse_path_link = self.reverse_path_link[:-1]
        return None

    def find_neighbor_link(self, src_node_ip, src_ip, dst_ip):
        logging.debug("Find neighbor: %s %s %s", src_node_ip, src_ip, dst_ip)
        # Find interfaces than receive this flow
        flow_from = self.netflow_service.netflow.aggregate([{
            '$match': {
                'ipv4_src_addr': src_ip,
                'ipv4_dst_addr': dst_ip,
                # Todo support port, protocol
                'from_ip': src_node_ip
            }
        }, {
            '$group': {
                '_id': {
                    'input_snmp': '$input_snmp'
                },
                'in_bytes': {'$sum': '$in_bytes'}
            }
        }])
        # flow_from = self.netflow_service.netflow.find({
        #     'ipv4_src_addr': src_ip,
        #     'ipv4_dst_addr': dst_ip,
        #     'from_ip': src_node_ip
        # })

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
                # logging.debug(link)
                if link['src_node_ip'] == src_node_ip:
                    src_node_ip = link['dst_node_ip']
                    src_if_ip = link['dst_if_ip']
                    dst_node_ip = link['src_node_ip']
                    dst_if_ip = link['src_if_ip']
                else:
                    src_node_ip = link['src_node_ip']
                    src_if_ip = link['src_if_ip']
                    dst_node_ip = link['dst_node_ip']
                    dst_if_ip = link['dst_if_ip']
                node_ips.append({
                    'src_node_ip': src_node_ip,
                    'dst_node_ip': dst_node_ip,
                    'src_if_ip': src_if_ip,
                    'dst_if_ip': dst_if_ip
                })
        return node_ips
