""" SDN Handmade for legacy cisco device """
import logging
import multiprocessing as mp
# import readline
# import sys
import threading
import time
# import tty
# from logging import handlers

import logbug as lb
import sdn_handmade as sdn


def main():
    """ Run SDN Controller Server
    """
    # Start SNMP worker
    # snmp_worker = SNMPWorker()
    # Start Netflow worker
    # netflow_worker = NetflowWorker()

    q = mp.Queue()
    # print(logging.handlers)

    logbug__ = lb.LogBug(q)
    # Start listener_thread
    threading.Thread(target=logbug__.listener_thread).start()

    logbug__.worker_config()
    # logger = logging.getLogger()
    # print(dir(handlers))
    # h = logging.handlers.QueueHandler(q)
    root = logging.getLogger()
    # root.addHandler(h)
    # root.setLevel(logging.DEBUG)
    logging.log(50, "TEST Logging.....")
    # SSH connection info (for tests)
    ssh_info = {
        'username': 'cisco',
        'password': 'cisco',
        'port': 22,
        'secret': 'cisco',
        'verbose': False # For debugging
    }

    # Create topoloygy
    topoloygy = sdn.Topoloygy(
        netflow_ip='192.168.106.1'
    )

    # Create device object
    device_maingw = sdn.CiscoRouter(
        ip='192.168.106.200',
        ssh_info=ssh_info
    )
    # print(device_maingw.get_interfaces())
    device_r1 = sdn.CiscoRouter(
        ip='192.168.106.201',
        ssh_info=ssh_info
    )
    device_r2 = sdn.CiscoRouter(
        ip='192.168.106.202',
        ssh_info=ssh_info
    )
    device_r3 = sdn.CiscoRouter(
        ip='192.168.106.203',
        ssh_info=ssh_info
    )
    device_r4 = sdn.CiscoRouter(
        ip='192.168.106.204',
        ssh_info=ssh_info
    )

    # Add device to topoloygy
    topoloygy.add_device([device_maingw, device_r1, device_r2, device_r3,
                          device_r4])

    # Start topoloygy loop
    topoloygy.run()

    # time.sleep(2)
    # logging.debug(topoloygy.create_graph())
    # logging.debug(topoloygy.create_subnet())
    # topoloygy.find_path_by_subnet('192.168.100.0/24', '192.168.106.0/24')
    # logging.debug(topoloygy.find_path_by_device(device_r1, device_r4, False))
    # logging.debug(topoloygy.find_path_by_device(device_r1, device_r2, False))
    # logging.debug(topoloygy.find_path_by_device(device_r1, device_r3, False))
    # logging.debug(topoloygy.find_path_by_device(device_r1, device_maingw, False))
    logging.debug('aaaa')
    logging.debug('dasdsadasdsad')
    while 1:
        # logbug__.setPrompt("SDN Handmade (0.0.1)# ")
        inp = logbug__.read_input("SDN Handmade (0.0.1)# ")
        # inp = command_line()
        if inp == 'exit' or inp is None:
            logbug__.pre_shutdown()
            logging.debug("Shutdown...")
            topoloygy.shutdown()
            time.sleep(0.5)
            q.put(None)
            time.sleep(0.5)
            break
        if inp == '':
            continue
        inp_split = inp.split(' ')

        if inp_split[0] == 'status':
            topoloygy.print_status()
        elif inp_split[0] == 'show':
            if len(inp_split) < 2:
                print("Error: using show {...}")
                continue
            if inp_split[1] == 'graph':
                print(topoloygy.create_graph())
            elif inp_split[1] == 'version':
                print("SDN Handmade: 0.0.1")
            elif inp_split[1] == 'devices':
                for index, device in enumerate(topoloygy.devices):
                    print("[{}] {}".format(index, device.infomation_text()))
            elif inp_split[1] == 'device':
                try:
                    device_n = int(inp_split[2])
                    if device_n > len(topoloygy.devices):
                        print("Device number must be less than {}".format(
                            len(self.devices)
                        ))
                    elif inp_split[3] == 'id':
                        print(topoloygy.devices[device_n].get_serial_number())
                except ValueError:
                    print("Device index must be integer only")
        elif inp_split[0] == 'add':
            if len(inp_split) != 3:
                print("Error: incorrect command using 'add device [type {cisco}] [Device ip]'")
                continue
            ip = inp_split[2]
            topoloygy.add_device(
                sdn.CiscoRouter(ip, ssh_info)
            )
        else:
            print("Command {} not found.".format(inp))

if __name__ == '__main__':
    # FORMAT = '%(asctime)-15s - %(name)s - %(message)s'
    # logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
    #                     format=FORMAT)
    main()
