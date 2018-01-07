""" SDN Handmade for legacy cisco device """
import multiprocessing
import logging
import time
# import threading
from snmp.snmp_worker import device


def main():
    """ test
    """
    print(device)

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    logging.debug('Starting')
    main()
