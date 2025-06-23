# app/models/user_models.py
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    role = Column(String, nullable=False, index=True)  # 'student', 'parent', 'teacher', 'admin'
    phone = Column(Integer, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False, index=True)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Student(Base):
    __tablename__ = "students"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False, index=True)
    parent_id = Column(String, ForeignKey("parents.id"), nullable=True, index=True)
    graduation_year = Column(Integer, nullable=False, index=True)

    user = relationship("User", backref="student_profile")
    group = relationship("Group", back_populates="students")
    parent = relationship("Parent", back_populates="students")


class Parent(Base):
    __tablename__ = "parents"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)

    user = relationship("User", backref="parent_profile")
    students = relationship("Student", back_populates="parent")


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)

    user = relationship("User", backref="teacher_profile")