from worker.netflow.netflow_worker import NetflowWorker
import logbug
import settings


def main():
    netflow_worker = NetflowWorker(settings.netflow['bind_ip'], settings.netflow['bind_port'])
    try:
        netflow_worker.start()
        netflow_worker.join()
    except KeyboardInterrupt:
        netflow_worker.shutdown()


if __name__ == '__main__':
    logbug.init()
    main()
