import asyncio
import time
import uvloop
from pysnmp.hlapi.asyncio import *

@asyncio.coroutine
def run_all_devices():
    """aaa
    """
    ips = [
        '192.168.106.100',
        # '192.168.106.101',
        # '192.168.106.102',
        # '192.168.106.103'
    ]

    varBinds = [
        ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr'))
        # ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.1')),
        # ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.2')),
        # ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.3')),
        # ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.4'))
    ]
    start = time.time()
    futures = [asyncio.ensure_future(run(ip, varBinds)) for ip in ips]
    # asyncio.wait(futures)
    for i, future in enumerate(asyncio.wait(futures)):
        result = yield from future
        # print('{} {}'.format(">>" * (i + 1), len(result[3])))

    print("Process took: {:.2f} seconds".format(time.time() - start))


@asyncio.coroutine
def run(ip, varBinds):
    snmpEngine = SnmpEngine()
    while True:
        (errorIndication,
         errorStatus,
         errorIndex,
         varBindTable) = yield from bulkCmd(
            snmpEngine,
            CommunityData('public'),
            # UsmUserData('usr-none-none'),
            UdpTransportTarget((ip, 161)),
            ContextData(),
            0, 1,
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
            for varBindRow in varBindTable:
                for varBind in varBindRow:
                    print(' = '.join([x.prettyPrint() for x in varBind]))
        # print(isEndOfMib(varBinds))
        varBinds = varBindTable[-1]
        if isEndOfMib(varBinds):
            break

    snmpEngine.transportDispatcher.closeDispatcher()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_all_devices())
    loop.close()

if __name__ == '__main__':
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    main()
