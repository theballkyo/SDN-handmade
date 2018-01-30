import snmp_worker
import multiprocessing as mp
import logging
import services


def main():
    device_service = services.get_service('device')
    devices = device_service.get_all()
    for device in devices:
        device_service.set_snmp_running(device['management_ip'], False)
    worker = snmp_worker.SNMPWorker()
    mp.Process(target=worker.run).start()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
