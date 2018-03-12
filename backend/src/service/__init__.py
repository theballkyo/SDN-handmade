from service.app_service import AppService
from service.base_service import BaseService
from service.cdp_service import CdpService
from service.device_service import DeviceService
from service.link_service import LinkService
from service.netflow_service import NetflowService
from service.policy_log_service import PolicyLogService
from service.policy_seq_service import PolicySeqService
from service.policy_service import PolicyRoute, PolicyService
from service.route_service import RouteService
from service.topology_path_service import TopologyPathService
from service.topology_service import TopologyService

_services = {}

_list_service = {
    'app_service': AppService,
    'cdp_service': CdpService,
    'device_service': DeviceService,
    'link_service': LinkService,
    'netflow_service': NetflowService,
    'policy_log_service': PolicyLogService,
    'policy_seq_service': PolicySeqService,
    'policy_service': PolicyService,
    'route_service': RouteService,
    'topology_path_service': TopologyPathService,
    'topology_service': TopologyService
}


def get_service(name):
    global _services

    if not name.endswith('_service'):
        name += '_service'

    if name not in _list_service.keys():
        raise ValueError("No service name %s", name)
    if _services.get(name) is None:
        _services[name] = _list_service[name]()

    return _services[name]


def get_flow_table_service():
    global _services
    if _services.get('flow_table') is None:
        _services['flow_table'] = PolicyService()
    return _services['flow_table']


__all__ = ["BaseService", "PolicyRoute", "get_service", "get_flow_table_service"]
