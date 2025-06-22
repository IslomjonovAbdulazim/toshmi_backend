from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    role = Column(String, nullable=False)  # 'student', 'parent', 'teacher', 'admin'
    phone = Column(Integer, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Student(Base):
    __tablename__ = "students"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    parent_id = Column(String, ForeignKey("parents.id"), nullable=False)
    graduation_year = Column(Integer, nullable=False)

    user = relationship("User")
    group = relationship("Group")
    parent = relationship("Parent")


class Parent(Base):
    __tablename__ = "parents"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    student_ids = Column(ARRAY(String), nullable=False)

    user = relationship("User")


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    group_subject_ids = Column(ARRAY(String), nullable=False)

    user = relationship("User")