import asyncio
import logging
import multiprocessing
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, wait

from pymongo import ReplaceOne

import sdn_utils
from database import MongoDB
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
        self.loop_time = 60
        self.__shutdown = multiprocessing.Queue()
        self.worker_p = []
        # asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    def add_device(self, device, run=False, port=161):
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
            t_s.start()
            self.device_running.append(t_s)

    def remove_device(self, device, port=161):
        """ Remove device from worker
        """
        try:
            self.devices = self.devices.remove(device)
        except ValueError:
            pass

    async def get_and_store(self, device):
        """ Get snmp infomation and add to database
        """
        mongo = MongoDB()

        host = device.ip
        community = device.snmp_community
        port = device.snmp_port

        results = await asyncio.gather(
            asyncio.ensure_future(get_system_info(host, community, port)),
            asyncio.ensure_future(get_routes(host, community, port)),
            asyncio.ensure_future(get_ip_addr(host, community, port)),
            asyncio.ensure_future(get_interfaces(host, community, port)),
            asyncio.ensure_future(get_cdp(host, community, port)),
            # asyncio.ensure_future(get_lldp(host, community, port)), # Todo
        )

        if all(r is None for r in results):
            logging.debug("SNMP Server for device ip %s is gone down", host)
            return

        system_info = results[0]
        routes = results[1]
        ip_addrs = results[2]
        interfaces = results[3]
        # CDP
        cdp = results[4]
        # LLDP
        # lldp = results[5]

        # Todo optimize this
        # for if_index, interface in enumerate(interfaces):
        #     for ip_index, ip_addr in enumerate(ip_addrs):
        #         if interface['index'] == ip_addr['if_index']:
        #             interface['ipv4_address'] = ip_addr['ipv4_address']
        #             interface['subnet'] = ip_addr['subnet']

        for if_index in range(len(interfaces)):
            for ip_index in range(len(ip_addrs)):
                if interfaces[if_index]['index'] == ip_addrs[ip_index]['if_index']:
                    interfaces[if_index]['ipv4_address'] = ip_addrs[ip_index]['ipv4_address']
                    interfaces[if_index]['subnet'] = ip_addrs[ip_index]['subnet']
                    break

        # print(interfaces[0])
        my_device = mongo.db.device.find_one({
            'device_ip': host
        })

        if my_device:
            for interface in interfaces:
                for my_interface in my_device['interfaces']:
                    if interface['description'] == my_interface['description']:
                        # In
                        in_octets = interface['out_octets'] - my_interface['out_octets']
                        in_in_time = system_info['uptime'] - my_device['uptime']
                        bw_in_usage_percent = sdn_utils.cal_bw_usage_percent(
                            in_octets,
                            interface['speed'],
                            in_in_time)
                        # Out
                        out_octets = interface['out_octets'] - my_interface['out_octets']
                        out_in_time = system_info['uptime'] - my_device['uptime']
                        bw_out_usage_percent = sdn_utils.cal_bw_usage_percent(
                            out_octets,
                            interface['speed'],
                            out_in_time)
                        
                        # Add infomation
                        interface['bw_in_usage_octets'] = in_octets
                        interface['bw_in_usage_percent'] = bw_in_usage_percent

                        interface['bw_out_usage_octets'] = out_octets
                        interface['bw_out_usage_percent'] = bw_out_usage_percent

                        interface['bw_usage_update'] = time.time()
                        
                        logging.debug(
                            ' || BW in usage %.3f || %d bytes',
                            bw_in_usage_percent,
                            in_octets)

                        logging.debug(
                            ' || BW out usage %.3f || %d bytes',
                            bw_out_usage_percent,
                            out_octets)
                        break

        system_info['interfaces'] = interfaces

        # Clear old routes
        mongo.db.route.delete_many({
            'device_ip': host
        })

        # Insert net routes
        mongo.db.route.insert_many(routes)
        mongo.device.update_one({
            'ipv4_address': host
        }, {
            '$set': system_info
        }, upsert=True)

        # Insert CDP
        mongo.db.cdp.update_one({
            'device_ip': host
        }, {
            '$set': {
                'device_ip': host,
                'neighbor': cdp
            }
        }, upsert=True)

    def run_loop(self, device):
        """ Run loop
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while 1:
            logging.debug("Start loop")
            start = time.time()
            device.status = device.STATUS_SNMP_WORKING
            loop.run_until_complete(
                self.get_and_store(device)
            )
            device.status = device.STATUS_ONLINE
            # logging.debug("Process took: {:.2f} seconds".format(time.time() - start))
            sleep_time = self.loop_time - (time.time() - start)
            # logging.debug("Sleep time {:.2f}".format(sleep_time))
            if sleep_time < 1:
                sleep_time = 1
            try:
                shutdown_flag = self.__shutdown.get(True, sleep_time)
            except queue.Empty:
                shutdown_flag = None
            logging.debug(shutdown_flag)
            if shutdown_flag:
                logging.debug("MP Shutdown")
                break

    def shutdown(self):
        """ shutdown
        """
        # Todo
        logging.debug("SNMP Worker shutdown...")
        for _ in range(len(self.device_running)+2):
            logging.debug("SNMP Worker send shutdown signal")
            self.__shutdown.put(True)
        time.sleep(1)
        for device_proc in self.device_running:
            logging.debug("SNMP Worker wait for process end...")
            logging.debug(device_proc)
            device_proc.join()
        logging.debug("SNMP Worker shutdown complete")

    def run(self):
        for device in self.devices:
            t_s = multiprocessing.Process(name=device['host'],
                                          target=self.run_loop,
                                          args=(device['host'],
                                                device['community'],
                                                device['port']))
            t_s.start()
            self.device_running.append(t_s)
