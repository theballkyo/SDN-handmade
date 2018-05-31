import queue
import netmiko
import time

from netmiko.ssh_exception import NetMikoTimeoutException, NetMikoAuthenticationException
import threading
import multiprocessing as mp
import logging
import repository
from router_command.policy_command import get_netmiko_type


class SSHQueueWorker(threading.Thread):

    def __init__(self, ssh_info, work_q, result_q, is_connect_value, stop_signal_value, **kwargs):
        super(SSHQueueWorker, self).__init__()
        self.ssh_info = ssh_info
        self._work_queue = work_q
        self._result_q = result_q
        self._is_connect = is_connect_value
        self._stop_signal = stop_signal_value
        if kwargs.get('max_retry_timeout'):
            self._max_retry_timeout = kwargs.get('max_retry_timeout')
        else:
            self._max_retry_timeout = 3
        self._lock = threading.Lock()

        self.setName('SSH-Q-WORKER' + ssh_info['ip'])
        self.device_repository = repository.get("device")

    def run(self):
        self.new_worker_queue()

    def new_worker_queue(self):
        work = None  # Default null
        ssh_info = self.ssh_info
        retry_count = 0
        while True:
            self._is_connect.value = False
            self.device_repository.set_ssh_is_connect_by_mgmt_ip(ssh_info['ip'], False)
            try:
                net_connect = netmiko.ConnectHandler(
                    # device_type=ssh_info['device_type'],  # Old style
                    device_type=get_netmiko_type(ssh_info['device_type']),  # New style
                    ip=ssh_info['ip'],
                    username=ssh_info['username'],
                    password=ssh_info['password'],
                    port=ssh_info['port'],
                    secret=ssh_info['secret'],
                    verbose=False,
                    global_delay_factor=0.5,
                    timeout=5,
                )
                #  Enter enable mode
                net_connect.enable()
                reconnect = False
                self._is_connect.value = True
                retry_count = 0
                # Set ssh is connect status
                self.device_repository.set_ssh_is_connect_by_mgmt_ip(ssh_info['ip'], True)
            except NetMikoTimeoutException:
                retry_count += 1
                logging.info("Name: %s ssh timeout %d", self.getName(), retry_count)
                if retry_count >= self._max_retry_timeout:
                    self._result_q.put("timeout")
                    break
                if self._stop_signal.value:
                    break
                continue

            except NetMikoAuthenticationException:
                #  Stop
                logging.info("Name: %s can't connect ssh", self.getName())
                self._result_q.put(None)
                break

            while True:
                # logging.info("Name: %s run looping", self.getName())
                if not reconnect:
                    try:
                        work = self._work_queue.get(timeout=30)
                    except queue.Empty:
                        work = None
                else:
                    break

                # logging.info("Start find prompt")
                try:
                    net_connect.find_prompt(delay_factor=1)
                    self._is_connect.value = True
                except ValueError:
                    self._is_connect.value = False
                    reconnect = True
                # logging.info("End find prompt")

                if not work:
                    continue
                if not isinstance(work, dict):
                    continue
                if not work.get('type', None):
                    continue

                if work["type"] == "reconnect":
                    ssh_info = work["ssh_info"]
                    self._result_q.put("ok")
                    net_connect.disconnect()
                    break

                if work['type'] == 'recheck':
                    self._result_q.put(self._is_connect.value)

                #  Reconnecting...
                if reconnect:
                    break

                if work['type'] == 'send_config':
                    # Send config
                    logging.info("Start send config")
                    while True:
                        try:
                            net_connect.enable()
                            net_connect.send_config_set(work['data'], max_loops=2000)
                        except ValueError:
                            logging.exception("SSH Worker: set config: %s")
                            continue
                        break
                    logging.info("End send config")
                    self._result_q.put(True)
