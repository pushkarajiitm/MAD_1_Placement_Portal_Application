"""Initialize the database and create a default admin user."""
from flask import Flask
from models import db, User
import os

def init_db():
    app = Flask(__name__)
    
    # Configure same db as main app
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement_portal.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        # Create tables
        db.create_all()
        print("Database initialized!")
        
        # Add default admin user if not there
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            print("Creating the admin...")
            admin_user = User(
                username='admin',
                password='admin123', # Standard weak password for student proj
                email='admin@institute.edu',
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin created.")
        else:
            print("Admin already there.")

if __name__ == '__main__':
    init_db()
