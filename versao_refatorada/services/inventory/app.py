    from flask import Flask, request, jsonify
    import os
    from common.bulkhead import Bulkhead
    import time, os
from flask import request

def maybe_simulate_instability():
    # query params have priority
    fail = request.args.get("fail")
    delay_ms = request.args.get("delay_ms")
    if delay_ms:
        try:
            time.sleep(float(delay_ms)/1000.0)
        except Exception:
            pass
    if fail in ("1", "true", "True"):
        return True
    # env fallbacks
    if os.getenv("ALWAYS_FAIL", "0") == "1":
        return True
    return False


    app = Flask(__name__)
    BULK = Bulkhead(int(os.getenv("BULKHEAD_LIMIT", "5")))

    STOCK = {
        "SKU-001": 10,
        "SKU-002": 5,
        "SKU-003": 2
    }

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "inventory"}, 200

    @app.get("/stock/<string:sku>")
    def get_stock(sku: str):
        try:
            with BULK.acquire():
                if maybe_simulate_instability():
                    return {"error":"simulated failure"}, 500
                return {"sku": sku, "available": STOCK.get(sku, 0)}
        except TimeoutError:
            return {"error":"bulkhead full"}, 503

    @app.post("/reserve")
    def reserve():
        try:
            with BULK.acquire():
                if maybe_simulate_instability():
                    return {"error":"simulated failure"}, 500
                data = request.get_json(force=True) or {}
                items = data.get("items", [])
                for item in items:
                    sku = item.get("product_id")
                    qty = int(item.get("qty", 0))
                    if STOCK.get(sku, 0) < qty:
                        return {"error": f"insufficient stock for {sku}"}, 400
                for item in items:
                    sku = item["product_id"]
                    qty = int(item["qty"])
                    STOCK[sku] = STOCK.get(sku, 0) - qty
                return {"status": "reserved"}
        except TimeoutError:
            return {"error":"bulkhead full"}, 503

    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=5000)
