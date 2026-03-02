from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Company, PlacementDrive, Application, Student
from datetime import datetime
from functools import wraps

# Initialize the Company Blueprint
company_bp = Blueprint('company', __name__, url_prefix='/company')

# Custom decorator to check if the user is a company
def company_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Redirect if user is not logged in or doesn't have the 'company' role
        if not current_user.is_authenticated or current_user.role != 'company':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Route: Company Dashboard
@company_bp.route('/dashboard')
@login_required
@company_required
def company_dashboard():
    # Make sure the company profile actually exists
    company_record = current_user.company_profile
    if not company_record:
        flash('Company profile not found.', 'danger')
        return redirect(url_for('index'))
        
    # Check if the admin has approved this company
    if company_record.approval_status != 'Approved':
        return render_template('company/pending_approval.html')

    # Aggregate statistics for the company dashboard
    count_my_drives = PlacementDrive.query.filter_by(company_id=company_record.id).count()
    
    # Get all the applications for all the drives this company has created
    my_drives = PlacementDrive.query.filter_by(company_id=company_record.id).all()
    drive_ids = [drive.id for drive in my_drives]
    count_total_applications = Application.query.filter(Application.drive_id.in_(drive_ids)).count() if drive_ids else 0
    count_shortlisted = Application.query.filter(Application.drive_id.in_(drive_ids), Application.status == 'Shortlisted').count() if drive_ids else 0
    
    return render_template('company/dashboard.html', 
                          my_drives_count=count_my_drives, 
                          total_applications=count_total_applications,
                          shortlisted_count=count_shortlisted)

# Route: View and Create placement drives
@company_bp.route('/drives', methods=['GET', 'POST'])
@login_required
@company_required
def company_drives():
    company_record = current_user.company_profile
    
    # Make sure they are approved first
    if company_record.approval_status != 'Approved':
        return redirect(url_for('company.company_dashboard'))

    # If the company submits the form to create a new job drive
    if request.method == 'POST':
        # Get details from form
        job_title_input = request.form.get('job_title')
        description_input = request.form.get('job_description')
        eligibility_input = request.form.get('eligibility_criteria')
        deadline_input = request.form.get('application_deadline')
        
        # Convert the string date from the HTML form into a Python Date object
        deadline_date = datetime.strptime(deadline_input, '%Y-%m-%d')
        
        # Create the new job posting
        new_drive_record = PlacementDrive(
            company_id=company_record.id,
            job_title=job_title_input,
            job_description=description_input,
            eligibility_criteria=eligibility_input,
            application_deadline=deadline_date
        )
        
        # Save to database
        db.session.add(new_drive_record)
        db.session.commit()
        
        flash('New placement drive created and is pending admin approval!', 'success')
        return redirect(url_for('company.company_drives'))

    # For a GET request, just show all the drives this specific company has created
    my_drives = PlacementDrive.query.filter_by(company_id=company_record.id).all()
    return render_template('company/drives.html', drives=my_drives)

# Route: View Applications for a specific Drive
@company_bp.route('/drive/<int:drive_id>/applications')
@login_required
@company_required
def view_applications(drive_id):
    company_record = current_user.company_profile
    drive_record = PlacementDrive.query.get(drive_id)
    
    # Check: Does this drive exist, and does it belong to THIS logged in company?
    if not drive_record or drive_record.company_id != company_record.id:
        flash('Invalid Access.', 'danger')
        return redirect(url_for('company.company_drives'))
        
    # Get all student applications for this specific job drive
    application_records = Application.query.filter_by(drive_id=drive_id).all()
    
    return render_template('company/applications.html', drive=drive_record, applications=application_records)

# Route: Update the status of a specific student application
@company_bp.route('/application/<int:app_id>/status/<string:new_status>')
@login_required
@company_required
def update_application_status(app_id, new_status):
    # Allowed statuses a company can set
    valid_statuses = ['Shortlisted', 'Selected', 'Rejected']
    if new_status not in valid_statuses:
        flash('Invalid status update.', 'danger')
        return redirect(url_for('company.company_dashboard'))
        
    company_record = current_user.company_profile
    application_record = Application.query.get(app_id)
    
    # Security check: Ensure this application belongs to a drive owned by THIS company
    if not application_record or application_record.drive.company_id != company_record.id:
        flash('Invalid Access.', 'danger')
        return redirect(url_for('company.company_dashboard'))
        
    # Update status and save
    application_record.status = new_status
    db.session.commit()
    
    flash(f'Application status updated to {new_status}.', 'success')
    # Go back to the list of applications for that specific drive
    return redirect(url_for('company.view_applications', drive_id=application_record.drive_id))
