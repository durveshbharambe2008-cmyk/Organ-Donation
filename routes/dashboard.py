from flask import Blueprint, jsonify, session
from db import query, query_one

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")

@dashboard_bp.before_request
def check_auth():
    if not session.get("user"):
        return jsonify({"error": "Please sign in."}), 401

@dashboard_bp.route("", methods=["GET"])
def get_dashboard():
    # Fetch counts for summary cards
    donors_count = query_one("SELECT COUNT(*) AS cnt FROM Donors")["cnt"]
    recipients_count = query_one("SELECT COUNT(*) AS cnt FROM Recipients")["cnt"]
    donations_count = query_one("SELECT COUNT(*) AS cnt FROM Donations WHERE status = 'AVAILABLE'")["cnt"]
    requests_count = query_one("SELECT COUNT(*) AS cnt FROM Requests WHERE status = 'WAITING'")["cnt"]
    transplants_count = query_one("SELECT COUNT(*) AS cnt FROM Transplants")["cnt"]

    # Available per organ
    available_by_organ = query("""
        SELECT o.organ_name, COUNT(*) AS available
        FROM Donations dn
        JOIN Organs o ON o.organ_id = dn.organ_id
        WHERE dn.status = 'AVAILABLE'
        GROUP BY o.organ_name
        ORDER BY o.organ_name ASC
    """)

    # Recent transplants (latest 5)
    recent_transplants = query("""
        SELECT t.transplant_id, o.organ_name, d.name AS donor, rc.name AS patient,
               t.transplant_date, t.outcome
        FROM Transplants t
        JOIN Donations dn  ON dn.donation_id = t.donation_id
        JOIN Donors d      ON d.donor_id = dn.donor_id
        JOIN Requests r    ON r.request_id = t.request_id
        JOIN Recipients rc ON rc.recipient_id = r.recipient_id
        JOIN Organs o      ON o.organ_id = dn.organ_id
        ORDER BY t.transplant_date DESC, t.transplant_id DESC
        LIMIT 5
    """)

    return jsonify({
        "totals": {
            "donors": donors_count,
            "recipients": recipients_count,
            "availableDonations": donations_count,
            "waitingRequests": requests_count,
            "transplants": transplants_count
        },
        "availableByOrgan": available_by_organ,
        "recentTransplants": recent_transplants
    }), 200
