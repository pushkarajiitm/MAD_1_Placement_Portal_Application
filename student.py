from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, Student, Company, PlacementDrive, Application
from datetime import datetime
from functools import wraps
import os
from werkzeug.utils import secure_filename

# Initialize the Student Blueprint
student_bp = Blueprint('student', __name__, url_prefix='/student')

# Custom decorator to check if the user is a student
def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('Access denied.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Route: Student Dashboard
@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    student_record = current_user.student_profile
    if not student_record:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('index'))
    
    # Get all approved drives (active ones)
    approved_drives = PlacementDrive.query.filter_by(status='Approved').filter(PlacementDrive.application_deadline >= datetime.now()).all()
    
    # Get all applications by this student
    my_applications = Application.query.filter_by(student_id=student_record.id).all()
    
    return render_template('student/dashboard.html', 
                           student=student_record, 
                           approved_drives=approved_drives, 
                           applications=my_applications)

# Route: View all currently approved placement drives
@student_bp.route('/drives')
@login_required
@student_required
def drives():
    # Only show approved drives where deadline hasn't passed
    drive_records = PlacementDrive.query.filter_by(status='Approved').filter(PlacementDrive.application_deadline >= datetime.now()).all()
    return render_template('student/drives.html', drives=drive_records)

# Route: Apply for a placement drive
@student_bp.route('/apply/<int:drive_id>')
@login_required
@student_required
def apply(drive_id):
    student_record = current_user.student_profile
    drive_record = PlacementDrive.query.get_or_404(drive_id)
    
    # Check if student is blacklisted
    if student_record.is_blacklisted:
        flash('You are blacklisted from applying to drives.', 'danger')
        return redirect(url_for('student.drives'))

    # Check if student is already placed
    if student_record.placement_status == 'Placed':
        flash('You are already placed.', 'info')
        return redirect(url_for('student.drives'))

    # Prevention: Multiple applications check (DB constraint handles this but good to catch early)
    existing_app = Application.query.filter_by(student_id=student_record.id, drive_id=drive_id).first()
    if existing_app:
        flash('You have already applied for this drive.', 'warning')
        return redirect(url_for('student.drives'))

    # Logic: Apply
    new_app = Application(student_id=student_record.id, drive_id=drive_id)
    db.session.add(new_app)
    db.session.commit()
    
    flash('Applied successfully!', 'success')
    return redirect(url_for('student.dashboard'))

# Route: View and update profile
@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@student_required
def profile():
    student_record = current_user.student_profile
    
    if request.method == 'POST':
        student_record.full_name = request.form.get('full_name')
        student_record.contact_number = request.form.get('contact_number')
        student_record.department = request.form.get('department')
        student_record.cgpa = float(request.form.get('cgpa')) if request.form.get('cgpa') else 0.0
        
        # Resume update logic
        resume_file = request.files.get('resume')
        if resume_file and resume_file.filename != '':
            secure_name = secure_filename(f"{current_user.username}_{resume_file.filename}")
            resume_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], secure_name))
            student_record.resume_path = f"uploads/resumes/{secure_name}"
            
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('student.profile'))

    return render_template('student/profile.html', student=student_record)

# Route: View application history
@student_bp.route('/history')
@login_required
@student_required
def history():
    student_record = current_user.student_profile
    all_applications = Application.query.filter_by(student_id=student_record.id).order_by(Application.application_date.desc()).all()
    return render_template('student/history.html', applications=all_applications)
