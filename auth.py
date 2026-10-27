
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
    # Accept JSON sent by the frontend.
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Invalid request. Send JSON containing username and password."
        }), 400

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    # Read credentials from environment variables.
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password_hash = os.getenv("ADMIN_PASSWORD_HASH", "")

    # Do not allow login when the password hash is not configured.
    if not admin_password_hash:
        return jsonify({
            "error": "Server authentication is not configured. Set ADMIN_PASSWORD_HASH."
        }), 500

    # Compare username safely.
    username_matches = hmac.compare_digest(
        username.encode("utf-8"),
        admin_username.encode("utf-8")
    )

    # Verify the submitted password against the stored hash.
    try:
        password_matches = check_password_hash(
            admin_password_hash,
            password
        )
    except (ValueError, TypeError):
        password_matches = False

    if not (username_matches and password_matches):
        return jsonify({
            "error": "Invalid username or password."
        }), 401

    # Establish the authenticated session.
    session.clear()
    session.permanent = True
    session["user"] = admin_username

    return jsonify({
        "message": "Login successful.",
        "username": admin_username
    }), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()

    return jsonify({
        "message": "Signed out."
    }), 200


@auth_bp.route("/me", methods=["GET"])
def me():
    user = session.get("user")

    if not user:
        return jsonify({
            "error": "Please sign in."
        }), 401

    return jsonify({
        "username": user
    }), 200
