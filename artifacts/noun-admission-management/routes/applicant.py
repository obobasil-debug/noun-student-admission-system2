from datetime import date, datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from decorators import role_required
from extensions import db
from models import Application

applicant_bp = Blueprint("applicant", __name__)

PROGRAMMES = [
    "B.Sc. Information Technology",
    "B.Sc. Computer Science",
    "B.Sc. Information Systems",
]
QUALIFICATIONS = [
    "Senior Secondary School Certificate",
    "National Diploma",
    "Higher National Diploma",
    "Bachelor's Degree",
    "Other",
]
STUDY_CENTRES = [
    "Abuja Study Centre",
    "Enugu Study Centre",
    "Ibadan Study Centre",
    "Kano Study Centre",
    "Lagos Study Centre",
    "Port Harcourt Study Centre",
]
SUBMITTED_STATUSES = {"Pending", "Under Review", "Approved", "Rejected"}


def _application() -> Application:
    application = current_user.application
    if application is None:
        abort(404)
    return application


def _editable(application: Application) -> bool:
    if application.status != "Draft":
        flash("Submitted applications are read-only in this demonstration.", "info")
        return False
    return True


def _completion(application: Application) -> tuple[int, int]:
    checks = [
        bool(
            application.date_of_birth
            and application.gender
            and application.phone
            and application.state_of_origin
            and application.address
        ),
        bool(application.highest_qualification and application.prior_institution and application.examination_body),
        bool(application.programme and application.study_centre),
    ]
    completed = sum(checks)
    return round(completed / len(checks) * 100), completed


def _first_incomplete(application: Application) -> str | None:
    if not (
        application.date_of_birth
        and application.gender
        and application.phone
        and application.state_of_origin
        and application.address
    ):
        return "applicant.personal"
    if not (
        application.highest_qualification
        and application.prior_institution
        and application.examination_body
    ):
        return "applicant.academic"
    if not application.programme or not application.study_centre:
        return "applicant.programme"
    return None


@applicant_bp.route("/dashboard")
@role_required("applicant")
def dashboard():
    application = _application()
    completion_percent, _ = _completion(application)
    return render_template(
        "applicant/dashboard.html",
        application=application,
        completion_percent=completion_percent,
        status=application.status,
    )


@applicant_bp.route("/application/personal", methods=["GET", "POST"])
@role_required("applicant")
def personal():
    application = _application()
    if request.method == "POST":
        if not _editable(application):
            return redirect(url_for("applicant.details"))
        full_fields = {
            "phone": ("Phone number", 32),
            "state_of_origin": ("State of origin", 80),
            "address": ("Residential address", 500),
        }
        values = {key: request.form.get(key, "").strip() for key in full_fields}
        gender = request.form.get("gender", "").strip()
        date_value = request.form.get("date_of_birth", "").strip()
        error = None
        for key, (label, max_length) in full_fields.items():
            if not values[key] or len(values[key]) > max_length:
                error = f"{label} is required and must be no longer than {max_length} characters."
                break
        if not error and gender not in {
            "Female",
            "Male",
            "Another identity",
            "Prefer not to say",
        }:
            error = "Select one of the listed gender options."
        parsed_date = None
        if not error:
            try:
                parsed_date = date.fromisoformat(date_value)
                if parsed_date >= date.today():
                    error = "Date of birth must be in the past."
            except ValueError:
                error = "Enter a valid date of birth."
        if not error:
            digits = "".join(character for character in values["phone"] if character.isdigit())
            if not 7 <= len(digits) <= 15:
                error = "Enter a phone number containing 7 to 15 digits."
        if error:
            flash(error, "error")
        else:
            application.date_of_birth = parsed_date
            application.gender = gender
            application.phone = values["phone"]
            application.state_of_origin = values["state_of_origin"]
            application.address = values["address"]
            db.session.commit()
            flash("Personal information saved.", "success")
            return redirect(url_for("applicant.academic"))

    return render_template("applicant/personal.html", application=application)


@applicant_bp.route("/application/academic", methods=["GET", "POST"])
@role_required("applicant")
def academic():
    application = _application()
    if request.method == "POST":
        if not _editable(application):
            return redirect(url_for("applicant.details"))
        fields = {
            "highest_qualification": ("Highest qualification", 120),
            "prior_institution": ("Institution", 160),
            "examination_body": ("Examination body", 120),
        }
        values = {key: request.form.get(key, "").strip() for key in fields}
        error = None
        for key, (label, max_length) in fields.items():
            if not values[key] or len(values[key]) > max_length:
                error = f"{label} is required and must be no longer than {max_length} characters."
                break
        if not error and values["highest_qualification"] not in QUALIFICATIONS:
            error = "Select a qualification from the available options."
        year_value = request.form.get("graduation_year", "").strip()
        graduation_year = None
        if not error and year_value:
            try:
                graduation_year = int(year_value)
                if graduation_year < 1950 or graduation_year > date.today().year:
                    error = "Enter a valid graduation year."
            except ValueError:
                error = "Graduation year must be a whole number."
        grade = request.form.get("grade", "").strip()
        if not error and len(grade) > 80:
            error = "Grade must be no longer than 80 characters."
        if error:
            flash(error, "error")
        else:
            application.highest_qualification = values["highest_qualification"]
            application.prior_institution = values["prior_institution"]
            application.examination_body = values["examination_body"]
            application.graduation_year = graduation_year
            application.grade = grade
            db.session.commit()
            flash("Academic qualification saved.", "success")
            return redirect(url_for("applicant.programme"))

    return render_template(
        "applicant/academic.html",
        application=application,
        qualifications=QUALIFICATIONS,
    )


@applicant_bp.route("/application/programme", methods=["GET", "POST"])
@role_required("applicant")
def programme():
    application = _application()
    if request.method == "POST":
        if not _editable(application):
            return redirect(url_for("applicant.details"))
        selected_programme = request.form.get("programme", "")
        selected_centre = request.form.get("study_centre", "")
        if selected_programme not in PROGRAMMES or selected_centre not in STUDY_CENTRES:
            flash("Choose a programme and study centre from the available demonstration options.", "error")
        else:
            application.programme = selected_programme
            application.study_centre = selected_centre
            db.session.commit()
            flash("Programme and study centre saved.", "success")
            return redirect(url_for("applicant.review"))

    return render_template(
        "applicant/programme.html",
        application=application,
        programmes=PROGRAMMES,
        study_centres=STUDY_CENTRES,
    )


@applicant_bp.route("/application/review")
@role_required("applicant")
def review():
    return render_template("applicant/review.html", application=_application())


@applicant_bp.route("/application/submit", methods=["POST"])
@role_required("applicant")
def submit_application():
    application = _application()
    if application.status != "Draft":
        flash("This application has already been submitted.", "info")
        return redirect(url_for("applicant.status"))
    if request.form.get("confirm_review") != "yes":
        flash("Confirm that you reviewed the demonstration record before submitting.", "error")
        return redirect(url_for("applicant.review"))
    incomplete = _first_incomplete(application)
    if incomplete:
        flash("Complete all application sections before submitting.", "error")
        return redirect(url_for(incomplete))
    application.status = "Pending"
    application.submitted_at = datetime.now().astimezone()
    db.session.commit()
    flash("Your application has been submitted for review.", "success")
    return redirect(url_for("applicant.status"))


@applicant_bp.route("/application/status")
@role_required("applicant")
def status():
    return render_template("applicant/status.html", application=_application())


@applicant_bp.route("/application/details")
@role_required("applicant")
def details():
    return render_template("applicant/details.html", application=_application())
