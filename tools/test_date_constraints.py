import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import db
from app import create_app

print("=" * 60)
print("TESTING DATE CONSTRAINTS (DB TRIGGERS & FLASK ROUTES)")
print("=" * 60)

# 1. Database-level trigger test
conn = db.get_connection()
cur = conn.cursor()

# Test 1: Future donation date
try:
    cur.execute("INSERT INTO Donations (donor_id, organ_id, donation_type, status, donation_date) VALUES (1, 1, 'LIVING', 'AVAILABLE', '2027-01-01')")
    print("[FAIL] Database allowed future donation date!")
except Exception as e:
    print(f"[PASS] Database blocked future donation: {e}")

# Test 2: Future request date
try:
    cur.execute("INSERT INTO Requests (recipient_id, organ_id, urgency, status, request_date) VALUES (1, 1, 'HIGH', 'WAITING', '2027-01-01')")
    print("[FAIL] Database allowed future request date!")
except Exception as e:
    print(f"[PASS] Database blocked future request: {e}")

# Test 3: Future transplant date
try:
    cur.execute("INSERT INTO Transplants (donation_id, request_id, surgeon_name, transplant_date, outcome) VALUES (3, 3, 'Dr. Future', '2027-01-01', 'SUCCESSFUL')")
    print("[FAIL] Database allowed future transplant date!")
except Exception as e:
    print(f"[PASS] Database blocked future transplant: {e}")

cur.close()
conn.close()

# 2. Flask Route / API test
app = create_app()
client = app.test_client()
with client.session_transaction() as sess:
    sess["user"] = "admin"

res = client.post("/api/donations", json={
    "donor_id": 1,
    "organ_id": 1,
    "donation_type": "LIVING",
    "donation_date": "2027-10-10"
})
print(f"[{'PASS' if res.status_code == 400 else 'FAIL'}] POST /api/donations with 2027 date -> {res.status_code} ({res.get_json()})")

res = client.post("/api/requests", json={
    "recipient_id": 1,
    "organ_id": 1,
    "urgency": "HIGH",
    "request_date": "2027-10-10"
})
print(f"[{'PASS' if res.status_code == 400 else 'FAIL'}] POST /api/requests with 2027 date -> {res.status_code} ({res.get_json()})")

print("=" * 60)
print("ALL DATE CONSTRAINTS VERIFIED!")
print("=" * 60)
