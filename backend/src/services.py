from database import get_mongodb
import os
import time


class Service:
    def __init__(self, *args, **kwargs):
        self.mongodb = get_mongodb()
        self.db = self.mongodb.db


class AppService(Service):
    def __init__(self, *args, **kwargs):
        super(AppService, self).__init__(*args, **kwargs)

    def is_running(self):
        app = self.db.app.find_one({}, {'is_running': 1})
        return app

    def set_running(self, running):
        self.db.app.update_one({}, {
            '$set': {
                'is_running': running
            }
        })


class CdpService(Service):
    def __init__(self, *args, **kwargs):
        super(CdpService, self).__init__(*args, **kwargs)
        self.cdp = self.db.cdp

    def get_by_management_ip(self, management_ip):
        return self.db.cdp.find_one({'management_ip': management_ip})


class DeviceService(Service):
    """ Device service
    """

    def __init__(self, *args, **kwargs):
        super(DeviceService, self).__init__(*args, **kwargs)
        self.device = self.db.device

    def get_device(self, management_ip):
        """ Get device object """
        return self.device.find_one({'management_ip': management_ip})

    def get_active(self):
        """ Get devices is active """
        return self.device.find({'active': True})

    def get_all(self):
        return self.device.find()

    def get_by_snmp_can_run(self, delay):
        return self.device.find({
            'snmp_is_running': False,
            'snmp_last_run_time': {
                '$lte': time.time() - delay
            }
        })

    def set_snmp_running(self, management_ip, is_running):
        self.device.update_one({
            'management_ip': management_ip
        }, {
            '$set': {
                'snmp_is_running': is_running
            }
        })

    def set_snmp_finish_running(self, management_ip):
        self.device.update_one({
            'management_ip': management_ip
        }, {
            '$set': {
                'snmp_is_running': False,
                'snmp_last_run_time': time.time()
            }
        })

    def snmp_is_running(self, management_ip):
        device = self.device.find_one({
            'management_ip': management_ip
        })
        if device is None:
            return True
        return device.get('snmp_is_running', False)

    def get_ssh_info(self, management_ip):
        data = self.db.device.find_one({
            'management_ip': management_ip
        })
        if data is None:
            return None
        return data['ssh_info']

    def find_by_if_ip(self, ip):
        """
        """
        return self.device.find_one({
            'interfaces.ipv4_address': ip
        })

    def add_device(self, device):
        """ Add device """
        if device.get('management_ip') is None:
            raise ValueError('Device dict must be `management_ip` key')

        snmp_info = device.get('snmp_info')
        if snmp_info is None:
            raise ValueError('SNMP must be not None')
        if snmp_info.get('community') is None:
            raise ValueError()
        if snmp_info.get('port') is None:
            raise ValueError()

        self.device.update_one({
            'management_ip': device.get('management_ip'),
        }, {
            '$set': device
        }, upsert=True)

    def increase_offline_count(self, management_ip):
        """ Update offline count by increase by 1
        """
        self.device.update_one({
            'management_ip': management_ip
        }, {
            '$inc': {
                'mark_offline_count': 1
            }
        })

    def remove(self, management_ip):
        """ Remove device """
        self.device.remove({'management_ip': management_ip})


class RouteService(Service):
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


class NetflowService(Service):
    def __init__(self, *args, **kwargs):
        super(NetflowService, self).__init__(*args, **kwargs)
        self.netflow = self.db.netflow

    def get_ingress_flow(self, start_time, end_time, limit=10, extra_match=None, group_by=(),
                         sort=None, side='ingress'):
        """
        Getting flow
        :param start_time: First switched time >= start time
        :param end_time:  First switched time <= end time
        :param limit: Limit flow
        :param extra_match: Extra match filter
        :param group_by: Group by default use 4 fields
        :param sort: Sort by default sort by total_in_bytes
        :param side: Side flow can be only ingress, egress and all
        :return:
        """

        # Match stage
        match = {
            'first_switched': {
                '$gte': start_time,
                '$lte': end_time
            }
        }

        if extra_match:
            match = {**extra_match, **match}
            print(match)

        # Group stage
        group = {
            '_id': {}
        }

        if side == 'ingress' or side == 'all':
            group['total_in_bytes'] = {'$sum': '$in_bytes'}
            group['total_in_pkts'] = {'$sum': '$in_pkts'}
        if side == 'egress' or side == 'all':
            group['total_out_bytes'] = {'$sum': '$out_bytes'}
            group['total_out_pkts'] = {'$sum': '$out_pkts'}

        if len(group_by) <= 0:
            group_by = ('ipv4_src_addr', 'ipv4_dst_addr', 'l4_src_port', 'l4_dst_port')

        for field in group_by:
            group['_id'][field] = '$' + field  # Add $ before field name

        # Sort stage
        if not sort:
            if side == 'ingress' or side == 'all':
                sort = {
                    'total_in_bytes': -1
                }
            if side == 'egress' or side == 'all':
                sort = {
                    'total_out_bytes': -1
                }

        # Add total flow count stage
        count_flow = {
            "_id": None,
            "total_flow": {
                "$sum": 1
            },
            "data": {
                "$push": {
                    "_id": "$_id",
                }
            }
        }
        if side == 'ingress' or side == 'all':
            count_flow["data"]["$push"]["total_in_bytes"] = "$total_in_bytes"
            count_flow["data"]["$push"]["total_in_pkts"] = "$total_in_pkts"

        if side == 'egress' or side == 'all':
            count_flow["data"]["$push"]["total_out_bytes"] = "$total_out_bytes"
            count_flow["data"]["$push"]["total_out_pkts"] = "$total_out_pkts"

        pipeline = [{'$match': match}, {'$group': group}, {'$sort': sort}, {'$limit': limit},
                    {'$group': count_flow}]

        print(pipeline)
        flows = self.netflow.aggregate(pipeline)
        return flows


_cache = {
    'app': {},
    'cdp': {},
    'device': {},
    'route': {},
    'netflow': {}
}

_SERVICES = {
    'app': AppService,
    'cdp': CdpService,
    'device': DeviceService,
    'route': RouteService,
    'netflow': NetflowService
}


def get_service(name):
    pid = os.getpid()
    if name not in _SERVICES:
        raise ValueError("No service name: {}".format(name)
                         )
    if pid not in _cache[name]:
        _cache[name]['pid'] = _SERVICES[name]()

    return _cache[name]['pid']


# Prepare to create a objects
app_service = AppService()
cdp_service = CdpService()
device_service = DeviceService()
route_service = RouteService()
