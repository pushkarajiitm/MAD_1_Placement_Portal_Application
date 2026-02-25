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

# Application table (student applying for a drive)
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default='Applied') # Statuses: Applied, Shortlisted, Selected, Rejected

    # To prevent double application by same student
    __table_args__ = (db.UniqueConstraint('student_id', 'drive_id', name='unique_student_drive_application'),)
