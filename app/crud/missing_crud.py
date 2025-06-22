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
def update_group_subject(db: Session, group_subject_id: str, group_subject_update: GroupSubjectCreate):
    gs = db.query(GroupSubject).filter(GroupSubject.id == group_subject_id).first()
    if gs:
        gs.group_id = group_subject_update.group_id
        gs.subject_id = group_subject_update.subject_id
        gs.teacher_id = group_subject_update.teacher_id
        db.commit()
        db.refresh(gs)
    return gs


def delete_group_subject(db: Session, group_subject_id: str):
    gs = db.query(GroupSubject).filter(GroupSubject.id == group_subject_id).first()
    if gs:
        db.delete(gs)
        db.commit()
        return True
    return False


# Student Enrollment
def enroll_student_in_group(db: Session, student_id: str, group_id: str):
    student = db.query(Student).filter(Student.id == student_id).first()
    if student:
        student.group_id = group_id
        # Update group's student list
        group = db.query(Group).filter(Group.id == group_id).first()
        if group and student_id not in group.student_ids:
            group.student_ids.append(student_id)
        db.commit()
        db.refresh(student)
    return student


def bulk_transfer_students(db: Session, student_ids: List[str], from_group_id: str, to_group_id: str):
    results = []
    for student_id in student_ids:
        student = enroll_student_in_group(db, student_id, to_group_id)
        if student:
            # Remove from old group
            from_group = db.query(Group).filter(Group.id == from_group_id).first()
            if from_group and student_id in from_group.student_ids:
                from_group.student_ids.remove(student_id)
            results.append(student)
    db.commit()
    return results


# Search & Filter
def search_students(db: Session, name: str = None, group_id: str = None, graduation_year: int = None):
    query = db.query(Student).join(User, Student.user_id == User.id)

    if name:
        query = query.filter(User.full_name.ilike(f"%{name}%"))
    if group_id:
        query = query.filter(Student.group_id == group_id)
    if graduation_year:
        query = query.filter(Student.graduation_year == graduation_year)

    return query.all()


def filter_grades(db: Session, student_id: str = None, subject_id: str = None, date_from=None, date_to=None):
    # Homework grades
    hw_query = (
        db.query(HomeworkGrade, Homework, GroupSubject)
        .join(Homework, HomeworkGrade.homework_id == Homework.id)
        .join(GroupSubject, Homework.group_subject_id == GroupSubject.id)
    )

    if student_id:
        hw_query = hw_query.filter(HomeworkGrade.student_id == student_id)
    if subject_id:
        hw_query = hw_query.filter(GroupSubject.subject_id == subject_id)
    if date_from:
        hw_query = hw_query.filter(HomeworkGrade.graded_at >= date_from)
    if date_to:
        hw_query = hw_query.filter(HomeworkGrade.graded_at <= date_to)

    return hw_query.all()


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


# Bulk Operations
def bulk_create_students(db: Session, students_data: List[dict]):
    results = []
    for student_data in students_data:
        # Create user first
        user = User(
            id=str(uuid.uuid4()),
            role="student",
            phone=student_data["phone"],
            full_name=student_data["full_name"],
            avatar_url=None
        )
        db.add(user)
        db.flush()  # Get the ID

        # Create student
        student = Student(
            id=str(uuid.uuid4()),
            user_id=user.id,
            group_id=student_data["group_id"],
            parent_id=student_data.get("parent_id"),
            graduation_year=student_data["graduation_year"]
        )
        db.add(student)
        results.append(student)

    db.commit()
    return results