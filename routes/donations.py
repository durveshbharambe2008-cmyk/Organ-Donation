from datetime import datetime
from flask import Blueprint, request, jsonify, session
from db import query, query_one, execute
from errors import AppError

donations_bp = Blueprint("donations", __name__, url_prefix="/api/donations")

VALID_DONATION_TYPES = {"LIVING", "DECEASED"}
ALLOWED_DONATION_STATUSES = {"AVAILABLE", "EXPIRED"}

@donations_bp.before_request
def check_auth():
    if not session.get("user"):
        return jsonify({"error": "Please sign in."}), 401

@donations_bp.route("", methods=["GET"])
def get_donations():
    donations = query("""
        SELECT dn.donation_id, dn.donor_id, dn.organ_id, d.name AS donor, d.blood_group,
               o.organ_name, dn.donation_type, dn.status, dn.donation_date
        FROM Donations dn
        JOIN Donors d ON d.donor_id = dn.donor_id
        JOIN Organs o ON o.organ_id = dn.organ_id
        ORDER BY dn.donation_id DESC
    """)
    return jsonify(donations), 200

@donations_bp.route("", methods=["POST"])
def create_donation():
    data = request.get_json(silent=True) or {}
    donor_id = data.get("donor_id")
    organ_id = data.get("organ_id")
    donation_type = str(data.get("donation_type", "")).strip()
    donation_date = str(data.get("donation_date", "")).strip()

    if donor_id is None or organ_id is None or not donation_type or not donation_date:
        raise AppError("Please check the form: a field is missing or has an invalid value.", 400)

    try:
        donor_id_int = int(donor_id)
        organ_id_int = int(organ_id)
        donation_date_obj = datetime.strptime(donation_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise AppError("Please check the form: a field is missing or has an invalid value.", 400)

    if donation_date_obj > datetime.now().date():
        raise AppError("Donation date cannot be in the future.", 400)

    if donation_type not in VALID_DONATION_TYPES:
        raise AppError("Please check the form: a field is missing or has an invalid value.", 400)

    result = execute("""
        INSERT INTO Donations (donor_id, organ_id, donation_type, donation_date)
        VALUES (%s, %s, %s, %s)
    """, (donor_id_int, organ_id_int, donation_type, donation_date))

    return jsonify({
        "id": result["lastrowid"],
        "message": "Donation recorded successfully."
    }), 201

@donations_bp.route("/<int:donation_id>", methods=["PUT"])
def update_donation(donation_id):
    existing = query_one("""
        SELECT donation_id, status FROM Donations WHERE donation_id = %s
    """, (donation_id,))
    
    if not existing:
        raise AppError("Record not found.", 404)

    if existing["status"] == "ALLOCATED":
        raise AppError("This donation is already used in a transplant and cannot be edited.", 409)

    data = request.get_json(silent=True) or {}
    donation_type = str(data.get("donation_type", "")).strip()
    donation_date = str(data.get("donation_date", "")).strip()
    status = str(data.get("status", "")).strip()

    if not donation_type or not donation_date or not status:
        raise AppError("Please check the form: a field is missing or has an invalid value.", 400)

    try:
        donation_date_obj = datetime.strptime(donation_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise AppError("Please check the form: a field is missing or has an invalid value.", 400)

    if donation_date_obj > datetime.now().date():
        raise AppError("Donation date cannot be in the future.", 400)

    if donation_type not in VALID_DONATION_TYPES:
        raise AppError("Please check the form: a field is missing or has an invalid value.", 400)

    if status not in ALLOWED_DONATION_STATUSES:
        raise AppError("Status can only be changed between AVAILABLE and EXPIRED.", 400)

    execute("""
        UPDATE Donations
        SET donation_type = %s, donation_date = %s, status = %s
        WHERE donation_id = %s
    """, (donation_type, donation_date, status, donation_id))

    return jsonify({"message": "Donation updated successfully."}), 200
