import logging
import time
from concurrent.futures import wait, ThreadPoolExecutor
from multiprocessing import Manager
from threading import Lock
from queue import Queue, Empty

from remote_access.ssh.worker_queue import SSHQueueWorker
from services import get_service


class SSHConnection:
    def __init__(self):
        self.devices = {}
        self.lock = Lock()

    def add_connection(self, device):
        self.lock.acquire()
        self.devices[device['device_ip']] = device['data']
        self.lock.release()

    def remove_connection(self, device_ip):
        self.lock.acquire()
        del self.devices[device_ip]
        self.lock.release()

    def check_connection(self, device_list):
        logging.debug("Check connect")
        self.lock.acquire()
        logging.debug("Start check connect")
        results = []
        for device in device_list:
            _device = self.devices.get(device)
            if not _device:
                results.append(False)
            else:
                results.append(_device['is_connect_value'].value)
        if not all(results):
            self.lock.release()
            return results
        results = []
        for device in device_list:
            self.devices[device]['work_q'].put({'type': 'recheck'})
        for device in device_list:
            result = self.devices[device]['result_q'].get()
            results.append(result)
        logging.info(results)
        self.lock.release()
        return results

    def send_config_set(self, config_set):
        self.lock.acquire()
        for device, cmd in config_set.items():
            _device = self.devices.get(device)
            if not _device:
                return False
        for _device, cmd in config_set.items():
            self.devices.get(_device)['work_q'].put({
                'type': 'send_config',
                'data': cmd
            })
        results = {}
        for _device in config_set.keys():
            results[_device] = self.devices.get(_device)['result_q'].get()
        self.lock.release()
        return results


class SSHWorker:
    def __init__(self, *tasks):
        # self.max_worker = 2  # Maximum update flow worker
        self.set_worker = []
        self.stop_signal = False
        self.device_service = get_service("device")
        self.results_q = Queue()
        self.ssh_connection = SSHConnection()
        self.manager = Manager()
        self.tasks = [task() for task in tasks]

    def stop(self):
        self.stop_signal = True
        logging.info("Waiting worker success task")
        wait(self.set_worker)
        logging.info("Stop SSHWorker success.")

    def _control_worker_queue(self, results_q):
        logging.info("Control worker queue start")
        _running = {}
        while True:
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
        while True:
            try:
                result = self.results_q.get(timeout=0.05)
                if result:
                    if result.get('remove'):
                        self.ssh_connection.remove_connection(result['device_ip'])
                    else:
                        self.ssh_connection.add_connection(result)
            except Empty:
                break

    def start(self):
        pool = ThreadPoolExecutor(1)
        # Start control worker queue
        pool.submit(self._control_worker_queue, self.results_q)
        time.sleep(10)
        while not self.stop_signal:
            self._update_worker_queue()
            try:
                logging.info("Start task")
                logging.info(self.tasks)
                for task in self.tasks:
                    task.run(self.ssh_connection)
                logging.info("End task")
                time.sleep(10)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(e)
