from worker.netflow.netflow_worker import NetflowWorker
import logging


def main():
    netflow_worker = NetflowWorker("0.0.0.0", 23456)
    try:
        netflow_worker.start()
        netflow_worker.join()
    except KeyboardInterrupt:
        netflow_worker.shutdown()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)-15s [%(levelname)s] (%(threadName)-10s): %(message)s',)
    main()
