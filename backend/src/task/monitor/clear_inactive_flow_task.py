import datetime

from repository import get_service
from worker.ssh.ssh_worker import SSHConnection


class ClearInactiveFlowTask:
    def __init__(self):
        self.inactive_time = 70  # In seconds
        # self.low_utilize = 60
        # self.normal_utilize = 70
        # self.high_utilize = 80
        self.device_service = get_service('device')
        self.policy_service = get_service('policy')
        self.policy_seq_service = get_service('policy_seq')
        self.netflow_service = get_service('netflow')

    def run(self, ssh_connection: SSHConnection):
        """
        1. Find interface than utilize < xx %
        2. Find policy is old path pass the interface
        3. check flow utilize
        4. if flow utilize + interface utilize < high load %. Remove policy
        :param ssh_connection:
        :return:
        """
        # later_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=self.inactive_time)
        later_time = datetime.datetime.now() - datetime.timedelta(seconds=self.inactive_time)
        self.netflow_service.netflow.delete_many({'created_at': {'$lte': later_time}})
        return True
