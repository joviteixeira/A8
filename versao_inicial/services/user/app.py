from flask import Flask, request, jsonify
from itertools import count

app = Flask(__name__)

_ids = count(1)
USERS = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
    2: {"id": 2, "name": "Bob", "email": "bob@example.com"}
}

@app.get("/health")
def health():
    return {"status": "ok", "service": "user"}, 200

@app.get("/users/<int:user_id>")
def get_user(user_id: int):
    user = USERS.get(user_id)
    if not user:
        return {"error": "user not found"}, 404
    return jsonify(user)

@app.post("/users")
def create_user():
    data = request.get_json(force=True) or {}
    name = data.get("name")
    email = data.get("email")
    if not name or not email:
        return {"error": "name and email required"}, 400
    new_id = next(_ids)
    USERS[new_id] = {"id": new_id, "name": name, "email": email}
    return jsonify(USERS[new_id]), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
