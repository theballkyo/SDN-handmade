""" SDN Handmade start class
"""
import logging
import threading
import time

import repository
from task.monitor.clear_device_task import ClearDeviceTask
from task.monitor.clear_inactive_flow_task import ClearInactiveFlowTask
from task.monitor.clear_policy_task import ClearPolicyTask
from task.monitor.policy_monitor_task import PolicyMonitorTask
from task.monitor.traffic_monitor_task import TrafficMonitorTask
from task.snmp_fetch import SNMPFetch
from worker.netflow.netflow_worker import NetflowWorker
from worker.ssh.ssh_worker import SSHWorker


class Topology:
    """ Topology class
    """

    def __init__(self, netflow_ip='127.0.0.1', netflow_port=23456):
        self._create_time = time.time()

        self.app_repository = repository.get("app")
        self.device_repository = repository.get("device")
        self.used_flow_id = repository.get("used_flow_id")

        self._netflow_worker = NetflowWorker(
            netflow_ip,
            netflow_port
        )

        # Tasks
        self._ssh_worker = SSHWorker(
            SNMPFetch,
            ClearInactiveFlowTask,
            ClearPolicyTask,
            TrafficMonitorTask,
            PolicyMonitorTask,
            ClearDeviceTask
        )

        # Thread for SSH Worker
        self._ssh_worker_t = None

        self.init()
        logging.info("Create topology")

    def init(self):
        from pymongo import UpdateOne
        op = []
        for i in range(0, 65535):
            op.append(
                UpdateOne({'_id': i}, {'$setOnInsert': {'in_use': False}}, upsert=True)
            )
        try:
            self.used_flow_id.model.bulk_write(op)
        except Exception as e:
            logging.error(e)

    def run(self):
        """ Start topology loop
        """

        # Resetting SNMP status
        devices = self.device_repository.get_all()
        for device in devices:
            self.device_repository.set_snmp_running(device['management_ip'], False)

        self._netflow_worker.start()
        self._ssh_worker_t = threading.Thread(target=self._ssh_worker.start)
        self._ssh_worker_t.name = "SSH-WORKER"
        self._ssh_worker_t.start()
        self.app_repository.set_running(True)

    def shutdown(self):
        """ Shutdown topology
        """
        self.app_repository.set_running(False)

        self._netflow_worker.shutdown()
        self._ssh_worker.stop()
        time.sleep(1)
        self._netflow_worker.join()
