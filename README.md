# Timetable Management System

## Overview

This project is a comprehensive web-based timetable management system. It caters to three user roles: administrators, teachers, and students. Each role has distinct functionalities to efficiently manage and access timetables.

## Technologies Used

- **Backend:** Python (Flask)
- **Frontend:** HTML, CSS, JavaScript
- **Database:** MySQL
- **PDF Generation:** ReportLab

## Local Setup Instructions

### Prerequisites

1. Python 3.x
2. MySQL Server
3. pip (Python package installer)

### Steps

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/timetable_management.git
   cd timetable_management
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup MySQL Database:**
   - Create a new database in MySQL named `timetable_db`.
   - Use the credentials: Username: `root`, Password: `1234567`.

4. **Run Database Schema:**
   - Import the database schema from `database/schema.sql` into your MySQL database.

5. **Run the Application:**
   ```bash
   python backend/app.py
   ```

6. **Access the Application:**
   - Open your web browser and go to `http://127.0.0.1:5000`.

## Features

- **User Authentication:** Signup and login functionality based on user roles.
- **Role-Based Authorization:** Access control based on roles (admin, teacher, student).
- **Class Management:** Create, edit, and delete classes.
- **Timetable Management:** Add, edit, and delete timetable slots with conflict detection.
- **Teacher Schedule Management:** View and edit assigned classes and schedules.
- **Student Timetable Retrieval:** Display student's timetable.
- **PDF Export:** Generate and download PDF timetables.

## Folder Structure

- **backend:** Contains the backend code (Flask app, database models, routes).
- **frontend:** Contains the frontend code (HTML templates, CSS, JavaScript).
- **database:** Database schema and initial data.
- **requirements.txt:** List of Python dependencies.

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes.

## License

This project is licensed under the MIT License.