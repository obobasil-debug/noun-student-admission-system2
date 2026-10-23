import re
import secrets
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Application, User

auth_bp = Blueprint("auth", __name__)
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _home_for_user(user: User):
    if user.role == "admin":
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("applicant.dashboard"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return _home_for_user(current_user)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(full_name) < 2 or len(full_name) > 120:
            flash("Enter your full name (2 to 120 characters).", "error")
        elif len(email) > 254 or not EMAIL_PATTERN.fullmatch(email):
            flash("Enter a valid email address.", "error")
        elif len(password) < 10:
            flash("Use a password with at least 10 characters.", "error")
        elif password != confirm_password:
            flash("The passwords do not match.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account already exists for that email address.", "error")
        else:
            user = User(full_name=full_name, email=email, role="applicant")
            user.set_password(password)
            application = Application(
                applicant=user,
                reference=f"NOUN-{date.today().year}-{secrets.token_hex(4).upper()}",
            )
            db.session.add_all([user, application])
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("That email address is already registered. Please sign in.", "error")
            else:
                login_user(user)
                flash("Your applicant account is ready. Start with your personal information.", "success")
                return redirect(url_for("applicant.dashboard"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _home_for_user(current_user)

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.role == "applicant" and user.check_password(password):
            login_user(user)
            return redirect(url_for("applicant.dashboard"))
        flash("Email or password is incorrect.", "error")

    return render_template("auth/login.html")


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if current_user.is_authenticated:
        return _home_for_user(current_user)

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email, role="admin").first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("admin.dashboard"))
        flash("Administrator email or password is incorrect.", "error")

    return render_template("auth/admin_login.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("home"))
