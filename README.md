# Placement Portal Application

A comprehensive platform for managing student placements, company registrations, and recruitment drives.

## Prerequisites

- Python 3.x
- Flask
- Flask-SQLAlchemy
- Flask-Login

## Getting Started

Follow these steps to set up and run the application on your local machine.

### 1. Extract and Navigate
Ensure you are in the project root directory:
```bash
cd MAD_1_Placement_Portal_Application
```

### 2. Set Up Virtual Environment (Recommended)
Create a virtual environment and activate it:
```bash
# Create venv
python -m venv .venv

# Activate on Mac/Linux
source .venv/bin/activate

# Activate on Windows
.venv\Scripts\activate
```

### 3. Install Dependencies
Install the required packages using the requirements file:
```bash
pip install -r requirements.txt
```

### 3. Initialize the Database
Before running the app for the first time, you must initialize the database. This script creates the necessary tables and sets up a default admin account.
```bash
python setup_db.py
```
*Note: A file named `placement_portal.db` will be created in the `instance/` folder.*

### 4. Run the Application
Start the Flask development server:
```bash
python app.py
```

### 5. Access the Portal
Open your web browser and go to:
`http://127.0.0.1:5000`

---

## Default Credentials

### Admin (Institute Placement Cell)
- **Username**: `admin`
- **Password**: `admin123`

### Students & Companies
Users can register directly through the **Login** -> **Register** links on the home page.

## Key Features

- **Students**: Register, upload resumes, and apply for approved placement drives.
- **Companies**: Register, create placement drives (awaiting admin approval), and view applicants.
- **Admin**: Approve/Reject company registrations and drives, manage all users, and blacklist/delete profiles.