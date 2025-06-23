# app/models.py
"""
Complete SQLAlchemy models for Education Center Management System
Designed with passion for clean, efficient, and scalable data structure!
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, Float, Date, UniqueConstraint, \
    Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid():
    """Generate UUID4 string for primary keys"""
    return str(uuid.uuid4())


class User(Base):
    """
    Core User model - handles all user types with role-based differentiation
    Phone numbers are unique per role (admin, teacher, student, parent)
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    role = Column(String(20), nullable=False, index=True)  # admin, teacher, student, parent
    phone = Column(Integer, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Unique constraint for role + phone combination
    __table_args__ = (
        UniqueConstraint('role', 'phone', name='unique_role_phone'),
        Index('idx_user_role_phone', 'role', 'phone'),
    )

    # Relationships
    student_profile = relationship("Student", back_populates="user", uselist=False)
    parent_profile = relationship("Parent", back_populates="user", uselist=False)
    teacher_profile = relationship("Teacher", back_populates="user", uselist=False)
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    files = relationship("File", back_populates="uploaded_by_user", cascade="all, delete-orphan")


class Group(Base):
    """Groups/Classes in the education center"""
    __tablename__ = "groups"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    students = relationship("Student", back_populates="group")
    group_subjects = relationship("GroupSubject", back_populates="group", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="group", cascade="all, delete-orphan")
    homework = relationship("Homework", back_populates="group", cascade="all, delete-orphan")
    exams = relationship("Exam", back_populates="group", cascade="all, delete-orphan")


class Subject(Base):
    """Academic subjects taught in the center"""
    __tablename__ = "subjects"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    group_subjects = relationship("GroupSubject", back_populates="subject", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="subject", cascade="all, delete-orphan")
    homework = relationship("Homework", back_populates="subject", cascade="all, delete-orphan")
    exams = relationship("Exam", back_populates="subject", cascade="all, delete-orphan")


class Student(Base):
    """Student profile extending User"""
    __tablename__ = "students"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    parent_id = Column(String, ForeignKey("parents.id"), nullable=True)
    graduation_year = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="student_profile")
    group = relationship("Group", back_populates="students")
    parent = relationship("Parent", back_populates="students")
    grades = relationship("Grade", back_populates="student", cascade="all, delete-orphan")
    attendance_records = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="student", cascade="all, delete-orphan")
    monthly_payment_status = relationship("MonthlyPaymentStatus", back_populates="student",
                                          cascade="all, delete-orphan")


class Parent(Base):
    """Parent profile extending User"""
    __tablename__ = "parents"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="parent_profile")
    students = relationship("Student", back_populates="parent")


class Teacher(Base):
    """Teacher profile extending User"""
    __tablename__ = "teachers"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="teacher_profile")
    group_subjects = relationship("GroupSubject", back_populates="teacher")
    schedules = relationship("Schedule", back_populates="teacher")
    homework = relationship("Homework", back_populates="teacher")
    exams = relationship("Exam", back_populates="teacher")
    grades_given = relationship("Grade", back_populates="graded_by_teacher")
    attendance_recorded = relationship("Attendance", back_populates="teacher")


class GroupSubject(Base):
    """Many-to-many relationship between groups and subjects with assigned teacher"""
    __tablename__ = "group_subjects"

    id = Column(String, primary_key=True, default=generate_uuid)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    subject_id = Column(String, ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(String, ForeignKey("teachers.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint: one teacher per group-subject combination
    __table_args__ = (
        UniqueConstraint('group_id', 'subject_id', name='unique_group_subject'),
        Index('idx_group_subject_teacher', 'group_id', 'subject_id', 'teacher_id'),
    )

    # Relationships
    group = relationship("Group", back_populates="group_subjects")
    subject = relationship("Subject", back_populates="group_subjects")
    teacher = relationship("Teacher", back_populates="group_subjects")


class Schedule(Base):
    """Weekly schedule for group-subject combinations"""
    __tablename__ = "schedules"

    id = Column(String, primary_key=True, default=generate_uuid)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    subject_id = Column(String, ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(String, ForeignKey("teachers.id"), nullable=False)
    day_of_week = Column(String(10), nullable=False)  # monday, tuesday, etc.
    start_time = Column(String(5), nullable=False)  # HH:MM format
    end_time = Column(String(5), nullable=False)  # HH:MM format
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint: no time conflicts for same group
    __table_args__ = (
        UniqueConstraint('group_id', 'day_of_week', 'start_time', name='unique_schedule_slot'),
        Index('idx_schedule_group_day', 'group_id', 'day_of_week'),
    )

    # Relationships
    group = relationship("Group", back_populates="schedules")
    subject = relationship("Subject", back_populates="schedules")
    teacher = relationship("Teacher", back_populates="schedules")


class Homework(Base):
    """Homework assignments created by teachers"""
    __tablename__ = "homework"

    id = Column(String, primary_key=True, default=generate_uuid)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    subject_id = Column(String, ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(String, ForeignKey("teachers.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    external_links = Column(Text, nullable=True)  # JSON array as string
    due_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    group = relationship("Group", back_populates="homework")
    subject = relationship("Subject", back_populates="homework")
    teacher = relationship("Teacher", back_populates="homework")
    grades = relationship("Grade", back_populates="homework", cascade="all, delete-orphan")
    files = relationship("File", back_populates="homework", cascade="all, delete-orphan")


class Exam(Base):
    """Exams created by teachers"""
    __tablename__ = "exams"

    id = Column(String, primary_key=True, default=generate_uuid)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    subject_id = Column(String, ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(String, ForeignKey("teachers.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    external_links = Column(Text, nullable=True)  # JSON array as string
    exam_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    group = relationship("Group", back_populates="exams")
    subject = relationship("Subject", back_populates="exams")
    teacher = relationship("Teacher", back_populates="exams")
    grades = relationship("Grade", back_populates="exam", cascade="all, delete-orphan")
    files = relationship("File", back_populates="exam", cascade="all, delete-orphan")


class Grade(Base):
    """Grades for homework and exams"""
    __tablename__ = "grades"

    id = Column(String, primary_key=True, default=generate_uuid)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    subject_id = Column(String, ForeignKey("subjects.id"), nullable=False)
    homework_id = Column(String, ForeignKey("homework.id"), nullable=True)
    exam_id = Column(String, ForeignKey("exams.id"), nullable=True)
    teacher_id = Column(String, ForeignKey("teachers.id"), nullable=False)
    grade = Column(Float, nullable=False)
    max_grade = Column(Float, nullable=False, default=100.0)
    comment = Column(Text, nullable=True)
    graded_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Constraints: must have either homework_id or exam_id, not both
    __table_args__ = (
        Index('idx_grade_student_subject', 'student_id', 'subject_id', 'graded_at'),
    )

    # Relationships
    student = relationship("Student", back_populates="grades")
    homework = relationship("Homework", back_populates="grades")
    exam = relationship("Exam", back_populates="grades")
    graded_by_teacher = relationship("Teacher", back_populates="grades_given")


class Attendance(Base):
    """Student attendance records"""
    __tablename__ = "attendance"

    id = Column(String, primary_key=True, default=generate_uuid)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    subject_id = Column(String, ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(String, ForeignKey("teachers.id"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String(10), nullable=False)  # present, absent, late
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint: one attendance record per student per subject per date
    __table_args__ = (
        UniqueConstraint('student_id', 'subject_id', 'date', name='unique_attendance_record'),
        Index('idx_attendance_date_student', 'date', 'student_id'),
    )

    # Relationships
    student = relationship("Student", back_populates="attendance_records")
    teacher = relationship("Teacher", back_populates="attendance_recorded")


class Payment(Base):
    """Payment records for students"""
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=generate_uuid)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    amount = Column(Float, nullable=False)
    month = Column(String(7), nullable=False)  # YYYY-MM format
    year = Column(Integer, nullable=False)
    payment_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    recorded_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_payment_student_month', 'student_id', 'month', 'year'),
        Index('idx_payment_date', 'payment_date'),
    )

    # Relationships
    student = relationship("Student", back_populates="payments")


class MonthlyPaymentStatus(Base):
    """Monthly payment status tracking"""
    __tablename__ = "monthly_payment_status"

    id = Column(String, primary_key=True, default=generate_uuid)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    month = Column(String(7), nullable=False)  # YYYY-MM format
    year = Column(Integer, nullable=False)
    is_fully_paid = Column(Boolean, default=False)
    total_amount_due = Column(Float, nullable=True)
    total_amount_paid = Column(Float, default=0.0)
    updated_by = Column(String, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint: one status record per student per month
    __table_args__ = (
        UniqueConstraint('student_id', 'month', 'year', name='unique_monthly_status'),
        Index('idx_monthly_status_student', 'student_id', 'year', 'month'),
    )

    # Relationships
    student = relationship("Student", back_populates="monthly_payment_status")


class News(Base):
    """News and announcements"""
    __tablename__ = "news"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    external_links = Column(Text, nullable=True)  # JSON array as string
    published_by = Column(String, ForeignKey("users.id"), nullable=False)
    published_at = Column(DateTime, default=datetime.utcnow)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    files = relationship("File", back_populates="news", cascade="all, delete-orphan")


class Notification(Base):
    """User notifications"""
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(20), nullable=False)  # payment, grade, homework, exam, news, general
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_notification_user_read', 'user_id', 'is_read', 'created_at'),
    )

    # Relationships
    user = relationship("User", back_populates="notifications")


class File(Base):
    """File management for uploads"""
    __tablename__ = "files"

    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(20), nullable=False)  # image, document
    mime_type = Column(String(100), nullable=False)
    uploaded_by = Column(String, ForeignKey("users.id"), nullable=False)

    # Foreign keys for different content types (nullable)
    homework_id = Column(String, ForeignKey("homework.id"), nullable=True)
    exam_id = Column(String, ForeignKey("exams.id"), nullable=True)
    news_id = Column(String, ForeignKey("news.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # For profile pictures

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    uploaded_by_user = relationship("User", back_populates="files", foreign_keys=[uploaded_by])
    homework = relationship("Homework", back_populates="files")
    exam = relationship("Exam", back_populates="files")
    news = relationship("News", back_populates="files")


# Create all tables function
def create_all_tables(engine):
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)