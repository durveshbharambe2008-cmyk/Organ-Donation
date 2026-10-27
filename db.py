
import os
import logging
from pathlib import Path

import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_pool = None


def get_pool():
    """Create and reuse a MySQL connection pool."""
    global _pool

    if _pool is not None:
        return _pool

    required = ("DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME")
    missing = [name for name in required if not os.getenv(name)]

    if missing:
        raise RuntimeError(
            "Missing required database environment variables: "
            + ", ".join(missing)
        )

    try:
        port = int(os.getenv("DB_PORT", "3306"))
    except ValueError as exc:
        raise RuntimeError("DB_PORT must be a valid integer.") from exc

    # Prefer an explicit certificate path when provided.
    default_ca = Path(__file__).resolve().parent / "certs" / "ca.pem"
    ca_value = os.getenv("DB_SSL_CA")
    ca_path = Path(ca_value) if ca_value else default_ca

    if not ca_path.is_file():
        raise RuntimeError(
            "MySQL CA certificate not found. Set DB_SSL_CA to the "
            "correct certificate path or include certs/ca.pem."
        )

    config = {
        "pool_name": "organ_donation_pool",
        "pool_size": 5,
        "pool_reset_session": True,
        "host": os.environ["DB_HOST"],
        "port": port,
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
        "database": os.environ["DB_NAME"],
        "ssl_ca": str(ca_path),
        "ssl_verify_cert": True,
        "ssl_verify_identity": True,
        "connection_timeout": 10,
    }

    try:
        _pool = pooling.MySQLConnectionPool(**config)
        logger.info("MySQL connection pool initialized successfully.")
        return _pool
    except mysql.connector.Error:
        logger.exception(
            "Could not initialize MySQL connection pool. "
            "Check database credentials, user permissions, hostname, "
            "and TLS configuration."
        )
        raise


def get_connection():
    """Get a connection from the pool."""
    try:
        return get_pool().get_connection()
    except mysql.connector.Error:
        logger.exception("Could not obtain a MySQL connection.")
        raise


def query(sql, params=None):
    """Execute SELECT and return all rows as dictionaries."""
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
    """Execute SELECT and return one row or None."""
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
    """Execute INSERT, UPDATE, or DELETE in a transaction."""
    conn = get_connection()

    try:
        cursor = conn.cursor()

        try:
            cursor.execute(sql, params or ())
            conn.commit()

            return {
                "lastrowid": cursor.lastrowid,
                "rowcount": cursor.rowcount,
            }

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()

    finally:
        conn.close()
