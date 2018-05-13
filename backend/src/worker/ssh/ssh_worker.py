import logging
import time
import traceback

from concurrent.futures import wait, ThreadPoolExecutor
from multiprocessing import Manager
from threading import Lock
from queue import Queue, Empty

from remote_access.ssh.worker_queue import SSHQueueWorker
from repository import DeviceRepository
import repository


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

    def update(self, device_ip, ssh_info):
        logging.info("Wait update")
        self.lock.acquire()
        logging.info("Start Update")
        try:
            self.devices[device_ip]['work_q'].put({
                "type": "reconnect",
                "ssh_info": ssh_info
            })
            result = self.devices[device_ip]["result_q"].get()
            logging.info(result)
        except Exception as e:
            logging.info(e)
        logging.info("End Update")
        self.lock.release()
        logging.info("Release Update")

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
                self.lock.release()
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
        self.device_repository = repository.get("device")
        self.results_q = Queue()
        self.ssh_connection = SSHConnection()
        self.manager = Manager()
        self.tasks = [task() for task in tasks]
        self.initialTasks = []
        self.pool = None
        self.stop_control_q = Queue(maxsize=1)

    def stop(self):
        self.stop_signal = True
        logging.info("Waiting worker success task")
        self.stop_control_q.put('')
        self.pool.shutdown()

    def _control_worker_queue(self, results_q, stop_control_q):
        logging.info("Control worker queue start")
        _running = {}
        while True:
            try:
                stop_control_q.get(timeout=0.01)
                break
            except Empty:
                pass

            devices = self.device_repository.get_all()
            for device in devices:
                # If exists skip
                if device['management_ip'] in _running.keys():
                    if device.get("status") == DeviceRepository.STATUS_WAIT_UPDATE:
                        # logging.info("Start ssh update")
                        device_ip = device['management_ip']
                        ssh_info = device['ssh_info']
                        ssh_info['ip'] = device['management_ip']
                        ssh_info['device_type'] = device['type']
                        # logging.info(ssh_info)
                        results_q.put({
                            "type": "update",
                            "device_ip": device_ip,
                            "ssh_info": ssh_info
                        })
                        self.device_repository.model.update_one({
                            "management_ip": device_ip
                        }, {"$set": {"status": DeviceRepository.STATUS_ACTIVE}})

                    continue

                ssh_info = device['ssh_info']
                ssh_info['ip'] = device['management_ip']
                ssh_info['device_type'] = device['type']

                result = {
                    'device_ip': device['management_ip'],
                    'data': {
                        'ssh_info': ssh_info,
                        'work_q': Queue(maxsize=1),
                        'result_q': Queue(maxsize=1),
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
                logging.info(self.results_q.qsize())
                result = self.results_q.get(timeout=0.05)
                if result:
                    if result.get('remove'):
                        self.ssh_connection.remove_connection(result['device_ip'])
                    elif result.get("type") == "update":
                        self.ssh_connection.update(result["device_ip"], result["ssh_info"])
                    else:
                        self.ssh_connection.add_connection(result)
            except Empty:
                break

    def start(self):
        self.pool = ThreadPoolExecutor(1)
        # Start control worker queue
        self.pool.submit(self._control_worker_queue, self.results_q, self.stop_control_q)
        time.sleep(10)
        # Todo initial task

        # -------------------
        while not self.stop_signal:
            self._update_worker_queue()
            try:
                # logging.info("Start task")
                # logging.info("Tasks: {}".format(self.tasks))
                for task in self.tasks:
                    task.run(self.ssh_connection)
                    time.sleep(0.1)
                # logging.info("End task")
                time.sleep(3)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logging.error(traceback.format_exc())
