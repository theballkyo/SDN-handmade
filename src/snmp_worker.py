import asyncio
import uvloop
from snmp_async import get_interfaces, get_routes, get_ip_addr, get_system_info, get_cdp, get_lldp
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from database import MongoDB
from pymongo import ReplaceOne
import multiprocessing
import utils
import time
import threading
import logging


mongo = None
class SNMPWorker(multiprocessing.Process):
    def __init__(self):
        super(SNMPWorker, self).__init__()
        self.devices = []
        self.device_running = []
        self.daemon = True
        self.loop_time = 60
        # asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


    def add_device(self, host, community, run=False, port=161):
        print(host, community, port)
        self.devices.append({
            'host': host,
            'port': port,
            'community': community
        })

        if run:
            t_s = multiprocessing.Process(
                name=host,
                target=self.run_loop,
                args=(host,
                      community,
                      port
                      )
                )
            t_s.start()
            self.device_running.append(t_s)


    def remove_device(self, host, community, port=161):
        try:
            self.devices = self.devices.remove({'host': host, 'community': community, 'port': port})
        except ValueError:
            pass

    async def get_and_store(self, host, community, port=161):
        """
        """
        mongo = self.mongo
        # asyncio.set_event_loop(loop)
        # futures = [
        #     asyncio.ensure_future(get_system_info(host, community, port)),
        #     asyncio.ensure_future(get_routes(host, community, port)),
        #     asyncio.ensure_future(get_ip_addr(host, community, port)),
        #     asyncio.ensure_future(get_interfaces(host, community, port))
        #     ]
        # asyncio.set_event_loop(loop)
        results = await asyncio.gather(
            asyncio.ensure_future(get_system_info(host, community, port)),
            asyncio.ensure_future(get_routes(host, community, port)),
            asyncio.ensure_future(get_ip_addr(host, community, port)),
            asyncio.ensure_future(get_interfaces(host, community, port)),
            asyncio.ensure_future(get_cdp(host, community, port)),
            asyncio.ensure_future(get_lldp(host, community, port)),
        )

        system_info = results[0]
        routes = results[1]
        ip_addr = results[2]
        interfaces = results[3]
        # CDP
        cdp = results[4]
        # LLDP
        lldp = results[5]

        for interface_index in range(len(interfaces)):
            for ip_index in range(len(ip_addr)):
                if interfaces[interface_index]['index'] == ip_addr[ip_index]['if_index']:
                    interfaces[interface_index]['ipv4_address'] = ip_addr[ip_index]['ipv4_address']
                    interfaces[interface_index]['subnet'] = ip_addr[ip_index]['subnet']
                    break

        system_info['interfaces'] = interfaces

        # print(interfaces[0])
        my_device = mongo.db.device.find_one({
            'device_ip': host
        })

        if my_device:
            for interface in interfaces:
                for my_interface in my_device['interfaces']:
                    if interface['description'] == my_interface['description']:
                        octets = interface['out_octets'] - my_interface['out_octets']
                        in_time = system_info['uptime'] - my_device['uptime']
                        # print('Delta time: ' + str(in_time), end='')
                        # print(' || IF OUT: ' + str(octets), end='')
                        # print(' || BW Usage {:.10f}%s || {} Bytes'.format(
                        #     utils.calculate_bw_usage_percent(octets, interface['speed'], in_time),
                        #     octets
                        #     ))
                        break

        deleted = mongo.db.route.delete_many({
            'device_ip': host
        })

        inserted = mongo.db.route.insert_many(routes)
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

    def run_loop(self, host, community, port=161):
        """ Run loop
        """
        self.mongo = MongoDB()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # print(get_lldp(host, community))
        #
        # return

        while 1:
            logging.debug("Start loop")
            start = time.time()
            loop.run_until_complete(
                self.get_and_store(host, community, port)
            )
            logging.debug("Process took: {:.2f} seconds".format(time.time() - start))
            sleep_time = self.loop_time - (time.time() - start)
            logging.debug("Sleep time {:.2f}".format(sleep_time))
            if sleep_time < 1:
                sleep_time = 1
            time.sleep(sleep_time)

    def run(self):
        start = time.time()
        t = []
        for device in self.devices:
            t_s = multiprocessing.Process(name=device['host'], target=self.run_loop, args=(device['host'], device['community'], device['port']))
            # t_s = threading.Thread(target=self.run_loop, args=(device['host'], device['community'], device['port']))
            t_s.start()
            self.device_running.append(t_s)

def add_device(host, community, port=161):
    pass


def calculate_bw_usage():
    pass
