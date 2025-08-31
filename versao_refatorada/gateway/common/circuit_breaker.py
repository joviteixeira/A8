import time
import threading

class CircuitBreaker:
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout_sec: int = 5, half_open_max_calls: int = 1):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.half_open_max_calls = half_open_max_calls

        self.state = self.CLOSED
        self.failures = 0
        self.opened_at = None
        self._lock = threading.Lock()
        self._half_open_calls = 0

    def _can_half_open(self):
        return (time.time() - (self.opened_at or 0)) >= self.recovery_timeout_sec

    def _to_open(self):
        self.state = self.OPEN
        self.opened_at = time.time()
        self._half_open_calls = 0

    def _to_closed(self):
        self.state = self.CLOSED
        self.failures = 0
        self.opened_at = None
        self._half_open_calls = 0

    def _to_half_open(self):
        self.state = self.HALF_OPEN
        self._half_open_calls = 0

    def allow_call(self):
        with self._lock:
            if self.state == self.OPEN:
                if self._can_half_open():
                    self._to_half_open()
                else:
                    return False
            if self.state == self.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    return False
                self._half_open_calls += 1
            return True

    def on_success(self):
        with self._lock:
            if self.state in (self.HALF_OPEN, self.OPEN):
                self._to_closed()
            else:
                # remain closed
                self.failures = 0

    def on_failure(self):
        with self._lock:
            if self.state == self.HALF_OPEN:
                self._to_open()
                return
            self.failures += 1
            if self.failures >= self.failure_threshold:
                self._to_open()

    def call(self, fn, *args, **kwargs):
        if not self.allow_call():
            raise RuntimeError(f"CircuitBreaker({self.name}) is OPEN")
        try:
            res = fn(*args, **kwargs)
        except Exception as ex:
            self.on_failure()
            raise
        else:
            # consider HTTP status 500+ as failure if response-like
            status = getattr(res, "status_code", None)
            if status is not None and status >= 500:
                self.on_failure()
            else:
                self.on_success()
            return res
