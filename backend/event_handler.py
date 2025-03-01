from flask import flash  
from database import db  
from models import Class, Subject, User, Teacher, Timetable  
  
def handle_event(event_type, data):  
    if event_type == 'class_updated':  
        class_ = Class.query.filter_by(class_name=data['class_name']).first()  
        if class_:  
            class_.class_name = data['new_class_name']  
            db.session.commit()  
            flash('Class updated successfully across all sections.', 'success')  
        else:  
            flash('Class not found.', 'error')  
    elif event_type == 'subject_updated':  
        subject = Subject.query.filter_by(subject_code=data['subject_code']).first()  
        if subject:  
            subject.subject_name = data['new_subject_name']  
            db.session.commit()  
            flash('Subject updated successfully across all sections.', 'success')  
        else:  
            flash('Subject not found.', 'error')  
    elif event_type == 'user_updated':  
        user = User.query.filter_by(user_id=data['user_id']).first()  
        if user:  
            user.username = data['new_username']  
            db.session.commit()  
            flash('User updated successfully across all sections.', 'success')  
        else:  
            flash('User not found.', 'error')  
    elif event_type == 'teacher_updated':  
        teacher = Teacher.query.filter_by(id=data['teacher_id']).first()  
        if teacher:  
            teacher.teacher_name = data['new_teacher_name']  
            db.session.commit()  
            flash('Teacher updated successfully across all sections.', 'success')  
              
            # Update the timetable  
            timetables = Timetable.query.filter_by(teacher_id=teacher.id).all()  
            for timetable in timetables:  
                timetable.teacher_id = teacher.id  # Assuming you store teacher_id in the timetable  
                db.session.commit()  
            flash('Timetable updated successfully.', 'success')  
        else:  
            flash('Teacher not found.', 'error')  
    # Add more event types as needed  
  
def trigger_event(event_type, data):  
    handle_event(event_type, data)  