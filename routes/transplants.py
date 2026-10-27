from datetime import datetime
from flask import Blueprint, request, jsonify, session
from db import query, query_one, execute
from errors import AppError

transplants_bp = Blueprint("transplants", __name__, url_prefix="/api/transplants")

VALID_OUTCOMES = {"SUCCESSFUL", "COMPLICATIONS", "FAILED"}

@transplants_bp.before_request
def check_auth():
    if not session.get("user"):
        return jsonify({"error": "Please sign in."}), 401

@transplants_bp.route("", methods=["GET"])
def get_transplants():
    transplants = query("""
        SELECT t.transplant_id, t.donation_id, t.request_id, o.organ_name,
               d.name AS donor, rc.name AS patient,
               t.surgeon_name, t.transplant_date, t.outcome
        FROM Transplants t
        JOIN Donations dn  ON dn.donation_id = t.donation_id
        JOIN Donors d      ON d.donor_id = dn.donor_id
        JOIN Requests r    ON r.request_id = t.request_id
        JOIN Recipients rc ON rc.recipient_id = r.recipient_id
        JOIN Organs o      ON o.organ_id = dn.organ_id
        ORDER BY t.transplant_id DESC
    """)
    return jsonify(transplants), 200

@transplants_bp.route("", methods=["POST"])
def create_transplant():
    data = request.get_json(silent=True) or {}
    donation_id = data.get("donation_id")
    request_id = data.get("request_id")
    surgeon_name = str(data.get("surgeon_name", "")).strip()
    transplant_date = str(data.get("transplant_date", "")).strip()
    outcome = str(data.get("outcome", "")).strip()

    if donation_id is None or request_id is None or not surgeon_name or not transplant_date or not outcome:
        raise AppError("Please check the form: a field is missing or has an invalid value.", 400)

    if len(surgeon_name) < 2:
        raise AppError("Surgeon name must be at least 2 characters.", 400)

    try:
        donation_id_int = int(donation_id)
        request_id_int = int(request_id)
        transplant_date_obj = datetime.strptime(transplant_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise AppError("Please check the form: a field is missing or has an invalid value.", 400)

    if transplant_date_obj > datetime.now().date():
        raise AppError("Transplant date cannot be in the future.", 400)

    if outcome not in VALID_OUTCOMES:
        raise AppError("Please check the form: a field is missing or has an invalid value.", 400)

    # Note: MySQL BEFORE INSERT trigger validates compatibility and status;
    # MySQL AFTER INSERT trigger updates Donations and Requests status.
    result = execute("""
        INSERT INTO Transplants (donation_id, request_id, surgeon_name, transplant_date, outcome)
        VALUES (%s, %s, %s, %s, %s)
    """, (donation_id_int, request_id_int, surgeon_name, transplant_date, outcome))

    return jsonify({
        "id": result["lastrowid"],
        "message": "Transplant recorded successfully."
    }), 201

@transplants_bp.route("/<int:transplant_id>", methods=["PUT"])
def update_transplant(transplant_id):
    existing = query_one("""
        SELECT transplant_id FROM Transplants WHERE transplant_id = %s
    """, (transplant_id,))

    if not existing:
        raise AppError("Record not found.", 404)

    data = request.get_json(silent=True) or {}
    surgeon_name = str(data.get("surgeon_name", "")).strip()
    transplant_date = str(data.get("transplant_date", "")).strip()
    outcome = str(data.get("outcome", "")).strip()

    if not surgeon_name or not transplant_date or not outcome:
        raise AppError("Please check the form: a field is missing or has an invalid value.", 400)

    if len(surgeon_name) < 2:
        raise AppError("Surgeon name must be at least 2 characters.", 400)

    try:
        transplant_date_obj = datetime.strptime(transplant_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise AppError("Please check the form: a field is missing or has an invalid value.", 400)

    if transplant_date_obj > datetime.now().date():
        raise AppError("Transplant date cannot be in the future.", 400)

    if outcome not in VALID_OUTCOMES:
        raise AppError("Please check the form: a field is missing or has an invalid value.", 400)

    execute("""
        UPDATE Transplants
        SET surgeon_name = %s, transplant_date = %s, outcome = %s
        WHERE transplant_id = %s
    """, (surgeon_name, transplant_date, outcome, transplant_id))

    return jsonify({"message": "Transplant updated successfully."}), 200
