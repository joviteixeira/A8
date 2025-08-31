import os
from .http_client import HttpClient
from .circuit_breaker import CircuitBreaker

class Container:
    def __init__(self):
        # Read config from environment
        self.cfg = {
            "USER_URL": os.getenv("USER_URL", "http://user:5000"),
            "INVENTORY_URL": os.getenv("INVENTORY_URL", "http://inventory:5000"),
            "PAYMENT_URL": os.getenv("PAYMENT_URL", "http://payment:5000"),
            "SHIPPING_URL": os.getenv("SHIPPING_URL", "http://shipping:5000"),
            "TIMEOUT_SEC": float(os.getenv("HTTP_TIMEOUT", "2.0")),
            "CB_THRESHOLD": int(os.getenv("CB_THRESHOLD", "3")),
            "CB_COOLDOWN": int(os.getenv("CB_COOLDOWN", "5")),
        }
        self._singletons = {}

    def _cb(self, name):
        return CircuitBreaker(name, failure_threshold=self.cfg["CB_THRESHOLD"], recovery_timeout_sec=self.cfg["CB_COOLDOWN"])

    def http_user(self):
        return self._get_singleton("http_user", lambda: HttpClient(self.cfg["USER_URL"], self.cfg["TIMEOUT_SEC"], self._cb("user")))

    def http_inventory(self):
        return self._get_singleton("http_inventory", lambda: HttpClient(self.cfg["INVENTORY_URL"], self.cfg["TIMEOUT_SEC"], self._cb("inventory")))

    def http_payment(self):
        return self._get_singleton("http_payment", lambda: HttpClient(self.cfg["PAYMENT_URL"], self.cfg["TIMEOUT_SEC"], self._cb("payment")))

    def http_shipping(self):
        return self._get_singleton("http_shipping", lambda: HttpClient(self.cfg["SHIPPING_URL"], self.cfg["TIMEOUT_SEC"], self._cb("shipping")))

    def _get_singleton(self, key, factory):
        if key not in self._singletons:
            self._singletons[key] = factory()
        return self._singletons[key]
