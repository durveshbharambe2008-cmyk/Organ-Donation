-- Organ Donation Management System | MySQL 8.0.16+
USE defaultdb;

DROP TABLE IF EXISTS Transplants, Requests, Donations, Organs, Recipients, Donors;

CREATE TABLE Donors (
    donor_id      INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    age           INT NOT NULL,
    gender        ENUM('M', 'F', 'Other') NOT NULL,
    blood_group   ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') NOT NULL,
    phone         VARCHAR(15) NOT NULL UNIQUE,
    registered_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_donor_name CHECK (CHAR_LENGTH(TRIM(name)) >= 2),
    CONSTRAINT chk_donor_age CHECK (age BETWEEN 18 AND 100),
    CONSTRAINT chk_donor_phone CHECK (phone REGEXP '^[0-9]{10}$')
);

CREATE TABLE Recipients (
    recipient_id  INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    age           INT NOT NULL,
    gender        ENUM('M', 'F', 'Other') NOT NULL,
    blood_group   ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') NOT NULL,
    phone         VARCHAR(15) NOT NULL UNIQUE,
    registered_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_recipient_name CHECK (CHAR_LENGTH(TRIM(name)) >= 2),
    CONSTRAINT chk_recipient_age CHECK (age BETWEEN 0 AND 100),
    CONSTRAINT chk_recipient_phone CHECK (phone REGEXP '^[0-9]{10}$')
);

CREATE TABLE Organs (
    organ_id   INT AUTO_INCREMENT PRIMARY KEY,
    organ_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE Donations (
    donation_id   INT AUTO_INCREMENT PRIMARY KEY,
    donor_id      INT NOT NULL,
    organ_id      INT NOT NULL,
    donation_type ENUM('LIVING', 'DECEASED') NOT NULL,
    status        ENUM('AVAILABLE', 'ALLOCATED', 'EXPIRED') NOT NULL DEFAULT 'AVAILABLE',
    donation_date DATE NOT NULL,
    FOREIGN KEY (donor_id) REFERENCES Donors(donor_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    FOREIGN KEY (organ_id) REFERENCES Organs(organ_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
);

CREATE TABLE Requests (
    request_id   INT AUTO_INCREMENT PRIMARY KEY,
    recipient_id INT NOT NULL,
    organ_id     INT NOT NULL,
    urgency      ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL,
    status       ENUM('WAITING', 'MATCHED', 'CLOSED') NOT NULL DEFAULT 'WAITING',
    request_date DATE NOT NULL,
    FOREIGN KEY (recipient_id) REFERENCES Recipients(recipient_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    FOREIGN KEY (organ_id) REFERENCES Organs(organ_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
);

CREATE TABLE Transplants (
    transplant_id   INT AUTO_INCREMENT PRIMARY KEY,
    donation_id     INT NOT NULL UNIQUE,
    request_id      INT NOT NULL UNIQUE,
    surgeon_name    VARCHAR(50) NOT NULL,
    transplant_date DATE NOT NULL,
    outcome         ENUM('SUCCESSFUL', 'COMPLICATIONS', 'FAILED') NOT NULL,
    FOREIGN KEY (donation_id) REFERENCES Donations(donation_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    FOREIGN KEY (request_id) REFERENCES Requests(request_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT chk_transplant_surgeon CHECK (CHAR_LENGTH(TRIM(surgeon_name)) >= 2)
);

DELIMITER $$

CREATE TRIGGER trg_transplant_before_insert
BEFORE INSERT ON Transplants
FOR EACH ROW
BEGIN
    DECLARE d_organ  INT;
    DECLARE r_organ  INT;
    DECLARE d_blood  VARCHAR(3);
    DECLARE r_blood  VARCHAR(3);
    DECLARE d_status VARCHAR(10);
    DECLARE r_status VARCHAR(10);

    SELECT dn.organ_id, dn.status, d.blood_group
      INTO d_organ, d_status, d_blood
      FROM Donations dn
      JOIN Donors d ON d.donor_id = dn.donor_id
     WHERE dn.donation_id = NEW.donation_id;

    SELECT rq.organ_id, rq.status, r.blood_group
      INTO r_organ, r_status, r_blood
      FROM Requests rq
      JOIN Recipients r ON r.recipient_id = rq.recipient_id
     WHERE rq.request_id = NEW.request_id;

    IF d_organ <> r_organ THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Donated organ and requested organ are different';
    END IF;
    IF d_blood <> r_blood THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Donor and recipient blood groups do not match';
    END IF;
    IF d_status <> 'AVAILABLE' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'This donation is not available';
    END IF;
    IF r_status <> 'WAITING' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'This request is not waiting for an organ';
    END IF;
END$$

CREATE TRIGGER trg_transplant_after_insert
AFTER INSERT ON Transplants
FOR EACH ROW
BEGIN
    UPDATE Donations SET status = 'ALLOCATED' WHERE donation_id = NEW.donation_id;
    UPDATE Requests  SET status = 'MATCHED'   WHERE request_id  = NEW.request_id;
END$$

DELIMITER ;
