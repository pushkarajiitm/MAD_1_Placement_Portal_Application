from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Student, Company, PlacementDrive, Application
from functools import wraps

# Initialize the Admin Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Custom decorator to check if the user is an admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Redirect if user is not logged in or doesn't have the 'admin' role
        if not current_user.is_authenticated or current_user.role != 'admin':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Route: Admin Dashboard
@admin_bp.route('/dashboard')
@login_required
@admin_required
def admin_dashboard():
    # Aggregate statistics from the database for the overview panels
    count_pending_companies = Company.query.filter_by(approval_status='Pending').count()
    count_pending_drives = PlacementDrive.query.filter_by(status='Pending').count()
    count_total_students = Student.query.count()
    count_total_placed = Student.query.filter_by(placement_status='Placed').count()
    
    # New statistics required by requirements
    count_total_companies = Company.query.count()
    count_total_drives = PlacementDrive.query.count()
    count_total_applications = Application.query.count()
    
    return render_template('admin/dashboard.html', 
                          pending_companies=count_pending_companies, 
                          pending_drives=count_pending_drives,
                          total_students=count_total_students,
                          total_placed=count_total_placed,
                          total_companies=count_total_companies,
                          total_drives=count_total_drives,
                          total_applications=count_total_applications)

# Route: List Companies
@admin_bp.route('/companies')
@login_required
@admin_required
def admin_companies():
    # Retrieve the search key from URL parameters if it exists
    search_query = request.args.get('search', '')
    
    # Filter the company queries based on the string provided
    if search_query:
        company_records = Company.query.filter(Company.name.ilike(f'%{search_query}%')).all()
    else:
        company_records = Company.query.all()
        
    return render_template('admin/companies.html', companies=company_records, search=search_query)

# Route: Approve Company
@admin_bp.route('/company/approve/<int:company_id>')
@login_required
@admin_required
def approve_company(company_id):
    # Retrieve the specific company record
    company_record = Company.query.get(company_id)
    if company_record:
        # Update the approval status
        company_record.approval_status = 'Approved'
        db.session.commit()
    return redirect(url_for('admin.admin_companies'))

# Route: Reject Company
@admin_bp.route('/company/reject/<int:company_id>')
@login_required
@admin_required
def reject_company(company_id):
    company_record = Company.query.get(company_id)
    if company_record:
        company_record.approval_status = 'Rejected'
        db.session.commit()
    return redirect(url_for('admin.admin_companies'))

# Route: Blacklist Company
@admin_bp.route('/company/blacklist/<int:company_id>')
@login_required
@admin_required
def blacklist_company(company_id):
    company_record = Company.query.get(company_id)
    if company_record:
        company_record.is_blacklisted = True
        db.session.commit()
    return redirect(url_for('admin.admin_companies'))

# Route: Remove Company from Blacklist
@admin_bp.route('/company/remove-blacklist/<int:company_id>')
@login_required
@admin_required
def remove_blacklist_company(company_id):
    company_record = Company.query.get(company_id)
    if company_record:
        company_record.is_blacklisted = False
        db.session.commit()
    return redirect(url_for('admin.admin_companies'))

# Route: Delete Company
@admin_bp.route('/company/delete/<int:company_id>')
@login_required
@admin_required
def delete_company(company_id):
    company_record = Company.query.get(company_id)
    if company_record:
        db.session.delete(company_record)
        db.session.commit()
    return redirect(url_for('admin.admin_companies'))

# Route: List Students
@admin_bp.route('/students')
@login_required
@admin_required
def admin_students():
    search_query = request.args.get('search', '')
    
    if search_query:
        # Check if search_query is an integer (for ID search)
        try:
            student_id = int(search_query)
            student_records = Student.query.filter(
                (Student.id == student_id) |
                (Student.full_name.ilike(f'%{search_query}%')) |
                (Student.contact_number.ilike(f'%{search_query}%'))
            ).all()
        except ValueError:
            student_records = Student.query.filter(
                (Student.full_name.ilike(f'%{search_query}%')) |
                (Student.contact_number.ilike(f'%{search_query}%'))
            ).all()
    else:
        student_records = Student.query.all()
        
    # We also query the approved companies to populate the "Mark as Placed" modal dropdown
    approved_companies = Company.query.filter_by(approval_status='Approved').all()
    
    return render_template('admin/students.html', students=student_records, search=search_query, companies=approved_companies)

# Route: Mark Student as Placed
@admin_bp.route('/student/<int:student_id>/place', methods=['POST'])
@login_required
@admin_required
def mark_as_placed(student_id):
    student_record = Student.query.get(student_id)
    
    # Retrieve form data from the placement modal
    placed_company_id = request.form.get('company_id')
    salary_package = request.form.get('package')
    role_title = request.form.get('role')
    
    # Verify input exists before updating the student's status
    if student_record and placed_company_id and salary_package and role_title:
        try:
            student_record.placement_status = 'Placed'
            student_record.placed_company_id = int(placed_company_id)
            student_record.package = float(salary_package)
            student_record.placed_role = role_title
            db.session.commit()
        except Exception:
            db.session.rollback()
            
    return redirect(url_for('admin.admin_students'))

# Route: Blacklist Student
@admin_bp.route('/student/blacklist/<int:student_id>')
@login_required
@admin_required
def blacklist_student(student_id):
    student_record = Student.query.get(student_id)
    if student_record:
        student_record.is_blacklisted = True
        db.session.commit()
    return redirect(url_for('admin.admin_students'))

# Route: Remove Student from Blacklist
@admin_bp.route('/student/remove-blacklist/<int:student_id>')
@login_required
@admin_required
def remove_blacklist_student(student_id):
    student_record = Student.query.get(student_id)
    if student_record:
        student_record.is_blacklisted = False
        db.session.commit()
    return redirect(url_for('admin.admin_students'))

# Route: Delete Student
@admin_bp.route('/student/delete/<int:student_id>')
@login_required
@admin_required
def delete_student(student_id):
    student_record = Student.query.get(student_id)
    if student_record:
        db.session.delete(student_record)
        db.session.commit()
    return redirect(url_for('admin.admin_students'))

# Route: View Placed Students
@admin_bp.route('/placed-students')
@login_required
@admin_required
def placed_students():
    placed_student_records = Student.query.filter_by(placement_status='Placed').all()
    return render_template('admin/placed_students.html', students=placed_student_records)

# Route: List Placement Drives
@admin_bp.route('/drives')
@login_required
@admin_required
def admin_drives():
    search_query = request.args.get('search', '')
    
    if search_query:
        # Join query to search across related fields in both Job Drive and Company Table
        drive_records = PlacementDrive.query.join(Company).filter(
            (PlacementDrive.job_title.ilike(f'%{search_query}%')) | 
            (Company.name.ilike(f'%{search_query}%'))
        ).all()
    else:
        drive_records = PlacementDrive.query.all()
        
    return render_template('admin/drives.html', drives=drive_records, search=search_query)

# Route: Approve Placement Drive
@admin_bp.route('/drive/approve/<int:drive_id>')
@login_required
@admin_required
def approve_drive(drive_id):
    drive_record = PlacementDrive.query.get(drive_id)
    if drive_record:
        drive_record.status = 'Approved'
        db.session.commit()
    return redirect(url_for('admin.admin_drives'))

# Route: Reject Placement Drive
@admin_bp.route('/drive/reject/<int:drive_id>')
@login_required
@admin_required
def reject_drive(drive_id):
    drive_record = PlacementDrive.query.get(drive_id)
    if drive_record:
        drive_record.status = 'Rejected'
        db.session.commit()
    return redirect(url_for('admin.admin_drives'))

# Route: Delete Placement Drive
@admin_bp.route('/drive/delete/<int:drive_id>')
@login_required
@admin_required
def delete_drive(drive_id):
    drive_record = PlacementDrive.query.get(drive_id)
    if drive_record:
        db.session.delete(drive_record)
        db.session.commit()
    return redirect(url_for('admin.admin_drives'))

# Route: View all historical placement data
@admin_bp.route('/placement-history')
@login_required
@admin_required
def placement_history():
    # Get all applications that resulted in selection
    placed_applications = Application.query.filter_by(status='Selected').order_by(Application.application_date.desc()).all()
    
    # Calculate some historical stats
    total_packages = sum([app.student.package for app in placed_applications if app.student.package])
    avg_package = total_packages / len(placed_applications) if placed_applications else 0
    
    return render_template('admin/placement_history.html', 
                           applications=placed_applications, 
                           avg_package=round(avg_package, 2))

# Route: View all student applications
@admin_bp.route('/applications')
@login_required
@admin_required
def admin_applications():
    search_query = request.args.get('search', '')
    drive_id = request.args.get('drive_id')
    
    query = Application.query.join(Student).join(PlacementDrive).join(Company)
    
    if drive_id:
        query = query.filter(Application.drive_id == int(drive_id))
    
    if search_query:
        query = query.filter(
            (Student.full_name.ilike(f'%{search_query}%')) | 
            (PlacementDrive.job_title.ilike(f'%{search_query}%')) |
            (Company.name.ilike(f'%{search_query}%'))
        )
        
    application_records = query.order_by(Application.application_date.desc()).all()
    
    return render_template('admin/applications.html', 
                           applications=application_records, 
                           search=search_query,
                           drive_id=drive_id)
