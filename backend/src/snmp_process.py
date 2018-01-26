from netaddr import IPNetwork

import snmp_async
import services
import sdn_utils
import time


async def process_cdp(host, community, port):
    cdp_service = services.get_service('cdp')
    device_service = services.get_service('device')
    cdp = await snmp_async.get_cdp(host, community, port)
    if cdp is None:
        cdp_enable = False
    else:
        cdp_enable = True

    # device = device_service.device.find_one({'management_ip': host})

    # for neighbor in cdp:
    #     for device_if in device['interfaces']:
    #         # print(neighbor)
    #         if device_if['index'] == neighbor['if_index']:
    #             neighbor['local_port'] = device_if['description']
    #             break

    # Insert CDP
    cdp_service.cdp.update_one({
        'management_ip': host
    }, {
        '$set': {
            'management_ip': host,
            'neighbor': cdp
        }
    }, upsert=True)

    device_service.device.update_one({
        'management_ip': host
    }, {
        '$set': {
            'cdp_enable': cdp_enable
        }
    })

    return True


async def process_system(host, community, port):
    device_service = services.get_service('device')
    system_info = await snmp_async.get_system_info(host, community, port)
    ip_addrs = await snmp_async.get_ip_addr(host, community, port)
    interfaces = await snmp_async.get_interfaces(host, community, port)

    # Todo optimize this
    for if_index, interface in enumerate(interfaces):
        for ip_index, ip_addr in enumerate(ip_addrs):
            if interface['index'] == ip_addr['if_index']:
                interface['ipv4_address'] = ip_addr['ipv4_address']
                interface['subnet'] = ip_addr['subnet']
                break

    # for if_index in range(len(interfaces)):
    #     for ip_index in range(len(ip_addrs)):
    #         if interfaces[if_index]['index'] == ip_addrs[ip_index]['if_index']:
    #             interfaces[if_index]['ipv4_address'] = ip_addrs[ip_index]['ipv4_address']
    #             interfaces[if_index]['subnet'] = ip_addrs[ip_index]['subnet']
    #             break

    # print(interfaces[0])
    my_device = device_service.device.find_one({
        'management_ip': host
    })

    if my_device.get('interfaces'):
        for if_index, interface in enumerate(interfaces):
            for my_interface in my_device['interfaces']:
                if interface['description'] == my_interface['description']:
                    # In
                    in_octets = interface['in_octets'] - my_interface['in_octets']
                    in_in_time = system_info['uptime'] - my_device['uptime']
                    bw_in_usage_percent = sdn_utils.cal_bw_usage_percent(
                        in_octets,
                        interface['speed'],
                        in_in_time)
                    # Out
                    out_octets = interface['out_octets'] - my_interface['out_octets']
                    out_in_time = system_info['uptime'] - my_device['uptime']
                    bw_out_usage_percent = sdn_utils.cal_bw_usage_percent(
                        out_octets,
                        interface['speed'],
                        out_in_time)

                    # Add infomation
                    interface['bw_in_usage_octets'] = in_octets
                    interface['bw_in_usage_percent'] = bw_in_usage_percent

                    interface['bw_out_usage_octets'] = out_octets
                    interface['bw_out_usage_percent'] = bw_out_usage_percent

                    interface['bw_usage_update'] = time.time()

                    # logging.debug(
                    #     ' || BW in usage %.3f%% || %d bytes',
                    #     bw_in_usage_percent,
                    #     in_octets)
                    #
                    # logging.debug(
                    #     ' || BW out usage %.3f%% || %d bytes',
                    #     bw_out_usage_percent,
                    #     out_octets)
                    break

    system_info['interfaces'] = interfaces

    # Update device info
    device_service.device.update_one({
        'management_ip': host
    }, {
        '$set': system_info
    }, upsert=True)
    return True


async def process_route(host, community, port):
    route_service = services.get_service('route')
    routes = await snmp_async.get_routes(host, community, port)
    # Clear old routes
    route_service.route.delete_many({
        'management_ip': host
    })

    for route in routes:
        ip = IPNetwork("{}/{}".format(route['dest'], route['mask']))

        if ip.size == 1:
            start_ip = ip.first
            end_ip = ip.first
        elif ip.size == 2:
            start_ip = ip.first
            end_ip = ip.last
        else:
            start_ip = ip.first + 1
            end_ip = ip.last - 1

        route['start_ip'] = start_ip
        route['end_ip'] = end_ip
        route['management_ip'] = route['device_ip']

    # Insert net routes
    route_service.route.insert_many(routes)
    return True
