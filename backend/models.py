from database import db
from sqlalchemy import event
from sqlalchemy.orm import validates
from sqlalchemy.exc import IntegrityError


# Function to get the last user ID and generate a new ID
def generate_user_id(role):
    if role == 'student':
        last_user = db.session.query(User).filter(User.role == 'student').order_by(User.user_id.desc()).first()
        new_id = int(last_user.user_id[1:]) + 1 if last_user else 1
        return f"S{new_id:02d}"  # Generate student ID like S01, S02, etc.
    elif role == 'teacher':
        last_user = db.session.query(User).filter(User.role == 'teacher').order_by(User.user_id.desc()).first()
        new_id = int(last_user.user_id[1:]) + 1 if last_user else 1
        return f"T{new_id:02d}"  # Generate teacher ID like T01, T02, etc.
    elif role == 'admin':
        admins_count = db.session.query(User).filter(User.role == 'admin').count()
        if admins_count >= 3:
            raise IntegrityError('Maximum number of admins reached.')
        return f"A{admins_count + 1:02d}"  # Generate admin ID like A01, A02, etc.


class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.String(50), primary_key=True)  # 'user_id' will be the primary key and store the unique ID
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Enum('admin', 'teacher', 'student'), nullable=False)
    class_name = db.Column(db.String(50), db.ForeignKey('class.class_name'), nullable=True) 
    class_ = db.relationship('Class', backref='students', lazy=True)
    teacher = db.relationship('Teacher', backref='user', uselist=False, cascade="all, delete-orphan")

    @validates('username')
    def validate_username(self, key, value):
        return value


class Subject(db.Model):
    __tablename__ = 'subjects'

    subject_code = db.Column(db.String(50), primary_key=True)  # 'subject_code' as the primary key
    subject_name = db.Column(db.String(100), nullable=False)

    @validates('subject_code')
    def validate_subject_code(self, key, value):
        return value

    @validates('subject_name')
    def validate_subject_name(self, key, value):
        return value

    def __repr__(self):
        return f"<Subject(subject_code={self.subject_code}, subject_name={self.subject_name})>"


# Association table for the many-to-many relationship between Teacher and Subject
teacher_subject = db.Table('teacher_subject',  
    db.Column('teacher_id', db.Integer, db.ForeignKey('teacher.id', ondelete="CASCADE"), primary_key=False),  
    db.Column('subject_code', db.String(50), db.ForeignKey('subjects.subject_code', ondelete="CASCADE"), primary_key=False)  
)
class Teacher(db.Model):
    __tablename__ = 'teacher'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.user_id'), nullable=False)
    teacher_name = db.Column(db.String(50), nullable=False)
    class_name = db.Column(db.String(50), db.ForeignKey('class.class_name'), nullable=True)  
    class_ = db.relationship('Class', backref='teachers', lazy=True)

    # Define the relationship to subjects with the secondary table and explicit joins
    subjects = db.relationship(
    'Subject',
    secondary=teacher_subject,
    lazy='subquery',
    backref=db.backref('teachers', lazy=True),
    primaryjoin=id == teacher_subject.c.teacher_id,
    secondaryjoin=Subject.subject_code == teacher_subject.c.subject_code
)

class Class(db.Model):
    __tablename__ = 'class'
    id = db.Column(db.Integer, primary_key=True)  # Primary key (usually an integer ID)
    class_name = db.Column(db.String(20), unique=True, nullable=False)  # class_name is unique


class Timetable(db.Model):  
    __tablename__ = 'timetable'  
    id = db.Column(db.Integer, primary_key=True)  
    class_name = db.Column(db.String(50), db.ForeignKey('class.class_name'), nullable=False)  # Referencing class_name  
    day = db.Column(db.Enum('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'), nullable=False)  
    time_slot = db.Column(db.String(50), nullable=False)  
    subject_code = db.Column(db.String(50), db.ForeignKey('subjects.subject_code'), nullable=False)  
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)  
  
    # Relationships  
    class_ = db.relationship('Class', backref='timetables', lazy=True)  
    subject = db.relationship('Subject', backref='timetables', lazy=True)  
    teacher = db.relationship('Teacher', backref='timetables', lazy=True)  


class StudentTimetable(db.Model):
    __tablename__ = 'student_timetable'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), db.ForeignKey('user.user_id'), nullable=False)
    timetable_id = db.Column(db.Integer, db.ForeignKey('timetable.id'), nullable=False)
    student = db.relationship('User', backref='student_timetables', lazy=True)
    timetable = db.relationship('Timetable', backref='student_timetables', lazy=True)
