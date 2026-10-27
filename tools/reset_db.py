"""
Resets and seeds the organ_donation database using schema.sql and seed.sql.
"""
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

def run_sql_file(cursor, file_path):
    print(f"Executing: {os.path.basename(file_path)}...")
    with open(file_path, "r", encoding="utf-8") as f:
        sql = f.read()

    # Split on DELIMITER $$ if present, otherwise split statements
    # Simple multi-statement execution
    statements = []
    # Remove delimiter lines
    clean_lines = []
    custom_delimiter = ";"
    
    for line in sql.splitlines():
        trimmed = line.strip()
        if trimmed.upper().startswith("DELIMITER"):
            parts = trimmed.split()
            if len(parts) > 1:
                custom_delimiter = parts[1]
            continue
        clean_lines.append(line)
        if trimmed.endswith(custom_delimiter):
            stmt = "\n".join(clean_lines)
            # strip delimiter
            stmt = stmt[:stmt.rfind(custom_delimiter)].strip()
            if stmt:
                statements.append(stmt)
            clean_lines = []
            
    if clean_lines:
        stmt = "\n".join(clean_lines).strip()
        if stmt:
            statements.append(stmt)

    for stmt in statements:
        if stmt.strip():
            cursor.execute(stmt)

def main():
    print("=" * 60)
    print("Resetting and seeding database: organ_donation")
    print("=" * 60)
    
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        # Connect without specifying database in case it's dropped/recreated
        autocommit=True
    )
    cursor = conn.cursor()
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    schema_path = os.path.join(project_root, "db", "schema.sql")
    seed_path = os.path.join(project_root, "db", "seed.sql")
    
    try:
        run_sql_file(cursor, schema_path)
        run_sql_file(cursor, seed_path)
        print("\n[SUCCESS] Database successfully reset and seeded to initial state!")
    except Exception as e:
        print(f"\n[ERROR] Failed to init DB: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
