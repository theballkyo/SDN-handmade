from flow import BaseFlowAnalyze
from services import get_service
from pprint import pprint


class NetflowAnalyze(BaseFlowAnalyze):
    def __init__(self):
        self.netflow_service = get_service("netflow")

    def get_biggest_flow(self, start_time, end_time):
        extra_match = {
            'l4_src_port': 443
        }
        return self.netflow_service.get_ingress_flow(start_time, end_time, addition_match=extra_match)
