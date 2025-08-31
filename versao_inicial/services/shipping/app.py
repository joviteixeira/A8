from flask import Flask, request, jsonify
import random, string

app = Flask(__name__)

@app.get("/health")
def health():
    return {"status": "ok", "service": "shipping"}, 200

def _track():
    return "TRK-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

@app.post("/ship")
def ship():
    data = request.get_json(force=True) or {}
    order_id = data.get("order_id")
    address = data.get("address")
    if not order_id or not address:
        return {"error": "order_id and address required"}, 400
    return {"status": "CREATED", "tracking": _track()}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
