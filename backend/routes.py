from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from database import db
from models import User, Teacher, Class, Subject, Timetable, generate_user_id  # <-- Import generate_user_id here
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

            # Check for existing user with the same username
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists. Please choose a different username.', 'error')
                return redirect(url_for('signup'))

            # Generate user_id based on the role
            user_id = generate_user_id(role)

            # Create a new user with both username and user_id
            user = User(username=username, password=password, role=role, user_id=user_id)

            # Add the new user to the database
            db.session.add(user)
            try:
                db.session.commit()
                flash(f'Registration successful! Your ID is {user_id}. Please log in.', 'success')
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

            # Find the user by their username
            user = User.query.filter_by(username=username).first()
            
            if user:
                # Check if the password is correct
                if check_password_hash(user.password, password):
                    # Store user info in the session
                    session['user_id'] = user.user_id  # Store user_id, not the username
                    session['user_role'] = user.role
                    flash('Login successful!', 'success')

                    # Redirect based on the user's role
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

        # Fetching all users, classes, teachers, and subjects
        users = User.query.all()
        classes = Class.query.all()
        teachers = Teacher.query.all()
        subjects = Subject.query.all()
        timetables = Timetable.query.all()
        print(timetables)

        total_users = len(users)
        total_classes = len(classes)
        total_subjects = len(subjects)
        total_timetables = len(timetables)
        
        recent_logs = []

        return render_template(
            'admin_dashboard.html',
            users=users,
            classes=classes,
            teachers=teachers,
            subjects=subjects,
            timetables=timetables,
            total_users=total_users,
            total_classes=total_classes,
            total_subjects=total_subjects,
            total_timetables=total_timetables,
            recent_logs=recent_logs
        )


    @app.route('/admin/add_user', methods=['POST'])
    def add_user():
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']
        class_name = request.form.get('class_name')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different username.', 'error')
            return redirect(url_for('admin_dashboard'))

        user_id = generate_user_id(role)  # Generate the user_id based on role

        user = User(username=username, password=password, role=role, user_id=user_id, class_name=class_name)
        db.session.add(user)
        try:
            db.session.commit()
            if role == 'teacher':
                teacher = Teacher(user_id=user.user_id, teacher_name=username)
                db.session.add(teacher)
                db.session.commit()
            flash('User added successfully.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while adding the user. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/edit_user/<string:user_id>', methods=['POST'])
    def edit_user(user_id):
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        user = User.query.get(user_id)
        user.username = request.form['username']
        user.role = request.form['role']
        user.class_name = request.form.get('class_name')

        if 'password' in request.form and request.form['password']:
            user.password = generate_password_hash(request.form['password'])

        try:
            db.session.commit()
            flash('User updated successfully.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while updating the user. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/delete_user/<string:user_id>', methods=['POST'])
    def delete_user(user_id):
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        user = User.query.get(user_id)
        
        if user.role == 'teacher':
            teacher = Teacher.query.filter_by(user_id=user.user_id).first()
            if teacher:
                db.session.delete(teacher)
        
        if user.role == 'student':
            student_timetables = Timetable.query.filter_by(class_name=user.class_name).all()
            for timetable in student_timetables:
                db.session.delete(timetable)

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

        # Check if the class already exists
        existing_class = Class.query.filter_by(class_name=class_name).first()
        if existing_class:
            flash('Class already exists. Please choose a different class name.', 'error')
            return redirect(url_for('admin_dashboard'))

        # Add the new class to the database
        class_ = Class(class_name=class_name)
        db.session.add(class_)
        try:
            db.session.commit()
            flash('Class added successfully.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while adding the class. Please try again.', 'error')
        
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/edit_class/<class_name>', methods=['POST'])
    def edit_class(class_name):
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        class_ = Class.query.filter_by(class_name=class_name).first()  # Use class_name for lookup
        if class_:
            class_.class_name = request.form['class_name']
            try:
                db.session.commit()
                flash('Class updated successfully.', 'success')
            except IntegrityError:
                db.session.rollback()
                flash('An error occurred while updating the class. Please try again.', 'error')
        else:
            flash('Class not found.', 'error')

        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/delete_class/<class_name>', methods=['POST'])
    def delete_class(class_name):
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        class_ = Class.query.filter_by(class_name=class_name).first()  # Use class_name for lookup
        if class_:
            db.session.delete(class_)
            try:
                db.session.commit()
                flash('Class deleted successfully.', 'success')
            except IntegrityError:
                db.session.rollback()
                flash('An error occurred while deleting the class. Please try again.', 'error')
        else:
            flash('Class not found.', 'error')

        return redirect(url_for('admin_dashboard'))


    @app.route('/admin/add_subject', methods=['POST'])
    def add_subject():
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        subject_code = request.form['subject_code']
        subject_name = request.form['subject_name']

        # Check if the subject_code already exists
        existing_subject_code = Subject.query.filter_by(subject_code=subject_code).first()
        if existing_subject_code:
            flash('Subject code already exists. Please choose a different code.', 'add_subject_error')
            return redirect(url_for('admin_dashboard'))

        # Check if the subject_name already exists
        existing_subject_name = Subject.query.filter_by(subject_name=subject_name).first()
        if existing_subject_name:
            flash('Subject name already exists. Please choose a different name.', 'add_subject_error')
            return redirect(url_for('admin_dashboard'))

        # Create a new subject if checks pass
        try:
            subject = Subject(subject_code=subject_code, subject_name=subject_name)
            db.session.add(subject)
            db.session.commit()
            flash('Subject added successfully.', 'add_subject_success')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while adding the subject. Please try again.', 'add_subject_error')

        return redirect(url_for('admin_dashboard'))


    @app.route('/admin/edit_subject/<subject_code>', methods=['GET', 'POST'])
    def edit_subject(subject_code):
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        subject = Subject.query.filter_by(subject_code=subject_code).first()

        if request.method == 'POST':  # If the form is submitted (on Save)
            new_subject_code = request.form['subject_code']
            new_subject_name = request.form['subject_name']

            # Check if the subject_code has changed, and if so, check if the new code already exists
            if new_subject_code != subject.subject_code:
                existing_subject_code = Subject.query.filter_by(subject_code=new_subject_code).first()
                if existing_subject_code:
                    flash('Duplicate entry! The subject code already exists. Please choose a different code.', 'duplicate_error')
                    return redirect(url_for('admin_dashboard'))

                subject.subject_code = new_subject_code  # Update subject_code if it was changed

            # Check if the subject_name has changed, and if so, check if the new name already exists
            if new_subject_name != subject.subject_name:
                existing_subject_name = Subject.query.filter_by(subject_name=new_subject_name).first()
                if existing_subject_name:
                    flash('Duplicate entry! The subject name already exists. Please choose a different name.', 'duplicate_error')
                    return redirect(url_for('admin_dashboard'))

                subject.subject_name = new_subject_name  # Update subject_name if it was changed

            try:
                db.session.commit()
                flash('Subject updated successfully.', 'subject_success')
            except IntegrityError:
                db.session.rollback()  # In case of any error, rollback the changes
                flash('An error occurred while updating the subject. Please try again.', 'subject_error')

            return redirect(url_for('admin_dashboard'))

        return render_template('edit_subject.html', subject=subject)

    @app.route('/admin/delete_subject/<subject_code>', methods=['POST']) 
    def delete_subject(subject_code):
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        subject = Subject.query.filter_by(subject_code=subject_code).first()  # Change from 'get' to 'filter_by' and use subject_code
        if subject:
            db.session.delete(subject)
            try:
                db.session.commit()
                flash('Subject deleted successfully.', 'success')
            except IntegrityError:
                db.session.rollback()
                flash('An error occurred while deleting the subject. Please try again.', 'error')
        else:
            flash('Subject not found.', 'error')

        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/create_timetable', methods=['POST'])
    def create_timetable():
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        class_name = request.form['class_name']  # Use class_name instead of class_name
        day = request.form['day']
        time_slot = request.form['time_slot']
        subject_name = request.form['subject_name']
        teacher_id = request.form['teacher_id']

        # Retrieve the class by class_name
        class_ = Class.query.filter_by(class_name=class_name).first()
        if not class_:
            flash('Invalid class selected.', 'error')
            return redirect(url_for('admin_dashboard'))

        # Retrieve subject_code from subject_name
        subject = Subject.query.filter_by(subject_name=subject_name).first()
        if not subject:
            flash('Invalid subject selected.', 'error')
            return redirect(url_for('admin_dashboard'))

        subject_code = subject.subject_code

        # Check for teacher and classroom conflicts
        conflict_teacher = Timetable.query.filter_by(day=day, time_slot=time_slot, teacher_id=teacher_id).first()
        if conflict_teacher:
            flash('Conflict detected: The same teacher is assigned to another class at this time.', 'error')
            return redirect(url_for('admin_dashboard'))

        conflict_classroom = Timetable.query.filter_by(day=day, time_slot=time_slot, class_name=class_name).first()
        if conflict_classroom:
            flash('Conflict detected: The classroom is already booked at this time.', 'error')
            return redirect(url_for('admin_dashboard'))

        timetable = Timetable(
            class_name=class_name,
            day=day, 
            time_slot=time_slot, 
            subject_code=subject_code, 
            teacher_id=teacher_id
        )
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

        class_name = request.form.get('class_name')  # Use class_name instead of class_name
        if not class_name:
            flash('Class name is missing.', 'error')
            return redirect(url_for('admin_dashboard'))

        timetable.class_name = class_name  # Update class_name
        timetable.day = request.form['day']
        timetable.time_slot = request.form['time_slot']
        subject_name = request.form['subject_name']
        timetable.teacher_id = request.form['teacher_id']

        subject = Subject.query.filter_by(subject_name=subject_name).first()
        if not subject:
            flash('Invalid subject selected.', 'error')
            return redirect(url_for('admin_dashboard'))

        timetable.subject_code = subject.subject_code

        # Check for teacher and classroom conflicts
        conflict_teacher = Timetable.query.filter_by(
            day=timetable.day, time_slot=timetable.time_slot, teacher_id=timetable.teacher_id
        ).filter(Timetable.id != timetable_id).first()

        if conflict_teacher:
            flash('Conflict detected: The same teacher is assigned to another class at this time.', 'error')
            return redirect(url_for('admin_dashboard'))

        conflict_classroom = Timetable.query.filter_by(
            day=timetable.day, time_slot=timetable.time_slot, class_name=timetable.class_name  # Use class_name here
        ).filter(Timetable.id != timetable_id).first()

        if conflict_classroom:
            flash('Conflict detected: The classroom is already booked at this time.', 'error')
            return redirect(url_for('admin_dashboard'))

        try:
            db.session.commit()
            flash('Timetable updated successfully.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while updating the timetable. Please try again.', 'error')

        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/view_timetables')
    def view_timetables():
        print("view_timetables route called")
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        try:
            timetables = Timetable.query.all()
            print(f"Timetables: {timetables}")
            for timetable in timetables:
                class_ = Class.query.filter_by(class_name=timetable.class_name).first()
                print(f"Class: {class_}")
                subject = Subject.query.filter_by(subject_code=timetable.subject_code).first()
                print(f"Subject: {subject}")
                teacher = Teacher.query.get(timetable.teacher_id)
                print(f"Teacher: {teacher}")
            timetables_data = db.session.query(
                Timetable, Class, Subject, Teacher
            ).join(
                Class, Timetable.class_name == Class.class_name
            ).join(
                Subject, Timetable.subject_code == Subject.subject_code
            ).join(
                Teacher, Timetable.teacher_id == Teacher.id
            ).all()
            print(f"Timetables data: {timetables_data}")
        except Exception as e:
            print(f"An error occurred: {e}")
            timetables_data = [] #set to empty list on error.

        classes = Class.query.all()
        subjects = Subject.query.all()
        teachers = Teacher.query.all()

        return render_template('admin_dashboard.html', timetables_data=timetables_data, classes=classes, subjects=subjects, teachers=teachers)

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
        subject_name = request.form['subject_name']  

        teacher = Teacher.query.get(teacher_id)
        subject = Subject.query.filter_by(subject_name=subject_name).first()  # Query by subject_name

        if not teacher:
            flash('Teacher not found.', 'error')
            return redirect(url_for('admin_dashboard'))

        if not subject:
            flash('Subject not found.', 'error')
            return redirect(url_for('admin_dashboard'))

        # Check if the teacher is already assigned to the subject
        if subject not in teacher.subjects:
            teacher.subjects.append(subject)
            try:
                db.session.commit()
                flash('Teacher assigned to subject successfully.', 'success')
            except IntegrityError:
                db.session.rollback()
                flash('An error occurred while assigning the teacher. Please try again.', 'error')
        else:
            flash('This teacher is already assigned to the selected subject.', 'warning')

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
        student = User.query.get(user_id)  # Assuming the 'User' model is used for both students and admins
        timetables = Timetable.query.filter_by(class_name=student.class_name).all()

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
