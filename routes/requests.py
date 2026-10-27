from datetime import datetime
from flask import Blueprint, request, jsonify, session
from db import query, query_one, execute
from errors import AppError

requests_bp = Blueprint("requests", __name__, url_prefix="/api/requests")

VALID_URGENCIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
ALLOWED_REQUEST_STATUSES = {"WAITING", "CLOSED"}

@requests_bp.before_request
def check_auth():
    if not session.get("user"):
        return jsonify({"error": "Please sign in."}), 401

@requests_bp.route("", methods=["GET"])
def get_requests():
    requests_list = query("""
        SELECT r.request_id, r.recipient_id, r.organ_id, rc.name AS patient, rc.blood_group,
               o.organ_name, r.urgency, r.status, r.request_date,
               DATEDIFF(CURDATE(), r.request_date) AS days_waiting
        FROM Requests r
        JOIN Recipients rc ON rc.recipient_id = r.recipient_id
        JOIN Organs o      ON o.organ_id = r.organ_id
        ORDER BY FIELD(r.urgency, 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'), r.request_date
    """)
    return jsonify(requests_list), 200

@requests_bp.route("", methods=["POST"])
def create_request():
    data = request.get_json(silent=True) or {}
    recipient_id = data.get("recipient_id")
    organ_id = data.get("organ_id")
    urgency = str(data.get("urgency", "")).strip()
    request_date = str(data.get("request_date", "")).strip()

    if recipient_id is None or organ_id is None or not urgency or not request_date:
        raise AppError("Please check the form: a field is missing or has an invalid value.", 400)

    try:
        recipient_id_int = int(recipient_id)
        organ_id_int = int(organ_id)
        request_date_obj = datetime.strptime(request_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise AppError("Please check the form: a field is missing or has an invalid value.", 400)

    if request_date_obj > datetime.now().date():
        raise AppError("Request date cannot be in the future.", 400)

    if urgency not in VALID_URGENCIES:
        raise AppError("Please check the form: a field is missing or has an invalid value.", 400)

    result = execute("""
        INSERT INTO Requests (recipient_id, organ_id, urgency, request_date)
        VALUES (%s, %s, %s, %s)
    """, (recipient_id_int, organ_id_int, urgency, request_date))

    return jsonify({
        "id": result["lastrowid"],
        "message": "Request recorded successfully."
    }), 201

@requests_bp.route("/<int:request_id>", methods=["PUT"])
def update_request(request_id):
    existing = query_one("""
        SELECT request_id, status FROM Requests WHERE request_id = %s
    """, (request_id,))

    if not existing:
        raise AppError("Record not found.", 404)

    if existing["status"] == "MATCHED":
        raise AppError("This request is already matched and cannot be edited.", 409)

    data = request.get_json(silent=True) or {}
    urgency = str(data.get("urgency", "")).strip()
    request_date = str(data.get("request_date", "")).strip()
    status = str(data.get("status", "")).strip()

    if not urgency or not request_date or not status:
        raise AppError("Please check the form: a field is missing or has an invalid value.", 400)

    try:
        request_date_obj = datetime.strptime(request_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise AppError("Please check the form: a field is missing or has an invalid value.", 400)

    if request_date_obj > datetime.now().date():
        raise AppError("Request date cannot be in the future.", 400)

    if urgency not in VALID_URGENCIES:
        raise AppError("Please check the form: a field is missing or has an invalid value.", 400)

    if status not in ALLOWED_REQUEST_STATUSES:
        raise AppError("Status can only be changed between WAITING and CLOSED.", 400)

    execute("""
        UPDATE Requests
        SET urgency = %s, request_date = %s, status = %s
        WHERE request_id = %s
    """, (urgency, request_date, status, request_id))

    return jsonify({"message": "Request updated successfully."}), 200
