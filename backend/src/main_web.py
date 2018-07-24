""" SDN Handmade for legacy Cisco device """
import argparse
import logging
import os

import database


def main():
    """ Run RestAPI Server
    """
    import logbug as lb
    from api.rest_server import RestServer

    lb.init(logging.INFO)

    # Start REST API Server
    rest_server = RestServer()
    rest_server.run()


if __name__ == '__main__':
    # Fix when draw image in terminal without display

    if os.name == 'nt':
        print("Warning: Windows is not fully support.")
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--db',
                        default='default',
                        help='Database name (default is default)')
    args = parser.parse_args()
    print(args.db)
    database.set_connection_name(args.db)
    main()
