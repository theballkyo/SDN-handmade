import matplotlib

matplotlib.use('Agg')


def main():
    from task.monitor.clear_policy_task import ClearPolicyTask
    from worker.ssh.fake_ssh_connection import FakeSSHConnection
    cpt = ClearPolicyTask()
    cpt.run(FakeSSHConnection())


if __name__ == '__main__':
    import logbug

    logbug.init()
    main()
