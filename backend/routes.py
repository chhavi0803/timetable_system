from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from database import db
from models import User, Teacher, Class, Subject, Timetable
from util import generate_pdf, generate_conflict_report, generate_timetable_report

def init_routes(app):
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'POST':
            username = request.form['username']
            password = generate_password_hash(request.form['password'])
            role = request.form['role']

            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists. Please choose a different username.', 'error')
                return redirect(url_for('signup'))

            user = User(username=username, password=password, role=role)
            db.session.add(user)
            try:
                db.session.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            except IntegrityError:
                db.session.rollback()
                flash('An error occurred while creating the account. Please try again.', 'error')
                return redirect(url_for('signup'))
        return render_template('signup.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            if user:
                if check_password_hash(user.password, password):
                    session['user_id'] = user.id
                    session['user_role'] = user.role
                    flash('Login successful!', 'success')
                    if user.role == 'admin':
                        return redirect(url_for('admin_dashboard'))
                    elif user.role == 'teacher':
                        return redirect(url_for('teacher_dashboard'))
                    elif user.role == 'student':
                        return redirect(url_for('student_dashboard'))
                else:
                    flash('Incorrect password. Please try again.', 'error')
            else:
                flash('Username not found. Please sign up first.', 'error')
        return render_template('login.html')

    @app.route('/admin_dashboard')
    def admin_dashboard():
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        users = User.query.all()
        classes = Class.query.all()
        teachers = Teacher.query.all()
        subjects = Subject.query.all()
        timetables = Timetable.query.all()

        total_users = len(users)
        total_classes = len(classes)
        total_subjects = len(subjects)
        total_timetables = len(timetables)
        recent_logs = []  # Implement logic for recent logs if needed

        return render_template('admin_dashboard.html', users=users, classes=classes, teachers=teachers, subjects=subjects, timetables=timetables,
                               total_users=total_users, total_classes=total_classes, total_subjects=total_subjects, total_timetables=total_timetables, recent_logs=recent_logs)

    @app.route('/admin/add_user', methods=['POST'])
    def add_user():
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']
        class_id = request.form.get('class_id')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different username.', 'error')
            return redirect(url_for('admin_dashboard'))

        user = User(username=username, password=password, role=role, class_id=class_id)
        db.session.add(user)
        try:
            db.session.commit()
            if role == 'teacher':
                teacher = Teacher(user_id=user.id, teacher_name=username)
                db.session.add(teacher)
                db.session.commit()
            flash('User added successfully.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while adding the user. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/edit_user/<int:user_id>', methods=['POST'])
    def edit_user(user_id):
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        user = User.query.get(user_id)
        user.username = request.form['username']
        user.role = request.form['role']
        user.class_id = request.form.get('class_id')

        if 'password' in request.form and request.form['password']:
            user.password = generate_password_hash(request.form['password'])

        try:
            db.session.commit()
            flash('User updated successfully.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while updating the user. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
    def delete_user(user_id):
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        user = User.query.get(user_id)
        db.session.delete(user)
        try:
            db.session.commit()
            flash('User deleted successfully.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while deleting the user. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/add_class', methods=['POST'])
    def add_class():
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        class_name = request.form['class_name']

        existing_class = Class.query.filter_by(class_name=class_name).first()
        if existing_class:
            flash('Class already exists. Please choose a different class name.', 'error')
            return redirect(url_for('admin_dashboard'))

        class_ = Class(class_name=class_name)
        db.session.add(class_)
        try:
            db.session.commit()
            flash('Class added successfully.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while adding the class. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/edit_class/<int:class_id>', methods=['POST'])
    def edit_class(class_id):
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        class_ = Class.query.get(class_id)
        class_.class_name = request.form['class_name']

        try:
            db.session.commit()
            flash('Class updated successfully.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while updating the class. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/delete_class/<int:class_id>', methods=['POST'])
    def delete_class(class_id):
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        class_ = Class.query.get(class_id)
        db.session.delete(class_)
        try:
            db.session.commit()
            flash('Class deleted successfully.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while deleting the class. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/add_subject', methods=['POST'])
    def add_subject():
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        subject_name = request.form['subject_name']

        existing_subject = Subject.query.filter_by(subject_name=subject_name).first()
        if existing_subject:
            flash('Subject already exists. Please choose a different subject name.', 'error')
            return redirect(url_for('admin_dashboard'))

        subject = Subject(subject_name=subject_name)
        db.session.add(subject)
        try:
            db.session.commit()
            flash('Subject added successfully.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while adding the subject. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/edit_subject/<int:subject_id>', methods=['POST'])
    def edit_subject(subject_id):
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        subject = Subject.query.get(subject_id)
        subject.subject_name = request.form['subject_name']

        try:
            db.session.commit()
            flash('Subject updated successfully.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while updating the subject. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/delete_subject/<int:subject_id>', methods=['POST'])
    def delete_subject(subject_id):
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        subject = Subject.query.get(subject_id)
        db.session.delete(subject)
        try:
            db.session.commit()
            flash('Subject deleted successfully.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while deleting the subject. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/create_timetable', methods=['POST'])
    def create_timetable():
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        class_id = request.form['class_id']
        day = request.form['day']
        time_slot = request.form['time_slot']
        subject_id = request.form['subject_id']
        teacher_id = request.form['teacher_id']

        # Check for conflicts
        conflict = Timetable.query.filter_by(day=day, time_slot=time_slot, teacher_id=teacher_id).first()
        if conflict:
            flash('Conflict detected: The same teacher is assigned to another class at the same time.', 'error')
            return redirect(url_for('admin_dashboard'))

        timetable = Timetable(class_id=class_id, day=day, time_slot=time_slot, subject_id=subject_id, teacher_id=teacher_id)
        db.session.add(timetable)
        try:
            db.session.commit()
            flash('Timetable created successfully.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while creating the timetable. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/edit_timetable/<int:timetable_id>', methods=['POST'])
    def edit_timetable(timetable_id):
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        timetable = Timetable.query.get(timetable_id)
        timetable.class_id = request.form['class_id']
        timetable.day = request.form['day']
        timetable.time_slot = request.form['time_slot']
        timetable.subject_id = request.form['subject_id']
        timetable.teacher_id = request.form['teacher_id']

        # Check for conflicts
        conflict = Timetable.query.filter_by(day=timetable.day, time_slot=timetable.time_slot, teacher_id=timetable.teacher_id).filter(Timetable.id != timetable_id).first()
        if conflict:
            flash('Conflict detected: The same teacher is assigned to another class at the same time.', 'error')
            return redirect(url_for('admin_dashboard'))

        try:
            db.session.commit()
            flash('Timetable updated successfully.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while updating the timetable. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/delete_timetable/<int:timetable_id>', methods=['POST'])
    def delete_timetable(timetable_id):
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        timetable = Timetable.query.get(timetable_id)
        db.session.delete(timetable)
        try:
            db.session.commit()
            flash('Timetable deleted successfully.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while deleting the timetable. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/assign_teacher_subject', methods=['POST'])
    def assign_teacher_subject():
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))
        teacher_id = request.form['teacher_id']
        subject_id = request.form['subject_id']
        teacher = Teacher.query.get(teacher_id)
        subject = Subject.query.get(subject_id)
        teacher.subjects.append(subject)
        try:
            db.session.commit()
            flash('Teacher assigned to subject successfully.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while assigning the teacher. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/generate_conflict_report', methods=['GET'])
    def generate_conflict_report_route():
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))
        pdf = generate_conflict_report()
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=conflict_report.pdf'
        return response

    @app.route('/admin/generate_timetable_report', methods=['GET'])
    def generate_timetable_report_route():
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))
        pdf = generate_timetable_report()
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=timetable_report.pdf'
        return response

    @app.route('/teacher_dashboard')
    def teacher_dashboard():
        if session.get('user_role') != 'teacher':
            return redirect(url_for('index'))
        user_id = session.get('user_id')
        teacher = Teacher.query.filter_by(user_id=user_id).first()
        if teacher is None:
            flash('Teacher not found.', 'error')
            return redirect(url_for('index'))
        timetables = Timetable.query.filter_by(teacher_id=teacher.id).all()
        return render_template('teacher_dashboard.html', timetables=timetables)

    @app.route('/teacher/request_slot_change', methods=['POST'])
    def request_slot_change():
        if session.get('user_role') != 'teacher':
            return redirect(url_for('index'))
        timetable_id = request.form['timetable_id']
        reason = request.form['reason']
        # Handle the request logic here (e.g., send a notification to the admin)
        flash('Request for timetable slot change sent successfully.', 'success')
        return redirect(url_for('teacher_dashboard'))

    @app.route('/student_dashboard')
    def student_dashboard():
        if session.get('user_role') != 'student':
            return redirect(url_for('index'))
        user_id = session.get('user_id')
        student = User.query.get(user_id)
        timetables = Timetable.query.filter_by(class_id=student.class_id).all()
        return render_template('student_dashboard.html', student=student, timetables=timetables)

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('index'))

    @app.route('/generate_pdf')
    def generate_pdf_route():
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
        pdf = generate_pdf(user_id)
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=timetable.pdf'
        return response