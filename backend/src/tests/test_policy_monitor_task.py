import matplotlib
import database

matplotlib.use('Agg')


def main():
    from task.monitor.policy_monitor_task import PolicyMonitorTask
    from task.monitor.traffic_monitor_task import TrafficMonitorTask
    from task.monitor.clear_policy_task import ClearPolicyTask
    from task.monitor.clear_device_task import ClearDeviceTask
    from mockup import FakeSSHConnection

    ssh_connection = FakeSSHConnection()
    pmt = PolicyMonitorTask()
    tmt = TrafficMonitorTask()
    cpt = ClearPolicyTask()
    cdt = ClearDeviceTask()

    tmt.run(None)
    # pmt.run(ssh_connection)
    # cpt.run(ssh_connection)
    # cdt.run(ssh_connection)


if __name__ == '__main__':
    import logbug

    logbug.init()
    database.set_connection_name('default')
    main()
