import os
from datetime import datetime, date, timedelta
from flask import Flask, session, redirect, send_from_directory
from flask.json.provider import DefaultJSONProvider

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

class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        return super().default(obj)

def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="")
    app.json = CustomJSONProvider(app)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "organ-donation-secret-key-default-production")
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)

    # Register error handlers
    register_error_handlers(app)

    # Register blueprints
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
        return send_from_directory(app.static_folder, "index.html")

    return app

app = create_app()

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "0").strip() == "1"
    port = int(os.getenv("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
