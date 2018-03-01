from service import BaseService
import netaddr


class RouteService(BaseService):
    route_type = {
        'other': 1,
        'reject': 2,
        'local': 3,
        'remote': 4
    }

    def __init__(self, *args, **kwargs):
        super(RouteService, self).__init__(*args, **kwargs)
        self.route = self.db.route

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
            'device_ip': 1
        })

        hosts = []

        for route in routes:
            hosts.append(route['device_ip'])

        return hosts
