from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

# Junction table for parent-student relationships
parent_student = Table('parent_students', Base.metadata,
    Column('parent_id', String, ForeignKey('parents.id'), primary_key=True),
    Column('student_id', String, ForeignKey('students.id'), primary_key=True)
)

# Junction table for teacher-group_subject relationships
teacher_group_subject = Table('teacher_group_subjects', Base.metadata,
    Column('teacher_id', String, ForeignKey('teachers.id'), primary_key=True),
    Column('group_subject_id', String, ForeignKey('group_subjects.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    role = Column(String, nullable=False, index=True)  # 'student', 'parent', 'teacher', 'admin'
    phone = Column(Integer, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False, index=True)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Student(Base):
    __tablename__ = "students"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False, index=True)
    graduation_year = Column(Integer, nullable=False, index=True)

    user = relationship("User", backref="student_profile")
    group = relationship("Group", back_populates="students")
    parents = relationship("Parent", secondary=parent_student, back_populates="students")


class Parent(Base):
    __tablename__ = "parents"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)

    user = relationship("User", backref="parent_profile")
    students = relationship("Student", secondary=parent_student, back_populates="parents")


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)

    user = relationship("User", backref="teacher_profile")
    group_subjects = relationship("GroupSubject", secondary=teacher_group_subject, back_populates="teachers")