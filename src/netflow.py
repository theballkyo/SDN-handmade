import logging
import multiprocessing
import socket
import threading
import time

from database import NetflowDB
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

    def run(self):
        """ Create netflow Server
        """
        # sys.stdout.write('\r'+' '*(len(readline.get_line_buffer())+2)+'\r')
        # print('Starting...')
        # sys.stdout.write('> ' + readline.get_line_buffer())
        # sys.stdout.flush()
        logging.debug("Starting...")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.sock.settimeout(10)
        # self.sock.setblocking(0)
        self.sock.bind((self.bind_ip, self.bind_port))
        logging.debug("Listening on interface {}:{}".format(self.bind_ip, self.bind_port))
        _templates = {}

        netflow_db = NetflowDB()
        while 1:
            if self.stop_flag:
                self.sock.close()
                break
            try:
                (data, sender) = self.sock.recvfrom(8192)
                logging.debug("Received data from {}, length {}".format(sender, len(data)))
                export = ExportPacket(data, _templates)
                _templates.update(export.templates)
                logging.debug("{:22}{:22}{:5} {}".format("SRC", "DST", "PROTO", "BYTES"))
                for flow in export.flows:
                    netflow_db.insert(flow.data)
                    data = flow.data
                    logging.debug("{:22}{:22}{:5} {}".format(
                        data['ipv4_src_addr'],
                        data['ipv4_dst_addr'],
                        data['protocol'],
                        data['in_bytes']
                    ))
                logging.debug("Processed ExportPacket with {} flows.".format(export.header.count))
            except ValueError:
                pass
            except KeyError:
                pass
            except KeyboardInterrupt:
                break
            except socket.timeout:
                continue
            except Exception as e:
                logging.debug(e)

        logging.debug("Netflow server stopped loop")

    def shutdown(self):
        """ Stop netflow Server
        """
        logging.debug("Shutdown Netflow server...")
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
