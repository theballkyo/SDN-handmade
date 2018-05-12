import pprint
from time import time

from repository import get_service, PolicyRoute
from router_command.policy_command import generate_config_command, generate_remove_command
import logging

from task.snmp_fetch import SNMPFetch
from worker.ssh.ssh_worker import SSHConnection
from typing import Dict


class PolicyMonitorTask:
    def __init__(self):
        self.device_repo = get_service('device')
        self.policy_service = get_service('policy')
        self.policy_seq_service = get_service('policy_seq')

    @staticmethod
    def diff(currently_policy: Dict[str, any], new_policy: Dict[str, any]) -> Dict[str, any]:
        if currently_policy['src_ip'] != new_policy['src_ip'] or \
                currently_policy['src_wildcard'] != new_policy['src_wildcard'] or \
                currently_policy['src_port'] != new_policy['src_port'] or \
                currently_policy['dst_ip'] != new_policy['dst_ip'] or \
                currently_policy['dst_wildcard'] != new_policy['dst_wildcard'] or \
                currently_policy['dst_port'] != new_policy['dst_port']:
            diff_policy = new_policy.copy()
            diff_policy['policy'] = 'changed'
        else:
            diff_policy = {'policy': 'not_changed'}

        diff_policy['actions'] = new_policy['actions'].copy()

        for key, action in currently_policy['actions'].items():
            if new_policy['actions'].get(key):
                # If not change
                if new_policy['actions'][key]['action'] == action['action'] and \
                        new_policy['actions'][key]['data'] == action['data']:
                    diff_policy['actions'].pop(key)
            else:
                diff_policy['actions'][key] = {
                    'action': 'remove',
                    'management_ip': action['management_ip']
                }
        return diff_policy

    def run(self, ssh_connection: SSHConnection) -> None:
        """
        1 Find pending policy
        2 Find current policy
        3 Process policy to update
          |> 3.1 If not have current policy -> Add new
          |> 3.2 If have, Call diff function -> Update
        4 Update policy
        5 SSH -> Device
        6 Update to policy table and remove in policy pending

        :param ssh_connection:
        :return:
        """
        logging.info("Policy monitor task is running...")

        # Step 1
        # new_policy = self.policy_service.policy_pending.find_one({}, sort=[('time', -1)])
        flow_routing_pending = self.policy_service.find_pending_apply()

        for flow in flow_routing_pending:
            if flow['info']['status'] == PolicyRoute.STATUS_WAIT_APPLY:
                self._apply_flow(flow, ssh_connection)
            elif flow['info']['status'] == PolicyRoute.STATUS_WAIT_REMOVE:
                self._remove_flow(flow, ssh_connection)

        # if not new_policy:
        #     return
        #
        # # Remove policy
        # if new_policy.get('type') == 'remove':
        #     return

        # Step 2
        # Automatic check exist flow
        # if new_policy['policy'].get('name'):
        #     current_policy = self.policy_service.policy.find_one({
        #         'name': new_policy['policy'].get('name')
        #     })
        # elif new_policy['policy'].get('policy_id'):
        #     current_policy = self.policy_service.policy.find_one({
        #         'policy_id': new_policy['policy'].get('policy_id')
        #     })
        # else:
        #     current_policy = self.policy_service.policy.find_one({
        #         'src_ip': new_policy['policy']['src_ip'],
        #         'src_wildcard': new_policy['policy']['src_wildcard'],
        #         'src_port': new_policy['policy']['src_port'],
        #         'dst_ip': new_policy['policy']['dst_ip'],
        #         'dst_wildcard': new_policy['policy']['dst_wildcard'],
        #         'dst_port': new_policy['policy']['dst_port']
        #     })

        # Step 3.2 Find diff
        # if current_policy:
        #     policy_id = current_policy['policy_id']
        #     policy_name = current_policy['name']
        #     diff_policy = self.diff(current_policy, new_policy['policy'])
        #     logging.info(pprint.pformat(diff_policy))
        #     actions = diff_policy['actions']
        #     policy = diff_policy['policy']
        # else:  # 3.2 New policy
        #     policy_id = self.policy_seq_service.get_new_id()
        #     if policy_id is None:
        #         raise ValueError('Policy ID is not available')
        #
        #     policy_name = "generate-{:.0f}".format(time() * 1000)
        #     actions = new_policy['policy']['actions']
        #     policy = new_policy['policy']
        #     print("Not found current policy")

        # new_policy['policy']['name'] = policy_name
        # new_policy['policy']['policy_id'] = policy_id
        #
        # # Step 4 update policy
        # policy_cmd = ''
        # if policy != 'not_changed':
        #     policy_cmd = generate_policy_command('cisco_ios', policy)
        # device_list = {}
        # for node_id, action in actions.items():
        #     logging.info(pprint.pformat("Node ID: {}".format(action['management_ip'])))
        #     action_cmd = generate_action_command('cisco_ios', policy_id, policy_name, action)  # Aka. route-map
        #     # logging.info(pprint.pformat(cmd))
        #     # if policy_cmd:
        #     #     cmd += policy_cmd
        #
        #     # Policy cmd + action cmd
        #     device_list[action['management_ip']] = ["\n".join(policy_cmd + action_cmd)]
        #     # device_list[action['management_ip']] = cmd
        #
        # logging.info(pprint.pformat(new_policy['policy']))
        # logging.info(pprint.pformat(device_list))
        # # Step 5 SSH to device(s)
        # connect = ssh_connection.check_connection(device_list.keys())
        # # pprint.pprint(connect)
        # if not all(connect):
        #     logging.info("Some device can't SSH")
        #     return
        # logging.info("Update...")
        # ssh_connection.send_config_set(device_list)
        #
        # # Step 6 Update policy table
        # self.policy_service.set_policy(new_policy['policy'])
        # self.policy_service.remove_pending(new_policy['_id'])
        # # Set policy seq to in_use is True
        # self.policy_seq_service.set_use_id(policy_id)

        # Force update SNMP interfaces
        # snmp_fetch = SNMPFetch()
        # snmp_fetch.run(ssh_connection)

    def _apply_flow(self, flow, ssh_connection):
        """
        Add new flow
        :param flow:
        :param ssh_connection:
        :return:
        """
        # Step 4 update policy
        # policy_cmd = ''

        flow_id = flow.get('flow_id')
        if not flow_id:
            flow_id = self.policy_seq_service.get_new_id()
            # flow['flow_id'] = flow_i
        # logging.info(flow_id)
        new_flow = flow.get('new_flow')
        new_flow['flow_id'] = flow_id
        flow_name = flow['name']
        flow_actions = new_flow['actions']

        device_list = {}
        for action in flow_actions:
            logging.info(pprint.pformat("Node ID: {}".format(action['management_ip'])))
            device = self.device_repo.get_device(action['management_ip'])
            # logging.info(device)
            # action_cmd = generate_action_command(device['type'], flow, flow_id, flow_name, action)
            cmd = generate_config_command(device['type'], new_flow, flow_id, flow_name, action)
            # Policy cmd + action cmd
            # device_list[action['management_ip']] = ["\n".join(policy_cmd + action_cmd)]
            device_list[action['management_ip']] = cmd

        # Remove old action
        for action in flow.get('actions', []):
            if device_list.get(action['management_ip']):
                continue

            logging.info(pprint.pformat("Node ID: {}".format(action['management_ip'])))
            device = self.device_repo.get_device(action['management_ip'])
            cmd = generate_remove_command(device['type'], flow)
            device_list[action['management_ip']] = cmd

        # logging.info(pprint.pformat(new_policy['policy']))
        logging.info(pprint.pformat(device_list))
        # Step 5 SSH to device(s)
        connect = ssh_connection.check_connection(device_list.keys())
        # pprint.pprint(connect)
        if not all(connect):
            logging.info("Some device can't SSH")
            return
        logging.info("Update...")
        ssh_connection.send_config_set(device_list)

        new_flow['flow_id'] = flow_id
        new_flow['info'] = flow['info']
        new_flow['info']['status'] = PolicyRoute.STATUS_ACTIVE
        new_flow['_id'] = flow['_id']
        # Remove new flow
        new_flow['new_flow'] = {}

        # flow = new_flow
        # flow['status'] = PolicyRoute.STATUS_ACTIVE

        logging.info(pprint.pformat(new_flow))

        # Step 6 Update policy table
        self.policy_service.update_flow(new_flow)
        # Set policy seq to in_use is True
        self.policy_seq_service.set_use_id(flow_id)

    def _update_flow(self, flow, ssh_connection):
        """
        Update flow
        :param flow:
        :param ssh_connection:
        :return:
        """
        pass

    def _remove_flow(self, flow, ssh_connection):
        device_list = {}
        # Remove old action
        for _, action in flow['actions'].items():
            if device_list.get(action['management_ip']):
                continue

            logging.info(pprint.pformat("Node ID: {}".format(action['management_ip'])))
            device = self.device_repo.get_device(action['management_ip'])
            cmd = generate_remove_command(device['type'], flow)
            device_list[action['management_ip']] = cmd

        # Send SSH Command
        connect = ssh_connection.check_connection(device_list.keys())
        # pprint.pprint(connect)
        if not all(connect):
            logging.info("Some device can't SSH")
            return
        logging.info("Update...")
        ssh_connection.send_config_set(device_list)

        # Remove flow routing

        # Return flow_id
