from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, ForeignKey, Text, Time, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, index=True)
    first_name = Column(String)
    last_name = Column(String)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, index=True)
    profile_image_id = Column(Integer, ForeignKey("files.id"))

    profile_image = relationship("File", foreign_keys=[profile_image_id])
    student_profile = relationship("Student", back_populates="user", uselist=False)
    group_subjects = relationship("GroupSubject", back_populates="teacher")
    notifications = relationship("Notification", back_populates="user", order_by="desc(Notification.created_at)")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String)
    message = Column(Text)
    type = Column(String, index=True)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index('idx_notification_user_read', 'user_id', 'is_read'),
        Index('idx_notification_type_date', 'type', 'created_at'),
    )


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    upload_date = Column(DateTime, default=datetime.utcnow)
    related_id = Column(Integer)
    file_type = Column(String, index=True)


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    academic_year = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    students = relationship("Student", back_populates="group")
    group_subjects = relationship("GroupSubject", back_populates="group")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    code = Column(String, unique=True, index=True)

    group_subjects = relationship("GroupSubject", back_populates="subject")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), index=True)
    parent_phone = Column(String, index=True)
    graduation_year = Column(Integer, index=True)

    user = relationship("User", back_populates="student_profile")
    group = relationship("Group", back_populates="students")
    homework_grades = relationship("HomeworkGrade", back_populates="student")
    exam_grades = relationship("ExamGrade", back_populates="student")
    attendance_records = relationship("Attendance", back_populates="student")
    payment_records = relationship("PaymentRecord", back_populates="student")

    __table_args__ = (
        Index('idx_student_group_parent', 'group_id', 'parent_phone'),
    )


class GroupSubject(Base):
    __tablename__ = "group_subjects"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), index=True)

    group = relationship("Group", back_populates="group_subjects")
    subject = relationship("Subject", back_populates="group_subjects")
    teacher = relationship("User", back_populates="group_subjects")
    homework = relationship("Homework", back_populates="group_subject")
    exams = relationship("Exam", back_populates="group_subject")
    attendance_records = relationship("Attendance", back_populates="group_subject")
    schedules = relationship("Schedule", back_populates="group_subject")

    __table_args__ = (
        Index('idx_group_subject_unique', 'group_id', 'subject_id', unique=True),
    )


class Homework(Base):
    __tablename__ = "homework"

    id = Column(Integer, primary_key=True, index=True)
    group_subject_id = Column(Integer, ForeignKey("group_subjects.id"), index=True)
    title = Column(String, index=True)
    description = Column(Text)
    due_date = Column(DateTime, index=True)
    max_points = Column(Integer, default=100)
    external_links = Column(JSON, default=list)
    document_ids = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    group_subject = relationship("GroupSubject", back_populates="homework")
    grades = relationship("HomeworkGrade", back_populates="homework")

    __table_args__ = (
        Index('idx_homework_due_date', 'due_date', 'group_subject_id'),
    )


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    group_subject_id = Column(Integer, ForeignKey("group_subjects.id"), index=True)
    title = Column(String, index=True)
    description = Column(Text)
    exam_date = Column(DateTime, index=True)
    max_points = Column(Integer, default=100)
    external_links = Column(JSON, default=list)
    document_ids = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    group_subject = relationship("GroupSubject", back_populates="exams")
    grades = relationship("ExamGrade", back_populates="exam")


class HomeworkGrade(Base):
    __tablename__ = "homework_grades"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    homework_id = Column(Integer, ForeignKey("homework.id"), index=True)
    points = Column(Integer)
    comment = Column(Text, default="")
    graded_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="homework_grades")
    homework = relationship("Homework", back_populates="grades")

    __table_args__ = (
        Index('idx_homework_grade_unique', 'student_id', 'homework_id', unique=True),
    )


class ExamGrade(Base):
    __tablename__ = "exam_grades"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), index=True)
    points = Column(Integer)
    comment = Column(Text, default="")
    graded_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="exam_grades")
    exam = relationship("Exam", back_populates="grades")

    __table_args__ = (
        Index('idx_exam_grade_unique', 'student_id', 'exam_id', unique=True),
    )


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    group_subject_id = Column(Integer, ForeignKey("group_subjects.id"), index=True)
    date = Column(Date, index=True)
    status = Column(String, index=True)

    student = relationship("Student", back_populates="attendance_records")
    group_subject = relationship("GroupSubject", back_populates="attendance_records")

    __table_args__ = (
        Index('idx_attendance_unique', 'student_id', 'group_subject_id', 'date', unique=True),
    )


class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    amount = Column(Integer)
    payment_date = Column(Date, index=True)
    payment_method = Column(String, default="cash")
    description = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="payment_records")


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    author_id = Column(Integer, ForeignKey("users.id"))
    external_links = Column(JSON, default=list)
    image_ids = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_published = Column(Boolean, default=True, index=True)


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    group_subject_id = Column(Integer, ForeignKey("group_subjects.id"), index=True)
    day = Column(Integer, index=True)
    start_time = Column(Time)
    end_time = Column(Time)
    room = Column(String)

    group_subject = relationship("GroupSubject", back_populates="schedules")

    __table_args__ = (
        Index('idx_schedule_day_time', 'day', 'start_time'),
    )