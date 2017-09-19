from queue import Queue
from threading import Thread, current_thread
import time
def do_stuff(q):
  while True:
    print("{}\t{}".format(current_thread().name, q.get()))
    q.task_done()
    break

q = Queue(maxsize=0)
num_threads = 10

for x in range(num_threads+1):
  # time.sleep(0.1)
  q.put(x)

for i in range(num_threads):
  worker = Thread(target=do_stuff, args=(q,))
  worker.setDaemon(True)
  worker.start()


q.join()
