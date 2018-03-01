import netaddr

from service import BaseService
from flow import FlowState
import logging
import time


class PolicyRoute:
    def __init__(self):
        # TODO Support port
        self.src_network = None
        self.dst_network = None

        self.actions = {}

    def set_policy(self, **kwargs):
        if kwargs.get('src_network'):
            self.src_network = netaddr.IPNetwork(kwargs.get('src_network'))

        if kwargs.get('dst_network'):
            self.dst_network = netaddr.IPNetwork(kwargs.get('dst_network'))

    def add_action(self, node, action, data=None):
        self.actions[str(netaddr.IPAddress(node).value)] = {
            'management_ip': node,
            'action': action,
            'data': data
        }

    def remove_action(self, node):
        self.actions = filter(lambda _node: _node != node, self.actions)

    def get_only_policy(self):
        return {
            'src_ip': str(self.src_network.ip),
            'src_port': None,
            'src_wildcard': str(self.src_network.hostmask),
            'dst_ip': str(self.dst_network.ip),
            'dst_port': None,
            'dst_wildcard': str(self.dst_network.hostmask),
        }

    def get_policy(self):
        return {
            'src_ip': str(self.src_network.ip),
            'src_port': None,
            'src_wildcard': str(self.src_network.hostmask),
            'dst_ip': str(self.dst_network.ip),
            'dst_port': None,
            'dst_wildcard': str(self.dst_network.hostmask),
            'actions': self.actions
        }


class PolicyService(BaseService):
    def __init__(self):
        super(PolicyService, self).__init__()
        self.policy = self.db.policy
        self.policy_pending = self.db.policy_pending

    def get_flows_by_state(self, state, limit=10):
        if state not in FlowState:
            raise ValueError("Flow state: {} not in FlowState class".format(state))

        flows = self.policy.find({'state': state.value}).limit(limit)

        return flows

    def set_flow_state(self, flow_id, state):
        if state not in FlowState:
            raise ValueError("Flow state: {} not in FlowState class".format(state))

        flow = self.policy.find_one({'flow_id': flow_id})
        if not flow:
            logging.warning("Flow id: {} not exist !!!".format(flow_id))
            return True

        self.policy.update_one({'flow_id': flow_id}, {'$set': {'state': state.value}})

        return True

    def add_new_pending_policy(self, policy):
        self.policy_pending.insert_one({
            'type': 'update',
            'policy': policy,
            'time': time.time()
        })

    def get_pending(self, limit=None):
        policy_list = self.policy_pending.find({}).sort('time', 1)

        if limit:
            policy_list.limit(limit)

        return policy_list

    def set_policy(self, policy):
        # Update time
        policy['time'] = time.time()
        self.policy.replace_one({
            'policy_id': policy['policy_id']
        }, policy, upsert=True)
        # else:
        #     self.policy.replace_one({
        #         'src_ip': policy['src_ip'],
        #         'src_port': policy['src_port'],
        #         'src_wildcard': policy['src_wildcard'],
        #         'dst_ip': policy['dst_ip'],
        #         'dst_port': policy['dst_port'],
        #         'dst_wildcard': policy['dst_wildcard']
        #     }, policy, upsert=True)

    def remove_pending(self, _id):
        self.policy_pending.remove(_id)
