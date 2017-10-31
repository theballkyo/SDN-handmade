# from snmp_worker import SNMPWorker
# from netflow import NetflowWorker
import time
import sdn_handmade as sdn
import logging, sys


def main():
    # Start SNMP worker
    # snmp_worker = SNMPWorker()
    # Start Netflow worker
    # netflow_worker = NetflowWorker()

    # Create topoloygy
    topoloygy = sdn.Topoloygy(
        netflow_ip='192.168.222.1'
    )

    # Create device object
    device_maingw = sdn.Router(
        ip='192.168.106.100',
    )
    device_r1 = sdn.Router(
        ip='192.168.106.101'
    )
    device_r2 = sdn.Router(
        ip='192.168.106.102',
    )
    device_r3 = sdn.Router(
        ip='192.168.106.103'
    )
    device_r4 = sdn.Router(
        ip='192.168.106.105',
    )

    # Add device to topoloygy
    topoloygy.add_device([device_maingw, device_r1, device_r2, device_r3,
                          device_r4])

    logging.debug(topoloygy.devices)

    # Start topoloygy loop
    topoloygy.run()
    # print('qqqqqqqqqqqqqqqqqqqqqqqqqqqq')
    time.sleep(10)
    print(topoloygy.get_neighbor())

if __name__ == '__main__':
    FORMAT = '%(asctime)-15s - %(name)s - %(message)s'
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
                        format=FORMAT)
    main()
