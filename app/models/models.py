from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, ForeignKey, Text, Time, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    profile_image_id = Column(Integer, ForeignKey("files.id"), nullable=True)

    profile_image = relationship("File", foreign_keys=[profile_image_id])
    student_profile = relationship("Student", back_populates="user", uselist=False)
    group_subjects = relationship("GroupSubject", back_populates="teacher")
    news_authored = relationship("News", back_populates="author")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    academic_year = Column(String)

    students = relationship("Student", back_populates="group")
    group_subjects = relationship("GroupSubject", back_populates="group")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    code = Column(String, unique=True)

    group_subjects = relationship("GroupSubject", back_populates="subject")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    parent_phone = Column(String)
    graduation_year = Column(Integer)

    user = relationship("User", back_populates="student_profile")
    group = relationship("Group", back_populates="students")
    homework_grades = relationship("HomeworkGrade", back_populates="student")
    exam_grades = relationship("ExamGrade", back_populates="student")
    attendance_records = relationship("Attendance", back_populates="student")
    payment_records = relationship("PaymentRecord", back_populates="student")
    monthly_payments = relationship("MonthlyPayment", back_populates="student")


class GroupSubject(Base):
    __tablename__ = "group_subjects"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    teacher_id = Column(Integer, ForeignKey("users.id"))

    group = relationship("Group", back_populates="group_subjects")
    subject = relationship("Subject", back_populates="group_subjects")
    teacher = relationship("User", back_populates="group_subjects")
    homework = relationship("Homework", back_populates="group_subject")
    exams = relationship("Exam", back_populates="group_subject")
    attendance_records = relationship("Attendance", back_populates="group_subject")
    schedules = relationship("Schedule", back_populates="group_subject")


class Homework(Base):
    __tablename__ = "homework"

    id = Column(Integer, primary_key=True, index=True)
    group_subject_id = Column(Integer, ForeignKey("group_subjects.id"))
    title = Column(String)
    description = Column(Text)
    due_date = Column(DateTime)
    max_points = Column(Integer, default=100)
    external_links = Column(JSON, default=list)
    document_ids = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    group_subject = relationship("GroupSubject", back_populates="homework")
    grades = relationship("HomeworkGrade", back_populates="homework")


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    group_subject_id = Column(Integer, ForeignKey("group_subjects.id"))
    title = Column(String)
    description = Column(Text)
    exam_date = Column(DateTime)
    max_points = Column(Integer, default=100)
    external_links = Column(JSON, default=list)
    document_ids = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    group_subject = relationship("GroupSubject", back_populates="exams")
    grades = relationship("ExamGrade", back_populates="exam")


class HomeworkGrade(Base):
    __tablename__ = "homework_grades"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    homework_id = Column(Integer, ForeignKey("homework.id"))
    points = Column(Integer)
    comment = Column(Text, default="")
    graded_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="homework_grades")
    homework = relationship("Homework", back_populates="grades")


class ExamGrade(Base):
    __tablename__ = "exam_grades"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    exam_id = Column(Integer, ForeignKey("exams.id"))
    points = Column(Integer)
    comment = Column(Text, default="")
    graded_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="exam_grades")
    exam = relationship("Exam", back_populates="grades")


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    group_subject_id = Column(Integer, ForeignKey("group_subjects.id"))
    date = Column(Date)
    status = Column(String)

    student = relationship("Student", back_populates="attendance_records")
    group_subject = relationship("GroupSubject", back_populates="attendance_records")


class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    amount = Column(Integer)
    payment_date = Column(Date)
    payment_method = Column(String, default="cash")
    description = Column(String, default="")

    student = relationship("Student", back_populates="payment_records")


class MonthlyPayment(Base):
    __tablename__ = "monthly_payments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    month = Column(Integer)
    year = Column(Integer)
    paid_amount = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    due_date = Column(Date)

    student = relationship("Student", back_populates="monthly_payments")


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(Text)
    author_id = Column(Integer, ForeignKey("users.id"))
    external_links = Column(JSON, default=list)
    image_ids = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_published = Column(Boolean, default=True)

    author = relationship("User", back_populates="news_authored")


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    upload_date = Column(DateTime, default=datetime.utcnow)
    related_id = Column(Integer)
    file_type = Column(String)

    uploader = relationship("User", foreign_keys=[uploaded_by])


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    group_subject_id = Column(Integer, ForeignKey("group_subjects.id"))
    day = Column(Integer)
    start_time = Column(Time)
    end_time = Column(Time)
    room = Column(String)

    group_subject = relationship("GroupSubject", back_populates="schedules")