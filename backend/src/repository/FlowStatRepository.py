import model
from repository.repository import Repository


class FlowStatRepository(Repository):

    def clear_inactive(self):
        pass

    def remove_flow(self, flow_stat: model.FlowStat):
        pass
