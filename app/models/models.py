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


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    academic_year = Column(String)


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    code = Column(String, unique=True)


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    parent_phone = Column(String)
    graduation_year = Column(Integer)


class GroupSubject(Base):
    __tablename__ = "group_subjects"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    teacher_id = Column(Integer, ForeignKey("users.id"))


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


class HomeworkGrade(Base):
    __tablename__ = "homework_grades"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    homework_id = Column(Integer, ForeignKey("homework.id"))
    points = Column(Integer)
    comment = Column(Text, default="")
    graded_at = Column(DateTime, default=datetime.utcnow)


class ExamGrade(Base):
    __tablename__ = "exam_grades"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    exam_id = Column(Integer, ForeignKey("exams.id"))
    points = Column(Integer)
    comment = Column(Text, default="")
    graded_at = Column(DateTime, default=datetime.utcnow)


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    group_subject_id = Column(Integer, ForeignKey("group_subjects.id"))
    date = Column(Date)
    status = Column(String)


class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    amount = Column(Integer)
    payment_date = Column(Date)
    payment_method = Column(String, default="cash")
    description = Column(String, default="")


class MonthlyPayment(Base):
    __tablename__ = "monthly_payments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    month = Column(Integer)
    year = Column(Integer)
    paid_amount = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    due_date = Column(Date)


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


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    group_subject_id = Column(Integer, ForeignKey("group_subjects.id"))
    day = Column(Integer)
    start_time = Column(Time)
    end_time = Column(Time)
    room = Column(String)