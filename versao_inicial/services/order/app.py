from flask import Flask, request, jsonify
import requests
from itertools import count

app = Flask(__name__)

# Hardcoded service URLs (tight coupling, no discovery, no timeouts) - anti-patterns
USER_URL = "http://user:5000"
INVENTORY_URL = "http://inventory:5000"
PAYMENT_URL = "http://payment:5000"
SHIPPING_URL = "http://shipping:5000"

ORDERS = {}
_ids = count(1)

@app.get("/health")
def health():
    return {"status": "ok", "service": "order"}, 200

@app.get("/orders/<int:order_id>")
def get_order(order_id: int):
    order = ORDERS.get(order_id)
    if not order:
        return {"error": "order not found"}, 404
    return jsonify(order)

@app.post("/orders")
def create_order():
    data = request.get_json(force=True) or {}
    user_id = data.get("user_id")
    items = data.get("items", [])
    address = data.get("address", "Rua Sem Nome, 123 - SAJ/BA")
    if not user_id or not items:
        return {"error": "user_id and items required"}, 400

    # 1) Validate user directly (no retries/timeout) - anti-pattern
    r_user = requests.get(f"{USER_URL}/users/{user_id}")
    if r_user.status_code != 200:
        return {"error": "invalid user"}, 400
    user = r_user.json()

    # 2) Reserve inventory (no idempotency) - anti-pattern
    r_inv = requests.post(f"{INVENTORY_URL}/reserve", json={"items": items})
    if r_inv.status_code != 200:
        return {"error": "inventory reservation failed", "details": r_inv.json()}, 400

    # 3) Compute total and pay (synchronous cascade) - anti-pattern
    total = 0.0
    for it in items:
        qty = float(it.get("qty", 0))
        # naive fixed price per item for demo
        total += 100.0 * qty

    r_pay = requests.post(f"{PAYMENT_URL}/pay", json={"order_id": "temp", "amount": total, "method": "CREDIT"})
    pay = r_pay.json()
    if pay.get("status") != "PAID":
        return {"error": "payment declined"}, 402

    # 4) Ship (last step)
    r_ship = requests.post(f"{SHIPPING_URL}/ship", json={"order_id": "temp", "address": address})
    ship = r_ship.json()
    if r_ship.status_code != 200:
        return {"error": "shipping failed"}, 500

    new_id = next(_ids)
    order = {
        "id": new_id,
        "user": user,
        "items": items,
        "total": total,
        "payment": pay,
        "shipping": ship,
        "status": "CONFIRMED"
    }
    ORDERS[new_id] = order
    return jsonify(order), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
