import logging
from typing import Optional, Dict

import netaddr

import sdn_utils
from flow import FlowState
from service import BaseService


# class PolicyAction:
#     def __init__(self, actions: Dict):
#         self.actions = actions.copy()


class PolicyRoute:
    FIELDS = ('src_ip',
              'src_wildcard',
              'src_port',
              'dst_ip',
              'dst_wildcard',
              'dst_port',
              'name',
              'policy_id',
              'time'
              )

    def __init__(self, policy=None, **kwargs):
        # TODO Support port
        self.src_network = None
        self.dst_network = None

        for field in self.FIELDS:
            setattr(self, field, None)

        if policy:
            for field, value in policy.items():
                if field in self.FIELDS:
                    setattr(self, field, value)

            self.policy = {}
            if policy.get('actions'):
                self.actions = policy['actions'].copy()
            else:
                self.actions = {}
        else:
            self.policy = {}
            self.actions = {}

        self.info = {}

    def set_policy(self, **kwargs):
        if kwargs.get('src_network'):
            self.src_network = netaddr.IPNetwork(kwargs.get('src_network'))

        if kwargs.get('dst_network'):
            self.dst_network = netaddr.IPNetwork(kwargs.get('dst_network'))

    def set_action(self, action: Dict[str, Optional[str]]):
        raise NotImplementedError()

    def diff(self, new_policy):
        raise NotImplementedError()

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
            'actions': self.actions.copy(),
            'info': self.info
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
            'time': sdn_utils.datetime_now()
        })

    def get_pending(self, limit=None, device_ip=None):

        policy_list = self.policy_pending.find({})
        policy_list.sort('time', 1)

        if limit:
            policy_list.limit(limit)

        return policy_list

    def sum_bytes_pending_has_pass_interface(self, interface_ip, limit=1, side='in'):
        if side == 'in':
            side = 'policy.info.old_path_link.in'
            new_side = 'policy.info.new_path_link.in'
        else:
            side = 'policy.info.old_path_link.out'
            new_side = 'policy.info.new_path_link.out'

        policy_list = self.policy_pending.aggregate([
            {
                '$match': {
                    side: interface_ip,
                    new_side: {'$ne': interface_ip}
                }
            },
            {
                '$group': {
                    '_id': {
                        'interface_ip': "$" + side
                    },
                    'total': {
                        '$sum': '$policy.info.total_in_bytes'
                    }
                }
            },
            {
                '$limit': limit
            }
        ])

        return policy_list

    def set_policy(self, policy):
        # Update time
        policy['time'] = sdn_utils.datetime_now()
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
