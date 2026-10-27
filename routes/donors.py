import re
from flask import Blueprint, request, jsonify, session
from db import query, query_one, execute
from errors import AppError

donors_bp = Blueprint("donors", __name__, url_prefix="/api/donors")

VALID_GENDERS = {"M", "F", "Other"}
VALID_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
PHONE_REGEX = re.compile(r"^[0-9]{10}$")

@donors_bp.before_request
def check_auth():
    if not session.get("user"):
        return jsonify({"error": "Please sign in."}), 401

@donors_bp.route("", methods=["GET"])
def get_donors():
    donors = query("""
        SELECT donor_id, name, age, gender, blood_group, phone, registered_on
        FROM Donors
        ORDER BY donor_id DESC
    """)
    return jsonify(donors), 200

@donors_bp.route("", methods=["POST"])
def create_donor():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    age = data.get("age")
    gender = str(data.get("gender", "")).strip()
    blood_group = str(data.get("blood_group", "")).strip()
    phone = str(data.get("phone", "")).strip()

    if not name or age is None or not gender or not blood_group or not phone:
        raise AppError("Please fill in all required fields.", 400)

    if len(name) < 2:
        raise AppError("Full name must be at least 2 characters.", 400)

    try:
        age_int = int(age)
    except (ValueError, TypeError):
        raise AppError("Age must be a valid number.", 400)

    if not (18 <= age_int <= 100):
        raise AppError("Donor age must be between 18 and 100.", 400)

    if gender not in VALID_GENDERS:
        raise AppError("Invalid gender selected.", 400)

    if blood_group not in VALID_BLOOD_GROUPS:
        raise AppError("Invalid blood group selected.", 400)

    if not PHONE_REGEX.match(phone):
        raise AppError("Phone number must be a valid 10-digit number.", 400)

    result = execute("""
        INSERT INTO Donors (name, age, gender, blood_group, phone)
        VALUES (%s, %s, %s, %s, %s)
    """, (name, age_int, gender, blood_group, phone))

    return jsonify({
        "id": result["lastrowid"],
        "message": "Donor registered successfully."
    }), 201

@donors_bp.route("/<int:donor_id>", methods=["PUT"])
def update_donor(donor_id):
    existing = query_one("SELECT donor_id FROM Donors WHERE donor_id = %s", (donor_id,))
    if not existing:
        raise AppError("Record not found.", 404)

    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    age = data.get("age")
    gender = str(data.get("gender", "")).strip()
    phone = str(data.get("phone", "")).strip()

    if not name or age is None or not gender or not phone:
        raise AppError("Please fill in all required fields.", 400)

    if len(name) < 2:
        raise AppError("Full name must be at least 2 characters.", 400)

    try:
        age_int = int(age)
    except (ValueError, TypeError):
        raise AppError("Age must be a valid number.", 400)

    if not (18 <= age_int <= 100):
        raise AppError("Donor age must be between 18 and 100.", 400)

    if gender not in VALID_GENDERS:
        raise AppError("Invalid gender selected.", 400)

    if not PHONE_REGEX.match(phone):
        raise AppError("Phone number must be a valid 10-digit number.", 400)

    execute("""
        UPDATE Donors
        SET name = %s, age = %s, gender = %s, phone = %s
        WHERE donor_id = %s
    """, (name, age_int, gender, phone, donor_id))

    return jsonify({"message": "Donor updated successfully."}), 200

@donors_bp.route("/<int:donor_id>", methods=["DELETE"])
def delete_donor(donor_id):
    existing = query_one("SELECT donor_id FROM Donors WHERE donor_id = %s", (donor_id,))
    if not existing:
        raise AppError("Record not found.", 404)

    # Check if donor has donations
    donation_count = query_one("SELECT COUNT(*) AS cnt FROM Donations WHERE donor_id = %s", (donor_id,))["cnt"]
    if donation_count > 0:
        raise AppError("This record is in use by other records and cannot be deleted.", 409)

    execute("DELETE FROM Donors WHERE donor_id = %s", (donor_id,))
    return jsonify({"message": "Donor deleted successfully."}), 200
