from service import BaseService
from flow import FlowState
import logging


class FlowTableService(BaseService):
    def __init__(self):
        super(FlowTableService, self).__init__()
        self.flow_table = self.db.flow_table

    def get_flows_by_state(self, state):
        if state not in FlowState:
            raise ValueError("Flow state: {} not in FlowState class".format(state))

        flows = self.db.flow_table.find({'state': state})

        return flows

    def set_flow_state(self, flow_id, state):
        if state not in FlowState:
            raise ValueError("Flow state: {} not in FlowState class".format(state))

        flow = self.db.flow_table.findOne({'flow_id': flow_id})
        if not flow:
            logging.warning("Flow id: {} not exist !!!".format(flow_id))
            return True

        self.db.flow_table.updateOne({'flow_id': flow_id}, {'$set': {'state': state}})

        return True
