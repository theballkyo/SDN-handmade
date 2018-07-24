""" SDN Handmade for legacy Cisco device """
import argparse
import logging
import os

import matplotlib

import database


def main():
    """ Run SDN Controller Server
    """
    import time
    import logbug as lb
    import sdn_handmade as sdn
    from cli.cli_controller import CLIController
    import settings

    lb.init(logging.INFO)

    # Create topology
    topology = sdn.Topology(
        netflow_ip=settings.netflow['bind_ip'],
        netflow_port=settings.netflow['bind_port']
    )

    # Start topology loop
    topology.run()

    # Start CLI
    cli = CLIController(settings.app['version'])
    # cli.init()

    cli.cmdloop("Welcome to SDN Handmade. Type help to list commands.\n")

    lb.get().pre_shutdown()
    time.sleep(0.5)
    topology.shutdown()
    time.sleep(0.5)
    lb.get().post_shutdown()


if __name__ == '__main__':
    # Fix when draw image in terminal without display
    matplotlib.use('Agg')

    if os.name == 'nt':
        print("Warning: Windows is not fully support.")
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--db',
                        default='default',
                        help='Database name (default is default)')
    args = parser.parse_args()
    print(args.db)
    database.set_connection_name(args.db)
    database.set_connection_name("default")
    main()
