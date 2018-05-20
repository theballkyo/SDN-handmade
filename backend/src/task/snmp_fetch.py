import logging

from task.task import Task
from snmp.snmp_worker import SNMPWorker
from repository import get_service
from concurrent.futures import wait, ProcessPoolExecutor
import sdn_utils
from tools import PathFinder


class SNMPFetch(Task):

    def __init__(self):
        self.device_service = get_service('device')
        num_worker = sdn_utils.get_snmp_num_worker()

        self.executor = ProcessPoolExecutor(num_worker)
        self.running_device = []
        self.path_finder = PathFinder(auto_update_graph=False)

    def run(self, ssh_connection):
        logging.info("SNMP fetch start")
        devices = self.device_service.get_all()
        for device in devices:
            self.running_device.append(self.executor.submit(SNMPWorker.run_loop, device))
        wait(self.running_device)
        logging.info("SNMP fetch end")
        self.path_finder.update_graph()
