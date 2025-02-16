import os
from datetime import datetime

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URL", "sqlite:///shop.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "your-secret-key")  # Для продакшена использовать переменную окружения

db = SQLAlchemy(app)
jwt = JWTManager(app)

MERCH_ITEMS = {
    "t-shirt": 80,
    "cup": 20,
    "book": 50,
    "pen": 10,
    "powerbank": 200,
    "hoody": 300,
    "umbrella": 200,
    "socks": 10,
    "wallet": 50,
    "pink-hoody": 500,
}

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    coins = db.Column(db.Integer, default=1000, nullable=False)
    purchases = db.relationship('Purchase', backref='user', lazy=True)
    sent_transactions = db.relationship('Transaction', foreign_keys='Transaction.sender_id', backref='sender', lazy=True)
    received_transactions = db.relationship('Transaction', foreign_keys='Transaction.recipient_id', backref='recipient', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.before_first_request
def create_tables():
    db.create_all()

@app.route("/api/auth", methods=["POST"])
def auth():
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"errors": "Username and password required"}), 400

    username = data["username"]
    password = data["password"]

    user = User.query.filter_by(username=username).first()
    if user:
        if not check_password_hash(user.password_hash, password):
            return jsonify({"errors": "Invalid credentials"}), 401
    else:
        user = User(username=username, password_hash=generate_password_hash(password), coins=1000)
        db.session.add(user)
        db.session.commit()

    access_token = create_access_token(identity=user.id)
    return jsonify({"token": access_token}), 200

@app.route("/api/info", methods=["GET"])
@jwt_required()
def info():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"errors": "User not found"}), 404

    inventory = {}
    for purchase in user.purchases:
        inventory[purchase.item] = inventory.get(purchase.item, 0) + 1
    inventory_list = [{"type": item, "quantity": qty} for item, qty in inventory.items()]

    received = [{"fromUser": tx.sender.username, "amount": tx.amount} for tx in user.received_transactions]
    sent = [{"toUser": tx.recipient.username, "amount": tx.amount} for tx in user.sent_transactions]

    response = {
        "coins": user.coins,
        "inventory": inventory_list,
        "coinHistory": {
            "received": received,
            "sent": sent
        }
    }
    return jsonify(response), 200

@app.route("/api/sendCoin", methods=["POST"])
@jwt_required()
def send_coin():
    data = request.get_json()
    if not data or "toUser" not in data or "amount" not in data:
        return jsonify({"errors": "toUser and amount are required"}), 400

    to_username = data["toUser"]
    amount = data["amount"]

    if amount <= 0:
        return jsonify({"errors": "Amount must be positive"}), 400

    sender_id = get_jwt_identity()
    sender = User.query.get(sender_id)
    if sender.coins < amount:
        return jsonify({"errors": "Insufficient coins"}), 400

    recipient = User.query.filter_by(username=to_username).first()
    if not recipient:
        return jsonify({"errors": "Recipient not found"}), 400

    sender.coins -= amount
    recipient.coins += amount
    transaction = Transaction(sender_id=sender.id, recipient_id=recipient.id, amount=amount)
    db.session.add(transaction)
    db.session.commit()

    return jsonify({"message": "Coins sent successfully"}), 200

@app.route("/api/buy/<string:item>", methods=["GET"])
@jwt_required()
def buy(item):
    if item not in MERCH_ITEMS:
        return jsonify({"errors": "Item not found"}), 400

    price = MERCH_ITEMS[item]
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if user.coins < price:
        return jsonify({"errors": "Insufficient coins"}), 400

    user.coins -= price
    purchase = Purchase(user_id=user.id, item=item, price=price)
    db.session.add(purchase)
    db.session.commit()

    return jsonify({"message": f"Purchased {item} successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)
