from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///placements.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "rdbsecretkey017"

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
        nullable=False,
        unique= True
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
        nullable=False,
        unique= True    
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
    experience = db.Column(db.String(200))
    salary = db.Column(db.String(50))
    job_type = db.Column(db.String(50), default="Full-time")
    is_approved = db.Column(db.Boolean, default=False)
    is_closed = db.Column(db.Boolean, default=False)
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


# Route for job posting by company
@app.route('/job-posting', methods=['GET', 'POST'])
def job_post():

    if request.method == 'POST':

        if 'user_id' not in session:
            return redirect('/login')

        company = CompanyProfile.query.filter_by(user_id=session['user_id']).first()

        if not company:
            return "Please complete company profile first"

        job = Job(
            company_id=company.id,
            title=request.form['title'],
            experience=request.form['experience'],
            description=request.form['description'],
            skills=request.form['skills'],
            salary=request.form['salary']
        )

        db.session.add(job)
        db.session.commit()

        return redirect('/company_dashboard')

    return render_template('job_posting.html')


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
            return redirect(url_for("student_dashboard"))

    return render_template("login.html")

# Dashboards

@app.route("/company-details/<int:company_id>")
def company_details(company_id):

    # get company profile
    company = CompanyProfile.query.filter_by(id=company_id).first()

    if not company:
        return "Company not found", 404

    return render_template(
        "company_details.html",
        company=company
    )

@app.route("/company_dashboard")
def company_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    company = CompanyProfile.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not company:
        return redirect("/complete-company-profile")

    jobs = Job.query.filter_by(company_id=company.id).all()

    job_data = []

    all_shortlisted = []
    all_selected = []

    for job in jobs:

        total_apps = Application.query.filter_by(job_id=job.id).count()

        shortlisted = Application.query.filter_by(
            job_id=job.id,
            status="Shortlisted"
        ).all()

        selected = Application.query.filter_by(
            job_id=job.id,
            status="Selected"
        ).all()

        all_shortlisted.extend(shortlisted)
        all_selected.extend(selected)

        job_data.append({
            "job": job,
            "total_apps": total_apps
        })

    return render_template(
        "company_dashboard.html",
        company=company,
        jobs=job_data,
        shortlisted=all_shortlisted,
        selected=all_selected
    )

@app.route("/delete-job/<int:job_id>", methods=["POST"])
def delete_job(job_id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "company":
        return "Unauthorized", 403

    user_id = session["user_id"]

    company = CompanyProfile.query.filter_by(user_id=user_id).first()
    if not company:
        return "Company profile not found", 404

    job = Job.query.filter_by(id=job_id, company_id=company.id).first()
    if not job:
        return "Job not found", 404

    # 🔥 Check if applications exist
    application_count = Application.query.filter_by(job_id=job.id).count()

    if application_count > 0:
        return render_template(
            "delete_warning.html",
            job=job,
            application_count=application_count
        )

    # If no applications → delete directly
    db.session.delete(job)
    db.session.commit()

    return redirect("/company_dashboard")



@app.route("/confirm-delete/<int:job_id>", methods=["POST"])
def confirm_delete(job_id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "company":
        return "Unauthorized", 403

    user_id = session["user_id"]

    company = CompanyProfile.query.filter_by(user_id=user_id).first()
    if not company:
        return "Company not found", 404

    job = Job.query.filter_by(id=job_id, company_id=company.id).first()
    if not job:
        return "Job not found", 404

    # delete related applications first
    Application.query.filter_by(job_id=job.id).delete()

    db.session.delete(job)
    db.session.commit()

    return redirect("/company_dashboard")


@app.route("/complete-company-profile", methods=["GET", "POST"])
def complete_company_profile():

    if not session.get('user_id'):
        return redirect(url_for('login'))

    user_id = session['user_id']
    company = CompanyProfile.query.filter_by(user_id=user_id).first()

    if request.method == "POST":

        if company:

            company.company_name = request.form["company_name"]
            company.industry = request.form["industry"]
            company.website = request.form["website"]
            company.location = request.form["location"]
            company.hr_contact = request.form["hr_contact"]

            db.session.commit()

            return redirect("/company_dashboard")

        else:

            company = CompanyProfile(
                user_id=user_id,
                company_name=request.form["company_name"],
                industry=request.form["industry"],
                website=request.form["website"],
                location=request.form["location"],
                hr_contact=request.form["hr_contact"]
            )

            db.session.add(company)
            db.session.commit()

            return redirect("/company_dashboard")

    return render_template("company_profile.html")








@app.route("/job-applications/<int:job_id>")
def view_applications(job_id):
    applications = Application.query.filter_by(job_id=job_id).all()

    return render_template(
        "applications.html",
        applications=applications
    )

@app.route("/company/student/<int:student_id>")
def view_student_profile(student_id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "company":
        return "Unauthorized", 403

    user_id = session["user_id"]

    company = CompanyProfile.query.filter_by(user_id=user_id).first()
    if not company:
        return "Company profile not found", 404

    student = StudentProfile.query.filter_by(id=student_id).first()
    if not student:
        return "Student not found", 404

    # using relationship instead of join
    applications = [
        app for app in student.applications
        if app.job.company_id == company.id
    ]

    total_applied = len(applications)

    return render_template(
        "student_details.html",
        student=student,
        applications=applications,
        total_applied=total_applied
    )

    
@app.route("/switch-status/<int:app_id>/<string:action>")
def switch_status(app_id, action):
    if "user_id" not in session:
        return redirect("/login")

    application = Application.query.get_or_404(app_id)

    if action == "shortlist":
        if application.status == "Shortlisted":
            application.status = "Applied"   # unshortlist
        else:
            application.status = "Shortlisted"

    elif action == "select":
        if application.status == "Selected":
            application.status = "Shortlisted"   # unselect
        else:
            application.status = "Selected"

    elif action == "reject":
        if application.status == "Rejected":
            application.status = "Applied"   # unreject
        else:
            application.status = "Rejected"

    db.session.commit()

    return redirect(request.referrer)


@app.route("/switch-job/<int:job_id>")
def switch_job(job_id):

    # simple login check
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "company":
        return "Unauthorized", 403

    # get company
    company = CompanyProfile.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not company:
        return "Company not found"

    # get job that belongs to this company
    job = Job.query.filter_by(
        id=job_id,
        company_id=company.id
    ).first()

    if not job:
        return "Job not found"

    # switch  status
    if job.is_closed:
        job.is_closed = False
    else:
        job.is_closed = True

    db.session.commit()

    # go back to dashboard
    return redirect("/company_dashboard")


@app.route("/edit-job/<int:job_id>", methods=["GET", "POST"])
def edit_job(job_id):

    # basic login check
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "company":
        return "Unauthorized", 403

    # get company of logged in user
    company = CompanyProfile.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not company:
        return "Company profile not found"

    # make sure job belongs to this company
    job = Job.query.filter_by(
        id=job_id,
        company_id=company.id
    ).first()

    if not job:
        return "Job not found"

    # if form submitted
    if request.method == "POST":

        # updating fields
        job.title = request.form["title"]
        job.skills = request.form["skills"]
        job.salary = request.form["salary"]

        # small thing so admin can recheck
        job.is_approved = False

        db.session.commit()

        return redirect("/company_dashboard")

    # show edit form
    return render_template("edit_job.html", job=job)







#Student dashboard and job application

@app.route("/student_dashboard")
def student_dashboard():

    # check login
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    # get student profile
    student = StudentProfile.query.filter_by(user_id=user_id).first()

    # get search value from URL
    search = request.args.get("search")

    # base query (only approved & open jobs)
    jobs_query = Job.query.filter_by(is_approved=True, is_closed=False)

    # if search exists -> filter
    if search:
        jobs_query = jobs_query.join(CompanyProfile).filter(
            (CompanyProfile.company_name.ilike(f"%{search}%")) |
            (Job.title.ilike(f"%{search}%")) |
            (Job.skills.ilike(f"%{search}%"))
        )

    jobs = jobs_query.all()

    # store applied jobs
    applied_jobs = {}

    if student:
        for app in student.applications:
            applied_jobs[app.job_id] = app.status

    return render_template(
        "employee_dashboard.html",
        student=student,
        jobs=jobs,
        applied_jobs=applied_jobs
    )

@app.route("/application-history")
def application_history():

    if "user_id" not in session:
        return redirect("/login")

    student = StudentProfile.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if not student:
        return redirect("/complete-student-profile")

    applications = Application.query.filter_by(
        student_id=student.id
    ).order_by(Application.applied_at.desc()).all()

    return render_template(
        "application_history.html",
        applications=applications
    )

@app.route("/apply-job/<int:job_id>")
def apply_job(job_id):
    if "user_id" not in session:
        return redirect("/login")

    student = StudentProfile.query.filter_by(
        user_id=session["user_id"]).first()

    if not student:
        return "Complete profile first!"

    # Check duplicate apply
    existing = Application.query.filter_by(
        job_id=job_id,
        student_id=student.id
    ).first()

    if existing:
        return "Already applied!"

    app = Application(
        job_id=job_id,
        student_id=student.id
    )

    db.session.add(app)
    db.session.commit()

    return redirect("/student_dashboard")


@app.route("/complete-student-profile", methods=["GET", "POST"])
def complete_student_profile():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    student = StudentProfile.query.filter_by(user_id=user_id).first()

    if request.method == "POST":

        if not student:
            student = StudentProfile(user_id=user_id)
            db.session.add(student)

        student.department = request.form["department"]
        student.cgpa = request.form["cgpa"]
        student.resume = request.form["resume"]

        db.session.commit()

        return redirect("/student_dashboard")

    return render_template("complete-student-profile.html", student=student)



#Admin routes for approving companies and jobs

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