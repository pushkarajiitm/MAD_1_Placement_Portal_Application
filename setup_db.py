from flask import Flask
from models import db, User
import os

def init_db():
    app = Flask(__name__)
    # Setup for the database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement_portal.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        # Create all the tables
        db.create_all()
        print("Done: Database tables created.")
        
        # Add the default admin if not there
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            print("Creating default admin...")
            admin_user = User(
                username='admin',
                password='admin123',
                email='admin@institute.edu',
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created successfully.")
        else:
            print("Admin already exists.")

if __name__ == '__main__':
    init_db()
