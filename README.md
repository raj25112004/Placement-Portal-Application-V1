# Placement Portal Application

A full-stack web-based Placement Portal developed using Flask to automate and simplify the campus placement process for students, companies, and administrators.

---

## Project Overview

The Placement Portal Application provides a centralized platform where:

- **Students** can register, upload resumes, apply for jobs, and track applications.
- **Companies** can register, post job openings, and manage applicants.
- **Admins** can approve/reject companies and jobs, monitor the platform, and manage placements.

The system ensures secure authentication, role-based access, placement tracking, and dashboard analytics.

---

## Features

### Authentication & Security
- User Registration/Login
- Password Hashing
- Flask-Login Integration
- Protected Routes
- Role-Based Access Control

### Student Module
- Register/Login as Student
- Upload Resume
- View Approved Jobs
- Apply for Jobs
- Track Application Status
- View Application History

### Company Module
- Register/Login as Company
- Admin Approval Required
- Post New Jobs
- View Applications
- Update Applicant Status
- Placement Selection Tracking

### Admin Module
- Dashboard Analytics
- Approve/Reject Companies
- Approve/Reject Jobs
- View Students
- Deactivate Users

### Additional Features
- Charts and Visualization using Chart.js
- REST APIs (GET, POST, PUT, DELETE)
- Responsive UI using Bootstrap
- Frontend and Backend Validation

---

## Technologies Used

### Frontend
- HTML5
- CSS3
- Bootstrap 5
- JavaScript
- Chart.js

### Backend
- Python
- Flask Framework

### Database
- SQLite

### Authentication
- Flask-Login

### ORM
- SQLAlchemy

---

## Database Schema

The application uses the following database tables:

- Users
- StudentProfile
- CompanyProfile
- Jobs
- Applications
- Placements

---

## API Endpoints

### GET
- `/api/students` → Fetch all students
- `/api/companies` → Fetch all companies
- `/api/jobs` → Fetch all approved jobs
- `/api/applications` → Fetch all applications

### POST
- `/api/job` → Add new job

### PUT
- `/api/application/<id>` → Update application

### DELETE
- `/api/job/<id>` → Delete job

---

## Installation & Setup

### Clone Repository
```bash
git clone <repository_url>
cd Placement-Portal-App
```

### Create Virtual Environment
```bash
python -m venv myenv
```

### Activate Virtual Environment
```bash
myenv\Scripts\activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Application
```bash
python app.py
```

---

## Default Admin Credentials

```text
Email: admin@gmail.com
Password: admin123
```

---

## Future Enhancements

- Email Notifications
- OTP Verification
- Interview Scheduling
- AI Resume Screening
- Advanced Filtering/Search


---