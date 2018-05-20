import asyncio
import logging
import time
from concurrent.futures import wait, ProcessPoolExecutor

import repository
import sdn_utils
from snmp import snmp_process

try:
    import uvloop

    can_uvloop = True
except ImportError:
    can_uvloop = False


class SNMPWorker:
    def __init__(self):
        self.running = []
        self.stop_signal = False
        self.loop_time = 7

    @staticmethod
    async def get_and_store(device):
        """ Get snmp information and add to database
        """

        device_id = device['_id']
        host = device['management_ip']
        community = device['snmp_info']['community']
        port = device['snmp_info']['port']

        results = await asyncio.gather(
            asyncio.ensure_future(snmp_process.process_system(device_id, host, community, port)),
            asyncio.ensure_future(snmp_process.process_route(device_id, host, community, port)),
            asyncio.ensure_future(snmp_process.process_cdp(device_id, host, community, port)),
        )

        device_repository = repository.get("device")
        l = [r for r in results]
        # logging.info(l)
        if not all(l):
            device_repository.set_snmp_is_connect_by_mgmt_ip(host, False)
            logging.info("SNMP Worker: Device ip %s is gone down", host)
        else:
            device_repository.set_snmp_is_connect_by_mgmt_ip(host, True)

        # await snmp_process.process_system(host, community, port)
        # await snmp_process.process_route(host, community, port)
        # await snmp_process.process_cdp(host, community, port)

    @staticmethod
    def run_loop(device):
        """ Run loop
        """
        management_ip = device['management_ip']
        device_repository = repository.get('device')
        # logging.info("SNMP Worker: Start loop device IP %s", management_ip)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        if can_uvloop:
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

        loop.run_until_complete(
            SNMPWorker.get_and_store(device)
        )
        device_repository.set_snmp_finish_running(management_ip)

        loop.close()
        # logging.info("SNMP Worker: device IP %s has stopped", device['management_ip'])

    def shutdown(self):
        """ shutdown
        """
        # Todo
        self.stop_signal = True
        logging.info("SNMP Worker: shutdown...")
        logging.debug(self.running)
        for future in self.running:
            future.cancel()
            time.sleep(0.1)
        wait(self.running)
        logging.info("SNMP Worker: shutdown complete")

    def run(self):
        num_worker = sdn_utils.get_snmp_num_worker()

        executor = ProcessPoolExecutor(num_worker)
        device_repository = repository.get('device')
        while not self.stop_signal:
            self.running = list(filter(lambda x: x.done() is False, self.running))
            active_device = device_repository.get_by_snmp_can_run(self.loop_time)

            for device in active_device:
                # device_service = services.get_service('device')
                management_ip = device['management_ip']
                if device_repository.snmp_is_running(management_ip):
                    return

                # Mark device SNMP is running
                device_repository.set_snmp_running(device['management_ip'], True)
                # Submit
                self.running.append(executor.submit(SNMPWorker.run_loop, device))
            time.sleep(1)
