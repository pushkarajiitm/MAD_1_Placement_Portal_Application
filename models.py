from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

# User table for login and roles
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False) # Store passwords as plain text
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False) # roles: admin, company, student
    created_at = db.Column(db.DateTime, default=datetime.now)

    # linking to profiles
    company_profile = db.relationship('Company', backref='user', uselist=False)
    student_profile = db.relationship('Student', backref='user', uselist=False)

# Company details table
class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    hr_contact = db.Column(db.String(20), nullable=False)
    website = db.Column(db.String(100))
    description = db.Column(db.Text)
    logo_path = db.Column(db.String(255), nullable=True) # Path to company logo
    approval_status = db.Column(db.String(20), default='Pending') # Statuses: Pending, Approved, Rejected
    is_blacklisted = db.Column(db.Boolean, default=False)

    # link to company's drives
    drives = db.relationship('PlacementDrive', backref='company', lazy=True)

# Student details table
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    resume_path = db.Column(db.String(255))
    department = db.Column(db.String(100))
    cgpa = db.Column(db.Float)
    is_blacklisted = db.Column(db.Boolean, default=False)

    # Placement details
    placement_status = db.Column(db.String(20), default='Unplaced') # Placed, Unplaced
    package = db.Column(db.Float, nullable=True) # LPA
    placed_role = db.Column(db.String(100), nullable=True) # Specific job role
    placed_company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)

    # Link to placed company object
    placed_company = db.relationship('Company', foreign_keys=[placed_company_id])

    # link to student's applications
    applications = db.relationship('Application', backref='student', lazy=True)

# Placement drive table (job postings)
class PlacementDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    eligibility_criteria = db.Column(db.Text, nullable=False)
    application_deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='Pending') # Statuses: Pending, Approved, Closed

    # link to drive applications
    applications = db.relationship('Application', backref='drive', lazy=True)
    
    # link to specific jobs offered by this drive
    offered_jobs = db.relationship('DriveJob', backref='drive', lazy=True, cascade="all, delete-orphan")

# Specific jobs/roles within a placement drive
class DriveJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'), nullable=False)
    role_title = db.Column(db.String(100), nullable=False)
    package = db.Column(db.Float, nullable=False) # LPA

# Application table (student applying for a drive)
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'), nullable=False)
    selected_job_id = db.Column(db.Integer, db.ForeignKey('drive_job.id'), nullable=True) # If selected, for which specific job
    application_date = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default='Applied') # Statuses: Applied, Shortlisted, Selected, Rejected

    # Linking to selected job object
    selected_job = db.relationship('DriveJob', foreign_keys=[selected_job_id])

    # To prevent double application by same student
    __table_args__ = (db.UniqueConstraint('student_id', 'drive_id', name='unique_student_drive_application'),)

# To ensure the logic works:
# 1. PlacementDrive is the main event.
# 2. DriveJob contains the roles (Software Engineer - 10 LPA, Data Analyst - 8 LPA).
# 3. Application tracks which drive the student applied to.
# 4. If Application.status == 'Selected', Application.selected_job_id tells us which role they got.
# 5. Student.placed_role, Student.package, and Student.placed_company_id cache the final result for quick access.
