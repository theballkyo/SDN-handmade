import multiprocessing as mp

import repository
from snmp import snmp_worker


def main():
    device_repository = repository.get('device')
    devices = device_repository.get_all()
    for device in devices:
        device_repository.set_snmp_running(device['management_ip'], False)
    worker = snmp_worker.SNMPWorker()
    a = mp.Process(target=worker.run)
    try:
        a.start()
    except KeyboardInterrupt:
        worker.shutdown()
        a.join()


if __name__ == '__main__':
    import logbug

    logbug.init()
    # logging.basicConfig(level=logging.DEBUG)
    main()
