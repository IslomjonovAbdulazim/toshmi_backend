# app/crud/missing_crud.py
from sqlalchemy.orm import Session
from app.models import *
from app.schemas import *
from typing import List, Optional
import uuid


# Profile Updates
def update_user_profile(db: Session, user_id: str, user_update: UserUpdate):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        if user_update.full_name:
            user.full_name = user_update.full_name
        if user_update.avatar_url:
            user.avatar_url = user_update.avatar_url
        db.commit()
        db.refresh(user)
    return user


# GroupSubject Management
def delete_group_subject(db: Session, group_subject_id: str):
    gs = db.query(GroupSubject).filter(GroupSubject.id == group_subject_id).first()
    if gs:
        db.delete(gs)
        db.commit()
        return True
    return False


# Reports
def get_class_report(db: Session, group_id: str, subject_id: str):
    group_subject = db.query(GroupSubject).filter(
        GroupSubject.group_id == group_id,
        GroupSubject.subject_id == subject_id
    ).first()

    if not group_subject:
        return None

    # Get homework grades for this class
    hw_grades = (
        db.query(HomeworkGrade)
        .join(Homework, HomeworkGrade.homework_id == Homework.id)
        .filter(Homework.group_subject_id == group_subject.id)
        .all()
    )

    # Get exam grades for this class
    exam_grades = (
        db.query(ExamGrade)
        .join(Exam, ExamGrade.exam_id == Exam.id)
        .filter(Exam.group_subject_id == group_subject.id)
        .all()
    )

    all_grades = [g.grade for g in hw_grades + exam_grades]
    avg_grade = sum(all_grades) / len(all_grades) if all_grades else 0

    students = db.query(Student).filter(Student.group_id == group_id).all()

    return ClassReport(
        group_id=group_id,
        subject_id=subject_id,
        average_grade=avg_grade,
        total_students=len(students),
        assignments_count=len(set([g.homework_id for g in hw_grades] + [g.exam_id for g in exam_grades]))
    )


def get_payment_report(db: Session, month: int, year: int):
    payments = db.query(Payment).filter(Payment.month == month, Payment.year == year).all()

    total_paid = sum(p.amount_paid for p in payments if p.is_fully_paid)
    total_unpaid = sum(p.amount_paid for p in payments if not p.is_fully_paid)
    students_paid = len([p for p in payments if p.is_fully_paid])
    students_unpaid = len([p for p in payments if not p.is_fully_paid])

    return PaymentReport(
        month=month,
        year=year,
        total_paid=total_paid,
        total_unpaid=total_unpaid,
        students_paid=students_paid,
        students_unpaid=students_unpaid
    )