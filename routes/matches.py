from flask import Blueprint, jsonify, session
from db import query

matches_bp = Blueprint("matches", __name__, url_prefix="/api/matches")

@matches_bp.before_request
def check_auth():
    if not session.get("user"):
        return jsonify({"error": "Please sign in."}), 401

@matches_bp.route("", methods=["GET"])
def get_matches():
    matches = query("""
        SELECT dn.donation_id, r.request_id,
               d.name  AS donor,  rc.name AS patient,
               o.organ_name, d.blood_group, r.urgency,
               DATEDIFF(CURDATE(), r.request_date) AS days_waiting
        FROM Donations dn
        JOIN Donors d      ON d.donor_id = dn.donor_id
        JOIN Requests r    ON r.organ_id = dn.organ_id AND r.status = 'WAITING'
        JOIN Recipients rc ON rc.recipient_id = r.recipient_id
                          AND rc.blood_group = d.blood_group
        JOIN Organs o      ON o.organ_id = dn.organ_id
        WHERE dn.status = 'AVAILABLE'
        ORDER BY FIELD(r.urgency, 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'), r.request_date
    """)
    return jsonify(matches), 200
