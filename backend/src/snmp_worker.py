import asyncio
import logging
import multiprocessing
import queue
import time
import snmp_process
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


class SNMPWorker(multiprocessing.Process):
    def __init__(self):
        super(SNMPWorker, self).__init__()
        self.devices = []
        self.device_running = []
        self.daemon = True
        self.loop_time = 15
        self.__shutdown = multiprocessing.Queue()
        self.worker_p = []
        # asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

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

    async def get_and_store(self, device):
        """ Get snmp infomation and add to database
        """

        host = device['management_ip']
        community = 'public'
        port = 161

        print("{} {} {}".format(host, community, port))
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
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        i = 1
        while i == 1:
            i += 1
            logging.debug("SNMP Worker: Start loop device IP %s", device['management_ip'])
            start = time.time()

            loop.run_until_complete(
                self.get_and_store(device)
            )

            # logging.debug("Process took: {:.2f} seconds".format(time.time() - start))
            # sleep_time = self.loop_time - (time.time() - start)
            # # logging.debug("Sleep time {:.2f}".format(sleep_time))
            # if sleep_time < 1:
            #     sleep_time = 1
            # try:
            #     shutdown_flag = self.__shutdown.get(True, sleep_time)
            # except queue.Empty:
            #     shutdown_flag = False
            # # logging.debug(shutdown_flag)
            # if shutdown_flag or shutdown_flag == device.ip:
            #     break
        loop.close()
        logging.debug("SNMP Worker: device IP %s has stopped", device['management_ip'])
        # Disconnect MongoDB
        # disconnect()

    def shutdown(self):
        """ shutdown
        """
        # Todo
        logging.info("SNMP Worker: shutdown...")
        for _ in range(len(self.device_running) + 2):
            logging.debug("SNMP Worker send shutdown signal")
            self.__shutdown.put(True)
            time.sleep(0.1)
        time.sleep(2)
        for device_proc in self.device_running:
            logging.info("SNMP Worker: wait for process end...")
            logging.debug(device_proc)
            device_proc.join(30)
        logging.info("SNMP Worker: shutdown complete")

    def run(self):
        active_device = services.device_service.get_all()
        for device in active_device:
            mp = multiprocessing.Process(target=self.run_loop, args=(device,))
            mp.daemon = True
            mp.start()
