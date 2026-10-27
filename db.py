import os
import mysql.connector
from mysql.connector import pooling
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    _env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.isfile(_env_path):
        with open(_env_path, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    _v = _v.strip()
                    if (_v.startswith('"') and _v.endswith('"')) or (_v.startswith("'") and _v.endswith("'")):
                        _v = _v[1:-1]
                    os.environ.setdefault(_k.strip(), _v)

_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="organ_donation_pool",
            pool_size=5,
            pool_reset_session=True,
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "defaultdb")
        )
    return _pool

def get_connection():
    return get_pool().get_connection()

def query(sql, params=None):
    """
    Executes a SELECT query and returns a list of dictionaries.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(sql, params or ())
            rows = cursor.fetchall()
            return rows
        finally:
            cursor.close()
    finally:
        conn.close()

def query_one(sql, params=None):
    """
    Executes a SELECT query and returns the first row as a dictionary or None.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(sql, params or ())
            row = cursor.fetchone()
            return row
        finally:
            cursor.close()
    finally:
        conn.close()

def execute(sql, params=None):
    """
    Executes an INSERT, UPDATE, or DELETE query.
    Commits on success, rolls back on error, and always closes the connection.
    Returns a dict with 'lastrowid' and 'rowcount'.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params or ())
            conn.commit()
            return {
                "lastrowid": cursor.lastrowid,
                "rowcount": cursor.rowcount
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
    finally:
        conn.close()
