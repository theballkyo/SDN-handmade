import asyncio
import logging
import multiprocessing
import queue
import time
import snmp_process
import threading
from netaddr import IPNetwork

import services

import sdn_utils
from database import get_mongodb, disconnect
from snmp_async import (get_cdp, get_interfaces, get_ip_addr, get_lldp,
                        get_routes, get_system_info)


# try:
#     import uvloop
# except:
#     pass


class SNMPWorker:
    def __init__(self):
        self.running = []
        self.stop_signal = False
        self.devices = []
        self.device_running = []
        self.daemon = True
        self.loop_time = 15
        self.__shutdown = multiprocessing.Queue()
        self.worker_p = []
        self.device_service = services.get_service('device')

    def add_device(self, device, run=False):
        """ Add device to worker
        """
        # if device
        # self.devices.append({
        #     'host': host,
        #     'port': port,
        #     'community': community
        # })
        self.devices.append(device)

        if run:
            t_s = multiprocessing.Process(
                name=device.ip,
                target=self.run_loop,
                args=(device,)
            )
            t_s.daemon = True
            t_s.start()
            self.device_running.append(t_s)

    def remove_device(self, device, port=161):
        """ Remove device from worker
        """
        try:
            for _ in self.device_running:
                self.__shutdown.put(device.ip)
            for device_run in self.device_running:
                if device_run.name == device.ip:
                    self.device_running.remove(device_run)
                    break
            self.devices.remove(device)
        except ValueError:
            pass

    @staticmethod
    async def get_and_store(device):
        """ Get snmp information and add to database
        """

        host = device['management_ip']
        community = 'public'
        port = 161

        results = await asyncio.gather(
            asyncio.ensure_future(snmp_process.process_system(host, community, port)),
            asyncio.ensure_future(snmp_process.process_route(host, community, port)),
            asyncio.ensure_future(snmp_process.process_cdp(host, community, port)),
        )

        if all(r is None for r in results):
            logging.info("SNMP Worker: Device ip %s is gone down", host)

    def run_loop(self, device):
        """ Run loop
        """
        device_service = services.get_service('device')
        management_ip = device['management_ip']
        if device_service.snmp_is_running(management_ip):
            return
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        logging.debug("SNMP Worker: Start loop device IP %s", management_ip)

        device_service.set_snmp_running(management_ip, True)
        loop.run_until_complete(
            self.get_and_store(device)
        )
        device_service.set_snmp_running(management_ip, False)

        loop.close()
        logging.debug("SNMP Worker: device IP %s has stopped", device['management_ip'])

    def shutdown(self):
        """ shutdown
        """
        # Todo
        self.stop_signal = True
        logging.info("SNMP Worker: shutdown...")
        logging.debug(self.running)
        for proc in self.running:
            proc.join(30)
        logging.info("SNMP Worker: shutdown complete")

    def run(self):
        while not self.stop_signal:
            logging.debug("SNMP worker: run loop")
            self.running = list(filter(lambda proc: proc.is_alive() or proc.exitcode is not None, self.running))

            active_device = self.device_service.get_by_snmp_is_running(False)
            for device in active_device:
                mp = multiprocessing.Process(target=self.run_loop, args=(device,))
                mp.daemon = True
                self.running.append(mp)
                mp.start()

            time.sleep(3)
