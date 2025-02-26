from fpdf import FPDF
from models import Timetable

def generate_pdf(user_id):
    # Generate a PDF for the user's timetable
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add content to PDF
    timetables = Timetable.query.filter_by(user_id=user_id).all()
    for timetable in timetables:
        pdf.cell(200, 10, txt=f"{timetable.day} - {timetable.time_slot} - {timetable.subject.subject_name} - {timetable.teacher.teacher_name}", ln=True)

    return pdf.output(dest="S").encode('latin1')

def generate_conflict_report():
    # Generate a conflict report PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add content to PDF (dummy content for now)
    pdf.cell(200, 10, txt="Conflict Report", ln=True)
    pdf.cell(200, 10, txt="No conflicts detected.", ln=True)

    return pdf.output(dest="S").encode('latin1')

def generate_timetable_report():
    # Generate a timetable report PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add content to PDF
    timetables = Timetable.query.all()
    for timetable in timetables:
        pdf.cell(200, 10, txt=f"{timetable.class_.class_name} - {timetable.day} - {timetable.time_slot} - {timetable.subject.subject_name} - {timetable.teacher.teacher_name}", ln=True)

    return pdf.output(dest="S").encode('latin1')