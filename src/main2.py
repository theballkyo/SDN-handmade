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
from cli.cli_controller import CLIController


def main():
    """ Run SDN Controller Server
    """
    # Start SNMP worker
    # snmp_worker = SNMPWorker()
    # Start Netflow worker
    # netflow_worker = NetflowWorker()

    q = mp.Queue()
    # print(logging.handlers)

    logbug = lb.LogBug(q)
    # Start listener_thread
    threading.Thread(target=logbug.listener_thread, daemon=True).start()

    logbug.worker_config()
    # logger = logging.getLogger()
    # print(dir(handlers))
    # h = logging.handlers.QueueHandler(q)
    # root = logging.getLogger()
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

    # Create topology
    topology = sdn.Topology(
        netflow_ip='192.168.106.1'
    )

    # Create device object
    device_maingw = sdn.CiscoIosRouter(
        {
            'ip': '192.168.106.200'
        },
        ssh_info,
        {
            'community': 'public',
            'port': 161
        }
    )
    # print(device_maingw.get_interfaces())
    device_r1 = sdn.CiscoIosRouter(
        {
            'ip': '192.168.106.201'
        },
        ssh_info,
        {
            'community': 'public',
            'port': 161
        }
    )
    device_r2 = sdn.CiscoIosRouter(
        {
            'ip': '192.168.106.202'
        },
        ssh_info,
        {
            'community': 'public',
            'port': 161
        }
    )
    device_r3 = sdn.CiscoIosRouter(
        {
            'ip': '192.168.106.203'
        },
        ssh_info,
        {
            'community': 'public',
            'port': 161
        }
    )
    device_r4 = sdn.CiscoIosRouter(
        {
            'ip': '192.168.106.204'
        },
        ssh_info,
        {
            'community': 'public',
            'port': 161
        }
    )

    # Add device to topoloygy
    # topology.add_device([device_maingw, device_r1, device_r2, device_r3,
    #                       device_r4])

    # Start topoloygy loop
    topology.run()

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

    # Start CLI
    cli = CLIController()
    cli.init(topology, logbug, '0.0.1')
    try:
        cli.cmdloop("Welcome to SDN Handmade. Type help or ? to list commands.\n")
    except KeyboardInterrupt:
        logbug.pre_shutdown()
        time.sleep(0.5)
        topology.shutdown()
        time.sleep(0.5)
        logbug.post_shutdown()
    # while 1:
    #     try:
    #         cli_return = cli.handle_input()
    #         if cli_return == 'shutdown':
    #             logbug.pre_shutdown()
    #             logging.debug("Shutdown...")
    #             topology.shutdown()
    #             time.sleep(0.5)
    #             # q.put(None)
    #             logbug.post_shutdown()
    #             time.sleep(0.5)
    #             break
    #     except:
    #         pass
        # logbug__.setPrompt("SDN Handmade (0.0.1)# ")
        # inp = logbug.read_input("SDN Handmade (0.0.1)# ")
        # # inp = command_line()
        # if inp == 'exit' or inp is None:
        #     logbug.pre_shutdown()
        #     logging.debug("Shutdown...")
        #     topology.shutdown()
        #     time.sleep(0.5)
        #     q.put(None)
        #     time.sleep(0.5)
        #     break
        # if inp == '':
        #     continue
        # inp_split = inp.split(' ')
        #
        # if inp_split[0] == 'status':
        #     topology.print_status()
        # elif inp_split[0] == 'show':
        #     if len(inp_split) < 2:
        #         print("Error: using show {...}")
        #         continue
        #     if inp_split[1] == 'graph':
        #         print(topology.create_graph())
        #     elif inp_split[1] == 'matrix':
        #         topology.print_matrix()
        #     elif inp_split[1] == 'version':
        #         print("SDN Handmade: 0.0.1")
        #     elif inp_split[1] == 'devices':
        #         for index, device in enumerate(topology.devices):
        #             print("[{}] {}".format(index, device.infomation_text()))
        #     elif inp_split[1] == 'device':
        #         try:
        #             device_n = int(inp_split[2])
        #             if device_n > len(topology.devices):
        #                 print("Device number must be less than {}".format(
        #                     len(topology.devices)
        #                 ))
        #             elif inp_split[3] == 'id':
        #                 print(topology.devices[device_n].get_serial_number())
        #         except ValueError:
        #             print("Device index must be integer only")
        # elif inp_split[0] == 'add':
        #     if len(inp_split) != 3:
        #         print("Error: incorrect command using 'add device [type {cisco}] [Device ip]'")
        #         continue
        #     ip = inp_split[2]
        #     topology.add_device(
        #         sdn.CiscoRouter(ip, ssh_info)
        #     )
        # else:
        #     print("Command {} not found.".format(inp))

if __name__ == '__main__':
    # FORMAT = '%(asctime)-15s - %(name)s - %(message)s'
    # logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
    #                     format=FORMAT)
    main()
