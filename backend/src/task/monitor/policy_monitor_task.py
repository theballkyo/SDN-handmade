import pprint
from time import time

from repository import get_service
from router_command.policy_command import generate_action_command, generate_policy_command
import logging

from task.snmp_fetch import SNMPFetch
from worker.ssh.ssh_worker import SSHConnection
from typing import Dict


class PolicyMonitorTask:
    def __init__(self):
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
        new_policy = self.policy_service.policy_pending.find_one({}, sort=[('time', -1)])
        if not new_policy:
            return

        # Remove policy
        if new_policy.get('type') == 'remove':
            pass
            return

        # Step 2
        # Automatic check exist flow
        if new_policy['policy'].get('name'):
            current_policy = self.policy_service.policy.find_one({
                'name': new_policy['policy'].get('name')
            })
        elif new_policy['policy'].get('policy_id'):
            current_policy = self.policy_service.policy.find_one({
                'policy_id': new_policy['policy'].get('policy_id')
            })
        else:
            current_policy = self.policy_service.policy.find_one({
                'src_ip': new_policy['policy']['src_ip'],
                'src_wildcard': new_policy['policy']['src_wildcard'],
                'src_port': new_policy['policy']['src_port'],
                'dst_ip': new_policy['policy']['dst_ip'],
                'dst_wildcard': new_policy['policy']['dst_wildcard'],
                'dst_port': new_policy['policy']['dst_port']
            })

        # Step 3.2 Find diff
        if current_policy:
            policy_id = current_policy['policy_id']
            policy_name = current_policy['name']
            diff_policy = self.diff(current_policy, new_policy['policy'])
            logging.info(pprint.pformat(diff_policy))
            actions = diff_policy['actions']
            policy = diff_policy['policy']
        else:  # 3.2 New policy
            policy_id = self.policy_seq_service.get_new_id()
            if policy_id is None:
                raise ValueError('Policy ID is not available')

            policy_name = "generate-{:.0f}".format(time() * 1000)
            actions = new_policy['policy']['actions']
            policy = new_policy['policy']
            print("Not found current policy")

        new_policy['policy']['name'] = policy_name
        new_policy['policy']['policy_id'] = policy_id

        # Step 4 update policy
        # policy_cmd = None
        # if policy != 'not_changed':
        policy_cmd = generate_policy_command('cisco_ios', policy)
        device_list = {}
        for node_id, action in actions.items():
            logging.info(pprint.pformat("Node ID: {}".format(action['management_ip'])))
            action_cmd = generate_action_command('cisco_ios', policy_id, policy_name, action)  # Aka. route-map
            # logging.info(pprint.pformat(cmd))
            # if policy_cmd:
            #     cmd += policy_cmd

            # Policy cmd + action cmd
            device_list[action['management_ip']] = ["\n".join(policy_cmd + action_cmd)]
            # device_list[action['management_ip']] = cmd

        logging.info(pprint.pformat(new_policy['policy']))
        logging.info(pprint.pformat(device_list))
        # Step 5 SSH to device(s)
        connect = ssh_connection.check_connection(device_list.keys())
        # pprint.pprint(connect)
        if not all(connect):
            logging.info("Some device can't SSH")
            return
        logging.info("Update...")
        ssh_connection.send_config_set(device_list)

        # Step 6 Update policy table
        self.policy_service.set_policy(new_policy['policy'])
        self.policy_service.remove_pending(new_policy['_id'])
        # Set policy seq to in_use is True
        self.policy_seq_service.set_use_id(policy_id)

        # Force update SNMP interfaces
        snmp_fetch = SNMPFetch()
        snmp_fetch.run(ssh_connection)
