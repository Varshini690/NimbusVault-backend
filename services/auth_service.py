from flask import Blueprint, jsonify, request, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from extensions import mongo
from datetime import timedelta

# Create Blueprint
auth_bp = Blueprint("auth", __name__)

# 🔒 Protected route
@auth_bp.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({"message": f"Hello, {current_user}! Protected route works ✅"})

# 🧑 Register route
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    if mongo.db.users.find_one({"username": username}):
        return jsonify({"error": "Username already exists"}), 400

    hashed_pw = generate_password_hash(password)
    mongo.db.users.insert_one({"username": username, "password": hashed_pw})
    return jsonify({"msg": "User created successfully"}), 201

# 🔑 Login route
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    user = mongo.db.users.find_one({"username": username})
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(
        identity=username,
        expires_delta=current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    )
    return jsonify({"access_token": access_token})
