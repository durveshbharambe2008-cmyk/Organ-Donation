import os
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.isfile(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("\"'"))
import mysql.connector
conn = mysql.connector.connect(
    host=os.getenv("DB_HOST","localhost"),
    port=int(os.getenv("DB_PORT","3306")),
    user=os.getenv("DB_USER","root"),
    password=os.getenv("DB_PASSWORD",""),
    database=os.getenv("DB_NAME","organ_donation"))
cur = conn.cursor(dictionary=True)
for table in ["Donors","Recipients","Organs","Donations","Requests","Transplants"]:
    print(f"\n=== {table.upper()} ===")
    cur.execute(f"SELECT * FROM {table}")
    for r in cur.fetchall():
        print(r)
cur.close()
conn.close()
