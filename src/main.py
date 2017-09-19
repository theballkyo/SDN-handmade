# from snmp import get_interfaces
from snmp_worker import store_interface
from netflow_server import netflow_server
from multiprocessing import Process

import logging
import threading

def main():
    p1 = Process(target=netflow_server, args=('192.168.222.1', 23456))
    p1.start()
    # p2 = Process(target=netflow_server, args=('192.168.222.1', 23457))
    # p2.start()
    # p3 = Process(target=netflow_server, args=('192.168.222.1', 23458))
    # p3.start()
    ps = [p1]
    # interfaces = get_interfaces(host='192.168.106.100', community='public')
    devices = [{'ip': '192.168.106.100'}, {'ip': '192.168.106.101'}]

    p_snmp_list = []

    for device in devices:
        p_snmp = Process(target=store_interface, args=(device['ip'], 'public'))
        p_snmp.daemon = True
        p_snmp.start()
        p_snmp_list.append(p_snmp)
    for p in p_snmp_list:
        p.join()

    port = 23459
    while 1:
        print("> ", end='')
        a = input()
        if a == 'stop':
            for p in ps:
                p.terminate()
        elif a == 'check':
            for p in ps:
                print(p)
        elif a == 'exit':
            for p in ps:
                p.terminate()
                p.join()
            print(p_snmp)
            break
        elif a == 'spawn':
            p = Process(target=netflow_server, args=('192.168.222.1', port))
            p.start()
            ps.append(p)
            port += 1

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.debug('Starting')
    main()
