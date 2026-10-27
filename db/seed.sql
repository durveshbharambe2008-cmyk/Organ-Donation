USE defaultdb;

INSERT INTO Donors (name, age, gender, blood_group, phone, registered_on) VALUES
    ('Rohan Mehta', 34, 'M', 'O+', '9820011111', '2026-09-01 09:00:00'),
    ('Anita Desai', 29, 'F', 'B+', '9820022222', '2026-09-10 11:30:00'),
    ('Karan Shah',  41, 'M', 'A+', '9820033333', '2026-10-02 10:15:00');

INSERT INTO Recipients (name, age, gender, blood_group, phone, registered_on) VALUES
    ('Suresh Patil',  45, 'M', 'B+', '9930011111', '2026-08-10 10:00:00'),
    ('Meena Iyer',    38, 'F', 'O+', '9930022222', '2026-09-25 14:00:00'),
    ('Imran Qureshi', 52, 'M', 'A+', '9930033333', '2026-09-30 12:45:00');

INSERT INTO Organs (organ_name) VALUES
    ('Kidney'), ('Liver'), ('Heart'), ('Lung'), ('Pancreas'), ('Cornea');

INSERT INTO Donations (donor_id, organ_id, donation_type, status, donation_date) VALUES
    (2, 1, 'LIVING',   'AVAILABLE', '2026-09-20'),
    (1, 2, 'DECEASED', 'AVAILABLE', '2026-10-10'),
    (3, 1, 'LIVING',   'AVAILABLE', '2026-10-12');

INSERT INTO Requests (recipient_id, organ_id, urgency, status, request_date) VALUES
    (1, 1, 'HIGH',     'WAITING', '2026-08-15'),
    (2, 2, 'CRITICAL', 'WAITING', '2026-09-28'),
    (3, 1, 'MEDIUM',   'WAITING', '2026-10-01');

INSERT INTO Transplants (donation_id, request_id, surgeon_name, transplant_date, outcome) VALUES
    (1, 1, 'Dr. R. Kulkarni', '2026-09-25', 'SUCCESSFUL');
