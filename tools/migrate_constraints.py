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

import mysql.connector

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "organ_donation")
)
cur = conn.cursor()

# Remove the invalid test row if present
cur.execute("DELETE FROM Donors WHERE phone = '958'")
conn.commit()

# Update constraints on Donors
try:
    cur.execute("ALTER TABLE Donors DROP CHECK chk_donor_age")
except Exception as e:
    print("drop chk_donor_age notice:", e)

try:
    cur.execute("ALTER TABLE Donors DROP CHECK chk_donor_phone")
except Exception as e:
    print("drop chk_donor_phone notice:", e)

try:
    cur.execute("ALTER TABLE Donors DROP CHECK chk_donor_name")
except Exception as e:
    print("drop chk_donor_name notice:", e)

cur.execute("ALTER TABLE Donors ADD CONSTRAINT chk_donor_age CHECK (age BETWEEN 18 AND 100)")
cur.execute("ALTER TABLE Donors ADD CONSTRAINT chk_donor_phone CHECK (phone REGEXP '^[0-9]{10}$')")
cur.execute("ALTER TABLE Donors ADD CONSTRAINT chk_donor_name CHECK (CHAR_LENGTH(TRIM(name)) >= 2)")

# Update constraints on Recipients
try:
    cur.execute("ALTER TABLE Recipients DROP CHECK chk_recipient_age")
except Exception as e:
    print("drop chk_recipient_age notice:", e)

try:
    cur.execute("ALTER TABLE Recipients DROP CHECK chk_recipient_phone")
except Exception as e:
    print("drop chk_recipient_phone notice:", e)

try:
    cur.execute("ALTER TABLE Recipients DROP CHECK chk_recipient_name")
except Exception as e:
    print("drop chk_recipient_name notice:", e)

cur.execute("ALTER TABLE Recipients ADD CONSTRAINT chk_recipient_age CHECK (age BETWEEN 0 AND 100)")
cur.execute("ALTER TABLE Recipients ADD CONSTRAINT chk_recipient_phone CHECK (phone REGEXP '^[0-9]{10}$')")
cur.execute("ALTER TABLE Recipients ADD CONSTRAINT chk_recipient_name CHECK (CHAR_LENGTH(TRIM(name)) >= 2)")

# Update constraints on Transplants
try:
    cur.execute("ALTER TABLE Transplants ADD CONSTRAINT chk_transplant_surgeon CHECK (CHAR_LENGTH(TRIM(surgeon_name)) >= 2)")
except Exception as e:
    print("add chk_transplant_surgeon notice:", e)

conn.commit()
print("All CHECK constraints applied to live database!")
cur.close()
conn.close()
