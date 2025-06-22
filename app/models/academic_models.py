from sqlalchemy import Column, String, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from app.database import Base


class Group(Base):
    __tablename__ = "groups"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)  # e.g., "10A"
    student_ids = Column(ARRAY(String), nullable=False)


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)  # e.g., "Math"


class GroupSubject(Base):
    __tablename__ = "group_subjects"

    id = Column(String, primary_key=True, index=True)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    subject_id = Column(String, ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(String, ForeignKey("teachers.id"), nullable=False)

    group = relationship("Group")
    subject = relationship("Subject")
    teacher = relationship("Teacher")


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(String, primary_key=True, index=True)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    group_subject_id = Column(String, ForeignKey("group_subjects.id"), nullable=False)
    day_of_week = Column(String, nullable=False)  # 'monday', 'tuesday', etc.
    start_time = Column(String, nullable=False)  # e.g., "08:30"
    end_time = Column(String, nullable=False)  # e.g., "09:15"
    room = Column(String, nullable=True)

    group = relationship("Group")
    group_subject = relationship("GroupSubject")