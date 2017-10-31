from netflow_packet import ExportPacket
from database import NetflowDB
import multiprocessing
import threading
import socket
import logging

class NetflowWorker(threading.Thread):

    def __init__(self, bind_ip, bind_port):
        threading.Thread.__init__(self)
        self.bind_ip = bind_ip
        self.bind_port = bind_port

    def run(self):
        """ Create netflow Server
        """
        # sys.stdout.write('\r'+' '*(len(readline.get_line_buffer())+2)+'\r')
        # print('Starting...')
        # sys.stdout.write('> ' + readline.get_line_buffer())
        # sys.stdout.flush()
        logging.debug("Starting...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.bind_ip, self.bind_port))
        logging.debug("Listening on interface {}:{}".format(self.bind_ip, self.bind_port))
        _templates = {}

        netflow_db = NetflowDB()

        while 1:
            try:
                (data, sender) = sock.recvfrom(8192)
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

    def stop(self):
        """ Stop netflow Server
        """
        pass
