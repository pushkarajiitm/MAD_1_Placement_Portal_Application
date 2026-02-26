from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, User, Student, Company, PlacementDrive, Application
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Basic config for the app
app.config['SECRET_KEY'] = 'my-secret-key-123' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement_portal.db' # Keeping it simple in root
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads/resumes'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize the database
db.init_app(app)

# Setup login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home page route
@app.route('/')
def index():
    return render_template('index.html')

# Login functionality
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_name = request.form.get('username')
        pass_word = request.form.get('password')
        
        # Check if user exists
        user = User.query.filter_by(username=user_name).first()
        
        # Simple password check
        if user and user.password == pass_word:
            login_user(user)
            flash('You are now logged in!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid login! Try again.', 'danger')
            
    return render_template('login.html')

# Student registration
@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        contact = request.form.get('contact_number')
        dept = request.form.get('department')
        cgpa = request.form.get('cgpa')
        
        # Handle file upload
        resume_file = request.files.get('resume')
        resume_path = None
        if resume_file and resume_file.filename:
            filename = secure_filename(f"{username}_{resume_file.filename}")
            resume_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            resume_path = os.path.join('uploads/resumes', filename)

        # Create basic user
        new_user = User(username=username, email=email, password=password, role='student')
        db.session.add(new_user)
        db.session.flush() # Get user ID

        # Create student profile
        new_student = Student(
            user_id=new_user.id, 
            full_name=full_name, 
            contact_number=contact, 
            department=dept, 
            cgpa=float(cgpa) if cgpa else 0.0,
            resume_path=resume_path
        )
        db.session.add(new_student)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register_student.html')

# Company registration
@app.route('/register/company', methods=['GET', 'POST'])
def register_company():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        contact = request.form.get('hr_contact')
        website = request.form.get('website')
        desc = request.form.get('description')

        # Create basic user
        new_user = User(username=username, email=email, password=password, role='company')
        db.session.add(new_user)
        db.session.flush()

        # Create company profile
        new_company = Company(user_id=new_user.id, name=name, hr_contact=contact, website=website, description=desc)
        db.session.add(new_company)
        db.session.commit()

        flash('Company registration sent for approval!', 'success')
        return redirect(url_for('login'))

    return render_template('register_company.html')

# Log out route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Successfully logged out.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Run the server
    app.run(debug=True)
