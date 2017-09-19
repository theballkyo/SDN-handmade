from snmp import get_interfaces, get_routes, get_ip_addr, get_system_info
from database import MongoDB
from pymongo import ReplaceOne
import utils

mongo = MongoDB()

def add_device(host, community, port=161):
    pass


def calculate_bw_usage():
    pass

def store_interface(host, community, port=161, oid='.1.3.6.1.2.1.2.1.0'):
    # print('Get interfaces....')
    interfaces = get_interfaces(host, community, port, oid)
    routes = get_routes(host, community, port)
    ip_addr = get_ip_addr(host, community, port)
    system_info = get_system_info(host, community, port)

    system_info['interfaces'] = interfaces
    # system_info['routes'] = routes
    system_info['ip_addr'] = ip_addr
    for route in routes:
        route['device_ip'] = host
    # print(routes)

    deleted = mongo.db.route.delete_many({
        'device_ip': host
    })
    print(deleted.deleted_count)

    inserted = mongo.db.route.insert_many(routes)
    print(len(inserted.inserted_ids))
    mongo.device.update_one({
        'ipv4_address': host
    }, {
        '$set': system_info
    }, upsert=True)

    # db.snmp.insert_many(interfaces)
    # print(interfaces)
    # print(routes[0])
    # print('Stored')
