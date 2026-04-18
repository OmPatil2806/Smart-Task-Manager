"""
Authentication routes: /signup, /login, /logout, /me
"""

from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from backend.database import get_db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400
    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters."}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, generate_password_hash(password))
        )
        db.commit()
        user = db.execute("SELECT id, username FROM users WHERE username = ?", (username,)).fetchone()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return jsonify({"message": "Account created.", "user": {"id": user["id"], "username": user["username"]}}), 201
    except Exception:
        return jsonify({"error": "Username already taken."}), 409
    finally:
        db.close()


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    db = get_db()
    try:
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Invalid credentials."}), 401

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return jsonify({"message": "Logged in.", "user": {"id": user["id"], "username": user["username"]}}), 200
    finally:
        db.close()


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out."}), 200


@auth_bp.route("/me", methods=["GET"])
def me():
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated."}), 401
    return jsonify({"user": {"id": session["user_id"], "username": session["username"]}}), 200
