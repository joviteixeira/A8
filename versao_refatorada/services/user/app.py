    from flask import Flask, request, jsonify
    from itertools import count
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
    BULK = Bulkhead(int(os.getenv("BULKHEAD_LIMIT", "10")))

    _ids = count(3)
    USERS = {
        1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
        2: {"id": 2, "name": "Bob", "email": "bob@example.com"}
    }

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "user"}, 200

    @app.get("/users/<int:user_id>")
    def get_user(user_id: int):
        try:
            with BULK.acquire():
                if maybe_simulate_instability():
                    return {"error":"simulated failure"}, 500
                user = USERS.get(user_id)
                if not user:
                    return {"error": "user not found"}, 404
                return jsonify(user)
        except TimeoutError:
            return {"error":"bulkhead full"}, 503

    @app.post("/users")
    def create_user():
        try:
            with BULK.acquire():
                if maybe_simulate_instability():
                    return {"error":"simulated failure"}, 500
                data = request.get_json(force=True) or {}
                if not data.get("name") or not data.get("email"):
                    return {"error":"name and email required"}, 400
                i = next(_ids)
                USERS[i] = {"id": i, "name": data["name"], "email": data["email"]}
                return jsonify(USERS[i]), 201
        except TimeoutError:
            return {"error":"bulkhead full"}, 503

    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=5000)
