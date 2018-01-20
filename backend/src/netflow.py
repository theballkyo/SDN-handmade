import logging
import multiprocessing
import socket
import socketserver
import threading
import time

from database import get_mongodb
from netflow_packet import ExportPacket


class NetflowWorker(threading.Thread):

    def __init__(self, bind_ip, bind_port):
        threading.Thread.__init__(self)
        self.bind_ip = bind_ip
        self.bind_port = bind_port
        self.sock = None
        self.stop_flag = False
        self.device = []
        self.daemon = True
        self.mongo = get_mongodb()

    def run(self):
        """ Create netflow Server
        """
        logging.info("Netflow server is starting...")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.sock = socketserver.UDPServer((self.bind_ip, self.bind_port))
        self.sock.bind((self.bind_ip, self.bind_port))
        logging.info("Netflow server: Listening on interface {}:{}".format(self.bind_ip, self.bind_port))
        _templates = {}

        netflow_db = self.mongo.netflow
        while 1:
            if self.stop_flag:
                self.sock.close()
                break
            try:
                (data, sender) = self.sock.recvfrom(8192)
                logging.debug("Received data from {}, length {}".format(sender, len(data)))
                export = ExportPacket(data, _templates)
                _templates.update(export.templates)
                # logging.debug("Netflow server: {:22}{:22}{:5} {}".format("SRC", "DST", "PROTO", "BYTES"))
                for flow in export.flows:
                    flow.data['device_ip'] = str(sender[0])
                    netflow_db.insert_one(flow.data)
                    data = flow.data
                #     logging.debug("Netflow server: {:22}{:22}{:5} {}".format(
                #         data['ipv4_src_addr'],
                #         data['ipv4_dst_addr'],
                #         data['protocol'],
                #         data['in_bytes']
                #     ))
                # logging.debug("Netflow server: Processed ExportPacket with {} flows.".format(export.header.count))
            except ValueError as e:
                logging.debug(e)
            except KeyError as e:
                logging.debug(e)
            except KeyboardInterrupt as e:
                logging.debug(e)
            except socket.timeout as e:
                logging.debug(e)
            except Exception as e:
                logging.debug(e)

        logging.info("Netflow server: stopped loop")

    def shutdown(self):
        """ Stop netflow Server
        """
        logging.info("Netflow server: shutdown...")
        self.stop_flag = True
        socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(
            b'stop', (self.bind_ip, self.bind_port)
        )
        # time.sleep(1)
        # try:
        #     self.sock.shutdown(socket.SHUT_WR)
        # except:
        #     pass
        # self.sock.close()

    def add_device(self, device):
        """ Add device for tell netflow than deivce is exist in topology
        """
        self.device.append(device)