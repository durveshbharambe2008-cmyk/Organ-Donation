
import os
from datetime import datetime, date, timedelta

from flask import Flask, session, redirect, send_from_directory
from flask.json.provider import DefaultJSONProvider

from errors import register_error_handlers
from auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.donors import donors_bp
from routes.recipients import recipients_bp
from routes.organs import organs_bp
from routes.donations import donations_bp
from routes.requests import requests_bp
from routes.matches import matches_bp
from routes.transplants import transplants_bp


# Load local .env variables when python-dotenv is installed.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")

        if isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")

        return super().default(obj)


def create_app():
    app = Flask(
        __name__,
        static_folder="static",
        static_url_path=""
    )

    app.json = CustomJSONProvider(app)

    # Configure the session signing key.
    secret_key = os.getenv("SECRET_KEY")

    if not secret_key:
        if os.getenv("VERCEL") == "1":
            raise RuntimeError(
                "SECRET_KEY must be configured in Vercel environment variables."
            )

        # Development-only fallback. Set SECRET_KEY in production.
        secret_key = "local-development-only-change-this-secret"

    app.config["SECRET_KEY"] = secret_key

    # Session configuration.
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = (
        os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
        or os.getenv("VERCEL") == "1"
    )
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)

    # Register error handlers.
    register_error_handlers(app)

    # Register existing application blueprints.
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(donors_bp)
    app.register_blueprint(recipients_bp)
    app.register_blueprint(organs_bp)
    app.register_blueprint(donations_bp)
    app.register_blueprint(requests_bp)
    app.register_blueprint(matches_bp)
    app.register_blueprint(transplants_bp)

    @app.route("/")
    def index():
        if not session.get("user"):
            return redirect("/login.html")

        return send_from_directory(
            app.static_folder,
            "index.html"
        )

    return app


app = create_app()


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    port = int(os.getenv("PORT", "3000"))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug_mode
    )
