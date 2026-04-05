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

        role = request.form.get('role')  # student / company
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check existing user
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "User already exists"

        # Hash password
        hashed_password = generate_password_hash(password)

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
                cgpa=request.form.get('cgpa')
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
    return "Admin Dashboard"


@app.route('/company/dashboard')
def company_dashboard():
    if 'user_id' not in session or session.get('role') != 'company':
        return redirect(url_for('login'))
    return "Company Dashboard"

@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))
    return "Student Dashboard"


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

