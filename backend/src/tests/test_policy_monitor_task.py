import matplotlib

matplotlib.use('Agg')


def main():
    from task.monitor.policy_monitor_task import PolicyMonitorTask

    pmt = PolicyMonitorTask()
    pmt.run(None)


if __name__ == '__main__':
    import logbug

    logbug.init()
    main()
