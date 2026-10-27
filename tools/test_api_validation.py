import os
import sys

# Load .env
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.isfile(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("\"'"))

# Import app directly to use Flask test client
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import create_app

app = create_app()
client = app.test_client()

# Sign in
with client.session_transaction() as sess:
    sess["user"] = "admin"

tests = [
    # (endpoint, payload, expected_status, expected_error_msg_substr)
    (
        "/api/donors",
        {"name": "Test", "age": 25, "gender": "M", "blood_group": "O+", "phone": "958"},
        400,
        "10-digit number"
    ),
    (
        "/api/donors",
        {"name": "Test", "age": 15, "gender": "M", "blood_group": "O+", "phone": "9820099999"},
        400,
        "between 18 and 100"
    ),
    (
        "/api/donors",
        {"name": "Test", "age": 120, "gender": "M", "blood_group": "O+", "phone": "9820099999"},
        400,
        "between 18 and 100"
    ),
    (
        "/api/donors",
        {"name": "T", "age": 25, "gender": "M", "blood_group": "O+", "phone": "9820099999"},
        400,
        "at least 2 characters"
    ),
    (
        "/api/recipients",
        {"name": "Test", "age": 25, "gender": "F", "blood_group": "A+", "phone": "12345"},
        400,
        "10-digit number"
    ),
    (
        "/api/recipients",
        {"name": "Test", "age": 105, "gender": "F", "blood_group": "A+", "phone": "9930099999"},
        400,
        "between 0 and 100"
    ),
    (
        "/api/donors",
        {"name": "Nine Digit Donor", "age": 28, "gender": "M", "blood_group": "O+", "phone": "982001119"},
        400,
        "10-digit number"
    ),
    (
        "/api/donors",
        {"name": "Ten Digit Donor", "age": 28, "gender": "M", "blood_group": "O+", "phone": "9820011199"},
        201,
        "registered successfully"
    ),
]

all_passed = True
for ep, payload, status, msg_sub in tests:
    res = client.post(ep, json=payload)
    data = res.get_json() or {}
    err = data.get("error", "") or data.get("message", "")
    passed = res.status_code == status and msg_sub.lower() in err.lower()
    print(f"[{'PASS' if passed else 'FAIL'}] POST {ep} -> {res.status_code} ({err})")
    if not passed:
        all_passed = False

# Cleanup test records
from db import execute
execute("DELETE FROM Donors WHERE phone IN ('982001119', '9820011199')")

if all_passed:
    print("\nAll API validation tests PASSED successfully!")
else:
    print("\nSome API validation tests failed.")
    sys.exit(1)
