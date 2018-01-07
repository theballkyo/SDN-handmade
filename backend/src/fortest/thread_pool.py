import concurrent.futures
import time
import logging

from pysnmp.hlapi import *

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

def get_bulk_list(host, community, object_types, max_repetitions=16, port=161, mibs=None):
    ''' Get SNMP bulk
    '''
    data = []

    # logging.basicConfig(level=logging.DEBUG)
    # logging.debug('test')
    for errorIndication, errorStatus, errorIndex, varBinds in bulkCmd(SnmpEngine(),
               CommunityData(community, mpModel=1),
               UdpTransportTarget((host, port)),
               ContextData(),
               0, max_repetitions,
               *object_types,
               lexicographicMode=False):

        logging.debug('---------------------------------------------------------------')
        context = {}
        for index, varBind in enumerate(varBinds):
            logging.debug(' = '.join([x.prettyPrint() for x in varBind]))
            logging.debug(' (type = {})'.format(type(varBind[1])))
            if mibs:
                context[mibs[index]] = to_value(varBind[1])
            else:
                context[str(varBind[0].getOid())] = to_value(varBind[1])
            # print(context)
        data.append(context)
        logging.debug('---------------------------------------------------------------')
    return data


def get_interfaces(host, community, port=161, oid='.1.3.6.1.2.1.2.1.0'):
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

    return get_bulk_list(host, community, object_types, max_repetitions=100, mibs=mibs)

# import ..snmp
def wait_on_b():
    time.sleep(1)
    print('b')
    # print(b.result())  # b will never complete because it is waiting on a.
    return 5

def wait_on_a():
    time.sleep(3)
    print('a')
    # print(a.result())  # a will never complete because it is waiting on b.
    return 6

def run():
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        a = executor.submit(get_interfaces, '192.168.106.100', 'public')
        b = executor.submit(get_interfaces, '192.168.106.100', 'public')
        c = executor.submit(get_interfaces, '192.168.106.100', 'public')
        d = executor.submit(get_interfaces, '192.168.106.100', 'public')

        print('all_submit')
        submit_time = time.time()
        concurrent.futures.wait([a, b, c, d])
        print('submit_end {:.2f}'.format(time.time() - submit_time))

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    a = executor.submit(run)
    b = executor.submit(run)
    c = executor.submit(run)
    d = executor.submit(run)
    print('start')
    start_time = time.time()
    concurrent.futures.wait([a, b, c, d])
    print('{:.2f}'.format(time.time() - start_time))
    print('end')
