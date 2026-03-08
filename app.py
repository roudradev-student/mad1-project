from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///placements.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET KEY"] = "rdbsecretkey017"

db = SQLAlchemy(app)


# Models Formation


# User model

class Users(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(15))
    is_approved = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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


#Student Profile model

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

    user = db.relationship("Users", back_populates="student_profile")

    applications = db.relationship(
        "Application",
        back_populates="student"
    )

# Company Profile model


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

#Application model

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
    
    
# Routes


@app.route("/")
def index():
    return render_template("index.html")



# Registration and Login

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        contact_number = request.form["contact_number"]

        if role == "admin":
            return "Admin cannot be registered"

        if Users.query.filter_by(email=email).first():
            return "Email already registered"

        hashed_password = generate_password_hash(password)

        user = Users(
            name=name,
            email=email,
            password=hashed_password,
            role=role,
            is_approved=False if role == "company" else True,
            contact_number=contact_number
        )

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("regis.html")



# Route for login


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = Users.query.filter_by(email=email).first()

        if not user:
            return "No user found"

        if not check_password_hash(user.password, password):
            return "Wrong password"

        if user.role == "company" and not user.is_approved:
            return "Company not approved yet"

        session["user_id"] = user.id
        session["role"] = user.role

        if user.role == "admin":
            return redirect(url_for("admin_dashboard"))

        elif user.role == "company":
            return redirect(url_for("company_dashboard"))

        elif user.role == "employee":
            return redirect(url_for("employee_dashboard"))

    return render_template("login.html")

# Dashboards


@app.route("/company_dashboard")
def company_dashboard():
    return "This is company dashboard"


@app.route("/student_dashboard")
def student_dashboard():
    return "This is student dashboard"


@app.route("/admin_dashboard")
def admin_dashboard():
    return "This is admin dashboard"

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))



# Running the application


if __name__ == "__main__":

    with app.app_context():

        # recreate database (development only)
        db.drop_all()
        db.create_all()

        # creating admin user if not exists
        admin = Users.query.filter_by(email="admin@gmail.com").first()

        if not admin:

            admin_user = Users(
                name="admin",
                email="admin@gmail.com",
                password=generate_password_hash("admin"),
                role="admin",
                is_approved=True
            )

            db.session.add(admin_user)
            db.session.commit()

            print("Admin user created!")

    app.run(debug=True)