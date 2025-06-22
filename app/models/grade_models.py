from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Homework(Base):
    __tablename__ = "homework"

    id = Column(String, primary_key=True, index=True)
    group_subject_id = Column(String, ForeignKey("group_subjects.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    due_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    group_subject = relationship("GroupSubject")


class HomeworkGrade(Base):
    __tablename__ = "homework_grades"

    id = Column(String, primary_key=True, index=True)
    homework_id = Column(String, ForeignKey("homework.id"), nullable=False)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    grade = Column(Float, nullable=False)
    comment = Column(Text, nullable=True)
    graded_at = Column(DateTime, default=datetime.utcnow)

    homework = relationship("Homework")
    student = relationship("Student")


class Exam(Base):
    __tablename__ = "exams"

    id = Column(String, primary_key=True, index=True)
    group_subject_id = Column(String, ForeignKey("group_subjects.id"), nullable=False)
    title = Column(String, nullable=False)
    exam_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    group_subject = relationship("GroupSubject")


class ExamGrade(Base):
    __tablename__ = "exam_grades"

    id = Column(String, primary_key=True, index=True)
    exam_id = Column(String, ForeignKey("exams.id"), nullable=False)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    grade = Column(Float, nullable=False)
    comment = Column(Text, nullable=True)
    graded_at = Column(DateTime, default=datetime.utcnow)

    exam = relationship("Exam")
    student = relationship("Student")