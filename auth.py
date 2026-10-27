import os
import hmac
from functools import wraps
from flask import Blueprint, request, jsonify, session
from werkzeug.security import check_password_hash

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user"):
            return jsonify({"error": "Please sign in."}), 401
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password_hash = os.getenv("ADMIN_PASSWORD_HASH", "")

    # Compare username in constant time
    username_matches = hmac.compare_digest(username.encode("utf-8"), admin_username.encode("utf-8"))
    password_matches = False

    if admin_password_hash:
        try:
            password_matches = check_password_hash(admin_password_hash, password)
        except Exception:
            password_matches = False

    if not (username_matches and password_matches):
        return jsonify({"error": "Invalid username or password."}), 401

    session.permanent = True
    session["user"] = admin_username
    return jsonify({"username": admin_username}), 200

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Signed out."}), 200

@auth_bp.route("/me", methods=["GET"])
def me():
    user = session.get("user")
    if not user:
        return jsonify({"error": "Please sign in."}), 401
    return jsonify({"username": user}), 200
