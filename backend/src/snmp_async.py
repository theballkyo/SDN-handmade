import asyncio
# import uvloop
import sys
import logging
import sdn_utils
import random
import time

from pysnmp.hlapi.varbinds import *
from pysnmp.proto.rfc1905 import endOfMibView, EndOfMibView
from pysnmp.hlapi.asyncio import *
from pyasn1.type.univ import Null
import pysnmp.proto.errind as errind
from snmp_type import IF_TYPE


def to_value(rfc1902_object):
    """Convert rfc1902_object to value
    """
    # if isinstance(rfc1902_object, IpAddress):
    #     return str(rfc1902_object.prettyPrint())
    # if isinstance(rfc1902_object, OctetString):
    #     return str(rfc1902_object)
    # print(type(rfc1902_object))
    if isinstance(rfc1902_object, Counter64) or \
            isinstance(rfc1902_object, Counter32) or \
            isinstance(rfc1902_object, Integer) or \
            isinstance(rfc1902_object, Integer32) or \
            isinstance(rfc1902_object, Gauge32) or \
            isinstance(rfc1902_object, Unsigned32) or \
            isinstance(rfc1902_object, TimeTicks):
        return int(rfc1902_object)

    return rfc1902_object.prettyPrint()


async def get(host, community, varBinds, max_repetitions=16, port=161, mibs=None):
    # print(host + ' >>> Running...')
    data = []
    snmp_engine = SnmpEngine()
    vb_processor = CommandGeneratorVarBinds()
    initial_vars = [x[0] for x in vb_processor.makeVarBinds(snmp_engine, varBinds)]
    null_var_binds = [False] * len(varBinds)
    lexicographic_mode = False
    stop_flag = False
    start_time = time.time()

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
            *varBinds,
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
                error_index and varBinds[int(error_index) - 1][0] or '?'
            )
                  )
        else:
            for row in range(len(var_bind_table)):
                stop_flag = True
                if len(var_bind_table[row]) != len(varBinds):
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
                        varBind = var_bind_table[row][col]
                        if mibs:
                            context[mibs[col]] = to_value(varBind[1])
                        else:
                            context[str(varBind[0].getOid())] = to_value(varBind[1])

                if len(context) > 0:
                    # print(context)
                    context['device_ip'] = host
                    data.append(context)

                if stop_flag:
                    var_bind_table = row and var_bind_table[:row - 1] or []
                    break

            if not stop_flag:
                varBinds = var_bind_table[-1]

    snmp_engine.transportDispatcher.closeDispatcher()
    return data


async def get_interfaces(host, community, port=161, oid='.1.3.6.1.2.1.2.1.0'):
    '''Get interfaces infomation
    '''
    object_types = (
        ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.1')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.2')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.3')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.4')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.5')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.6')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.7')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.8')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.9')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.10')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.11')),
        #    ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.12')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.13')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.14')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.15')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.16')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.17')),
        #    ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.18')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.19')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.20')),
        #    ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.21')),
        #    ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.22')),
    )

    mibs = [
        'index',
        'description',
        'type',
        'mtu',
        'speed',
        'physical_address',
        'admin_status',
        'operational_status',
        'last_change',
        'in_octets',
        'in_ucast_packets',
        'in_discards',
        'in_errors',
        'in_unknown_protos',
        'out_octets',
        'out_ucast_packets',
        'out_discards',
        'out_errors',
    ]

    return await get(host, community, object_types, max_repetitions=100, mibs=mibs)


async def get_ip_addr(host, community, port):
    """
    """
    object_types = (
        ObjectType(ObjectIdentity('1.3.6.1.2.1.4.20.1.1')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.4.20.1.2')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.4.20.1.3'))
    )

    mibs = [
        'ipv4_address',
        'if_index',
        'subnet'
    ]

    return await get(host, community, object_types, mibs=mibs)


async def get_routes(host, community, port=161):
    ''' Get routing table
    '''

    object_types = (
        ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.1')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.2')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.3')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.4')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.5')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.6')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.7')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.8')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.9')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.10')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.11')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.12')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.13')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.14')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.15')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.4.24.4.1.16'))
    )

    mibs = [
        'dest',
        'mask',
        'tos',
        'next_hop',
        'if_index',
        'type',
        'proto',
        'age',
        'info',
        'next_hop_AS',
        'metric1',
        'metric2',
        'metric3',
        'metric4',
        'metric5',
        'status'
    ]

    return await get(host, community, object_types, mibs=mibs)


async def get_system_info(host, community, port=161):
    """
    """

    object_types = (
        ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.1.3')),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.1.5'))
    )

    mibs = [
        'description',
        'uptime',
        'name'
    ]
    data = await get(host, community, object_types, mibs=mibs)
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
    object_types = (
        ObjectType(ObjectIdentity('1.3.6.1.4.1.9.9.23.1.2.1.1.4')),
        ObjectType(ObjectIdentity('1.3.6.1.4.1.9.9.23.1.2.1.1.5')),
        ObjectType(ObjectIdentity('1.3.6.1.4.1.9.9.23.1.2.1.1.6')),
        ObjectType(ObjectIdentity('1.3.6.1.4.1.9.9.23.1.2.1.1.7')),
    )

    mibs = [
        'ip_addr',
        'version',
        'name',
        'port',
    ]

    data = await get(host, community, object_types, mibs=mibs)

    if data is None or len(data) == 0:
        return None

    for dat in data:
        dat['version'] = sdn_utils.hex_to_string(dat['version'])
        dat['ip_addr'] = sdn_utils.hex_to_ip(dat['ip_addr'])

    return data


async def get_lldp(host, community, port=161):
    """ Get LLDP
    """

    object_types = (
        ObjectType(ObjectIdentity('1.0.8802.1.1.2.1.3.7.1.3')),
        ObjectType(ObjectIdentity('1.0.8802.1.1.2.1.3.7.1.4')),
        # ObjectType(ObjectIdentity('1.0.8802.1.1.2.1.4.1.1.5.0')),
        # ObjectType(ObjectIdentity('1.0.8802.1.1.2.1.3.8.1.5.1.4')),
        # ObjectType(ObjectIdentity('1.3.6.1.4.1.9.9.23.1.2.1.1.7')),
    )

    mibs = [
        'name',
        'full_name',
        # 'if_id',
        # 'mac',
        # 'if_id',
        # 'port',
    ]

    data = await get(host, community, object_types, mibs=mibs)

    object_types = (
        ObjectType(ObjectIdentity('1.0.8802.1.1.2.1.3.8.1.5.1.4')),
        ObjectType(ObjectIdentity('1.0.8802.1.1.2.1.4.1.1.9')),
        ObjectType(ObjectIdentity('1.0.8802.1.1.2.1.4.1.1.5.0')),
        # ObjectType(ObjectIdentity('1.0.8802.1.1.2.1.4.1.1.5.0')),
        # ObjectType(ObjectIdentity('1.0.8802.1.1.2.1.3.8.1.5.1.4')),
        # ObjectType(ObjectIdentity('1.3.6.1.4.1.9.9.23.1.2.1.1.7')),
    )

    mibs = [
        'for_if_id',
        'sys_name',
        'chassis_id',
        # 'if_id',
        # 'mac',
        # 'if_id',
        # 'port',
    ]

    info = await get(host, community, object_types, mibs=mibs)

    # return data
    raise NotImplementedError()
