from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///placements.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# MODELS



class Users(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(15))
    is_approved = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships

    student_profile = db.relationship(
        "StudentProfile",
        back_populates="user",
        uselist=False
    )

    company_profile = db.relationship(
        "CompanyProfile",
        back_populates="user",
        uselist=False
    )


# StudentProfile model
class StudentProfile(db.Model):
    __tablename__ = "student_profiles"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    cgpa = db.Column(db.Float)
    department = db.Column(db.String(100))
    current_year = db.Column(db.Integer)
    skills = db.Column(db.String(200))
    resume = db.Column(db.String(200))
    placement_status = db.Column(db.String(50), default="Not Placed")

    # relation to User
    user = db.relationship("Users", back_populates="student_profile")

    applications = db.relationship(
        "Application",
        back_populates="student"
    )


# CompanyProfile model
class CompanyProfile(db.Model):
    __tablename__ = "company_profiles"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    company_name = db.Column(db.String(150))
    industry = db.Column(db.String(200))
    website = db.Column(db.String(200))
    location = db.Column(db.String(200))
    hr_contact = db.Column(db.String(15))

    user = db.relationship("Users", back_populates="company_profile")

    jobs = db.relationship(
        "Job",
        back_populates="company"
    )


# Job model
class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("company_profiles.id")
    )

    description = db.Column(db.Text)
    title = db.Column(db.String(150))
    skills = db.Column(db.String(200))
    salary = db.Column(db.String(50))
    job_type = db.Column(db.String(50), default="Full-time")
    is_approved = db.Column(db.Boolean, default=False)
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)

    company = db.relationship("CompanyProfile", back_populates="jobs")

    applications = db.relationship(
        "Application",
        back_populates="job"
    )


# Application model
class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student_profiles.id")
    )

    job_id = db.Column(
        db.Integer,
        db.ForeignKey("jobs.id")
    )

    status = db.Column(db.String(50), default="Applied")
    remarks = db.Column(db.String(200))
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime)

    job = db.relationship("Job", back_populates="applications")

    student = db.relationship("StudentProfile", back_populates="applications")
# App running

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

        user = Users.query.filter_by(name='admin')
        if not user:
            admin_user = Users(
                name="admin",
                email="admin@gmail.com",
                password=generate_password_hash("admin"),
                role="admin",
                is_approved=True
            )
            db.session.add(admin_user)
            db.session.commit()

    app.run(debug=True)