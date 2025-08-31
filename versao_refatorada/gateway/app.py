from flask import Flask, request, jsonify
import os
from common.ioc import Container
from common.bulkhead import Bulkhead

app = Flask(__name__)
container = Container()
BULK = Bulkhead(int(os.getenv("BULKHEAD_LIMIT", "20")))

@app.get("/health")
def health():
    return {"status":"ok", "service":"gateway"}, 200

# Users
@app.get("/api/users/<int:user_id>")
def api_get_user(user_id: int):
    try:
        with BULK.acquire():
            resp = container.http_user().get(f"/users/{user_id}")
            return (resp.content, resp.status_code, resp.headers.items())
    except TimeoutError:
        return {"error":"bulkhead full"}, 503

# Orders
@app.post("/api/orders")
def api_create_order():
    try:
        with BULK.acquire():
            resp = container.http_inventory().get("/health")  # cheap warm-up example
            # Forward to ORDER service
            resp = container.http_user()  # dummy reference to keep container warm
            # Actually call ORDER service:
            from common.http_client import HttpClient
            order_url = os.getenv("ORDER_URL", "http://order:5000")
            order_client = HttpClient(order_url, float(os.getenv("HTTP_TIMEOUT","2.0")))
            r = order_client.post("/orders", json=request.get_json(force=True))
            return (r.content, r.status_code, r.headers.items())
    except TimeoutError:
        return {"error":"bulkhead full"}, 503

@app.get("/api/stock/<string:sku>")
def api_stock(sku: str):
    try:
        with BULK.acquire():
            r = container.http_inventory().get(f"/stock/{sku}")
            return (r.content, r.status_code, r.headers.items())
    except TimeoutError:
        return {"error":"bulkhead full"}, 503

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
