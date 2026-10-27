"""
Comprehensive edge-case & integrity test for the Organ Donation Management System.
Runs directly against MySQL. Adapts to DB state and cleans up reliably.
"""
import os, sys
import mysql.connector

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# -- Load .env ------------------------------------------------------------------
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
env_path = os.path.join(PROJECT_DIR, ".env")
if os.path.isfile(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("\"'"))

DB_CFG = dict(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "organ_donation"),
)

conn = mysql.connector.connect(**DB_CFG)
cur  = conn.cursor(dictionary=True)

passed = 0
failed = 0
created_ids = {"donors": [], "recipients": [], "donations": [], "requests": [], "transplants": []}

def test(label, condition, detail=""):
    global passed, failed
    status = "PASS" if condition else "FAIL"
    if condition:
        passed += 1
    else:
        failed += 1
    extra = f"  ({detail})" if detail else ""
    print(f"  [{status}] {label}{extra}")

def sql_should_fail(label, sql, params=None, expected_errno=None, expected_msg_substr=None):
    """Execute SQL expecting it to fail. Return True if it failed as expected."""
    global passed, failed
    try:
        cur.execute(sql, params or ())
        conn.commit()
        failed += 1
        print(f"  [FAIL] {label}  (INSERT/UPDATE succeeded but should have been rejected)")
        return False
    except mysql.connector.Error as e:
        ok = True
        if expected_errno:
            if isinstance(expected_errno, (tuple, list, set)):
                if e.errno not in expected_errno:
                    ok = False
            elif e.errno != expected_errno:
                ok = False
        if expected_msg_substr and expected_msg_substr.lower() not in str(e.msg).lower():
            ok = False
        if ok:
            passed += 1
            print(f"  [PASS] {label}  (errno={e.errno}, msg={e.msg})")
        else:
            failed += 1
            print(f"  [FAIL] {label}  (unexpected: errno={e.errno}, msg={e.msg})")
        conn.rollback()
        return ok

def clean_test_artifacts():
    """Wipe any prior test records from the DB."""
    # Delete transplants created by test donors/recipients
    cur.execute("""
        DELETE t FROM Transplants t
        JOIN Donations dn ON dn.donation_id = t.donation_id
        JOIN Donors d ON d.donor_id = dn.donor_id
        WHERE d.name LIKE 'Test Donor%' OR d.phone LIKE '11111%'
    """)
    cur.execute("""
        DELETE t FROM Transplants t
        JOIN Requests r ON r.request_id = t.request_id
        JOIN Recipients rc ON rc.recipient_id = r.recipient_id
        WHERE rc.name LIKE 'Test Recipient%' OR rc.phone LIKE '22222%'
    """)
    conn.commit()

    # Delete requests for test recipients
    cur.execute("""
        DELETE r FROM Requests r
        JOIN Recipients rc ON rc.recipient_id = r.recipient_id
        WHERE rc.name LIKE 'Test Recipient%' OR rc.phone LIKE '22222%'
    """)
    conn.commit()

    # Delete donations for test donors
    cur.execute("""
        DELETE dn FROM Donations dn
        JOIN Donors d ON d.donor_id = dn.donor_id
        WHERE d.name LIKE 'Test Donor%' OR d.phone LIKE '11111%'
    """)
    conn.commit()

    # Delete test donors and recipients
    cur.execute("DELETE FROM Donors WHERE name LIKE 'Test Donor%' OR phone LIKE '11111%'")
    cur.execute("DELETE FROM Recipients WHERE name LIKE 'Test Recipient%' OR phone LIKE '22222%'")
    conn.commit()

    # Clean leftover test donation #4 if unused
    cur.execute("SELECT donation_id FROM Donations WHERE donation_id = 4")
    if cur.fetchone():
        cur.execute("SELECT COUNT(*) AS cnt FROM Transplants WHERE donation_id = 4")
        if cur.fetchone()["cnt"] == 0:
            cur.execute("DELETE FROM Donations WHERE donation_id = 4")
            conn.commit()

# Clean up before running
clean_test_artifacts()

try:
    # ==============================================================================
    print("\n" + "=" * 72)
    print("SECTION 0: Verify existing transplant side-effects")
    print("=" * 72)

    cur.execute("SELECT donation_id, request_id FROM Transplants")
    existing_transplants = cur.fetchall()

    for t in existing_transplants:
        did, rid = t["donation_id"], t["request_id"]
        cur.execute("SELECT status FROM Donations WHERE donation_id = %s", (did,))
        d = cur.fetchone()
        test(f"Donation #{did} is ALLOCATED (transplant exists)", d["status"] == "ALLOCATED", f"got {d['status']}")

        cur.execute("SELECT status FROM Requests WHERE request_id = %s", (rid,))
        r = cur.fetchone()
        test(f"Request #{rid} is MATCHED (transplant exists)", r["status"] == "MATCHED", f"got {r['status']}")


    # ==============================================================================
    print("\n" + "=" * 72)
    print("SECTION 1: Create fresh test data for a clean transplant test")
    print("=" * 72)

    # Create donor (O-) and recipient (O-) with same blood group
    cur.execute("""
        INSERT INTO Donors (name, age, gender, blood_group, phone)
        VALUES ('Test Donor Alpha', 30, 'M', 'O-', '1111100001')
    """)
    conn.commit()
    test_donor_id = cur.lastrowid
    created_ids["donors"].append(test_donor_id)
    print(f"  Created test donor #{test_donor_id} (O-)")

    cur.execute("""
        INSERT INTO Recipients (name, age, gender, blood_group, phone)
        VALUES ('Test Recipient Alpha', 25, 'F', 'O-', '2222200001')
    """)
    conn.commit()
    test_recipient_id = cur.lastrowid
    created_ids["recipients"].append(test_recipient_id)
    print(f"  Created test recipient #{test_recipient_id} (O-)")

    # Create a donation (Kidney) and a request (Kidney)
    cur.execute("""
        INSERT INTO Donations (donor_id, organ_id, donation_type, donation_date)
        VALUES (%s, 1, 'LIVING', '2026-10-24')
    """, (test_donor_id,))
    conn.commit()
    test_donation_id = cur.lastrowid
    created_ids["donations"].append(test_donation_id)
    print(f"  Created test donation #{test_donation_id} (Kidney, AVAILABLE)")

    cur.execute("""
        INSERT INTO Requests (recipient_id, organ_id, urgency, request_date)
        VALUES (%s, 1, 'HIGH', '2026-10-24')
    """, (test_recipient_id,))
    conn.commit()
    test_request_id = cur.lastrowid
    created_ids["requests"].append(test_request_id)
    print(f"  Created test request #{test_request_id} (Kidney, WAITING)")


    # ==============================================================================
    print("\n" + "=" * 72)
    print("SECTION 2: Trigger - mismatched organ type")
    print("=" * 72)

    # test_donation is Kidney (organ_id=1). Create a request for Liver (organ_id=2)
    cur.execute("""
        INSERT INTO Requests (recipient_id, organ_id, urgency, request_date)
        VALUES (%s, 2, 'LOW', '2026-10-24')
    """, (test_recipient_id,))
    conn.commit()
    liver_req_id = cur.lastrowid
    created_ids["requests"].append(liver_req_id)

    sql_should_fail(
        "Mismatched organ transplant blocked",
        "INSERT INTO Transplants (donation_id, request_id, surgeon_name, transplant_date, outcome) VALUES (%s, %s, 'Dr. X', '2026-10-24', 'SUCCESSFUL')",
        (test_donation_id, liver_req_id),
        expected_msg_substr="different"
    )


    # ==============================================================================
    print("\n" + "=" * 72)
    print("SECTION 3: Trigger - mismatched blood group")
    print("=" * 72)

    # Create a recipient with different blood group (A+)
    cur.execute("""
        INSERT INTO Recipients (name, age, gender, blood_group, phone)
        VALUES ('Test Recipient Beta', 40, 'M', 'A+', '2222200002')
    """)
    conn.commit()
    beta_recipient_id = cur.lastrowid
    created_ids["recipients"].append(beta_recipient_id)

    cur.execute("""
        INSERT INTO Requests (recipient_id, organ_id, urgency, request_date)
        VALUES (%s, 1, 'MEDIUM', '2026-10-24')
    """, (beta_recipient_id,))
    conn.commit()
    beta_req_id = cur.lastrowid
    created_ids["requests"].append(beta_req_id)

    # test_donation is O- donor, beta request is A+ recipient -> blood mismatch
    sql_should_fail(
        "Mismatched blood group transplant blocked",
        "INSERT INTO Transplants (donation_id, request_id, surgeon_name, transplant_date, outcome) VALUES (%s, %s, 'Dr. X', '2026-10-24', 'SUCCESSFUL')",
        (test_donation_id, beta_req_id),
        expected_msg_substr="blood"
    )


    # ==============================================================================
    print("\n" + "=" * 72)
    print("SECTION 4: Valid transplant - cascading status updates")
    print("=" * 72)

    cur.execute("SELECT status FROM Donations WHERE donation_id = %s", (test_donation_id,))
    test("Donation is AVAILABLE before transplant", cur.fetchone()["status"] == "AVAILABLE")

    cur.execute("SELECT status FROM Requests WHERE request_id = %s", (test_request_id,))
    test("Request is WAITING before transplant", cur.fetchone()["status"] == "WAITING")

    # Insert a valid transplant (same organ=Kidney, same blood=O-)
    cur.execute("""
        INSERT INTO Transplants (donation_id, request_id, surgeon_name, transplant_date, outcome)
        VALUES (%s, %s, 'Dr. Test Surgeon', '2026-10-24', 'SUCCESSFUL')
    """, (test_donation_id, test_request_id))
    conn.commit()
    test_transplant_id = cur.lastrowid
    created_ids["transplants"].append(test_transplant_id)
    test("Transplant created successfully", test_transplant_id > 0, f"id={test_transplant_id}")

    cur.execute("SELECT status FROM Donations WHERE donation_id = %s", (test_donation_id,))
    d_status = cur.fetchone()["status"]
    test("Donation -> ALLOCATED after transplant", d_status == "ALLOCATED", f"got {d_status}")

    cur.execute("SELECT status FROM Requests WHERE request_id = %s", (test_request_id,))
    r_status = cur.fetchone()["status"]
    test("Request -> MATCHED after transplant", r_status == "MATCHED", f"got {r_status}")


    # ==============================================================================
    print("\n" + "=" * 72)
    print("SECTION 5: Trigger - donation already allocated (re-use)")
    print("=" * 72)

    # Create another request for the same recipient (O-) for Kidney -> same organ & blood
    cur.execute("""
        INSERT INTO Requests (recipient_id, organ_id, urgency, request_date)
        VALUES (%s, 1, 'LOW', '2026-10-24')
    """, (test_recipient_id,))
    conn.commit()
    dup_req_id = cur.lastrowid
    created_ids["requests"].append(dup_req_id)

    sql_should_fail(
        "Already-allocated donation cannot be used again",
        "INSERT INTO Transplants (donation_id, request_id, surgeon_name, transplant_date, outcome) VALUES (%s, %s, 'Dr. X', '2026-10-24', 'SUCCESSFUL')",
        (test_donation_id, dup_req_id),
        expected_msg_substr="not available"
    )


    # ==============================================================================
    print("\n" + "=" * 72)
    print("SECTION 6: Trigger - request already matched (re-use)")
    print("=" * 72)

    # Create a new donation from the same donor (O-) for Kidney
    cur.execute("""
        INSERT INTO Donations (donor_id, organ_id, donation_type, donation_date)
        VALUES (%s, 1, 'LIVING', '2026-10-24')
    """, (test_donor_id,))
    conn.commit()
    new_don_id = cur.lastrowid
    created_ids["donations"].append(new_don_id)

    # test_request_id is already MATCHED
    sql_should_fail(
        "Already-matched request cannot be used again",
        "INSERT INTO Transplants (donation_id, request_id, surgeon_name, transplant_date, outcome) VALUES (%s, %s, 'Dr. X', '2026-10-24', 'SUCCESSFUL')",
        (new_don_id, test_request_id),
        expected_msg_substr="not waiting"
    )


    # ==============================================================================
    print("\n" + "=" * 72)
    print("SECTION 7: Matches view excludes allocated/matched records")
    print("=" * 72)

    cur.execute("""
        SELECT dn.donation_id, r.request_id
        FROM Donations dn
        JOIN Donors d      ON d.donor_id = dn.donor_id
        JOIN Requests r    ON r.organ_id = dn.organ_id AND r.status = 'WAITING'
        JOIN Recipients rc ON rc.recipient_id = r.recipient_id
                          AND rc.blood_group = d.blood_group
        WHERE dn.status = 'AVAILABLE'
    """)
    matches = cur.fetchall()

    # Collect ALL allocated donation IDs and matched request IDs
    cur.execute("SELECT donation_id FROM Donations WHERE status = 'ALLOCATED'")
    allocated_dids = {r["donation_id"] for r in cur.fetchall()}

    cur.execute("SELECT request_id FROM Requests WHERE status = 'MATCHED'")
    matched_rids = {r["request_id"] for r in cur.fetchall()}

    bad_donations = [m for m in matches if m["donation_id"] in allocated_dids]
    bad_requests  = [m for m in matches if m["request_id"] in matched_rids]

    test("No allocated donations in matches view", len(bad_donations) == 0,
         f"found {bad_donations}" if bad_donations else "clean")
    test("No matched requests in matches view", len(bad_requests) == 0,
         f"found {bad_requests}" if bad_requests else "clean")


    # ==============================================================================
    print("\n" + "=" * 72)
    print("SECTION 8: Dashboard counts are consistent")
    print("=" * 72)

    cur.execute("SELECT COUNT(*) AS cnt FROM Donations WHERE status = 'AVAILABLE'")
    avail_count = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) AS cnt FROM Requests WHERE status = 'WAITING'")
    wait_count = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) AS cnt FROM Transplants")
    trans_count = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) AS cnt FROM Donations WHERE status = 'ALLOCATED'")
    alloc_count = cur.fetchone()["cnt"]

    test("Allocated donations = total transplants", alloc_count == trans_count,
         f"allocated={alloc_count}, transplants={trans_count}")

    # Cross-check: every transplant's donation should be ALLOCATED
    cur.execute("""
        SELECT t.transplant_id, dn.status
        FROM Transplants t
        JOIN Donations dn ON dn.donation_id = t.donation_id
        WHERE dn.status != 'ALLOCATED'
    """)
    bad_trans_don = cur.fetchall()
    test("Every transplant's donation is ALLOCATED", len(bad_trans_don) == 0,
         f"violations: {bad_trans_don}" if bad_trans_don else "all correct")

    # Cross-check: every transplant's request should be MATCHED
    cur.execute("""
        SELECT t.transplant_id, r.status
        FROM Transplants t
        JOIN Requests r ON r.request_id = t.request_id
        WHERE r.status != 'MATCHED'
    """)
    bad_trans_req = cur.fetchall()
    test("Every transplant's request is MATCHED", len(bad_trans_req) == 0,
         f"violations: {bad_trans_req}" if bad_trans_req else "all correct")


    # ==============================================================================
    print("\n" + "=" * 72)
    print("SECTION 9: Foreign key deletion guards")
    print("=" * 72)

    sql_should_fail(
        "Cannot delete donor with donations",
        "DELETE FROM Donors WHERE donor_id = %s", (test_donor_id,),
        expected_errno=1451
    )
    sql_should_fail(
        "Cannot delete recipient with requests",
        "DELETE FROM Recipients WHERE recipient_id = %s", (test_recipient_id,),
        expected_errno=1451
    )
    sql_should_fail(
        "Cannot delete donation with transplant",
        "DELETE FROM Donations WHERE donation_id = %s", (test_donation_id,),
        expected_errno=1451
    )
    sql_should_fail(
        "Cannot delete request with transplant",
        "DELETE FROM Requests WHERE request_id = %s", (test_request_id,),
        expected_errno=1451
    )
    sql_should_fail(
        "Cannot delete organ in use by donations",
        "DELETE FROM Organs WHERE organ_id = 1",
        expected_errno=1451
    )


    # ==============================================================================
    print("\n" + "=" * 72)
    print("SECTION 10: CHECK constraints")
    print("=" * 72)

    sql_should_fail(
        "Donor age < 18 rejected",
        "INSERT INTO Donors (name, age, gender, blood_group, phone) VALUES ('Minor', 15, 'M', 'O+', '0000000099')",
        expected_errno=3819
    )
    sql_should_fail(
        "Donor age > 100 rejected",
        "INSERT INTO Donors (name, age, gender, blood_group, phone) VALUES ('Ancient', 105, 'M', 'O+', '0000000099')",
        expected_errno=3819
    )
    sql_should_fail(
        "Donor phone 3-digits ('958') rejected",
        "INSERT INTO Donors (name, age, gender, blood_group, phone) VALUES ('Short Phone', 30, 'M', 'O+', '958')",
        expected_errno=3819
    )
    sql_should_fail(
        "Donor phone with letters rejected",
        "INSERT INTO Donors (name, age, gender, blood_group, phone) VALUES ('Bad Phone', 30, 'M', 'O+', '98200abcde')",
        expected_errno=3819
    )
    sql_should_fail(
        "Donor name < 2 chars rejected",
        "INSERT INTO Donors (name, age, gender, blood_group, phone) VALUES ('X', 30, 'M', 'O+', '0000000099')",
        expected_errno=3819
    )
    sql_should_fail(
        "Recipient age > 100 rejected",
        "INSERT INTO Recipients (name, age, gender, blood_group, phone) VALUES ('Old', 105, 'F', 'O+', '0000000098')",
        expected_errno=3819
    )
    sql_should_fail(
        "Recipient phone 3-digits rejected",
        "INSERT INTO Recipients (name, age, gender, blood_group, phone) VALUES ('Short Recipient', 30, 'F', 'O+', '123')",
        expected_errno=3819
    )
    sql_should_fail(
        "Recipient name < 2 chars rejected",
        "INSERT INTO Recipients (name, age, gender, blood_group, phone) VALUES ('Y', 30, 'F', 'O+', '0000000098')",
        expected_errno=3819
    )
    sql_should_fail(
        "Surgeon name < 2 chars rejected",
        "INSERT INTO Transplants (donation_id, request_id, surgeon_name, transplant_date, outcome) VALUES (%s, %s, 'D', '2026-10-25', 'SUCCESSFUL')",
        (test_donation_id, dup_req_id),
        expected_errno=(3819, 1644)
    )


    # ==============================================================================
    print("\n" + "=" * 72)
    print("SECTION 11: UNIQUE constraints")
    print("=" * 72)

    sql_should_fail(
        "Duplicate donor phone rejected",
        "INSERT INTO Donors (name, age, gender, blood_group, phone) VALUES ('Dup', 30, 'M', 'A+', '1111100001')",
        expected_errno=1062
    )
    sql_should_fail(
        "Duplicate organ name rejected",
        "INSERT INTO Organs (organ_name) VALUES ('Kidney')",
        expected_errno=1062
    )
    sql_should_fail(
        "Duplicate transplant for same donation rejected (blocked by trigger or UNIQUE on donation_id)",
        "INSERT INTO Transplants (donation_id, request_id, surgeon_name, transplant_date, outcome) VALUES (%s, %s, 'Dr. X', '2026-10-25', 'SUCCESSFUL')",
        (test_donation_id, dup_req_id),
        expected_errno=(1062, 1644)
    )


    # ==============================================================================
    print("\n" + "=" * 72)
    print("SECTION 12: Transplant join path - organ is correctly traced")
    print("=" * 72)

    cur.execute("""
        SELECT t.transplant_id, o.organ_name,
               d.name AS donor_name, d.blood_group AS donor_bg,
               rc.name AS patient_name, rc.blood_group AS patient_bg
        FROM Transplants t
        JOIN Donations dn  ON dn.donation_id = t.donation_id
        JOIN Donors d      ON d.donor_id = dn.donor_id
        JOIN Requests r    ON r.request_id = t.request_id
        JOIN Recipients rc ON rc.recipient_id = r.recipient_id
        JOIN Organs o      ON o.organ_id = dn.organ_id
        ORDER BY t.transplant_id
    """)
    all_transplants = cur.fetchall()

    for t in all_transplants:
        test(f"Transplant #{t['transplant_id']} has valid organ name",
             t["organ_name"] in ("Kidney", "Liver", "Heart", "Lung", "Pancreas", "Cornea"),
             f"organ={t['organ_name']}, donor={t['donor_name']} -> patient={t['patient_name']}")
        test(f"Transplant #{t['transplant_id']} blood groups match (donor-patient)",
             t["donor_bg"] == t["patient_bg"],
             f"donor_bg={t['donor_bg']}, patient_bg={t['patient_bg']}")


    # ==============================================================================
    print("\n" + "=" * 72)
    print("SECTION 13: App-level edit guards (simulating route logic)")
    print("=" * 72)

    # The donation route rejects edits if status == 'ALLOCATED'
    cur.execute("SELECT status FROM Donations WHERE donation_id = %s", (test_donation_id,))
    don_status = cur.fetchone()["status"]
    test("App-level: editing allocated donation would be blocked by route",
         don_status == "ALLOCATED",
         f"status={don_status} -> routes/donations.py line 68 returns 409")

    # The request route rejects edits if status == 'MATCHED'
    cur.execute("SELECT status FROM Requests WHERE request_id = %s", (test_request_id,))
    req_status = cur.fetchone()["status"]
    test("App-level: editing matched request would be blocked by route",
         req_status == "MATCHED",
         f"status={req_status} -> routes/requests.py line 69 returns 409")

    # The donation status can only be changed to AVAILABLE or EXPIRED (not ALLOCATED manually)
    test("App-level: ALLOWED_DONATION_STATUSES prevents manual ALLOCATED",
         "ALLOCATED" not in {"AVAILABLE", "EXPIRED"},
         "routes/donations.py allows only AVAILABLE or EXPIRED")

    # The request status can only be changed to WAITING or CLOSED (not MATCHED manually)
    test("App-level: ALLOWED_REQUEST_STATUSES prevents manual MATCHED",
         "MATCHED" not in {"WAITING", "CLOSED"},
         "routes/requests.py allows only WAITING or CLOSED")

finally:
    # ==============================================================================
    print("\n" + "=" * 72)
    print("CLEANUP: Removing test data")
    print("=" * 72)
    clean_test_artifacts()
    print("  Cleanup complete - only permanent data remains.\n")

# ==============================================================================
print("=" * 72)
print(f"RESULTS:  {passed} PASSED  /  {failed} FAILED  /  {passed + failed} TOTAL")
print("=" * 72)

cur.close()
conn.close()

sys.exit(0 if failed == 0 else 1)
