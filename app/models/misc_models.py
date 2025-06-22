from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, Float, Text, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(String, primary_key=True, index=True)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    group_subject_id = Column(String, ForeignKey("group_subjects.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)  # 'present', 'absent', 'late'
    comment = Column(Text, nullable=True)

    student = relationship("Student")
    group_subject = relationship("GroupSubject")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, index=True)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    amount_paid = Column(Float, nullable=False)
    is_fully_paid = Column(Boolean, default=False)
    paid_at = Column(DateTime, default=datetime.utcnow)
    comment = Column(Text, nullable=True)

    student = relationship("Student")


class News(Base):
    __tablename__ = "news"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    media_urls = Column(ARRAY(String), nullable=True)  # image/video URLs
    links = Column(ARRAY(String), nullable=True)  # resource URLs
    created_at = Column(DateTime, default=datetime.utcnow)