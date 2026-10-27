import sys
import logging
from flask import jsonify
import mysql.connector

logger = logging.getLogger(__name__)

class AppError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def map_mysql_error(err):
    errno = getattr(err, "errno", None)
    sqlstate = getattr(err, "sqlstate", None)
    msg = getattr(err, "msg", str(err))

    # Trigger SIGNAL emits SQLSTATE '45000'
    if sqlstate == "45000":
        return msg, 400

    if errno == 1062:
        return "A record with this value already exists (phone numbers and organ names must be unique).", 409
    elif errno == 3819:
        msg_lower = msg.lower()
        if "phone" in msg_lower:
            return "Phone number must be a valid 10-digit number.", 400
        if "age" in msg_lower:
            return "Age is outside the allowed range (18-100 for donors, 0-100 for recipients).", 400
        if "name" in msg_lower or "surgeon" in msg_lower:
            return "Name must be at least 2 characters.", 400
        return "A value is outside the allowed range (for example donor age must be 18 to 100).", 400
    elif errno == 1452:
        return "The selected donor, recipient, organ, donation or request does not exist.", 400
    elif errno == 1451:
        return "This record is in use by other records and cannot be deleted.", 409
    elif errno in (1048, 1265, 1366, 1292):
        return "Please check the form: a field is missing or has an invalid value.", 400
    else:
        logger.error(f"Database error [{errno}|{sqlstate}]: {msg}", exc_info=True)
        return "Something went wrong on the server.", 500

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"error": err.message}), err.status_code

    @app.errorhandler(mysql.connector.Error)
    def handle_database_error(err):
        message, status_code = map_mysql_error(err)
        return jsonify({"error": message}), status_code

    @app.errorhandler(400)
    def handle_bad_request(e):
        return jsonify({"error": getattr(e, "description", "Bad request.")}), 400

    @app.errorhandler(401)
    def handle_unauthorized(e):
        return jsonify({"error": getattr(e, "description", "Please sign in.")}), 401

    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({"error": getattr(e, "description", "Record not found.")}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(500)
    def handle_server_error(e):
        logger.error(f"Internal server error: {e}", exc_info=True)
        return jsonify({"error": "Something went wrong on the server."}), 500
