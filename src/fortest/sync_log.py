import queue, logging
import time,readline,multiprocessing,threading
import sys,struct,fcntl,termios

def blank_current_readline():
    # Next line said to be reasonably portable for various Unixes
    (rows,cols) = struct.unpack('hh', fcntl.ioctl(sys.stdout, termios.TIOCGWINSZ,'1234'))

    text_len = len(readline.get_line_buffer())+2

    # ANSI escape sequences (All VT100 except ESC[0G)
    sys.stdout.write('\x1b[2K')                         # Clear current line
    sys.stdout.write('\x1b[1A\x1b[2K'*(text_len//cols))  # Move cursor up and clear line
    sys.stdout.write('\x1b[0G')                         # Move to start of line


def noisy_thread(q):
    logging.debug('cccc')
    while True:
        # print("From MP#1")
        time.sleep(2)
        print("buff: " + readline.get_line_buffer())
        q.put(str(time.time()))
        # msg = q.get()
        # print("Buffer is: " + str(readline.get_line_buffer()))
        # print("Wait for queue")
        # msg = q.get()
        # if msg is None:
        #     break
        # buffer_ = msg
        # blank_current_readline()
        # print("Received: " + msg)
        # print('Interrupting text!')
        # sys.stdout.write('> ' + msg)
        # sys.stdout.flush()          # Needed or text doesn't show until a key is pressed

class LogBug:

    def __init__(self, q):
        self.q = q
        self.readline__ = readline

    def readline(self):
        return self.readline__.get_line_buffer()

    def debug(self, msg):
        print(msg)

def log_bug_watch(q):
    logging.debug('bbbb')
    while 1:
        msg = q.get()
        print(msg)
        # print(readline.get_line_buffer())


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    logging.debug('aaaa')
    q = multiprocessing.Queue()
    # logbug = LogBug(q)
    # threading.Thread(target=logbug).start()
    multiprocessing.Process(target=noisy_thread, args=(q,)).start()
    # p = multiprocessing.Process(target=noisy_thread, args=(logbug, q))
    # p.daemon = True
    # p.start()
    threading.Thread(target=log_bug_watch, args=(q,)).start()
    while True:
        s = input('> ')
        # logbug.debug(s)
        print(s)
