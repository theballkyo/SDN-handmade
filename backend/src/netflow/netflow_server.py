""" Netflow Server """
import socket
# import struct
# import sys
# import readline
from netflow.netflow_packet import ExportPacket
from database import NetflowDB

# HOST = sys.argv[1]
# PORT = int(sys.argv[2])

def netflow_server(host, port):
    """ Create netflow Server
    """
    # sys.stdout.write('\r'+' '*(len(readline.get_line_buffer())+2)+'\r')
    # print('Starting...')
    # sys.stdout.write('> ' + readline.get_line_buffer())
    # sys.stdout.flush()
    print("Starting...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    print("Listening on interface {}:{}".format(host, port))
    _templates = {}

    netflow_db = NetflowDB()

    while 1:
        try:
            (data, sender) = sock.recvfrom(8192)
            print("Received data from {}, length {}".format(sender, len(data)))

            export = ExportPacket(data, _templates)
            _templates.update(export.templates)
            print("{:22}{:22}{:5} {}".format("SRC", "DST", "PROTO", "BYTES"))
            for flow in export.flows:
                netflow_db.insert(flow.data)
            print("Processed ExportPacket with {} flows.".format(export.header.count))
        except ValueError:
            pass
        except KeyError:
            pass
        except KeyboardInterrupt:
            break
