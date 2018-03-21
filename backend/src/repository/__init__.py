from repository.app_service import AppService
from repository.base_service import BaseService
from repository.cdp_service import CdpService
from repository.device_service import DeviceService
from repository.link_service import LinkService
from repository.netflow_service import NetflowService
from repository.policy_log_service import PolicyLogService
from repository.policy_seq_service import PolicySeqService
from repository.policy_service import PolicyRoute, PolicyService
from repository.route_service import RouteService
from repository.topology_path_service import TopologyPathService
from repository.topology_service import TopologyService

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
        raise ValueError("No repository name %s", name)
    if _services.get(name) is None:
        _services[name] = _list_service[name]()

    return _services[name]


def get_flow_table_service():
    global _services
    if _services.get('flow_table') is None:
        _services['flow_table'] = PolicyService()
    return _services['flow_table']


__all__ = ["BaseService", "PolicyRoute", "get_service", "get_flow_table_service"]