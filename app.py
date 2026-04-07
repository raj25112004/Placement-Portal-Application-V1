from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "mysecret123"



app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement_portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ------------------------------------------
# MODELS
# ------------------------------------------


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    role = db.Column(db.String(20), nullable=False)  # 'student', 'company', 'admin'
    phone_number = db.Column(db.String(20), nullable=True)
    is_approved = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())



    student_profile = db.relationship('StudentProfile', back_populates='user', uselist=False)
    company_profile = db.relationship('CompanyProfile', back_populates='user', uselist=False)



class StudentProfile(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    branch = db.Column(db.String(120), nullable=False)
    year_of_passing = db.Column(db.Integer, nullable=False)
    cgpa = db.Column(db.Float, nullable=False)
    skills = db.Column(db.String(255), nullable=True)
    resume_link = db.Column(db.String(255), nullable=True)

    user = db.relationship('User',back_populates = 'student_profile')
    applications = db.relationship('Application', back_populates='student')


class CompanyProfile(db.Model):
    __tablename__ = 'company'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    company_name = db.Column(db.String(120), nullable=False)
    industry = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(120), nullable=True)
    company_size = db.Column(db.String(50), nullable=True)

    description = db.Column(db.Text, nullable=True)

    user = db.relationship('User', back_populates='company_profile', uselist=False)

    jobs = db.relationship('Job', back_populates='company')

class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    skills_required = db.Column(db.String(255), nullable=True)
    is_approved = db.Column(db.Boolean, default=False)
    location = db.Column(db.String(120), nullable=True)
    salary_range = db.Column(db.String(50), nullable=True)
    job_type = db.Column(db.String(50), nullable=True)  # e.g., 'Full-time', 'Internship'

    company = db.relationship('CompanyProfile', back_populates='jobs')

    applications = db.relationship('Application', back_populates='job')

class Application(db.Model):
    __tablename__ = 'applications'

    __table_args__ = (
    db.UniqueConstraint('job_id', 'student_id', name='unique_application'),
    )
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    status = db.Column(db.String(20), default='Applied')  # 'Applied', 'Shortlisted', 'Rejected'
    applied_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    remarks = db.Column(db.Text, nullable=True)

    job = db.relationship('Job', back_populates='applications')
    student = db.relationship('StudentProfile', back_populates='applications')

class Placement(db.Model):
    __tablename__ = 'placements'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    placed_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    package = db.Column(db.String(50))

    application = db.relationship('Application', backref='placement', uselist=False)

# ------------------------------------------
# APP START
# ------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if not user:
            return "No user found"

        # Correct password check
        if not check_password_hash(user.password, password):
            return "Incorrect password"

        # Company approval check
        if user.role == 'company' and not user.is_approved:
            return "Company registration pending approval"

        # Session set
        session['user_id'] = user.id
        session['role'] = user.role

        # Role-based redirect
        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))

        elif user.role == 'company':
            return redirect(url_for('company_dashboard'))

        else:
            return redirect(url_for('student_dashboard'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        role = request.form.get('role')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check existing user
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "User already exists"

        # Hash password
        hashed_password = generate_password_hash(password)

        # Handle resume upload
        resume = request.files.get('resume')
        filename = None

        if resume and resume.filename != "":
            filename = resume.filename
            resume.save("static/resumes/" + filename)

        # Create user
        new_user = User(
            username=name,
            email=email,
            password=hashed_password,
            role=role,
            is_approved=False if role == 'company' else True
        )

        db.session.add(new_user)
        db.session.commit()

        # Create profile based on role
        if role == 'student':
            student = StudentProfile(
                user_id=new_user.id,
                name=name,
                branch=request.form.get('branch'),
                year_of_passing=request.form.get('year'),
                cgpa=request.form.get('cgpa'),
                resume_link=filename   # 👈 important
            )
            db.session.add(student)

        elif role == 'company':
            company = CompanyProfile(
                user_id=new_user.id,
                company_name=request.form.get('company_name'),
                industry=request.form.get('industry')
            )
            db.session.add(company)

        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    total_students = StudentProfile.query.count()
    total_companies = CompanyProfile.query.count()
    total_jobs = Job.query.count()
    total_applications = Application.query.count()

    return render_template(
        'admin/dashboard.html',
        students=total_students,
        companies=total_companies,
        jobs=total_jobs,
        applications=total_applications
    )


@app.route('/company/dashboard')
def company_dashboard():
    if 'user_id' not in session or session.get('role') != 'company':
        return redirect(url_for('login'))

    user_id = session['user_id']
    company = CompanyProfile.query.filter_by(user_id=user_id).first()

    jobs = Job.query.filter_by(company_id=company.id).all()

    return render_template('company/dashboard.html', jobs=jobs)

@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))
    return "Student Dashboard"


@app.route('/admin/companies')
def view_companies():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    companies = CompanyProfile.query.all()
    return render_template('admin/companies.html', companies=companies)


@app.route('/admin/company/approve/<int:user_id>')
def approve_company(user_id):
    user = User.query.get(user_id)
    user.is_approved = True
    db.session.commit()
    return redirect(url_for('view_companies'))


@app.route('/admin/company/reject/<int:user_id>')
def reject_company(user_id):
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('view_companies'))

@app.route('/admin/jobs')
def view_jobs():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    jobs = Job.query.all()
    return render_template('admin/jobs.html', jobs=jobs)


@app.route('/admin/job/approve/<int:job_id>')
def approve_job(job_id):
    job = Job.query.get(job_id)
    job.is_approved = True
    db.session.commit()
    return redirect(url_for('view_jobs'))


@app.route('/admin/job/reject/<int:job_id>')
def reject_job(job_id):
    job = Job.query.get(job_id)
    db.session.delete(job)
    db.session.commit()
    return redirect(url_for('view_jobs'))

@app.route('/admin/students')
def view_students():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    students = StudentProfile.query.all()
    return render_template('admin/students.html', students=students)

@app.route('/admin/search/student')
def search_student():
    query = request.args.get('q')

    students = StudentProfile.query.filter(
        StudentProfile.name.contains(query)
    ).all()

    return render_template('admin/students.html', students=students)

@app.route('/admin/search/company')
def search_company():
    query = request.args.get('q')

    companies = CompanyProfile.query.filter(
        CompanyProfile.company_name.contains(query)
    ).all()

    return render_template('admin/companies.html', companies=companies)

@app.route('/admin/student/deactivate/<int:user_id>')
def deactivate_student(user_id):
    user = User.query.get(user_id)
    user.is_active = False
    db.session.commit()
    return redirect(url_for('view_students'))

@app.route('/admin/company/deactivate/<int:user_id>')
def deactivate_company(user_id):
    user = User.query.get(user_id)
    user.is_active = False
    db.session.commit()
    return redirect(url_for('view_companies'))


@app.route('/company/job/create', methods=['GET', 'POST'])
def create_job():
    # Check login + role
    if 'user_id' not in session or session.get('role') != 'company':
        return redirect(url_for('login'))

    # Get company
    company = CompanyProfile.query.filter_by(user_id=session['user_id']).first()

    #Only approved company can create jobs
    if not company.user.is_approved:
        return "Company not approved by admin"

    if request.method == 'POST':

        title = request.form.get('title')
        description = request.form.get('description')

        # Basic validation
        if not title or not description:
            return "Title and Description are required"

        job = Job(
            company_id=company.id,
            title=title,
            description=description,
            skills_required=request.form.get('skills'),
            salary_range=request.form.get('salary'),
            job_type=request.form.get('job_type'),
            location=request.form.get('location'),

            is_approved=False
        )

        db.session.add(job)
        db.session.commit()

        return redirect(url_for('company_dashboard'))

    return render_template('company/create_job.html')

@app.route('/company/job/applications/<int:job_id>')
def view_applications(job_id):
    if session.get('role') != 'company':
        return redirect(url_for('login'))
    
    company = CompanyProfile.query.filter_by(user_id=session['user_id']).first()
    applications = Application.query.join(Job).filter(
    Job.company_id == company.id,
    Job.id == job_id
    ).all()

    return render_template('company/applications.html', applications=applications)

@app.route('/company/application/update/<int:app_id>/<status>')
def update_application(app_id, status):
    if session.get('role') != 'company':
        return redirect(url_for('login'))

    application = Application.query.get(app_id)

    allowed_status = ['Shortlisted', 'Interview', 'Selected', 'Rejected']

    if status not in allowed_status:
        return "Invalid status"

    application.status = status

    #Placement logic
    if status == "Selected":
        if not application.placement:
            placement = Placement(
                application_id=application.id,
                package="Not Disclosed"
            )
            db.session.add(placement)

    db.session.commit()

    return redirect(url_for('company_dashboard'))


@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))

    # Only approved jobs
    jobs = Job.query.filter_by(is_approved=True).all()

    return render_template('student/dashboard.html', jobs=jobs)

@app.route('/student/search')
def search_jobs():
    query = request.args.get('q')

    jobs = Job.query.filter(
        Job.title.contains(query) | Job.skills_required.contains(query)
    ).all()

    return render_template('student/dashboard.html', jobs=jobs)

@app.route('/student/apply/<int:job_id>')
def apply_job(job_id):
    if session.get('role') != 'student':
        return redirect(url_for('login'))

    student = StudentProfile.query.filter_by(user_id=session['user_id']).first()

    # Prevent duplicate (already added constraint but still safe)
    existing = Application.query.filter_by(
        job_id=job_id,
        student_id=student.id
    ).first()

    if existing:
        return "Already applied"

    application = Application(
        job_id=job_id,
        student_id=student.id
    )

    db.session.add(application)
    db.session.commit()

    return redirect(url_for('student_dashboard'))

@app.route('/student/applications')
def student_applications():
    if session.get('role') != 'student':
        return redirect(url_for('login'))

    student = StudentProfile.query.filter_by(user_id=session['user_id']).first()

    applications = Application.query.filter_by(student_id=student.id).all()

    return render_template('student/applications.html', applications=applications)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        user = User.query.filter_by(username='admin').first()
        if not user:
            admin_user = User(
                username='admin',
                email='admin@gmail.com',
                password='admin123',
                role='admin',
                is_approved=True
            )
            db.session.add(admin_user)
            db.session.commit()
    app.run(debug=True)

