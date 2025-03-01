from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response  
from werkzeug.security import generate_password_hash, check_password_hash  
from sqlalchemy.exc import IntegrityError  
from database import db  
from models import User, Teacher, Class, Subject, Timetable, generate_user_id, db, teacher_subject
from util import generate_pdf, generate_conflict_report, generate_timetable_report  
from event_handler import trigger_event  
  
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
  
            user_id = generate_user_id(role)  
            user = User(username=username, password=password, role=role, user_id=user_id)  
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
  
            user = User.query.filter_by(username=username).first()  
  
            if user:  
                if check_password_hash(user.password, password):  
                    session['user_id'] = user.user_id  
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
    
        teacher_assignments = db.session.query(  
            teacher_subject.c.teacher_id,  
            teacher_subject.c.subject_code,  
            Teacher.teacher_name,  
            Subject.subject_name  
        ).join(  
            Teacher, teacher_subject.c.teacher_id == Teacher.id  
        ).join(  
            Subject, teacher_subject.c.subject_code == Subject.subject_code  
        ).all()  
    
        total_users = len(users)  
        total_classes = len(classes)  
        total_subjects = len(subjects)  
        total_timetables = len(Timetable.query.all())  
    
        recent_logs = []  
    
        try:  
            timetables_data = db.session.query(  
                Timetable, Class, Subject, Teacher  
            ).join(  
                Class, Timetable.class_name == Class.class_name  
            ).join(  
                Subject, Timetable.subject_code == Subject.subject_code  
            ).join(  
                Teacher, Timetable.teacher_id == Teacher.id  
            ).all()  
        except Exception as e:  
            print(f"An error occurred: {e}")  
            timetables_data = []  
    
        return render_template(  
            'admin_dashboard.html',  
            users=users,  
            classes=classes,  
            teachers=teachers,  
            subjects=subjects,  
            total_users=total_users,  
            total_classes=total_classes,  
            total_subjects=total_subjects,  
            total_timetables=total_timetables,  
            recent_logs=recent_logs,  
            teacher_assignments=teacher_assignments,  
            timetables_data=timetables_data  
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


    @app.route('/admin/assign_teacher_subject', methods=['POST'])
    def assign_teacher_subject():
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))

        teacher_id = request.form['teacher_id']
        subject_name = request.form['subject_name']  
  
        teacher = Teacher.query.get(teacher_id)  
        subject = Subject.query.filter_by(subject_name=subject_name).first()  
  
        if not teacher:  
            flash('Teacher not found.', 'error')  
            return redirect(url_for('admin_dashboard'))  
        if not subject:  
            flash('Subject not found.', 'error')  
            return redirect(url_for('admin_dashboard'))  
  
        assigned_teacher = db.session.query(Teacher).join(teacher_subject).filter(teacher_subject.c.subject_code == subject.subject_code).first()  
        if assigned_teacher:  
            flash(f'This subject is already assigned to {assigned_teacher.teacher_name}.', 'warning')  
            return redirect(url_for('admin_dashboard'))  
  
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
  
    @app.route('/admin/remove_teacher_assignment', methods=['POST'])  
    def remove_teacher_assignment():  
        if session.get('user_role') != 'admin':  
            return redirect(url_for('index'))  
  
        teacher_id = request.form['teacher_id']  
        subject_code = request.form['subject_code']  
  
        assignment = db.session.query(teacher_subject).filter(  
            teacher_subject.c.teacher_id == teacher_id,  
            teacher_subject.c.subject_code == subject_code  
        ).first()  
  
        if assignment:  
            try:  
                db.session.execute(  
                    teacher_subject.delete().where(  
                        teacher_subject.c.teacher_id == teacher_id,  
                        teacher_subject.c.subject_code == subject_code  
                    )  
                )  
                db.session.commit()  
                flash('Teacher assignment removed successfully.', 'success')  
            except IntegrityError:  
                db.session.rollback()  
                flash('An error occurred while removing the assignment. Please try again.', 'error')  
        else:  
            flash('Assignment not found.', 'error')  
  
        return redirect(url_for('admin_dashboard'))  

    @app.route('/admin/reassign_teacher_subjects', methods=['POST'])  
    def reassign_teacher_subjects():  
        if session.get('user_role') != 'admin':  
            return redirect(url_for('index'))  
    
        old_teacher_id = request.form['old_teacher_id']  
        new_teacher_name = request.form['new_teacher_name']  
    
        new_teacher = Teacher.query.filter_by(teacher_name=new_teacher_name).first()  
    
        if not new_teacher:  
            flash('New teacher not found.', 'error')  
            return redirect(url_for('admin_dashboard'))  
    
        assignments = db.session.query(teacher_subject).filter(  
            teacher_subject.c.teacher_id == old_teacher_id  
        ).all()  
    
        if assignments:  
            try:  
                for assignment in assignments:  
                    db.session.execute(  
                        teacher_subject.update().where(  
                            teacher_subject.c.teacher_id == old_teacher_id,  
                            teacher_subject.c.subject_code == assignment.subject_code  
                        ).values(teacher_id=new_teacher.id)  
                    )  
                    # Update the timetable entries as well  
                    timetables = Timetable.query.filter_by(teacher_id=old_teacher_id, subject_code=assignment.subject_code).all()  
                    for timetable in timetables:  
                        timetable.teacher_id = new_teacher.id  
                        db.session.commit()  
                db.session.commit()  
                flash('All subjects reassigned successfully.', 'success')  
            except IntegrityError:  
                db.session.rollback()  
                flash('An error occurred while reassigning the subjects. Please try again.', 'error')  
        else:  
            flash('No assignments found for the old teacher.', 'error')  
    
        return redirect(url_for('admin_dashboard'))  

  
    @app.route('/admin/view_timetables')  
    def view_timetables():  
        if session.get('user_role') != 'admin':  
            return redirect(url_for('index'))  
  
        try:  
            teachers = Teacher.query.all()  
            teacher_assignments = {}  
            assignments = db.session.query(  
                teacher_subject.c.teacher_id,  
                teacher_subject.c.subject_code,  
                Subject.subject_name,  
                Teacher.teacher_name  
            ).join(  
                Subject, teacher_subject.c.subject_code == Subject.subject_code  
            ).join(  
                Teacher, teacher_subject.c.teacher_id == Teacher.id  
            ).all()  
  
            for assignment in assignments:  
                teacher_id = assignment.teacher_id  
                if teacher_id not in teacher_assignments:  
                    teacher_assignments[teacher_id] = {  
                        'teacher_name': assignment.teacher_name,  
                        'subjects': []  
                    }  
                teacher_assignments[teacher_id]['subjects'].append({  
                    'subject_code': assignment.subject_code,  
                    'subject_name': assignment.subject_name  
                })  
        except Exception as e:  
            print(f"An error occurred: {e}")  
            teachers = []  
            teacher_assignments = {}  
  
        return render_template('admin_dashboard.html', teachers=teachers, teacher_assignments=teacher_assignments)  
  
    @app.route('/admin/create_timetable', methods=['POST'])  
    def create_timetable():  
        if session.get('user_role') != 'admin':  
            return redirect(url_for('index'))  
  
        class_name = request.form.get('class_name')  
        day = request.form.get('day')  
        time_slot = request.form.get('time_slot')  
        subject_name = request.form.get('subject_name')  
        teacher_id = request.form.get('teacher_id')  
  
        if not class_name or not day or not time_slot or not subject_name or not teacher_id:  
            flash('All fields are required.', 'error')  
            return redirect(url_for('admin_dashboard'))  
  
        subject = Subject.query.filter_by(subject_name=subject_name).first()  
        if not subject:  
            flash('Invalid subject selected.', 'error')  
            return redirect(url_for('admin_dashboard'))  
  
        timetable = Timetable(class_name=class_name, day=day, time_slot=time_slot, subject_code=subject.subject_code, teacher_id=teacher_id)  
  
        conflict_teacher = Timetable.query.filter_by(day=day, time_slot=time_slot, teacher_id=teacher_id).first()  
        if conflict_teacher:  
            flash('Conflict detected: The same teacher is assigned to another class at this time.', 'error')  
            return redirect(url_for('admin_dashboard'))  
  
        conflict_classroom = Timetable.query.filter_by(day=day, time_slot=time_slot, class_name=class_name).first()  
        if conflict_classroom:  
            flash('Conflict detected: The same classroom is used for another class at this time.', 'error')  
            return redirect(url_for('admin_dashboard'))  
  
        db.session.add(timetable)  
        db.session.commit()  
        flash('Timetable created successfully.', 'success')  
        return redirect(url_for('admin_dashboard'))  
  
    @app.route('/admin/edit_timetable/<int:timetable_id>', methods=['POST'])  
    def edit_timetable(timetable_id):  
        if session.get('user_role') != 'admin':  
            return redirect(url_for('index'))  
  
        timetable = Timetable.query.get(timetable_id)  
        if not timetable:  
            flash('Timetable not found.', 'error')  
            return redirect(url_for('admin_dashboard'))  
  
        class_name = request.form.get('class_name')  
        day = request.form.get('day')  
        time_slot = request.form.get('time_slot')  
        subject_name = request.form.get('subject_name')  
        teacher_id = request.form.get('teacher_id')  
  
        if not class_name or not day or not time_slot or not subject_name or not teacher_id:  
            flash('All fields are required.', 'error')  
            return redirect(url_for('admin_dashboard'))  
  
        subject = Subject.query.filter_by(subject_name=subject_name).first()  
        if not subject:  
            flash('Invalid subject selected.', 'error')  
            return redirect(url_for('admin_dashboard'))  
  
        timetable.class_name = class_name  
        timetable.day = day  
        timetable.time_slot = time_slot  
        timetable.subject_code = subject.subject_code  
        timetable.teacher_id = teacher_id  
  
        conflict_teacher = Timetable.query.filter_by(day=day, time_slot=time_slot, teacher_id=teacher_id).filter(Timetable.id != timetable_id).first()  
        if conflict_teacher:  
            flash('Conflict detected: The same teacher is assigned to another class at this time.', 'error')  
            return redirect(url_for('admin_dashboard'))  
  
        conflict_classroom = Timetable.query.filter_by(day=day, time_slot=time_slot, class_name=class_name).filter(Timetable.id != timetable_id).first()  
        if conflict_classroom:  
            flash('Conflict detected: The same classroom is used for another class at this time.', 'error')  
            return redirect(url_for('admin_dashboard'))  
  
        db.session.commit()  
        flash('Timetable updated successfully.', 'success')  
        return redirect(url_for('admin_dashboard'))  
  
    @app.route('/admin/delete_timetable/<int:timetable_id>', methods=['POST'])  
    def delete_timetable(timetable_id):  
        if session.get('user_role') != 'admin':  
            return redirect(url_for('index'))  
  
        timetable = Timetable.query.get(timetable_id)  
        if not timetable:  
            flash('Timetable not found.', 'error')  
            return redirect(url_for('admin_dashboard'))  
  
        db.session.delete(timetable)  
        db.session.commit()  
        flash('Timetable deleted successfully.', 'success')  
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/edit_teacher_assignment/<teacher_id>/<subject_code>', methods=['POST'])  
    def edit_teacher_assignment(teacher_id, subject_code):  
        if session.get('user_role') != 'admin':  
            return redirect(url_for('index'))  
    
        new_subject_name = request.form['subject_name']  
        subject = Subject.query.filter_by(subject_code=subject_code).first()  
    
        if subject:  
            try:  
                subject.subject_name = new_subject_name  
                db.session.commit()  
    
                # Update the timetables as well  
                timetables = Timetable.query.filter_by(teacher_id=teacher_id, subject_code=subject_code).all()  
                for timetable in timetables:  
                    timetable.subject_code = subject.subject_code  
                    db.session.commit()  
    
                flash('Subject name and related timetables updated successfully.', 'success')  
            except IntegrityError:  
                db.session.rollback()  
                flash('An error occurred while updating the subject. Please try again.', 'error')  
        else:  
            flash('Subject not found.', 'error')  
  
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
