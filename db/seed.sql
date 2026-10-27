
-- Organ Donation Management System
-- Sample data for MySQL 8.0.16+
-- Safe to rerun for these specific sample records.

USE defaultdb;

START TRANSACTION;

-- 1. Donors
INSERT INTO Donors
    (name, age, gender, blood_group, phone, registered_on)
SELECT v.name, v.age, v.gender, v.blood_group, v.phone, v.registered_on
FROM (
    SELECT 'Rohan Mehta' AS name, 34 AS age, 'M' AS gender,
           'O+' AS blood_group, '9820011111' AS phone,
           CAST('2026-09-01 09:00:00' AS DATETIME) AS registered_on
    UNION ALL
    SELECT 'Anita Desai', 29, 'F', 'B+', '9820022222',
           CAST('2026-09-10 11:30:00' AS DATETIME)
    UNION ALL
    SELECT 'Karan Shah', 41, 'M', 'A+', '9820033333',
           CAST('2026-10-02 10:15:00' AS DATETIME)
) AS v
WHERE NOT EXISTS (
    SELECT 1 FROM Donors d WHERE d.phone = v.phone
);

-- 2. Recipients
INSERT INTO Recipients
    (name, age, gender, blood_group, phone, registered_on)
SELECT v.name, v.age, v.gender, v.blood_group, v.phone, v.registered_on
FROM (
    SELECT 'Suresh Patil' AS name, 45 AS age, 'M' AS gender,
           'B+' AS blood_group, '9930011111' AS phone,
           CAST('2026-08-10 10:00:00' AS DATETIME) AS registered_on
    UNION ALL
    SELECT 'Meena Iyer', 38, 'F', 'O+', '9930022222',
           CAST('2026-09-25 14:00:00' AS DATETIME)
    UNION ALL
    SELECT 'Imran Qureshi', 52, 'M', 'A+', '9930033333',
           CAST('2026-09-30 12:45:00' AS DATETIME)
) AS v
WHERE NOT EXISTS (
    SELECT 1 FROM Recipients r WHERE r.phone = v.phone
);

-- 3. Organs
INSERT INTO Organs (organ_name)
SELECT v.organ_name
FROM (
    SELECT 'Kidney' AS organ_name
    UNION ALL SELECT 'Liver'
    UNION ALL SELECT 'Heart'
    UNION ALL SELECT 'Lung'
    UNION ALL SELECT 'Pancreas'
    UNION ALL SELECT 'Cornea'
) AS v
WHERE NOT EXISTS (
    SELECT 1 FROM Organs o WHERE o.organ_name = v.organ_name
);

-- 4. Donations
-- Donor 2 (Anita, B+) and organ Kidney.
-- The donor and organ are resolved by unique values, not fixed IDs.
INSERT INTO Donations
    (donor_id, organ_id, donation_type, status, donation_date)
SELECT d.donor_id, o.organ_id, 'LIVING', 'AVAILABLE', '2026-09-20'
FROM Donors d
JOIN Organs o ON o.organ_name = 'Kidney'
WHERE d.phone = '9820022222'
  AND NOT EXISTS (
      SELECT 1
      FROM Donations dn
      WHERE dn.donor_id = d.donor_id
        AND dn.organ_id = o.organ_id
        AND dn.donation_date = '2026-09-20'
  );

INSERT INTO Donations
    (donor_id, organ_id, donation_type, status, donation_date)
SELECT d.donor_id, o.organ_id, 'DECEASED', 'AVAILABLE', '2026-10-10'
FROM Donors d
JOIN Organs o ON o.organ_name = 'Liver'
WHERE d.phone = '9820011111'
  AND NOT EXISTS (
      SELECT 1
      FROM Donations dn
      WHERE dn.donor_id = d.donor_id
        AND dn.organ_id = o.organ_id
        AND dn.donation_date = '2026-10-10'
  );

INSERT INTO Donations
    (donor_id, organ_id, donation_type, status, donation_date)
SELECT d.donor_id, o.organ_id, 'LIVING', 'AVAILABLE', '2026-10-12'
FROM Donors d
JOIN Organs o ON o.organ_name = 'Kidney'
WHERE d.phone = '9820033333'
  AND NOT EXISTS (
      SELECT 1
      FROM Donations dn
      WHERE dn.donor_id = d.donor_id
        AND dn.organ_id = o.organ_id
        AND dn.donation_date = '2026-10-12'
  );

-- 5. Requests
INSERT INTO Requests
    (recipient_id, organ_id, urgency, status, request_date)
SELECT r.recipient_id, o.organ_id, 'HIGH', 'WAITING', '2026-08-15'
FROM Recipients r
JOIN Organs o ON o.organ_name = 'Kidney'
WHERE r.phone = '9930011111'
  AND NOT EXISTS (
      SELECT 1
      FROM Requests rq
      WHERE rq.recipient_id = r.recipient_id
        AND rq.organ_id = o.organ_id
        AND rq.request_date = '2026-08-15'
  );

INSERT INTO Requests
    (recipient_id, organ_id, urgency, status, request_date)
SELECT r.recipient_id, o.organ_id, 'CRITICAL', 'WAITING', '2026-09-28'
FROM Recipients r
JOIN Organs o ON o.organ_name = 'Liver'
WHERE r.phone = '9930022222'
  AND NOT EXISTS (
      SELECT 1
      FROM Requests rq
      WHERE rq.recipient_id = r.recipient_id
        AND rq.organ_id = o.organ_id
        AND rq.request_date = '2026-09-28'
  );

INSERT INTO Requests
    (recipient_id, organ_id, urgency, status, request_date)
SELECT r.recipient_id, o.organ_id, 'MEDIUM', 'WAITING', '2026-10-01'
FROM Recipients r
JOIN Organs o ON o.organ_name = 'Kidney'
WHERE r.phone = '9930033333'
  AND NOT EXISTS (
      SELECT 1
      FROM Requests rq
      WHERE rq.recipient_id = r.recipient_id
        AND rq.organ_id = o.organ_id
        AND rq.request_date = '2026-10-01'
  );

-- 6. One valid transplant: Anita (B+) -> Suresh (B+), Kidney.
-- Resolve the matching donation and request by their related records.
INSERT INTO Transplants
    (donation_id, request_id, surgeon_name, transplant_date, outcome)
SELECT dn.donation_id, rq.request_id,
       'Dr. R. Kulkarni', '2026-09-25', 'SUCCESSFUL'
FROM Donations dn
JOIN Donors d ON d.donor_id = dn.donor_id
JOIN Organs od ON od.organ_id = dn.organ_id
JOIN Requests rq ON rq.request_date = '2026-08-15'
JOIN Recipients r ON r.recipient_id = rq.recipient_id
JOIN Organs orq ON orq.organ_id = rq.organ_id
WHERE d.phone = '9820022222'
  AND od.organ_name = 'Kidney'
  AND dn.donation_date = '2026-09-20'
  AND r.phone = '9930011111'
  AND orq.organ_name = 'Kidney'
  AND dn.status = 'AVAILABLE'
  AND rq.status = 'WAITING'
  AND NOT EXISTS (
      SELECT 1
      FROM Transplants t
      WHERE t.donation_id = dn.donation_id
         OR t.request_id = rq.request_id
  );

COMMIT;

-- 7. Verify sample records
SELECT * FROM Donors;
SELECT * FROM Recipients;
SELECT * FROM Organs;
SELECT * FROM Donations;
SELECT * FROM Requests;
SELECT * FROM Transplants;
