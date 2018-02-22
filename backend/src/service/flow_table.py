from service import BaseService
from flow import FlowState
import logging


class FlowTableService(BaseService):
    def __init__(self):
        super(FlowTableService, self).__init__()
        self.flow_table = self.db.flow_table

    def get_flows_by_state(self, state, limit=10):
        if state not in FlowState:
            raise ValueError("Flow state: {} not in FlowState class".format(state))

        flows = self.db.flow_table.find({'state': state.value}).limit(limit)

        return flows

    def set_flow_state(self, flow_id, state):
        if state not in FlowState:
            raise ValueError("Flow state: {} not in FlowState class".format(state))

        flow = self.db.flow_table.find_one({'flow_id': flow_id})
        if not flow:
            logging.warning("Flow id: {} not exist !!!".format(flow_id))
            return True

        self.db.flow_table.update_one({'flow_id': flow_id}, {'$set': {'state': state.value}})

        return True
