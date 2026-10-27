# Organ Donation Management System

A relational database system for a hospital to record organ donors, recipients (patients) and donations, match available organs with waiting patients by blood group compatibility, and track surgical transplant outcomes.

---

## 1. Project Overview

- **Database:** MySQL 8.0.16+ (6 normalized BCNF tables, 6 foreign keys with `ON DELETE RESTRICT`, CHECK constraints, and triggers).
- **Backend:** Python 3.10+ with Flask and `mysql-connector-python`.
- **Frontend:** Responsive, clean hospital admin interface built with pure semantic HTML, modern CSS, and vanilla JavaScript (no build step, no external CDNs).
- **Security & Integrity:** Trigger-enforced matching validation and status changes, parameterised SQL queries, hashed credentials via Werkzeug, secure HTTP-only session cookies.

---

## 2. Database Design

### Entities & Relational Schema (BCNF)
- **Donors** (`donor_id` [PK], `name`, `age`, `gender`, `blood_group`, `phone` [UK], `registered_on`) — *CHECK: age &ge; 18*
- **Recipients** (`recipient_id` [PK], `name`, `age`, `gender`, `blood_group`, `phone` [UK], `registered_on`) — *CHECK: age BETWEEN 0 AND 100*
- **Organs** (`organ_id` [PK], `organ_name` [UK])
- **Donations** (`donation_id` [PK], `donor_id`* [FK], `organ_id`* [FK], `donation_type`, `status`, `donation_date`)
- **Requests** (`request_id` [PK], `recipient_id`* [FK], `organ_id`* [FK], `urgency`, `status`, `request_date`)
- **Transplants** (`transplant_id` [PK], `donation_id`* [FK, UK], `request_id`* [FK, UK], `surgeon_name`, `transplant_date`, `outcome`)

*All foreign keys enforce `ON DELETE RESTRICT ON UPDATE RESTRICT`.*

### Database Triggers
1. **`trg_transplant_before_insert`**:
   - Ensures donated organ and requested organ are identical.
   - Ensures donor and recipient have matching blood groups.
   - Verifies donation status is `AVAILABLE` and request status is `WAITING`.
   - Signals custom SQLSTATE '45000' with descriptive message if validation fails.
2. **`trg_transplant_after_insert`**:
   - Automatically updates `Donations.status` to `ALLOCATED`.
   - Automatically updates `Requests.status` to `MATCHED`.

---

## 3. Setup and Run Instructions

### Prerequisites
- MySQL Server 8.0.16 or later (running on port 3306)
- Python 3.10 or later

### Step 1: Initialize Database
Open MySQL Workbench (or MySQL Command Line) and run:
```sql
SOURCE db/schema.sql;
SOURCE db/seed.sql;
```
*(Or execute `db/schema.sql` followed by `db/seed.sql` in MySQL Workbench).*

### Step 2: Create Virtual Environment & Install Dependencies
In the project root folder:
```powershell
# Windows
python -m venv venv
venv\Scripts\activate

# Install required packages (Flask, mysql-connector-python)
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Generate an administrator password hash:
```powershell
python tools/hash_password.py
```
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
Open `.env` and fill in:
- `DB_USER` and `DB_PASSWORD` (your MySQL credentials)
- `ADMIN_USERNAME` (default: `admin`)
- `ADMIN_PASSWORD_HASH` (paste the hash generated in Step 3)
- `SECRET_KEY` (a random secure secret string)

### Step 4: Run Application
```powershell
python app.py
```
Open your browser and navigate to:
```
http://localhost:3000
```
Sign in with your configured admin credentials.

---

## 4. Suggested Viva / Lab Demo Flow

1. **Sign-In Page**:
   - Enter invalid credentials &rarr; Verify generic error message *"Invalid username or password."*
   - Sign in with valid admin credentials &rarr; Lands on the Dashboard.
2. **Dashboard Overview**:
   - Verify summary metric cards (Donors: 3, Recipients: 3, Available Donations: 2, Waiting Requests: 2, Completed Transplants: 1).
   - View *Available Organs by Type* and *Recent Transplants*.
3. **Donors & Integrity Checks**:
   - Click **+ Register Donor**: Enter age 17 &rarr; Verify database `CHECK` constraint rejection.
   - Enter duplicate phone number &rarr; Verify `409 Conflict` unique constraint rejection.
   - Try to delete donor `Anita Desai` (has an associated donation) &rarr; Verify `ON DELETE RESTRICT` rejection (*"This record is in use by other records and cannot be deleted."*).
   - Register a dummy donor with no donations and delete them &rarr; Deletion succeeds.
4. **Requests & Priority Waiting List**:
   - Notice waiting list is prioritized automatically by urgency (`CRITICAL` &rarr; `HIGH` &rarr; `MEDIUM` &rarr; `LOW`) and request date.
   - Matched requests show immutable `Matched` badge with no edit/delete action.
5. **Matching & Transplants**:
   - Navigate to **Matching & Transplants**: Shows compatible pairs where organ type and blood group match exactly.
   - Click **Record Transplant** on a match &rarr; Fill surgeon name and date &rarr; Save.
   - Demonstrate that MySQL triggers automatically allocate the donation, match the request, remove the pair from the matches table, and append the record into Completed Transplants.
6. **Editing Transplants & Permanent Medical Records**:
   - Edit the transplant outcome to `COMPLICATIONS` &rarr; Proves medical records are updated/annotated and never deleted.

