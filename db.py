
import os
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

load_dotenv()

_pool = None

def get_pool():
    global _pool

    if _pool is None:
        ca_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "certs",
            "ca.pem"
        )

        if not os.path.isfile(ca_path):
            raise FileNotFoundError(
                f"MySQL CA certificate not found: {ca_path}"
            )

        _pool = pooling.MySQLConnectionPool(
            pool_name="organ_donation_pool",
            pool_size=5,
            pool_reset_session=True,
            host=os.environ["DB_HOST"],
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_NAME"],
            ssl_ca=ca_path,
            ssl_verify_cert=True,
            ssl_verify_identity=True,
        )

    return _pool


def get_connection():
    return get_pool().get_connection()


def query(sql, params=None):
    """Execute a SELECT query and return rows as dictionaries."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(sql, params or ())
            return cursor.fetchall()
        finally:
            cursor.close()
    finally:
        conn.close()


def query_one(sql, params=None):
    """Execute a SELECT query and return one row or None."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(sql, params or ())
            return cursor.fetchone()
        finally:
            cursor.close()
    finally:
        conn.close()


def execute(sql, params=None):
    """Execute an INSERT, UPDATE, or DELETE query."""
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
