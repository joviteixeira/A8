from flask import Flask, request, jsonify
from itertools import count
import os
from common.ioc import Container
from common.bulkhead import Bulkhead

app = Flask(__name__)
container = Container()
BULK = Bulkhead(int(os.getenv("BULKHEAD_LIMIT", "8")))

ORDERS = {}
_ids = count(1)

@app.get("/health")
def health():
    return {"status":"ok", "service":"order"}, 200

@app.get("/orders/<int:order_id>")
def get_order(order_id: int):
    try:
        with BULK.acquire():
            order = ORDERS.get(order_id)
            if not order:
                return {"error":"order not found"}, 404
            return jsonify(order)
    except TimeoutError:
        return {"error":"bulkhead full"}, 503

@app.post("/orders")
def create_order():
    try:
        with BULK.acquire():
            data = request.get_json(force=True) or {}
            user_id = data.get("user_id")
            items = data.get("items", [])
            address = data.get("address", "Rua Sem Nome, 123 - SAJ/BA")
            if not user_id or not items:
                return {"error":"user_id and items required"}, 400

            http_user = container.http_user()
            http_inventory = container.http_inventory()
            http_payment = container.http_payment()
            http_shipping = container.http_shipping()

            # 1) user
            r_user = http_user.get(f"/users/{user_id}")
            if r_user.status_code != 200:
                return {"error":"invalid user"}, 400
            user = r_user.json()

            # 2) inventory
            r_inv = http_inventory.post("/reserve", json={"items": items})
            if r_inv.status_code != 200:
                return {"error":"inventory reservation failed", "details": r_inv.json()}, 400

            # 3) total & payment
            total = 0.0
            for it in items:
                qty = float(it.get("qty", 0))
                total += 100.0 * qty
            r_pay = http_payment.post("/pay", json={"order_id":"temp", "amount": total, "method": "CREDIT"})
            if r_pay.status_code != 200 or r_pay.json().get("status") != "PAID":
                return {"error":"payment declined"}, 402

            # 4) shipping
            r_ship = http_shipping.post("/ship", json={"order_id":"temp", "address": address})
            if r_ship.status_code != 200:
                return {"error":"shipping failed"}, 500

            new_id = next(_ids)
            order = {
                "id": new_id,
                "user": user,
                "items": items,
                "total": total,
                "payment": r_pay.json(),
                "shipping": r_ship.json(),
                "status": "CONFIRMED"
            }
            ORDERS[new_id] = order
            return jsonify(order), 201
    except TimeoutError:
        return {"error":"bulkhead full"}, 503

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
