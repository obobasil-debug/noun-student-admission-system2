from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(254), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="applicant", index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    application = db.relationship(
        "Application",
        back_populates="applicant",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(32), nullable=False, unique=True, index=True)
    applicant_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    status = db.Column(db.String(24), nullable=False, default="Draft", index=True)

    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(40), nullable=True)
    phone = db.Column(db.String(32), nullable=True)
    state_of_origin = db.Column(db.String(80), nullable=True)
    address = db.Column(db.String(500), nullable=True)

    highest_qualification = db.Column(db.String(120), nullable=True)
    prior_institution = db.Column(db.String(160), nullable=True)
    examination_body = db.Column(db.String(120), nullable=True)
    graduation_year = db.Column(db.Integer, nullable=True)
    grade = db.Column(db.String(80), nullable=True)

    programme = db.Column(db.String(160), nullable=True)
    study_centre = db.Column(db.String(120), nullable=True)

    qualification_verified = db.Column(db.Boolean, nullable=False, default=False)
    verification_notes = db.Column(db.Text, nullable=False, default="")
    review_notes = db.Column(db.Text, nullable=False, default="")
    submitted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    applicant = db.relationship("User", back_populates="application")
