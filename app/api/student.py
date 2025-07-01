from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload, selectinload
from datetime import datetime
from app.database import get_db
from app.models.models import User, Homework, Exam, Schedule, GroupSubject, ExamGrade, HomeworkGrade, Attendance
from app.core.security import require_role, get_student_by_user

router = APIRouter()


@router.get("/homework")
def get_homework(current_user: User = Depends(require_role(["student"])), db: Session = Depends(get_db)):
    student = get_student_by_user(current_user, db)

    homework = db.query(Homework).options(
        joinedload(Homework.group_subject).joinedload(GroupSubject.subject),
        joinedload(Homework.group_subject).joinedload(GroupSubject.teacher)
    ).filter(
        Homework.group_subject.has(group_id=student.group_id)
    ).all()

    grade_map = {g.homework_id: g for g in student.homework_grades}

    return [{
        "id": h.id,
        "title": h.title,
        "description": h.description,
        "due_date": h.due_date,
        "max_points": h.max_points,
        "external_links": h.external_links,
        "document_ids": h.document_ids,
        "subject": h.group_subject.subject.name,
        "teacher": h.group_subject.teacher.full_name,
        "grade": {
            "points": grade_map[h.id].points if h.id in grade_map else None,
            "comment": grade_map[h.id].comment if h.id in grade_map else ""
        }
    } for h in homework]


@router.get("/exams")
def get_exams(current_user: User = Depends(require_role(["student"])), db: Session = Depends(get_db)):
    student = get_student_by_user(current_user, db)

    exams = db.query(Exam).options(
        joinedload(Exam.group_subject).joinedload(GroupSubject.subject),
        joinedload(Exam.group_subject).joinedload(GroupSubject.teacher)
    ).filter(
        Exam.group_subject.has(group_id=student.group_id)
    ).all()

    grade_map = {g.exam_id: g for g in student.exam_grades}

    return [{
        "id": e.id,
        "title": e.title,
        "description": e.description,
        "exam_date": e.exam_date,
        "max_points": e.max_points,
        "external_links": e.external_links,
        "document_ids": e.document_ids,
        "subject": e.group_subject.subject.name,
        "teacher": e.group_subject.teacher.full_name,
        "grade": {
            "points": grade_map[e.id].points if e.id in grade_map else None,
            "comment": grade_map[e.id].comment if e.id in grade_map else ""
        }
    } for e in exams]


@router.get("/grades")
def get_grades(current_user: User = Depends(require_role(["student"])), db: Session = Depends(get_db)):
    student = get_student_by_user(current_user, db)

    # Fixed: Use proper relationship objects instead of strings
    homework_grades = db.query(HomeworkGrade).options(
        joinedload(HomeworkGrade.homework).joinedload(Homework.group_subject).joinedload(GroupSubject.subject)
    ).filter(HomeworkGrade.student_id == student.id).all()

    exam_grades = db.query(ExamGrade).options(
        joinedload(ExamGrade.exam).joinedload(Exam.group_subject).joinedload(GroupSubject.subject)
    ).filter(ExamGrade.student_id == student.id).all()

    return {
        "homework_grades": [{
            "homework_title": g.homework.title,
            "subject": g.homework.group_subject.subject.name,
            "points": g.points,
            "max_points": g.homework.max_points,
            "percentage": round((g.points / g.homework.max_points) * 100, 1) if g.homework.max_points > 0 else 0,
            "comment": g.comment,
            "graded_at": g.graded_at
        } for g in homework_grades],
        "exam_grades": [{
            "exam_title": g.exam.title,
            "subject": g.exam.group_subject.subject.name,
            "points": g.points,
            "max_points": g.exam.max_points,
            "percentage": round((g.points / g.exam.max_points) * 100, 1) if g.exam.max_points > 0 else 0,
            "comment": g.comment,
            "graded_at": g.graded_at
        } for g in exam_grades]
    }


@router.get("/attendance")
def get_attendance(current_user: User = Depends(require_role(["student"])), db: Session = Depends(get_db)):
    student = get_student_by_user(current_user, db)

    # Fixed: Use proper relationship objects instead of strings
    attendance = db.query(Attendance).options(
        joinedload(Attendance.group_subject).joinedload(GroupSubject.subject),
        joinedload(Attendance.group_subject).joinedload(GroupSubject.teacher)
    ).filter(Attendance.student_id == student.id).all()

    return [{
        "date": a.date,
        "status": a.status,
        "subject": a.group_subject.subject.name,
        "teacher": a.group_subject.teacher.full_name
    } for a in attendance]


@router.get("/schedule")
def get_schedule(current_user: User = Depends(require_role(["student"])), db: Session = Depends(get_db)):
    student = get_student_by_user(current_user, db)

    schedules = db.query(Schedule).options(
        joinedload(Schedule.group_subject).joinedload(GroupSubject.subject),
        joinedload(Schedule.group_subject).joinedload(GroupSubject.teacher)
    ).filter(
        Schedule.group_subject.has(group_id=student.group_id)
    ).all()

    schedule_list = [{
        "day": s.day,
        "start_time": s.start_time,
        "end_time": s.end_time,
        "room": s.room,
        "subject": s.group_subject.subject.name,
        "teacher": s.group_subject.teacher.full_name
    } for s in schedules]

    return sorted(schedule_list, key=lambda x: (x["day"], x["start_time"]))


@router.get("/payments")
def get_payments(current_user: User = Depends(require_role(["student"])), db: Session = Depends(get_db)):
    student = get_student_by_user(current_user, db)

    # Fixed: Removed non-existent monthly_payments reference
    return {
        "payment_records": [{
            "amount": r.amount,
            "payment_date": r.payment_date,
            "payment_method": r.payment_method,
            "description": r.description,
            "created_at": r.created_at
        } for r in student.payment_records]
    }


@router.get("/dashboard")
def get_dashboard(current_user: User = Depends(require_role(["student"])), db: Session = Depends(get_db)):
    student = get_student_by_user(current_user, db)

    upcoming_homework = db.query(Homework).options(
        joinedload(Homework.group_subject).joinedload(GroupSubject.subject)
    ).filter(
        Homework.group_subject.has(group_id=student.group_id),
        Homework.due_date > datetime.utcnow()
    ).order_by(Homework.due_date).limit(5).all()

    upcoming_exams = db.query(Exam).options(
        joinedload(Exam.group_subject).joinedload(GroupSubject.subject)
    ).filter(
        Exam.group_subject.has(group_id=student.group_id),
        Exam.exam_date > datetime.utcnow()
    ).order_by(Exam.exam_date).limit(5).all()

    # Fixed: Get grades properly and handle different grade types
    homework_grades = db.query(HomeworkGrade).options(
        joinedload(HomeworkGrade.homework)
    ).filter(HomeworkGrade.student_id == student.id).order_by(HomeworkGrade.graded_at.desc()).limit(3).all()

    exam_grades = db.query(ExamGrade).options(
        joinedload(ExamGrade.exam)
    ).filter(ExamGrade.student_id == student.id).order_by(ExamGrade.graded_at.desc()).limit(3).all()

    # Combine and sort recent grades
    recent_grades = []

    for g in homework_grades:
        recent_grades.append({
            "title": g.homework.title,
            "type": "homework",
            "points": g.points,
            "max_points": g.homework.max_points,
            "graded_at": g.graded_at
        })

    for g in exam_grades:
        recent_grades.append({
            "title": g.exam.title,
            "type": "exam",
            "points": g.points,
            "max_points": g.exam.max_points,
            "graded_at": g.graded_at
        })

    # Sort by graded_at and take top 5
    recent_grades = sorted(recent_grades, key=lambda x: x["graded_at"], reverse=True)[:5]

    return {
        "upcoming_homework": [{
            "id": h.id,
            "title": h.title,
            "due_date": h.due_date,
            "subject": h.group_subject.subject.name
        } for h in upcoming_homework],
        "upcoming_exams": [{
            "id": e.id,
            "title": e.title,
            "exam_date": e.exam_date,
            "subject": e.group_subject.subject.name
        } for e in upcoming_exams],
        "recent_grades": recent_grades
    }