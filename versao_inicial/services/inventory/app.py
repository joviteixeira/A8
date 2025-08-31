from flask import Flask, request, jsonify

app = Flask(__name__)

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
    qty = STOCK.get(sku, 0)
    return {"sku": sku, "available": qty}

@app.post("/reserve")
def reserve():
    data = request.get_json(force=True) or {}
    items = data.get("items", [])
    # naive check & reserve (no transactions, no rollback) - anti-pattern on purpose
    # verify availability
    for item in items:
        sku = item.get("product_id")
        qty = int(item.get("qty", 0))
        if STOCK.get(sku, 0) < qty:
            return {"error": f"insufficient stock for {sku}"}, 400
    # reserve (deduct)
    for item in items:
        sku = item["product_id"]
        qty = int(item["qty"])
        STOCK[sku] = STOCK.get(sku, 0) - qty
    return {"status": "reserved"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
