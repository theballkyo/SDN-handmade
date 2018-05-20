# import pprint
import errno
import logging
import logging.handlers
import struct
import pprint
from multiprocessing import Queue
from threading import Thread
# import readline
from datetime import datetime
from time import time
import os

try:
    import readline
except ImportError:
    import pyreadline as readline


class LogBugHandler(logging.Handler):

    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        """ nothing
        """
        pass


def debug(msg):
    """ Pretty print for debug
    """
    pprint.pprint(msg)


class LogBug:

    def __init__(self, use_pprint=False, queue=None):
        self.queue = queue
        self.prompt = ''
        self.is_wait_input = False
        self.shutdown = False
        self.log_level = 0
        self.use_pprint = use_pprint
        self.to_file = True
        # self.sys = sys

    def auto_run(self):
        self.queue = Queue()
        Thread(target=self.listener_thread, daemon=True).start()
        self.worker_config()

    def pre_shutdown(self):
        self.prompt = ""

    def post_shutdown(self):
        self.shutdown = True
        self.queue.put(None)

    def read_input(self, prompt=None):
        if prompt is not None:
            self.prompt = prompt
        self.is_wait_input = True
        data = input(self.prompt)
        self.is_wait_input = False
        return data

    def worker_config(self):
        h = logging.handlers.QueueHandler(self.queue)
        h2 = LogBugHandler()
        root = logging.getLogger()
        root.addHandler(h)
        root.addHandler(h2)
        root.setLevel(logging.DEBUG)

    def listener_thread(self):
        # self.listener_configurer()
        # import fcntl
        # import termios
        if self.to_file:
            filename = "logs/{}.txt".format(time())
            if not os.path.exists(os.path.dirname(filename)):
                try:
                    os.makedirs(os.path.dirname(filename))
                except OSError as exc:  # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise
            f = open(filename, "w")
        import sys
        template = "[{created:%Y-%m-%d %H:%M:%S} {levelname}] [{processName}-{threadName}]: {message}\n"
        while True:
            try:
                # time.sleep(1)
                record = self.queue.get()
                if record is None:
                    if self.shutdown:  # We send this as a sentinel to tell the listener to quit.
                        print("LogBug -> shutdown listener thread")
                        break
                    continue

                if record.levelno < self.log_level:
                    continue

                # # logger = logging.getLogger(record.name)
                buff = readline.get_line_buffer()
                # print("Buff2: " + str(len(buff)))
                # _, cols = struct.unpack('hh', fcntl.ioctl(sys.stdout, termios.TIOCGWINSZ, '1234'))
                # # print(readline.get_)
                text_len = len(buff) + 2
                text_len += len(self.prompt)
                #
                # ANSI escape sequences (All VT100 except ESC[0G)
                # Clear current line
                sys.stdout.write('\x1b[2K')
                # sys.stdout.write('\x1b[1A\x1b[2K'*(text_len//cols))  # Move cursor up and clear line
                # Move to start of line
                sys.stdout.write('\x1b[1000D')
                # print(record.__dict__)
                data = vars(record)
                data.update({'created': datetime.fromtimestamp(record.created)})

                # If use pretty print
                if self.use_pprint:
                    data.update({'message': pprint.pformat(record.message, indent=8)})

                sys.stdout.write(
                    template.format(**data))
                # sys.stdout.write(record)
                if self.is_wait_input:
                    sys.stdout.write(self.prompt + buff)
                sys.stdout.flush()
                # # logger.handle(record) # No level or filter logic applied - just do it!
                if self.to_file:
                    f.write(template.format(**data))
            except (KeyboardInterrupt, SystemExit):
                raise
            except EOFError:
                break
            except Exception:
                import sys
                import traceback
                # print >> sys.stderr, 'Whoops! Problem:'
                traceback.print_exc(file=sys.stderr)

    # def listener_configurer(self):
    #     root = logging.getLogger()
    #     # h = logging.StreamHandler()
    #     h = LogBugHandler()
    #     root.addHandler(h)


_logbug = {'logbug': LogBug()}


def init(level=0):
    _logbug['logbug'].log_level = level
    _logbug['logbug'].auto_run()


def get():
    if not _logbug['logbug']:
        init()

    return _logbug['logbug']
