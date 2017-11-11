import pprint
import logging
import struct
import readline
from datetime import datetime

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
        # self.sys = sys

    def pre_shutdown(self):
        self.prompt = ""

    def read_input(self, prompt=None):
        if prompt is not None:
            self.prompt = prompt
        return input(self.prompt)

    def worker_config(self):
        h = logging.handlers.QueueHandler(self.queue)
        root = logging.getLogger()
        root.addHandler(h)
        root.setLevel(logging.DEBUG)
        print("Worker config")

    def listener_thread(self):
        self.listener_configurer()
        import fcntl
        import termios
        import sys
        while True:
            try:
                # time.sleep(1)
                record = self.queue.get()

                # # logger = logging.getLogger(record.name)
                buff = readline.get_line_buffer()
                # print("Buff2: " + str(len(buff)))
                _, cols = struct.unpack('hh', fcntl.ioctl(sys.stdout, termios.TIOCGWINSZ, '1234'))
                # # print(readline.get_)
                text_len = len(buff) + 2
                text_len += len(self.prompt)
                #
                # ANSI escape sequences (All VT100 except ESC[0G)
                sys.stdout.write('\x1b[2K')                         # Clear current line
                sys.stdout.write('\x1b[1A\x1b[2K'*(text_len//cols))  # Move cursor up and clear line
                sys.stdout.write('\x1b[0G')                         # Move to start of line
                # print(record.__dict__)

                if record is None: # We send this as a sentinel to tell the listener to quit.
                    print("LogBug -> shutdown listener thread")
                    break
                data = {
                    'created': datetime.fromtimestamp(record.created),
                    'levelname': record.levelname,
                    'message': record.message
                }
                print("{created} [{levelname}] {message}".format(**data))
                # sys.stdout.write(record)
                sys.stdout.write(self.prompt + buff)
                sys.stdout.flush()
                # # logger.handle(record) # No level or filter logic applied - just do it!
            except (KeyboardInterrupt, SystemExit):
                raise
            except EOFError:
                break
            except:
                import sys, traceback
                # print >> sys.stderr, 'Whoops! Problem:'
                traceback.print_exc(file=sys.stderr)

    def listener_configurer(self):
        root = logging.getLogger()
        # h = logging.StreamHandler()
        h = LogBugHandler()
        root.addHandler(h)
