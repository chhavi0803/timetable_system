from database import db

# Association table for the many-to-many relationship between Teacher and Subject
teacher_subject = db.Table('teacher_subject',
    db.Column('teacher_id', db.Integer, db.ForeignKey('teacher.id'), primary_key=True),
    db.Column('subject_id', db.Integer, db.ForeignKey('subject.id'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Enum('admin', 'teacher', 'student'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=True)
    class_ = db.relationship('Class', backref='students', lazy=True)
    teacher = db.relationship('Teacher', backref='user', uselist=False)

class Teacher(db.Model):
    __tablename__ = 'teacher'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    teacher_name = db.Column(db.String(50), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=True)
    class_ = db.relationship('Class', backref='teachers', lazy=True)
    subjects = db.relationship('Subject', secondary=teacher_subject, lazy='subquery',
        backref=db.backref('teachers', lazy=True))

class Class(db.Model):
    __tablename__ = 'class'
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(50), unique=True, nullable=False)

class Subject(db.Model):
    __tablename__ = 'subject'
    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(50), unique=True, nullable=False)

class Timetable(db.Model):
    __tablename__ = 'timetable'
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    day = db.Column(db.Enum('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'), nullable=False)
    time_slot = db.Column(db.String(50), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    class_ = db.relationship('Class', backref='timetables', lazy=True)
    subject = db.relationship('Subject', backref='timetables', lazy=True)
    teacher = db.relationship('Teacher', backref='timetables', lazy=True)

class StudentTimetable(db.Model):
    __tablename__ = 'student_timetable'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timetable_id = db.Column(db.Integer, db.ForeignKey('timetable.id'), nullable=False)
    student = db.relationship('User', backref='student_timetables', lazy=True)
    timetable = db.relationship('Timetable', backref='student_timetables', lazy=True)