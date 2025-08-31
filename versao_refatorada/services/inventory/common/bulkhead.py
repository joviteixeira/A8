import threading
from contextlib import contextmanager

class Bulkhead:
    def __init__(self, max_concurrent: int = 5):
        if max_concurrent < 1:
            max_concurrent = 1
        self._sem = threading.BoundedSemaphore(max_concurrent)

    @contextmanager
    def acquire(self, timeout: float = 0.1):
        ok = self._sem.acquire(timeout=timeout)
        if not ok:
            raise TimeoutError("Bulkhead full")
        try:
            yield
        finally:
            self._sem.release()
