import matplotlib

matplotlib.use('Agg')

from task.monitor.traffic_monitor_task import TrafficMonitorTask


def main():
    tmt = TrafficMonitorTask()
    tmt.run()


if __name__ == '__main__':
    import logbug
    logbug.init()
    # logbug = logbug.LogBug(
    # logbug.auto_run()
    # FORMAT = '%(asctime)-15s [%(levelname)s] (%(threadName)-10s) %(message)s'
    # logging.basicConfig(level=logging.DEBUG,
    #                     format=FORMAT)
    main()
