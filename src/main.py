""" SDN Handmade for legacy cisco device """
import multiprocessing
import logging
import time
# import threading

from snmp_worker import SNMPWorker
from netflow_server import netflow_server


def main():
    """ test
    """
    p1 = multiprocessing.Process(
        daemon=True,
        target=netflow_server, args=('192.168.222.1', 23456)
        )
    # p1.start()

    snmp_worker = SNMPWorker()
    ps = [p1]
    devices = [
        {'host': '192.168.106.100', 'community': 'public'},
        {'host': '192.168.106.101', 'community': 'public'},
        {'host': '192.168.106.102', 'community': 'public'},
        {'host': '192.168.106.103', 'community': 'public'},
        {'host': '192.168.106.105', 'community': 'public'},
        # {'host': '192.168.222.101', 'community': 'public'},
        #   {'host': '10.30.6.53', 'community': 'public'}
        ]


    for device in devices:
        snmp_worker.add_device(**device)

    snmp_worker.run()

    time.sleep(5)
    # snmp_worker.add_device('192.168.106.103', 'public', run=True)
    print('New run')

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    logging.debug('Starting')
    main()
