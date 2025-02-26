from io import BytesIO
from flask import current_app
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from models import User, Timetable, Subject, Teacher, Class

def generate_pdf(user_id):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    user = User.query.get(user_id)
    if user.role == 'student':
        class_id = user.class_id
        timetables = Timetable.query.filter_by(class_id=class_id).all()
    elif user.role == 'teacher':
        teacher = Teacher.query.filter_by(user_id=user_id).first()
        timetables = Timetable.query.filter_by(teacher_id=teacher.id).all()
    else:
        timetables = []

    p.drawString(100, height - 100, f"Timetable for {user.username}")
    y = height - 150

    for timetable in timetables:
        subject = timetable.subject.subject_name
        teacher = timetable.teacher.teacher_name
        p.drawString(100, y, f"{timetable.day} {timetable.time_slot} - {subject} ({teacher})")
        y -= 20

    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer.getvalue()

def generate_conflict_report():
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    conflicts = detect_conflicts()
    p.drawString(100, height - 100, "Conflict Report")
    y = height - 150

    for conflict in conflicts:
        p.drawString(100, y, conflict)
        y -= 20

    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer.getvalue()

def generate_timetable_report():
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    timetables = Timetable.query.all()
    p.drawString(100, height - 100, "Timetable Report")
    y = height - 150

    for timetable in timetables:
        class_name = timetable.class_.class_name
        subject = timetable.subject.subject_name
        teacher = timetable.teacher.teacher_name
        p.drawString(100, y, f"{class_name} - {timetable.day} {timetable.time_slot} - {subject} ({teacher})")
        y -= 20

    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer.getvalue()

def detect_conflicts():
    conflicts = []
    timetables = Timetable.query.all()

    teacher_schedule = {}
    class_schedule = {}

    for timetable in timetables:
        # Check for teacher conflicts
        teacher_key = (timetable.teacher_id, timetable.day, timetable.time_slot)
        if teacher_key in teacher_schedule:
            conflict = f"Teacher {timetable.teacher.teacher_name} has a conflict on {timetable.day} at {timetable.time_slot} for class {timetable.class_.class_name} and {teacher_schedule[teacher_key]}"
            conflicts.append(conflict)
        else:
            teacher_schedule[teacher_key] = timetable.class_.class_name

        # Check for class conflicts
        class_key = (timetable.class_id, timetable.day, timetable.time_slot)
        if class_key in class_schedule:
            conflict = f"Classroom {timetable.class_.class_name} has a conflict on {timetable.day} at {timetable.time_slot} for subject {timetable.subject.subject_name} and {class_schedule[class_key]}"
            conflicts.append(conflict)
        else:
            class_schedule[class_key] = timetable.subject.subject_name

    return conflicts