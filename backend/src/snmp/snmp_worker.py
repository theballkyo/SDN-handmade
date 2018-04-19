import asyncio
import logging
import time
from concurrent.futures import wait, ProcessPoolExecutor

import sdn_utils
import services
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

        host = device['management_ip']
        community = device['snmp_info']['community']
        port = device['snmp_info']['port']

        # results = await asyncio.gather(
        #     asyncio.ensure_future(snmp_process.process_system(host, community, port)),
        #     asyncio.ensure_future(snmp_process.process_route(host, community, port)),
        #     asyncio.ensure_future(snmp_process.process_cdp(host, community, port)),
        # )

        # if all(r is None for r in results):
        #     logging.info("SNMP Worker: Device ip %s is gone down", host)

        await snmp_process.process_system(host, community, port)
        await snmp_process.process_route(host, community, port)
        await snmp_process.process_cdp(host, community, port)

    @staticmethod
    def run_loop(device):
        """ Run loop
        """
        management_ip = device['management_ip']
        device_service = services.get_service('device')
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        if can_uvloop:
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        logging.debug("SNMP Worker: Start loop device IP %s", management_ip)

        loop.run_until_complete(
            SNMPWorker.get_and_store(device)
        )
        device_service.set_snmp_finish_running(management_ip)

        loop.close()
        logging.debug("SNMP Worker: device IP %s has stopped", device['management_ip'])

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
        device_service = services.get_service('device')
        while not self.stop_signal:
            self.running = list(filter(lambda x: x.done() is False, self.running))
            active_device = device_service.get_by_snmp_can_run(self.loop_time)

            for device in active_device:
                # device_service = services.get_service('device')
                management_ip = device['management_ip']
                if device_service.snmp_is_running(management_ip):
                    return

                # Mark device SNMP is running
                device_service.set_snmp_running(device['management_ip'], True)
                # Submit
                self.running.append(executor.submit(SNMPWorker.run_loop, device))
            time.sleep(1)
