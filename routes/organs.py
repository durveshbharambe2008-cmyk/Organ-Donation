from flask import Blueprint, jsonify, session
from db import query

organs_bp = Blueprint("organs", __name__, url_prefix="/api/organs")

@organs_bp.before_request
def check_auth():
    if not session.get("user"):
        return jsonify({"error": "Please sign in."}), 401

@organs_bp.route("", methods=["GET"])
def get_organs():
    organs = query("SELECT organ_id, organ_name FROM Organs ORDER BY organ_id ASC")
    return jsonify(organs), 200
