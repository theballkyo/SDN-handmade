from flow import NetflowAnalyze
from datetime import datetime
from pprint import pprint
import logging
# import pytz


def main():
    # pytz.timezone('Asia/Bangkok')
    netflow_analyze = NetflowAnalyze()
    start_time = datetime(2016, 5, 16, 4, 18)
    end_time = datetime(2016, 5, 16, 4, 20)
    flow_1 = netflow_analyze.get_biggest_flow(start_time, end_time)
    flow_1 = list(flow_1)
    pprint(flow_1)


if __name__ == '__main__':
    FORMAT = '%(asctime)-15s [%(levelname)s] (%(threadName)-10s) %(message)s'
    logging.basicConfig(level=logging.DEBUG,
                        format=FORMAT)
    main()
