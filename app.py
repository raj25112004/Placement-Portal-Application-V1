from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask import jsonify


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

        if not email or not password:
            return "All fields are required"

        if '@' not in email:
            return "Invalid email format"

        if len(password) < 6:
            return "Password must be at least 6 characters"

        user = User.query.filter_by(email=email).first()

        if not user:
            return "No user found"

        if not check_password_hash(user.password, password):
            return "Incorrect password"

        if user.role == 'company' and not user.is_approved:
            return "Company registration pending approval"

        session['user_id'] = user.id
        session['role'] = user.role

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

        if not name or not email or not password or not role:
            return "All fields are required"

        if '@' not in email:
            return "Invalid email format"

        if len(password) < 6:
            return "Password must be at least 6 characters"

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "User already exists"

        hashed_password = generate_password_hash(password)

        resume = request.files.get('resume')
        filename = None

        if resume and resume.filename != "":
            if not (resume.filename.endswith('.pdf') or resume.filename.endswith('.doc') or resume.filename.endswith('.docx')):
                return "Invalid file type"

            filename = resume.filename
            resume.save("static/resumes/" + filename)

        new_user = User(
            username=name,
            email=email,
            password=hashed_password,
            role=role,
            is_approved=False if role == 'company' else True
        )

        db.session.add(new_user)
        db.session.commit()

        if role == 'student':

            cgpa = request.form.get('cgpa')
            year = request.form.get('year')

            if cgpa and (float(cgpa) < 0 or float(cgpa) > 10):
                return "Invalid CGPA"

            student = StudentProfile(
                user_id=new_user.id,
                name=name,
                branch=request.form.get('branch'),
                year_of_passing=year,
                cgpa=cgpa,
                resume_link=filename
            )
            db.session.add(student)

        elif role == 'company':

            company_name = request.form.get('company_name')

            if not company_name:
                return "Company name required"

            company = CompanyProfile(
                user_id=new_user.id,
                company_name=company_name,
                industry=request.form.get('industry')
            )
            db.session.add(company)

        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    students = StudentProfile.query.count()
    companies = CompanyProfile.query.count()
    jobs = Job.query.count()
    applications = Application.query.count()

    try:
        placements = Placement.query.count()
    except:
        placements = 0

    return render_template(
        'admin/dashboard.html',
        students=students,
        companies=companies,
        jobs=jobs,
        applications=applications,
        placements=placements
    )

@app.route('/company/dashboard')
def company_dashboard():
    if session.get('role') != 'company':
        return redirect(url_for('login'))

    company = CompanyProfile.query.filter_by(user_id=session['user_id']).first()
    jobs = Job.query.filter_by(company_id=company.id).all()

    titles = []
    counts = []

    for job in jobs:
        titles.append(job.title)
        counts.append(len(job.applications))

    return render_template(
        'company/dashboard.html',
        jobs=jobs,
        titles=titles,
        counts=counts
    )




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

    if 'user_id' not in session or session.get('role') != 'company':
        return redirect(url_for('login'))

    company = CompanyProfile.query.filter_by(user_id=session['user_id']).first()

    if not company:
        return "Invalid company"

    if not company.user.is_approved:
        return "Company not approved by admin"

    if request.method == 'POST':

        title = request.form.get('title')
        description = request.form.get('description')
        skills = request.form.get('skills')
        salary = request.form.get('salary')
        job_type = request.form.get('job_type')
        location = request.form.get('location')

        if not title or not description:
            return "Title and Description are required"

        if len(title) < 3:
            return "Job title too short"

        if len(description) < 10:
            return "Description too short"

        if salary and not salary.replace('-', '').replace(' ', '').isdigit():
            return "Invalid salary format"

        job = Job(
            company_id=company.id,
            title=title,
            description=description,
            skills_required=skills,
            salary_range=salary,
            job_type=job_type,
            location=location,
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
    if session.get('role') != 'student':
        return redirect(url_for('login'))

    student = StudentProfile.query.filter_by(user_id=session['user_id']).first()
    applications = Application.query.filter_by(student_id=student.id).all()

    jobs = Job.query.filter_by(is_approved=True).all()

    status_count = {
        "Applied": 0,
        "Shortlisted": 0,
        "Selected": 0,
        "Rejected": 0
    }

    for app in applications:
        if app.status in status_count:
            status_count[app.status] += 1

    return render_template(
        'student/dashboard.html',
        jobs=jobs,
        status_data=status_count
    )

@app.route('/student/search')
def search_jobs():
    query = request.args.get('q')

    jobs = Job.query.filter(
        Job.title.contains(query) | Job.skills_required.contains(query)
    ).all()

    return render_template('student/dashboard.html', jobs=jobs)

@app.route('/student/apply/<int:job_id>')
def apply_job(job_id):

    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))

    student = StudentProfile.query.filter_by(user_id=session['user_id']).first()

    if not student:
        return "Invalid student"

    job = Job.query.get(job_id)

    if not job:
        return "Job not found"

    if not job.is_approved:
        return "Job not approved yet"

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


# ----------- API ROUTES START -----------

@app.route('/api/students', methods=['GET'])
def api_students():
    students = StudentProfile.query.all()

    result = []
    for s in students:
        result.append({
            "id": s.id,
            "name": s.name,
            "branch": s.branch,
            "cgpa": s.cgpa
        })

    return jsonify(result)

@app.route('/api/companies', methods=['GET'])
def api_companies():
    companies = CompanyProfile.query.all()

    result = []
    for c in companies:
        result.append({
            "id": c.id,
            "name": c.company_name,
            "industry": c.industry
        })

    return jsonify(result)

@app.route('/api/jobs', methods=['GET'])
def api_jobs():
    jobs = Job.query.filter_by(is_approved=True).all()

    result = []
    for j in jobs:
        result.append({
            "id": j.id,
            "title": j.title,
            "company": j.company.company_name,
            "location": j.location,
            "salary": j.salary_range
        })

    return jsonify(result)

@app.route('/api/applications', methods=['GET'])
def api_applications():
    applications = Application.query.all()

    result = []
    for a in applications:
        result.append({
            "id": a.id,
            "student": a.student.name,
            "job": a.job.title,
            "status": a.status
        })

    return jsonify(result)

@app.route('/api/job', methods=['POST'])
def api_create_job():
    data = request.get_json()

    job = Job(
        company_id=data['company_id'],
        title=data['title'],
        description=data['description'],
        skills_required=data.get('skills'),
        salary_range=data.get('salary'),
        location=data.get('location'),
        is_approved=False
    )

    db.session.add(job)
    db.session.commit()

    return jsonify({"message": "Job created"}), 201


@app.route('/api/application/<int:id>', methods=['PUT'])
def api_update_application(id):
    data = request.get_json()

    application = Application.query.get(id)
    application.status = data.get('status')

    db.session.commit()

    return jsonify({"message": "Application updated"})

@app.route('/api/job/<int:id>', methods=['DELETE'])
def api_delete_job(id):
    job = Job.query.get(id)

    db.session.delete(job)
    db.session.commit()

    return jsonify({"message": "Job deleted"})

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

