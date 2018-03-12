""" SDN Handmade for legacy Cisco device """
import matplotlib
import os
import logging


def main():
    """ Run SDN Controller Server
    """
    import multiprocessing as mp
    import threading
    import time
    import logbug as lb
    import sdn_handmade as sdn
    from cli.cli_controller import CLIController
    import settings
    from api.rest_server import RestServer

    lb.init()
    # log_bug = lb.LogBug(queue)
    # Start listener_thread
    # threading.Thread(target=log_bug.listener_thread, daemon=True).start()

    # log_bug.worker_config()

    # Create topology
    topology = sdn.Topology(
        netflow_ip=settings.netflow['bind_ip'],
        netflow_port=settings.netflow['bind_port']
    )

    # Start topology loop
    topology.run()

    # Start REST API Server
    # Todo change from thread to multiprocessing
    # mp.Process(target=rest_server.__run__, daemon=True).start()
    rest_server = RestServer()
    rest_server.run()

    # Start CLI
    cli = CLIController()
    cli.init(topology, log_bug, settings.app['version'])

    cli.cmdloop("Welcome to SDN Handmade. Type help to list commands.\n")

    log_bug.pre_shutdown()
    time.sleep(0.5)
    topology.shutdown()
    rest_server.shutdown()
    time.sleep(0.5)
    log_bug.post_shutdown()


if __name__ == '__main__':
    # Fix when draw image in terminal without display
    matplotlib.use('Agg')
    # format = '[%(levelname)s] (%(threadName)-10s) %(message)s'
    # FORMAT = '%(asctime)-15s [%(levelname)s] (%(processName)-10s) (%(threadName)-10s): %(message)s'
    # logging.basicConfig(level=logging.DEBUG)

    if os.name == 'nt':
        print("Warning: Windows is not fully support.")
    main()
