
import logging

from flask import jsonify
import mysql.connector


logger = logging.getLogger(__name__)


class AppError(Exception):
    """Application error with a safe message and HTTP status code."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def map_mysql_error(err):
    """Convert MySQL errors into safe, user-friendly API responses."""

    errno = getattr(err, "errno", None)
    sqlstate = getattr(err, "sqlstate", None)
    msg = getattr(err, "msg", str(err))
    msg_lower = msg.lower()

    # Custom SQL SIGNAL errors.
    if sqlstate == "45000":
        return msg, 400

    # Duplicate unique values.
    if errno == 1062:
        return (
            "A record with this value already exists. "
            "Check unique fields such as phone numbers or organ names.",
            409,
        )

    # CHECK constraint violations.
    if errno == 3819:
        if "phone" in msg_lower:
            return "Phone number must be a valid 10-digit number.", 400

        if "age" in msg_lower:
            return (
                "Age is outside the allowed range for this record.",
                400,
            )

        if "name" in msg_lower or "surgeon" in msg_lower:
            return "Name must be at least 2 characters.", 400

        return "One or more values violate a database constraint.", 400

    # Foreign key violations.
    if errno == 1452:
        return (
            "A selected related record does not exist. "
            "Check the selected donor, recipient, organ, or request.",
            400,
        )

    if errno == 1451:
        return (
            "This record is referenced by other records and cannot be deleted.",
            409,
        )

    # Missing or invalid values.
    if errno in (1048, 1265, 1366, 1292):
        return (
            "Please check the form. A required field may be missing "
            "or a value may be invalid.",
            400,
        )

    # Connection errors and other unexpected database errors.
    logger.error(
        "MySQL error: errno=%s, sqlstate=%s, message=%s",
        errno,
        sqlstate,
        msg,
        exc_info=True,
    )

    return "A database error occurred. Please try again later.", 500


def register_error_handlers(app):
    """Register centralized Flask error handlers."""

    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"error": err.message}), err.status_code

    @app.errorhandler(mysql.connector.Error)
    def handle_database_error(err):
        message, status_code = map_mysql_error(err)
        return jsonify({"error": message}), status_code

    @app.errorhandler(400)
    def handle_bad_request(err):
        return jsonify({
            "error": getattr(err, "description", None) or "Bad request."
        }), 400

    @app.errorhandler(401)
    def handle_unauthorized(err):
        return jsonify({
            "error": getattr(err, "description", None) or "Please sign in."
        }), 401

    @app.errorhandler(403)
    def handle_forbidden(err):
        return jsonify({"error": "You do not have permission to perform this action."}), 403

    @app.errorhandler(404)
    def handle_not_found(err):
        return jsonify({
            "error": getattr(err, "description", None) or "Resource not found."
        }), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(err):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(500)
    def handle_server_error(err):
        # Log the underlying exception on the server, not in the API response.
        logger.error(
            "Internal server error: %s",
            err,
            exc_info=(type(err), err, err.__traceback__),
        )

        return jsonify({
            "error": "Something went wrong on the server."
        }), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        # Do not expose stack traces, SQL statements, or credentials to clients.
        logger.error(
            "Unhandled application exception: %s",
            err,
            exc_info=(type(err), err, err.__traceback__),
        )

        return jsonify({
            "error": "Something went wrong on the server."
        }), 500
