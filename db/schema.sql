
-- ============================================================
-- Organ Donation Management System
-- MySQL 8.0.16+
-- Database: defaultdb
--
-- SAFE SCHEMA:
--   * Does not drop databases or tables.
--   * Does not delete existing records.
--   * Creates missing tables and triggers.
--   * Existing tables are NOT automatically altered.
-- ============================================================

USE defaultdb;

-- ============================================================
-- 1. DONORS
-- ============================================================

CREATE TABLE IF NOT EXISTS Donors (
    donor_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    gender ENUM('M', 'F', 'Other') NOT NULL,
    blood_group ENUM(
        'A+', 'A-', 'B+', 'B-',
        'AB+', 'AB-', 'O+', 'O-'
    ) NOT NULL,
    phone VARCHAR(15) NOT NULL UNIQUE,
    registered_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_donor_name
        CHECK (CHAR_LENGTH(TRIM(name)) >= 2),
    CONSTRAINT chk_donor_age
        CHECK (age BETWEEN 18 AND 100),
    CONSTRAINT chk_donor_phone
        CHECK (phone REGEXP '^[0-9]{10}$')
) ENGINE=InnoDB;

-- ============================================================
-- 2. RECIPIENTS
-- ============================================================

CREATE TABLE IF NOT EXISTS Recipients (
    recipient_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    gender ENUM('M', 'F', 'Other') NOT NULL,
    blood_group ENUM(
        'A+', 'A-', 'B+', 'B-',
        'AB+', 'AB-', 'O+', 'O-'
    ) NOT NULL,
    phone VARCHAR(15) NOT NULL UNIQUE,
    registered_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_recipient_name
        CHECK (CHAR_LENGTH(TRIM(name)) >= 2),
    CONSTRAINT chk_recipient_age
        CHECK (age BETWEEN 0 AND 100),
    CONSTRAINT chk_recipient_phone
        CHECK (phone REGEXP '^[0-9]{10}$')
) ENGINE=InnoDB;

-- ============================================================
-- 3. ORGANS
-- ============================================================

CREATE TABLE IF NOT EXISTS Organs (
    organ_id INT AUTO_INCREMENT PRIMARY KEY,
    organ_name VARCHAR(50) NOT NULL UNIQUE,

    CONSTRAINT chk_organ_name
        CHECK (CHAR_LENGTH(TRIM(organ_name)) >= 2)
) ENGINE=InnoDB;

-- ============================================================
-- 4. DONATIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS Donations (
    donation_id INT AUTO_INCREMENT PRIMARY KEY,
    donor_id INT NOT NULL,
    organ_id INT NOT NULL,
    donation_type ENUM('LIVING', 'DECEASED') NOT NULL,
    status ENUM('AVAILABLE', 'ALLOCATED', 'EXPIRED')
        NOT NULL DEFAULT 'AVAILABLE',
    donation_date DATE NOT NULL,

    CONSTRAINT fk_donations_donor
        FOREIGN KEY (donor_id)
        REFERENCES Donors(donor_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,

    CONSTRAINT fk_donations_organ
        FOREIGN KEY (organ_id)
        REFERENCES Organs(organ_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- ============================================================
-- 5. REQUESTS
-- ============================================================

CREATE TABLE IF NOT EXISTS Requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    recipient_id INT NOT NULL,
    organ_id INT NOT NULL,
    urgency ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL,
    status ENUM('WAITING', 'MATCHED', 'CLOSED')
        NOT NULL DEFAULT 'WAITING',
    request_date DATE NOT NULL,

    CONSTRAINT fk_requests_recipient
        FOREIGN KEY (recipient_id)
        REFERENCES Recipients(recipient_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,

    CONSTRAINT fk_requests_organ
        FOREIGN KEY (organ_id)
        REFERENCES Organs(organ_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- ============================================================
-- 6. TRANSPLANTS
-- ============================================================

CREATE TABLE IF NOT EXISTS Transplants (
    transplant_id INT AUTO_INCREMENT PRIMARY KEY,
    donation_id INT NOT NULL UNIQUE,
    request_id INT NOT NULL UNIQUE,
    surgeon_name VARCHAR(50) NOT NULL,
    transplant_date DATE NOT NULL,
    outcome ENUM('SUCCESSFUL', 'COMPLICATIONS', 'FAILED') NOT NULL,

    CONSTRAINT fk_transplants_donation
        FOREIGN KEY (donation_id)
        REFERENCES Donations(donation_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,

    CONSTRAINT fk_transplants_request
        FOREIGN KEY (request_id)
        REFERENCES Requests(request_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,

    CONSTRAINT chk_transplant_surgeon
        CHECK (CHAR_LENGTH(TRIM(surgeon_name)) >= 2)
) ENGINE=InnoDB;

-- ============================================================
-- 7. TRANSPLANT VALIDATION TRIGGER
--    Checks organ, blood group and status before insertion.
-- ============================================================

DELIMITER $$

DROP TRIGGER IF EXISTS trg_transplant_before_insert$$

CREATE TRIGGER trg_transplant_before_insert
BEFORE INSERT ON Transplants
FOR EACH ROW
BEGIN
    DECLARE v_donation_found INT DEFAULT 0;
    DECLARE v_request_found INT DEFAULT 0;

    DECLARE v_donor_organ INT;
    DECLARE v_request_organ INT;

    DECLARE v_donor_blood VARCHAR(3);
    DECLARE v_recipient_blood VARCHAR(3);

    DECLARE v_donation_status VARCHAR(10);
    DECLARE v_request_status VARCHAR(10);

    -- Verify that the donation exists and retrieve donor details.
    SELECT COUNT(*)
    INTO v_donation_found
    FROM Donations
    WHERE donation_id = NEW.donation_id;

    IF v_donation_found = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Donation ID does not exist';
    END IF;

    SELECT dn.organ_id, dn.status, d.blood_group
    INTO v_donor_organ, v_donation_status, v_donor_blood
    FROM Donations dn
    JOIN Donors d ON d.donor_id = dn.donor_id
    WHERE dn.donation_id = NEW.donation_id;

    -- Verify that the request exists and retrieve recipient details.
    SELECT COUNT(*)
    INTO v_request_found
    FROM Requests
    WHERE request_id = NEW.request_id;

    IF v_request_found = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Request ID does not exist';
    END IF;

    SELECT rq.organ_id, rq.status, r.blood_group
    INTO v_request_organ, v_request_status, v_recipient_blood
    FROM Requests rq
    JOIN Recipients r ON r.recipient_id = rq.recipient_id
    WHERE rq.request_id = NEW.request_id;

    -- The donated organ must match the requested organ.
    IF v_donor_organ <> v_request_organ THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT =
                'Donated organ and requested organ are different';
    END IF;

    -- This project uses exact blood-group matching.
    IF v_donor_blood <> v_recipient_blood THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT =
                'Donor and recipient blood groups do not match';
    END IF;

    -- Only available donations can be used.
    IF v_donation_status <> 'AVAILABLE' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT =
                'This donation is not available';
    END IF;

    -- Only waiting requests can be fulfilled.
    IF v_request_status <> 'WAITING' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT =
                'This request is not waiting for an organ';
    END IF;
END$$

-- ============================================================
-- 8. UPDATE STATUSES AFTER A TRANSPLANT IS RECORDED
-- ============================================================

DROP TRIGGER IF EXISTS trg_transplant_after_insert$$

CREATE TRIGGER trg_transplant_after_insert
AFTER INSERT ON Transplants
FOR EACH ROW
BEGIN
    UPDATE Donations
    SET status = 'ALLOCATED'
    WHERE donation_id = NEW.donation_id;

    UPDATE Requests
    SET status = 'MATCHED'
    WHERE request_id = NEW.request_id;
END$$

DELIMITER ;

-- ============================================================
-- 9. VERIFICATION
-- ============================================================

SHOW TABLES;

SELECT
    TABLE_NAME
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME IN (
      'Donors',
      'Recipients',
      'Organs',
      'Donations',
      'Requests',
      'Transplants'
  )
ORDER BY TABLE_NAME;

-- End of schema.sql
