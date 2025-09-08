import threading
import time

class CancelToken:
    def __init__(self):
        self._evt = threading.Event()
    def cancel(self):
        self._evt.set()
    def is_cancelled(self):
        return self._evt.is_set()

def run_in_thread(func, *args, **kwargs):
    t = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
    t.start()
    return t
