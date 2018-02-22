import logging
import socket
import threading
import traceback

from database import get_mongodb
from netflow.netflow_packet import ExportPacket


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
        # Setting thread name
        self.name = 'netflow-sv'

    def run(self):
        """ Create netflow Server
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.bind_ip, self.bind_port))
        logging.info("Netflow server: Listening on interface {}:{}".format(self.bind_ip, self.bind_port))

        _templates = {}

        netflow_db = self.mongo.netflow
        while not self.stop_flag:
            try:
                (data, sender) = self.sock.recvfrom(8192)

                if data == b'stop':
                    continue

                logging.debug("Received data from {}, length {}".format(sender, len(data)))

                export = ExportPacket(data, _templates)

                # Update templates
                _templates.update(export.templates)

                flow_data = []
                for flow in export.flows:
                    flow.data['from_ip'] = str(sender[0])
                    flow_data.append(flow.data)

                netflow_db.insert_many(flow_data)

            except Exception:
                logging.info(traceback.format_exc())

        self.sock.close()
        logging.info("Netflow server: stopped loop")

    def shutdown(self):
        """ Stop netflow Server
        """
        logging.info("Netflow server: shutdown...")
        self.stop_flag = True
        socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(
            b'stop', (self.bind_ip, self.bind_port)
        )
