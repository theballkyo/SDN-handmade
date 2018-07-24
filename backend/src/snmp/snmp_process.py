import logging
import time

from netaddr import IPNetwork

import repository
import sdn_utils
from snmp import snmp_async


async def process_cdp(device_id, host, community, port):
    device_neighbor_repository = repository.get('device_neighbor')
    device_repository = repository.get('device')
    cdp = await snmp_async.get_cdp(host, community, port)

    if cdp is None:
        device_repository.set_cdp_by_mgmt_ip(host, False)
    else:
        # Insert CDP
        device_neighbor_repository.update_neighbor(device_id, host, cdp)
        device_repository.set_cdp_by_mgmt_ip(host, True)

    return True


async def process_system(device_id, host, community, port):
    device_repository = repository.get('device')
    system_info = await snmp_async.get_system_info(host, community, port)

    interfaces = await snmp_async.get_interfaces(host, community, port)
    interface_update_time = time.time()

    ip_addrs = await snmp_async.get_ip_addr(host, community, port)

    if not system_info:
        logging.info("SNMP (Process system [sys info]): host {} is down".format(host))
        return None

    if not ip_addrs:
        logging.info("SNMP (Process system [ip addr]): host {} is down".format(host))
        return None

    if not interfaces:
        logging.info("SNMP (Process system [interface]): host {} is down".format(host))
        return None

    # Todo optimize this
    for if_index, interface in enumerate(interfaces):
        for ip_index, ip_addr in enumerate(ip_addrs):
            if interface['index'] == ip_addr['if_index']:
                interface['ipv4_address'] = ip_addr['ipv4_address']
                interface['subnet'] = ip_addr['subnet']
                break

    my_device = device_repository.get_device_by_mgmt_ip(host)

    diff_interface_update_time = interface_update_time - my_device.get('interfaces_update_time', 0)
    diff_interface_update_time *= 100
    try:
        if my_device.get('interfaces'):
            for if_index, interface in enumerate(interfaces):
                for my_interface in my_device['interfaces']:
                    if interface['description'] == my_interface['description']:
                        # In
                        in_octets = interface['in_octets'] - my_interface['in_octets']
                        # in_in_time = system_info['uptime'] - my_device['uptime']
                        bw_in_usage_percent = sdn_utils.cal_bw_usage_percent(
                            in_octets,
                            interface['speed'],
                            diff_interface_update_time)
                        # Out
                        out_octets = interface['out_octets'] - my_interface['out_octets']
                        # out_in_time = system_info['uptime'] - my_device['uptime']
                        bw_out_usage_percent = sdn_utils.cal_bw_usage_percent(
                            out_octets,
                            interface['speed'],
                            diff_interface_update_time)

                        # Add information
                        interface['bw_in_usage_octets'] = in_octets
                        interface['bw_in_usage_persec'] = sdn_utils.bandwidth_usage_percent_to_bit(interface['speed'],
                                                                                                   bw_in_usage_percent)
                        interface['bw_in_usage_percent'] = bw_in_usage_percent

                        interface['bw_out_usage_octets'] = out_octets
                        # interface['bw_out_usage_persec'] = (out_octets / out_in_time) * 8
                        interface['bw_out_usage_persec'] = sdn_utils.bandwidth_usage_percent_to_bit(interface['speed'],
                                                                                                    bw_out_usage_percent)
                        interface['bw_out_usage_percent'] = bw_out_usage_percent

                        interface['bw_usage_update'] = time.time()

                        if interface.get('ipv4_address'):
                            ip = IPNetwork("{}/{}".format(interface['ipv4_address'], interface['subnet']))

                            if ip.size == 1:
                                start_ip = ip.first
                                end_ip = ip.first
                            elif ip.size == 2:
                                start_ip = ip.first
                                end_ip = ip.last
                            else:
                                start_ip = ip.first
                                end_ip = ip.last

                            interface['start_ip'] = start_ip
                            interface['end_ip'] = end_ip
                        break
    except Exception as e:
        logging.info("Except: %s", e)

    system_info['interfaces'] = interfaces
    system_info['interfaces_update_time'] = interface_update_time

    # Set update time
    system_info['updated_at'] = time.time()

    # Update device info
    device_repository.set(host, system_info)
    return True


async def process_route(device_id, host, community, port):
    copied_route_repository = repository.get('copied_route')
    routes = await snmp_async.get_routes(host, community, port)

    if routes is None:
        logging.info("SNMP (Process route): host {} is down".format(host))
        return None

    for route in routes:
        ip = IPNetwork("{}/{}".format(route['dst'], route['mask']))

        # /32
        if ip.size == 1:
            start_ip = ip.first
            end_ip = ip.first
        # /31
        elif ip.size == 2:
            start_ip = ip.first
            end_ip = ip.last
        # Other
        else:
            start_ip = ip.first + 1
            end_ip = ip.last - 1

        route['start_ip'] = start_ip
        route['end_ip'] = end_ip

        # route['device_ip'] = route['device_ip']
        del route['device_ip']

        route['device_id'] = device_id

        # Set update time
        route['updated_at'] = time.time()

    # Clear old routes
    # copied_route_repository.delete_all_by_device_ip(host)
    copied_route_repository.delete_all_by_device_id(device_id)
    # Insert net routes
    copied_route_repository.model.insert_many(routes)
    return True
