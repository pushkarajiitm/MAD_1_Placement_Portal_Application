from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, User, Student, Company, PlacementDrive, Application
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from werkzeug.utils import secure_filename
from functools import wraps

# Import the admin blueprint
from admin import admin_bp

app = Flask(__name__)

# Basic app configuration settings
app.config['SECRET_KEY'] = 'MAD-1' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement_portal.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads/resumes'

# Ensure the upload folder exists to prevent errors when saving files
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize the SQLAlchemy database instance with the Flask app
db.init_app(app)

# Setup Flask-Login to handle user authentication sessions
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Register the admin blueprint routes with the main application
app.register_blueprint(admin_bp)

# Define how Flask-Login loads a user object from the session user_id
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Custom decorator to check if the current user has the 'admin' role
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access denied.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Route: Home Page
@app.route('/')
def index():
    # Only admins are redirected straight to their dashboard from the homepage
    if current_user.is_authenticated and current_user.role == 'admin':
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('index.html')

# Route: Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Retrieve username and password input from the login form
        username_input = request.form.get('username')
        password_input = request.form.get('password')
        
        # Query the database for a user matching the provided username
        user_record = User.query.filter_by(username=username_input).first()
        
        # Check if the user exists and the password matches
        if user_record and user_record.password == password_input:
            # Create a session for the valid user
            login_user(user_record)
            
            # Redirect the user based on their specific role in the system
            if user_record.role == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
            
    # Render the login form for GET requests
    return render_template('login.html')

# Route: Student Registration Page
@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        # Retrieve all student input fields from the registration form
        form_username = request.form.get('username')
        form_email = request.form.get('email')
        form_password = request.form.get('password')
        form_full_name = request.form.get('full_name')
        form_contact_number = request.form.get('contact_number')
        form_department = request.form.get('department')
        form_cgpa = request.form.get('cgpa')
        
        # Handle the resume file upload securely
        resume_file = request.files.get('resume')
        resume_file_path = None
        
        if resume_file and resume_file.filename != '':
            # Create a secure filename combining the username and the original filename
            secure_name = secure_filename(f"{form_username}_{resume_file.filename}")
            # Save the file to the configured upload destination
            resume_file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_name))
            resume_file_path = f"uploads/resumes/{secure_name}"

        # Step 1: Create the base User authentication record
        new_user_account = User(username=form_username, email=form_email, password=form_password, role='student')
        db.session.add(new_user_account)
        db.session.flush() # Flush to assign an ID to new_user_account before committing

        # Step 2: Create the related Student profile record linking the newly created user_id
        new_student_profile = Student(
            user_id=new_user_account.id, 
            full_name=form_full_name, 
            contact_number=form_contact_number, 
            department=form_department, 
            cgpa=float(form_cgpa) if form_cgpa else 0.0,
            resume_path=resume_file_path
        )
        db.session.add(new_student_profile)
        
        # Commit both new records to the database simultaneously
        db.session.commit()

        flash('Registered successfully', 'success')
        return redirect(url_for('login'))

    # Render the empty student registration form for GET requests
    return render_template('register_student.html')

# Route: Company Registration Page
@app.route('/register/company', methods=['GET', 'POST'])
def register_company():
    if request.method == 'POST':
        # Retrieve base user authentication fields
        form_username = request.form.get('username')
        form_email = request.form.get('email')
        form_password = request.form.get('password')
        
        # Retrieve company-specific profile fields
        form_company_name = request.form.get('name')
        form_hr_contact = request.form.get('hr_contact')
        form_website = request.form.get('website')
        form_description = request.form.get('description')

        # Step 1: Create the base User authentication record
        new_user_account = User(username=form_username, email=form_email, password=form_password, role='company')
        db.session.add(new_user_account)
        db.session.flush() # Temp save to retrieve the ID

        # Step 2: Create the related Company profile record
        new_company_profile = Company(
            user_id=new_user_account.id, 
            name=form_company_name, 
            hr_contact=form_hr_contact, 
            website=form_website, 
            description=form_description
        )
        db.session.add(new_company_profile)
        
        # Save records permanently
        db.session.commit()

        flash('Registration pending approval', 'success')
        return redirect(url_for('login'))

    # Render the empty company registration form for GET requests
    return render_template('register_company.html')

# Route: Logout
@app.route('/logout')
@login_required
def logout():
    # End the current active user session
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Start the Flask application development server
    app.run(debug=True)
