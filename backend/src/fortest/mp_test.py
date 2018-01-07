import threading
import time
stdout_lock = threading.Lock()
def worker(lock):
    for _ in range(5):
        with lock:
            print("Test Test")
        time.sleep(1)
threading.Thread(target=worker, args=(stdout_lock,)).start()

with stdout_lock:
    r = input()
