""" SDN Handmade for legacy cisco device """
import logging
import multiprocessing as mp

import threading
import time

import logbug as lb
import sdn_handmade as sdn
from cli.cli_controller import CLIController


def main():
    """ Run SDN Controller Server
    """
    q = mp.Queue()

    logbug = lb.LogBug(q)
    # Start listener_thread
    threading.Thread(target=logbug.listener_thread, daemon=True).start()

    logbug.worker_config()

    # Create topology
    topology = sdn.Topology(
        netflow_ip='0.0.0.0',
        netflow_port=23455
    )

    # Start topoloygy loop
    topology.run()

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


if __name__ == '__main__':
    # FORMAT = '%(asctime)-15s - %(name)s - %(message)s'
    # logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
    #                     format=FORMAT)
    main()
