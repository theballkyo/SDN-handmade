# import pprint
import logging
import logging.handlers
import struct
# import readline
from datetime import datetime

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

    def __init__(self, queue):
        self.queue = queue
        self.prompt = ''
        self.is_wait_input = False
        self.shutdown = False
        self.log_level = 0
        # self.sys = sys

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
        root = logging.getLogger()
        root.addHandler(h)
        root.setLevel(logging.DEBUG)

    def listener_thread(self):
        self.listener_configurer()
        # import fcntl
        # import termios
        import sys
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

                data = {
                    'created': datetime.fromtimestamp(record.created),
                    'levelno': record.levelno,
                    'levelname': record.levelname,
                    'message': record.message
                }
                sys.stdout.write(
                    "{created} [{levelname}({levelno})] {message}\n".format(**data))
                # sys.stdout.write(record)
                if self.is_wait_input:
                    sys.stdout.write(self.prompt + buff)
                sys.stdout.flush()
                # # logger.handle(record) # No level or filter logic applied - just do it!
            except (KeyboardInterrupt, SystemExit):
                raise
            except EOFError:
                break
            except:
                import sys
                import traceback
                # print >> sys.stderr, 'Whoops! Problem:'
                traceback.print_exc(file=sys.stderr)

    def listener_configurer(self):
        root = logging.getLogger()
        # h = logging.StreamHandler()
        h = LogBugHandler()
        root.addHandler(h)
