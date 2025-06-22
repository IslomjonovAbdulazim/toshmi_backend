from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Group(Base):
    __tablename__ = "groups"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)  # e.g., "10A"

    students = relationship("Student", back_populates="group")
    schedules = relationship("Schedule", back_populates="group")
    group_subjects = relationship("GroupSubject", back_populates="group")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)  # e.g., "Math"

    group_subjects = relationship("GroupSubject", back_populates="subject")


class GroupSubject(Base):
    __tablename__ = "group_subjects"

    id = Column(String, primary_key=True, index=True)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False, index=True)
    subject_id = Column(String, ForeignKey("subjects.id"), nullable=False, index=True)

    group = relationship("Group", back_populates="group_subjects")
    subject = relationship("Subject", back_populates="group_subjects")
    teachers = relationship("Teacher", secondary="teacher_group_subjects", back_populates="group_subjects")

    # Back references
    homework = relationship("Homework", back_populates="group_subject")
    exams = relationship("Exam", back_populates="group_subject")
    schedules = relationship("Schedule", back_populates="group_subject")
    attendance = relationship("Attendance", back_populates="group_subject")


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(String, primary_key=True, index=True)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False, index=True)
    group_subject_id = Column(String, ForeignKey("group_subjects.id"), nullable=False, index=True)
    day_of_week = Column(String, nullable=False, index=True)  # 'monday', 'tuesday', etc.
    start_time = Column(String, nullable=False)  # e.g., "08:30"
    end_time = Column(String, nullable=False)  # e.g., "09:15"
    room = Column(String, nullable=True)

    group = relationship("Group", back_populates="schedules")
    group_subject = relationship("GroupSubject", back_populates="schedules")