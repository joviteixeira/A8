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

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "payment"}, 200

    @app.post("/pay")
    def pay():
        try:
            with BULK.acquire():
                if maybe_simulate_instability():
                    return {"error":"simulated failure"}, 500
                data = request.get_json(force=True) or {}
                amount = float(data.get("amount", 0))
                status = "PAID" if amount <= 9999.99 else "DECLINED"
                return {"status": status, "amount": amount}
        except TimeoutError:
            return {"error":"bulkhead full"}, 503

    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=5000)
