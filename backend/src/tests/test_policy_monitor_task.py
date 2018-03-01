import matplotlib

matplotlib.use('Agg')


def main():
    from worker.monitor.policy_monitor_task import PolicyMonitorTask

    pmt = PolicyMonitorTask()
    pmt.run()


if __name__ == '__main__':
    import logbug

    logbug.init()
    main()
