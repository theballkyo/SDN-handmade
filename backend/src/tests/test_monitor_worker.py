import matplotlib

matplotlib.use('Agg')

from task.monitor.traffic_monitor_task import TrafficMonitorTask


def main():
    # from repository import get_service
    # nfsv = get_service('netflow')
    # s = nfsv.summary_flow_v2(
    #     '192.168.1.6',
    #     # datetime.datetime(2018, 3, 15, 22, 00)
    # )
    # s = list(s)
    # print(s)
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
