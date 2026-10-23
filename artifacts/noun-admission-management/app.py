import os
import secrets
from getpass import getpass
from pathlib import Path

from flask import Flask, redirect, render_template, url_for
from flask_login import current_user

from extensions import csrf, db, login_manager
from models import User


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    instance_path = Path(app.instance_path)
    instance_path.mkdir(parents=True, exist_ok=True)
    database_path = Path(os.environ.get("ADMISSIONS_DB_PATH", instance_path / "admissions.sqlite3"))
    database_path.parent.mkdir(parents=True, exist_ok=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SESSION_SECRET") or secrets.token_hex(32),
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{database_path.resolve().as_posix()}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_HTTPONLY=True,
        WTF_CSRF_TIME_LIMIT=3600,
    )
    if test_config:
        app.config.update(test_config)
    elif not os.environ.get("SESSION_SECRET"):
        app.logger.warning(
            "SESSION_SECRET is unset; a temporary random session key is being used. "
            "Set SESSION_SECRET for sessions that must survive restarts."
        )

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Sign in to access your account."
    login_manager.login_message_category = "info"

    from routes.admin import admin_bp
    from routes.applicant import applicant_bp
    from routes.auth import auth_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(applicant_bp)
    app.register_blueprint(admin_bp)

    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    @app.route("/")
    def home():
        if current_user.is_authenticated:
            if current_user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("applicant.dashboard"))
        return render_template("home.html")

    @app.route("/favicon.ico")
    def favicon():
        return redirect(url_for("static", filename="favicon.svg"))

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.cli.command("create-admin")
    def create_admin():
        """Create an administrator account using an interactive password prompt."""
        email = input("Administrator email: ").strip().lower()
        full_name = input("Administrator name: ").strip()
        if not email or "@" not in email or len(email) > 254:
            raise SystemExit("Enter a valid email address.")
        if not full_name or len(full_name) > 120:
            raise SystemExit("Enter a name between 1 and 120 characters.")
        if User.query.filter_by(email=email).first():
            raise SystemExit("An account already uses that email address.")

        password = getpass("Administrator password (at least 10 characters): ")
        confirmation = getpass("Confirm password: ")
        if len(password) < 10:
            raise SystemExit("The password must contain at least 10 characters.")
        if password != confirmation:
            raise SystemExit("The passwords do not match.")

        user = User(full_name=full_name, email=email, role="admin")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"Administrator account created for {email}.")

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
