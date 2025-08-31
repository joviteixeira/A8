from flask import Flask, request, jsonify

app = Flask(__name__)

@app.get("/health")
def health():
    return {"status": "ok", "service": "payment"}, 200

@app.post("/pay")
def pay():
    data = request.get_json(force=True) or {}
    amount = float(data.get("amount", 0))
    # very naive "payment" (accept everything <= 9999.99) - anti-pattern
    status = "PAID" if amount <= 9999.99 else "DECLINED"
    return {"status": status, "amount": amount}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
