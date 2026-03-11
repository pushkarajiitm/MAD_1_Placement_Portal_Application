"""JSON API endpoints."""
from flask import Blueprint, jsonify
from models import User, Student, Company, PlacementDrive, Application

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/students')
def get_students():
    students = Student.query.all()
    return jsonify([{
        'id': s.id,
        'full_name': s.full_name,
        'department': s.department,
        'cgpa': s.cgpa,
        'placement_status': s.placement_status
    } for s in students])

@api_bp.route('/companies')
def get_companies():
    companies = Company.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'approval_status': c.approval_status,
        'is_blacklisted': c.is_blacklisted
    } for c in companies])

@api_bp.route('/drives')
def get_drives():
    drives = PlacementDrive.query.all()
    return jsonify([{
        'id': d.id,
        'company': d.company.name,
        'job_title': d.job_title,
        'status': d.status,
        'deadline': d.application_deadline.strftime('%Y-%m-%d')
    } for d in drives])

@api_bp.route('/applications')
def get_applications():
    apps = Application.query.all()
    return jsonify([{
        'id': a.id,
        'student': a.student.full_name,
        'drive': a.drive.job_title,
        'company': a.drive.company.name,
        'status': a.status,
        'date': a.application_date.strftime('%Y-%m-%d')
    } for a in apps])
