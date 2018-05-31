import netaddr
from bson.objectid import ObjectId

from repository.repository import Repository


class CopiedRouteRepository(Repository):
    route_type = {
        'other': 1,
        'reject': 2,
        'local': 3,
        'remote': 4
    }

    route_type_reverse = {
        1: 'other',
        2: 'reject',
        3: 'local',
        4: 'remote'
    }

    route_proto_reverse = {
        1: 'other',
        2: 'local',
        3: 'netmgmt',
        4: 'icmp',
        5: 'egp',
        6: 'ggp',
        7: 'hello',
        8: 'rip',
        9: 'isIs',
        10: 'esIs',
        11: 'ciscoIgrp',
        12: 'bbnSpfIgp',
        13: 'ospf',
        14: 'bgp',
        15: 'idpr',
        16: 'ciscoEigrp'
    }

    def __init__(self, *args, **kwargs):
        super(CopiedRouteRepository, self).__init__(*args, **kwargs)
        self.route = self.db.copied_route  # Todo deprecated
        self.model = self.db.copied_route

    def get_by_device_id(self, device_id):
        return self.model.find({'device_id': ObjectId(device_id)})

    def find_by_device(self, management_ip):
        # Todo fix device_ip to management_ip
        return self.route.find({'device_ip': management_ip})

    def find_by_network(self, network, mask, route_type=None):
        if route_type:
            route = self.route.find({
                'ipCidrRouteType': route_type,
                'ipCidrRouteDest': network,
                'ipCidrRouteMask': mask
            })
        else:
            route = self.route.find({
                'ipCidrRouteDest': network,
                'ipCidrRouteMask': mask
            })

        return route

    def find_by_type_is_local(self, network, mask):
        return self.find_by_network(network, mask, self.route_type['local'])

    def get_management_ip_from_host_ip(self, host_ip):
        host_ip = netaddr.IPAddress(host_ip)
        routes = self.route.find({
            'start_ip': {
                '$lte': host_ip.value
            },
            'end_ip': {
                '$gte': host_ip.value
            },
            'type': self.route_type['local']  # Local
        }, {
            'device_id': 1
        })

        hosts = []
        device_id = []

        for route in routes:
            device_id.append(ObjectId(route['device_id']))

        devices = self.db.device.find({
            '_id': {'$in': device_id}
        }, {
            'management_ip'
        })

        for device in devices:
            hosts.append(device['management_ip'])
        # hosts.append(route['device_ip'])

        return hosts

    def delete_all_by_device_ip(self, device_ip: str):
        return self.model.delete_many({
            'device_ip': device_ip
        })

    def delete_all_by_device_id(self, device_id: str):
        return self.model.delete_many({
            'device_id': ObjectId(device_id)
        })
