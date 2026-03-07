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
    
    # Get all the drives this company has created
    my_drives = PlacementDrive.query.filter_by(company_id=company_record.id).all()
    drive_ids = [drive.id for drive in my_drives]
    
    # Enrich drives with applicant counts (for the dashboard table)
    for drive in my_drives:
        drive.applicant_count = Application.query.filter_by(drive_id=drive.id).count()

    count_total_applications = Application.query.filter(Application.drive_id.in_(drive_ids)).count() if drive_ids else 0
    count_shortlisted = Application.query.filter(Application.drive_id.in_(drive_ids), Application.status == 'Shortlisted').count() if drive_ids else 0
    count_selected = Application.query.filter(Application.drive_id.in_(drive_ids), Application.status == 'Selected').count() if drive_ids else 0
    
    return render_template('company/dashboard.html', 
                          company=company_record,
                          my_drives=my_drives,
                          my_drives_count=count_my_drives, 
                          total_applications=count_total_applications,
                          shortlisted_count=count_shortlisted,
                          selected_count=count_selected)

# Route: Company Profile management
@company_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@company_required
def company_profile():
    company_record = current_user.company_profile
    if not company_record:
        flash('Company profile not found.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Retrieve updated profile details
        company_record.name = request.form.get('name')
        company_record.hr_contact = request.form.get('hr_contact')
        company_record.website = request.form.get('website')
        company_record.description = request.form.get('description')
        
        # Handle logo update
        logo_file = request.files.get('logo')
        if logo_file and logo_file.filename != '':
            from werkzeug.utils import secure_filename
            from flask import current_app
            import os
            secure_name = secure_filename(f"{current_user.username}_logo_{logo_file.filename}")
            logo_file.save(os.path.join(current_app.config['LOGO_UPLOAD_FOLDER'], secure_name))
            company_record.logo_path = f"uploads/logos/{secure_name}"

        db.session.commit()
        flash('Company profile updated successfully.', 'success')
        return redirect(url_for('company.company_profile'))

    return render_template('company/profile.html', company=company_record)

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
        
        # Get roles and packages (sent as lists)
        role_titles = request.form.getlist('role_titles[]')
        packages = request.form.getlist('packages[]')
        
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
        
        # Save drive first to get ID
        db.session.add(new_drive_record)
        db.session.flush()

        # Add specific roles
        from models import DriveJob
        for role_title, package in zip(role_titles, packages):
            if role_title and package:
                job = DriveJob(
                    drive_id=new_drive_record.id,
                    role_title=role_title,
                    package=float(package)
                )
                db.session.add(job)
        
        # Save to database
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
@company_bp.route('/application/<int:app_id>/status/<string:new_status>', methods=['GET', 'POST'])
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
        
    if new_status == 'Selected' and request.method == 'POST':
        selected_job_id = request.form.get('selected_job_id')
        if not selected_job_id:
            flash('Please select a role for the student.', 'warning')
            return redirect(url_for('company.view_applications', drive_id=application_record.drive_id))
            
        from models import DriveJob
        job = DriveJob.query.get(selected_job_id)
        if job:
            application_record.status = 'Selected'
            application_record.selected_job_id = job.id
            
            # Note: Final placement status update is now handled by the Admin
            db.session.commit()
            flash(f'Student selected for {job.role_title}!', 'success')
    else:
        # Update status and save
        application_record.status = new_status
        db.session.commit()
        flash(f'Application status updated to {new_status}.', 'success')
    
    # Go back to the list of applications for that specific drive
    return redirect(url_for('company.view_applications', drive_id=application_record.drive_id))

# Route: Edit a placement drive
@company_bp.route('/drive/edit/<int:drive_id>', methods=['GET', 'POST'])
@login_required
@company_required
def edit_drive(drive_id):
    company_record = current_user.company_profile
    drive_record = PlacementDrive.query.get_or_404(drive_id)
    
    if not drive_record or drive_record.company_id != company_record.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('company.company_drives'))
    
    # Ensure company is approved to edit
    if company_record.approval_status != 'Approved':
        flash('Account pending approval.', 'warning')
        return redirect(url_for('company.company_dashboard'))
        
    if request.method == 'POST':
        drive_record.job_title = request.form.get('job_title')
        drive_record.job_description = request.form.get('job_description')
        drive_record.eligibility_criteria = request.form.get('eligibility_criteria')
        deadline_input = request.form.get('application_deadline')
        drive_record.application_deadline = datetime.strptime(deadline_input, '%Y-%m-%d')
        
        # Simple implementation: Re-create roles (or more complex update logic)
        # For simplicity in this student project, we'll clear and re-add roles if provided
        from models import DriveJob
        role_titles = request.form.getlist('role_titles[]')
        packages = request.form.getlist('packages[]')
        
        if role_titles:
            # Clear old roles
            DriveJob.query.filter_by(drive_id=drive_id).delete()
            for role_title, package in zip(role_titles, packages):
                if role_title and package:
                    job = DriveJob(
                        drive_id=drive_record.id,
                        role_title=role_title,
                        package=float(package)
                    )
                    db.session.add(job)
        
        db.session.commit()
        flash('Drive updated successfully.', 'success')
        return redirect(url_for('company.company_drives'))
        
    return render_template('company/edit_drive.html', drive=drive_record)

# Route: Delete a placement drive
@company_bp.route('/drive/delete/<int:drive_id>')
@login_required
@company_required
def delete_drive(drive_id):
    company_record = current_user.company_profile
    drive_record = PlacementDrive.query.get_or_404(drive_id)
    
    if not drive_record or drive_record.company_id != company_record.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('company.company_drives'))

    # Ensure company is approved to delete
    if company_record.approval_status != 'Approved':
        flash('Account pending approval.', 'warning')
        return redirect(url_for('company.company_dashboard'))
        
    db.session.delete(drive_record)
    db.session.commit()
    flash('Drive deleted successfully.', 'success')
    return redirect(url_for('company.company_drives'))

# Route: Close a placement drive
@company_bp.route('/drive/close/<int:drive_id>')
@login_required
@company_required
def close_drive(drive_id):
    company_record = current_user.company_profile
    drive_record = PlacementDrive.query.get_or_404(drive_id)
    
    if not drive_record or drive_record.company_id != company_record.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('company.company_drives'))
    
    # Ensure company is approved to close
    if company_record.approval_status != 'Approved':
        flash('Account pending approval.', 'warning')
        return redirect(url_for('company.company_dashboard'))
        
    drive_record.status = 'Closed'
    db.session.commit()
    flash('Drive closed successfully.', 'success')
    return redirect(url_for('company.company_drives'))
# Route: View all applications across all drives with optional status filter
@company_bp.route('/applications/all')
@company_bp.route('/applications/all/<string:status_filter>')
@login_required
@company_required
def view_all_applications(status_filter=None):
    company_record = current_user.company_profile
    
    # Get all drives for this company
    my_drives = PlacementDrive.query.filter_by(company_id=company_record.id).all()
    drive_ids = [drive.id for drive in my_drives]
    
    if not drive_ids:
        flash('No drives found. Create a drive first!', 'info')
        return redirect(url_for('company.company_dashboard'))

    # Build the query
    query = Application.query.filter(Application.drive_id.in_(drive_ids))
    
    if status_filter:
        query = query.filter(Application.status == status_filter)
        
    application_records = query.order_by(Application.application_date.desc()).all()
    
    return render_template('company/all_applications.html', 
                           applications=application_records, 
                           current_filter=status_filter)
