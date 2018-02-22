import logging
import time
from concurrent.futures import wait, ThreadPoolExecutor

from flow import FlowState
from remote_access.ssh.ssh_process import run_flow_loop
from service import FlowTableService
from services import get_service
import router_command as router_cmd
from remote_access.ssh.worker_queue import SSHQueueWorker
from queue import Queue, Empty
from multiprocessing import Manager


class SSHWorker:
    def __init__(self, *tasks):
        # self.max_worker = 2  # Maximum update flow worker
        self.set_worker = []
        self.stop_signal = False
        self.device_service = get_service("device")
        self.results_q = Queue()
        self.ssh_connection = {}
        self.manager = Manager()
        self.tasks = (task() for task in tasks)

    def stop(self):
        self.stop_signal = True
        logging.info("Waiting worker success task")
        wait(self.set_worker)
        logging.info("Stop SSHWorker success.")

    def _control_worker_queue(self, results_q):
        logging.info("Control worker queue start")
        _running = {}
        while 1:
            devices = self.device_service.get_all()
            for device in devices:
                # If exists skip
                if device['management_ip'] in _running.keys():
                    continue

                ssh_info = device['ssh_info']
                ssh_info['ip'] = device['management_ip']
                ssh_info['device_type'] = device['type']

                result = {
                    'device_ip': device['management_ip'],
                    'data': {
                        'ssh_info': ssh_info,
                        'work_q': Queue(),
                        'result_q': Queue(),
                        'is_connect_value': self.manager.Value(bool, False),
                        'stop_signal_value': self.manager.Value(bool, False)
                    }
                }
                logging.info("Create SSHQueueWorker")
                queue_worker = SSHQueueWorker(**result['data'])
                queue_worker.start()
                logging.info("Started SSHQueueWorker")
                results_q.put(result)
                _running[device['management_ip']] = queue_worker

            # Clear not Alive thread
            _remove = []
            for device in _running.keys():
                if not _running[device].is_alive():
                    _remove.append(device)
            for remove in _remove:
                results_q.put({'device_ip': remove, 'remove': True})
                _running.pop(remove)
            time.sleep(1)

    def _update_worker_queue(self):
        # Loop when results_q is empty
        while 1:
            try:
                result = self.results_q.get(timeout=0.05)
                if result:
                    if result.get('remove'):
                        del self.ssh_connection[result['device_ip']]
                    else:
                        self.ssh_connection[result['device_ip']] = result['data']
            except Empty:
                break

    def start(self):
        pool = ThreadPoolExecutor(1)
        # Start control worker queue
        pool.submit(self._control_worker_queue, self.results_q)
        while not self.stop_signal:
            self._update_worker_queue()
            try:
                for task in self.tasks:
                    task.run(self.ssh_connection)
                time.sleep(1)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(e)
