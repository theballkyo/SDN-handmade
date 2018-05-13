import logging
import os
from typing import Union, Dict

from repository.app_repository import AppRepository
from repository.device_neighbor_repository import DeviceNeighborRepository
from repository.device_repository import DeviceRepository
from repository.flow_stat_repository import FlowStatRepository
from repository.link_utilization_repository import LinkUtilizationRepository
from repository.used_flow_id_repository import UsedFlowIdRepository
from repository.flow_routing_repository import PolicyRoute, FlowRoutingRepository
from repository.repository import Repository
from repository.copied_route_repository import CopiedRouteRepository

_services = {}

_list_service = {
    'app_service': AppRepository,
    'cdp_service': DeviceNeighborRepository,
    'device_neighbor_service': DeviceNeighborRepository,
    'device_service': DeviceRepository,
    'link_service': LinkUtilizationRepository,
    'netflow_service': FlowStatRepository,
    'flow_stat': FlowStatRepository,  # Changed from netflow
    'policy_seq_service': UsedFlowIdRepository,
    'policy_service': FlowRoutingRepository,
    'route_service': CopiedRouteRepository,
}

_current_pid = None


def get_all_service(remove_suffix=True):
    global _services, _current_pid
    services = {}
    for name, _ in _list_service.items():
        if remove_suffix:
            alias = name.replace('_service', '')
        else:
            alias = name
        services[alias] = get_service(name)
    print(services)
    return services


def get_service(name, suffix="_service"):
    global _services

    if not name.endswith(suffix):
        name += suffix

    if name not in _list_service.keys():
        raise ValueError("No repository name %s", name)
    if _services.get(name + '_' + str(os.getpid())) is None:
        _services[name + '_' + str(os.getpid())] = _list_service[name]()

    return _services[name + '_' + str(os.getpid())]


def get_flow_table_service():
    global _services
    if _services.get('flow_table') is None:
        _services['flow_table'] = FlowRoutingRepository()
    return _services['flow_table']


def get_flow_stat_repository():
    return FlowStatRepository()


# Todo cache instance for lower memory usage !
_cache: Dict[str, Union[AppRepository,
                        CopiedRouteRepository,
                        DeviceRepository,
                        DeviceNeighborRepository,
                        FlowRoutingRepository,
                        FlowStatRepository,
                        LinkUtilizationRepository,
                        UsedFlowIdRepository]] = {
}

_list = {
    "app": AppRepository,
    "copied_route": CopiedRouteRepository,
    "device": DeviceRepository,
    "device_neighbor": DeviceNeighborRepository,
    "flow_routing": FlowRoutingRepository,
    "flow_stat": FlowStatRepository,
    "link_utilization": LinkUtilizationRepository,
    "used_flow_id": UsedFlowIdRepository
}

_pid = os.getpid()


def get(name):
    global _pid, _cache
    if _pid != os.getpid():
        logging.info(str(os.getpid()) + ":" + str(_pid) + " -> (Get) " + name)
        _cache = {}
        _pid = os.getpid()
    repo = _cache.get(name)
    if repo is None:
        if _list.get(name):
            _cache[name] = _list[name]()
            repo = _cache[name]
        else:
            return None
    # else:
    # logging.info(str(os.getpid()) + " -> " + str(_cache))
    return repo


def get_all():
    for repo, _ in _list.items():
        get(repo)
    return _cache


__all__ = [
    "PolicyRoute",
    "Repository",
    "get",
    "get_all",
    "AppRepository",
    "CopiedRouteRepository",
    "DeviceRepository",
    "DeviceNeighborRepository",
    "FlowRoutingRepository",
    "FlowStatRepository",
    "LinkUtilizationRepository",
    "UsedFlowIdRepository"]
