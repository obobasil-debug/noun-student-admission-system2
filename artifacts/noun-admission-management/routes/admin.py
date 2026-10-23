import csv
import io
from datetime import date

from flask import Blueprint, abort, flash, make_response, redirect, render_template, request, url_for
from sqlalchemy import or_

from decorators import role_required
from extensions import db
from models import Application, User

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
APPLICATION_STATUSES = ["Pending", "Under Review", "Approved", "Rejected"]


def _spreadsheet_safe(value: str) -> str:
    if value and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


@admin_bp.route("/")
@role_required("admin")
def dashboard():
    stats = {
        "total": Application.query.filter(Application.status != "Draft").count(),
        "pending": Application.query.filter_by(status="Pending").count(),
        "under_review": Application.query.filter_by(status="Under Review").count(),
        "approved": Application.query.filter_by(status="Approved").count(),
        "rejected": Application.query.filter_by(status="Rejected").count(),
    }
    recent_applications = (
        Application.query.filter(Application.status != "Draft")
        .order_by(Application.submitted_at.desc(), Application.id.desc())
        .limit(8)
        .all()
    )
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_applications=recent_applications,
        statuses=APPLICATION_STATUSES,
    )


@admin_bp.route("/applications")
@role_required("admin")
def applications():
    query = request.args.get("q", "").strip()[:160]
    selected_status = request.args.get("status", "").strip()
    records = Application.query.join(User, Application.applicant_id == User.id)
    records = records.filter(Application.status != "Draft")
    if selected_status in APPLICATION_STATUSES:
        records = records.filter(Application.status == selected_status)
    if query:
        pattern = f"%{query}%"
        records = records.filter(
            or_(
                Application.reference.ilike(pattern),
                User.full_name.ilike(pattern),
                User.email.ilike(pattern),
                Application.programme.ilike(pattern),
            )
        )
    records = records.order_by(Application.submitted_at.desc(), Application.id.desc()).all()
    return render_template(
        "admin/applications.html",
        applications=records,
        q=query,
        selected_status=selected_status if selected_status in APPLICATION_STATUSES else "",
        statuses=APPLICATION_STATUSES,
    )


@admin_bp.route("/applications/export.csv")
@role_required("admin")
def export_applications():
    records = (
        Application.query.join(User, Application.applicant_id == User.id)
        .filter(Application.status != "Draft")
        .order_by(Application.submitted_at.desc(), Application.id.desc())
        .all()
    )
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Reference",
            "Applicant",
            "Email",
            "Phone",
            "Programme",
            "Study centre",
            "Status",
            "Qualification verified",
            "Submitted at",
        ]
    )
    for application in records:
        writer.writerow(
            [
                application.reference,
                _spreadsheet_safe(application.applicant.full_name),
                _spreadsheet_safe(application.applicant.email),
                _spreadsheet_safe(application.phone or ""),
                _spreadsheet_safe(application.programme or ""),
                _spreadsheet_safe(application.study_centre or ""),
                _spreadsheet_safe(application.status),
                "Yes" if application.qualification_verified else "No",
                application.submitted_at.isoformat() if application.submitted_at else "",
            ]
        )
    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = 'attachment; filename="noun-applications.csv"'
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@admin_bp.route("/applications/<int:application_id>", methods=["GET", "POST"])
@role_required("admin")
def application_detail(application_id: int):
    application = db.session.get(Application, application_id)
    if application is None or application.status == "Draft":
        abort(404)

    if request.method == "POST":
        status = request.form.get("status", "")
        if status not in APPLICATION_STATUSES:
            flash("Choose a valid application status.", "error")
        else:
            verification_notes = request.form.get("verification_notes", "").strip()
            review_notes = request.form.get("review_notes", "").strip()
            if len(verification_notes) > 4000 or len(review_notes) > 4000:
                flash("Review notes must be no longer than 4,000 characters.", "error")
            else:
                application.status = status
                application.qualification_verified = request.form.get("qualification_verified") in {
                    "on",
                    "yes",
                    "true",
                    "1",
                }
                application.verification_notes = verification_notes
                application.review_notes = review_notes
                db.session.commit()
                flash("Application review was saved.", "success")
                return redirect(url_for("admin.application_detail", application_id=application.id))

    return render_template(
        "admin/application_detail.html",
        application=application,
        statuses=APPLICATION_STATUSES,
    )
