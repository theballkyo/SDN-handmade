import asyncio
from pysnmp.hlapi.varbinds import *
from pysnmp.proto.rfc1905 import endOfMibView, EndOfMibView
from pysnmp.hlapi.asyncio import *
from pyasn1.type.univ import Null
import uvloop

import random

# import utils


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

# @asyncio.coroutine
async def run(ip, varBinds, mibs):
    print(ip + ' >>> Running...')
    data = []
    snmpEngine = SnmpEngine()
    vbProcessor = CommandGeneratorVarBinds()
    initialVars = [x[0] for x in vbProcessor.makeVarBinds(snmpEngine, varBinds)]
    nullVarBinds = [False] * len(varBinds)
    lexicographicMode = False
    stopFlag = False
    while not stopFlag:
        (errorIndication,
         errorStatus,
         errorIndex,
         varBindTable) = await bulkCmd(
            snmpEngine,
            CommunityData('public'),
            UdpTransportTarget((ip, 161)),
            ContextData(),
            0, 4,
            *varBinds,
            lexicographicMode=False)

        if errorIndication:
            print(errorIndication)
            break
        elif errorStatus:
            print('%s at %s' % (
                errorStatus.prettyPrint(),
                errorIndex and varBinds[int(errorIndex) - 1][0] or '?'
            )
                  )
        else:
            for row in range(len(varBindTable)):
                stopFlag = True
                if len(varBindTable[row]) != len(varBinds):
                    varBindTable = row and varBindTable[:row - 1] or []
                    break
                for col in range(len(varBindTable[row])):
                    # print(initialVars[col])
                    name, val = varBindTable[row][col]
                    if nullVarBinds[col]:
                        varBindTable[row][col] = name, endOfMibView
                        continue
                    stopFlag = False
                    if isinstance(val, Null):
                        nullVarBinds[col] = True
                    elif not lexicographicMode and not initialVars[col].isPrefixOf(name):
                        varBindTable[row][col] = name, endOfMibView
                        nullVarBinds[col] = True
                if stopFlag:
                    varBindTable = row and varBindTable[:row - 1] or []
                    break
            # print('------------------Start-----------------')
            for varBinds in varBindTable:
                context = {}
                for index, varBind in enumerate(varBinds):
                    # print('------------------Start2-----------------')
                    # print(index)
                    if isinstance(varBind[1], EndOfMibView):
                        stopFlag = True
                        break
                    # print(len(varBind))
                    # print(' = '.join([x.prettyPrint() for x in varBind]), end='')
                    # print(' (type = {})'.format(type(varBind[1])))
                    if mibs:
                        # print(varBind)
                        # print(mibs[index])
                        context[mibs[index]] = to_value(varBind[1])
                    else:
                        context[str(varBind[0].getOid())] = to_value(varBind[1])
                # print('------------------End2-----------------')
                if len(context) > 0:
                    # print(context)
                    data.append(context)
            # print('------------------End-----------------')
            if not stopFlag:
                varBinds = varBindTable[-1]


    sleep_time = random.random()
    print(ip + ' >>> Ending...')
    await asyncio.sleep(sleep_time)
    print(ip + ' >>> Sleep ' + str(sleep_time))
    # yield 123456
    # return 1
    snmpEngine.transportDispatcher.closeDispatcher()
    return data

# @asyncio.coroutine
async def run_all():
    host = [
        '192.168.106.100',
        '192.168.106.101',
        '192.168.106.102',
        '192.168.106.103'
    ]

    varBinds = [
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
        # ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.21')),
        # ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.22')),
    ]

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

    futures = [asyncio.ensure_future(run(ip, varBinds, mibs)) for ip in host]
    for i, future in enumerate(asyncio.as_completed(futures)):
        result = await future
        # for r in result:
        #     print(r)
        # print(len(result))


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
loop = asyncio.get_event_loop()
loop.run_until_complete(
    run_all()
)
