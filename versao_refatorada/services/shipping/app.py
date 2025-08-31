    from flask import Flask, request, jsonify
    import random, string, os
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
    BULK = Bulkhead(int(os.getenv("BULKHEAD_LIMIT", "3")))

    def _track():
        return "TRK-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "shipping"}, 200

    @app.post("/ship")
    def ship():
        try:
            with BULK.acquire():
                if maybe_simulate_instability():
                    return {"error":"simulated failure"}, 500
                data = request.get_json(force=True) or {}
                order_id = data.get("order_id")
                address = data.get("address")
                if not order_id or not address:
                    return {"error": "order_id and address required"}, 400
                return {"status": "CREATED", "tracking": _track()}
        except TimeoutError:
            return {"error":"bulkhead full"}, 503

    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=5000)
