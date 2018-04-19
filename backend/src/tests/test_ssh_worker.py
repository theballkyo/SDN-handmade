from worker.ssh.ssh_worker import SSHWorker
from task.monitor.policy_monitor_task import PolicyMonitorTask
from task.monitor.clear_policy_task import ClearPolicyTask
from task.monitor.clear_inactive_flow_task import ClearInactiveFlowTask
from threading import Thread
import logging
import timeit


def main():
    ssh_worker = SSHWorker(ClearPolicyTask)
    t = Thread(target=ssh_worker.start, daemon=True)
    t.start()
    try:
        t.join()
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        ssh_worker.stop()
    except Exception as e:
        print(e)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] (%(threadName)-10s) %(message)s',
    )
    # logbug.init(10)
    usage_time = timeit.timeit(main, number=1)
    # print("Usage time: {:.3f}".format(usage_time))
