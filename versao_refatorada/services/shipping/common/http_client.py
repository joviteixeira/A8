import os
import requests
from .circuit_breaker import CircuitBreaker

class HttpClient:
    def __init__(self, base_url: str, timeout: float = 2.0, breaker: CircuitBreaker | None = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.breaker = breaker or CircuitBreaker(name=f"http:{self.base_url}")

    def _request(self, method: str, path: str, **kwargs):
        url = self.base_url + (path if path.startswith("/") else f"/{path}")
        def _do():
            return self.session.request(method, url, timeout=self.timeout, **kwargs)
        return self.breaker.call(_do)

    def get(self, path: str, **kwargs):
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self._request("POST", path, **kwargs)
