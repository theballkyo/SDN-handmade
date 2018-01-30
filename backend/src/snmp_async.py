# import uvloop
import logging

from pyasn1.type.univ import Null
from pysnmp.hlapi.asyncio import *
from pysnmp.hlapi.varbinds import *
from pysnmp.proto.rfc1905 import endOfMibView
import pprint

import sdn_utils


def to_value(rfc1902_object):
    """Convert rfc1902_object to value
    """
    if isinstance(rfc1902_object, Counter64) or \
            isinstance(rfc1902_object, Counter32) or \
            isinstance(rfc1902_object, Integer) or \
            isinstance(rfc1902_object, Integer32) or \
            isinstance(rfc1902_object, Gauge32) or \
            isinstance(rfc1902_object, Unsigned32) or \
            isinstance(rfc1902_object, TimeTicks):
        return int(rfc1902_object)

    return rfc1902_object.prettyPrint()


async def get(host, community, port, oid_list, max_repetitions=16, extras=None):
    oid_name = tuple(oid_list.keys())
    var_binds = tuple(oid_list.values())
    data = []
    snmp_engine = SnmpEngine()
    vb_processor = CommandGeneratorVarBinds()
    initial_vars = [x[0] for x in vb_processor.makeVarBinds(snmp_engine, var_binds)]
    null_var_binds = [False] * len(var_binds)
    lexicographic_mode = False
    stop_flag = False
    if not extras:
        extras = {}

    while not stop_flag:
        (error_indication,
         error_status,
         error_index,
         var_bind_table) = await bulkCmd(
            snmp_engine,
            CommunityData(community),
            UdpTransportTarget((host, port)),
            ContextData(),
            0, max_repetitions,
            *var_binds,
            lexicographicMode=lexicographic_mode)

        # Received packet time
        # recv_time = time.time()
        # logging.debug("Usage time {:.3f}".format(recv_time - start_time))
        # print(var_bind_table)
        if error_indication:
            # No SNMP response received before timeout
            logging.debug(error_indication)
            data = None
            break
        elif error_status:
            print('%s at %s' % (
                error_status.prettyPrint(),
                error_index and var_binds[int(error_index) - 1][0] or '?'
            )
                  )
        else:
            for row in range(len(var_bind_table)):
                stop_flag = True
                if len(var_bind_table[row]) != len(var_binds):
                    var_bind_table = row and var_bind_table[:row - 1] or []
                    break
                context = {}
                for col in range(len(var_bind_table[row])):
                    name, val = var_bind_table[row][col]
                    if null_var_binds[col]:
                        var_bind_table[row][col] = name, endOfMibView
                        continue
                    stop_flag = False
                    if isinstance(val, Null):
                        null_var_binds[col] = True
                    elif not lexicographic_mode and not initial_vars[col].isPrefixOf(name):
                        var_bind_table[row][col] = name, endOfMibView
                        null_var_binds[col] = True
                    else:
                        var_bind = var_bind_table[row][col]
                        # if oid_name[col]:
                        context[oid_name[col]] = to_value(var_bind[1])

                        # Add extras field
                        cursor_extra = extras.get(oid_name[col])
                        if cursor_extra:
                            for extra in cursor_extra:
                                if extra.get('field_name') and extra.get('type'):
                                    extra_type = extra.get('type')
                                    if extra_type == 'add_index':
                                        start_oid = str(oid_list[oid_name[col]][0])
                                        current_oid = str(var_bind[0].getOid())
                                        index = current_oid.replace(start_oid, '').split('.')
                                        # Use index[1] because when split index[0] == '.'
                                        context[extra['field_name']] = extra['field_type'](index[1])
                                    else:
                                        logging.warning("extra type: %s can't not found", extra_type)

                if len(context) > 0:
                    # print(context)
                    context['device_ip'] = host
                    data.append(context)

                if stop_flag:
                    var_bind_table = row and var_bind_table[:row - 1] or []
                    break

            if not stop_flag:
                var_binds = var_bind_table[-1]

    snmp_engine.transportDispatcher.closeDispatcher()
    return data


async def get_interfaces(host, community, port=161):
    """ Get interfaces information
    """
    object_types = {
        'index': ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.1')),
        'description': ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.2')),
        'type': ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.3')),
        'mtu': ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.4')),
        'speed': ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.5')),
        'physical_address': ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.6')),
        'admin_status': ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.7')),
        'operational_status': ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.8')),
        'last_change': ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.9')),
        'in_octets': ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.10')),
        'in_ucast_packets': ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.11')),
        #    ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.12')),
        'in_discards': ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.13')),
        'in_errors': ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.14')),
        'in_unknown_protos': ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.15')),
        'out_octets': ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.16')),
        'out_ucast_packets': ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.17')),
        #    ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.18')),
        'out_discards': ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.19')),
        'out_errors': ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.20')),
        #    ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.21')),
        #    ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.22')),
    }

    return await get(host, community, port, object_types, max_repetitions=100)


async def get_ip_addr(host, community, port=161):
    """
    """
    object_types = {
        'ipv4_address': ObjectType(ObjectIdentity('1.3.6.1.2.1.4.20.1.1')),
        'if_index': ObjectType(ObjectIdentity('1.3.6.1.2.1.4.20.1.2')),
        'subnet': ObjectType(ObjectIdentity('1.3.6.1.2.1.4.20.1.3'))
    }

    return await get(host, community, port, object_types)


async def get_routes(host, community, port=161):
    """ Get routing table
    """

    object_types = {
        'dst': ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.1')),
        'mask': ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.2')),
        'tos': ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.3')),
        'next_hop': ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.4')),
        'if_index': ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.5')),
        'type': ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.6')),
        'proto': ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.7')),
        'age': ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.8')),
        'info': ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.9')),
        'next_hop_AS': ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.10')),
        'metric1': ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.11')),
        'metric2': ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.12')),
        'metric3': ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.13')),
        'metric4': ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.14')),
        'metric5': ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.15')),
        'status': ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.16'))
    }

    return await get(host, community, port, object_types)


async def get_system_info(host, community, port=161):
    """
    """

    object_types = {
        'description': ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1')),
        'uptime': ObjectType(ObjectIdentity('1.3.6.1.2.1.1.3')),
        'name': ObjectType(ObjectIdentity('1.3.6.1.2.1.1.5'))
    }

    data = await get(host, community, port, object_types)
    if data is None or len(data) == 0:
        return None
    data = data[0]
    data['description'] = sdn_utils.hex_to_string(data['description'])
    return data


async def get_cdp(host, community, port=161):
    """ Get CDP
    """
    # Todo add local interface
    # More detail: http://www.oidview.com/mibs/9/CISCO-CDP-MIB.html
    object_types = {
        'ip_addr': ObjectType(ObjectIdentity('1.3.6.1.4.1.9.9.23.1.2.1.1.4')),
        'version': ObjectType(ObjectIdentity('1.3.6.1.4.1.9.9.23.1.2.1.1.5')),
        'name': ObjectType(ObjectIdentity('1.3.6.1.4.1.9.9.23.1.2.1.1.6')),
        'port': ObjectType(ObjectIdentity('1.3.6.1.4.1.9.9.23.1.2.1.1.7')),
    }

    extras = {
        'port': [
            {
                'type': 'add_index',
                'field_name': 'local_ifindex',
                'field_type': int
            }
        ]
    }

    data = await get(host, community, port, object_types, extras=extras)

    if data is None or len(data) == 0:
        return None

    for dat in data:
        dat['version'] = sdn_utils.hex_to_string(dat['version'])
        dat['ip_addr'] = sdn_utils.hex_to_ip(dat['ip_addr'])

    return data


async def get_lldp(host, community, port=161):
    """ Get LLDP
    """
    raise NotImplementedError()
