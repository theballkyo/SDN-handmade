import logging

from repository import get_service, PolicyRoute
import sdn_utils
from worker.ssh.ssh_worker import SSHConnection
from router_command.policy_command import generate_remove_command


class ClearPolicyTask:
    def __init__(self):
        self.low_utilize = 60
        self.normal_utilize = 70
        self.high_utilize = 85
        self.device_service = get_service('device')
        self.flow_routing_repo = get_service('policy')
        self.policy_seq_service = get_service('policy_seq')
        self.netflow_service = get_service('netflow')

    def clear_policy_inactive_flow(self, ssh_connection: SSHConnection):
        """

        :param ssh_connection:
        :return:
        """
        active_policy = self.flow_routing_repo.get_by_submit_from_type(PolicyRoute.TYPE_AUTOMATE)
        for policy in active_policy:
            # Todo Reflect in policy get
            # if policy['info']['submit_from']['type'] == 1:
            #     continue
            flow = self.netflow_service.is_flow_exist_by_ip(policy['src_ip'], policy['dst_ip'])

            if not flow:
                device_list = {}
                for action in policy['actions']:
                    device = self.device_service.get_device_by_id(action['device_id'])
                    device_list[device['management_ip']] = generate_remove_command(device['type'], policy)

                connect = ssh_connection.check_connection(device_list.keys())
                if not all(connect):
                    logging.info("Some device can't SSH")
                    return

                ssh_connection.send_config_set(device_list)
                # Remove policy
                self.flow_routing_repo.remove_policy(policy['_id'])
                self.policy_seq_service.set_not_use_id(policy['flow_id'])

    def run(self, ssh_connection: SSHConnection):
        """
        1. Find interface than utilize < xx %
        2. Find policy is old path pass the interface
        3. check flow utilize
        4. if flow utilize + interface utilize < high load %. Remove policy
        :param ssh_connection:
        :return:
        """

        # Clear inactive flows
        self.clear_policy_inactive_flow(ssh_connection)

        # 1
        devices = self.device_service.get_by_if_utilization(self.low_utilize, 'in', '$lte')
        for device in devices:
            for interface in device['interfaces']:
                # 2
                if not interface.get('ipv4_address'):
                    continue
                if interface.get('bw_in_usage_percent') > self.low_utilize:
                    continue

                policy = self.flow_routing_repo.get_policy_old_path_has_pass_interface(
                    interface['ipv4_address'],
                    device_ip=device['management_ip'],
                    submit_from_type=PolicyRoute.TYPE_AUTOMATE
                )

                if policy.count() == 0:
                    continue
                policy = policy[0]

                # 3
                usage_per_sec = interface['bw_in_usage_persec'] + policy['info']['in_bytes_per_sec']
                new_utilize = sdn_utils.fraction_to_percent(usage_per_sec, interface['speed'])

                new_utilize += interface['bw_in_usage_percent']

                if new_utilize > self.high_utilize:
                    continue

                # Todo implement
                device_list = {}
                for action in policy['actions']:
                    device = self.device_service.get_device_by_id(action['device_id'])
                    device_list[device['management_ip']] = generate_remove_command(device['type'], policy)
                connect = ssh_connection.check_connection(device_list.keys())
                if not all(connect):
                    logging.info("Some device can't SSH")
                    return

                ssh_connection.send_config_set(device_list)
                # Remove policy
                self.flow_routing_repo.remove_policy(policy['_id'])
                self.policy_seq_service.set_not_use_id(policy['flow_id'])

        return True
