from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload, selectinload
from datetime import datetime
from app.database import get_db
from app.models.models import User, Homework, Exam, Schedule, GroupSubject
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

    homework_grades = db.query(User).options(
        selectinload(User.student_profile).selectinload(
            "homework_grades", HomeworkGrade.homework
        ).joinedload("group_subject").joinedload(GroupSubject.subject)
    ).filter(User.id == current_user.id).first().student_profile.homework_grades

    exam_grades = db.query(User).options(
        selectinload(User.student_profile).selectinload(
            "exam_grades", ExamGrade.exam
        ).joinedload("group_subject").joinedload(GroupSubject.subject)
    ).filter(User.id == current_user.id).first().student_profile.exam_grades

    return {
        "homework_grades": [{
            "homework_title": g.homework.title,
            "subject": g.homework.group_subject.subject.name,
            "points": g.points,
            "max_points": g.homework.max_points,
            "percentage": round((g.points / g.homework.max_points) * 100, 1),
            "comment": g.comment,
            "graded_at": g.graded_at
        } for g in homework_grades],
        "exam_grades": [{
            "exam_title": g.exam.title,
            "subject": g.exam.group_subject.subject.name,
            "points": g.points,
            "max_points": g.exam.max_points,
            "percentage": round((g.points / g.exam.max_points) * 100, 1),
            "comment": g.comment,
            "graded_at": g.graded_at
        } for g in exam_grades]
    }


@router.get("/attendance")
def get_attendance(current_user: User = Depends(require_role(["student"])), db: Session = Depends(get_db)):
    student = get_student_by_user(current_user, db)

    attendance = db.query(User).options(
        selectinload(User.student_profile).selectinload(
            "attendance_records"
        ).joinedload("group_subject").joinedload(GroupSubject.subject),
        selectinload(User.student_profile).selectinload(
            "attendance_records"
        ).joinedload("group_subject").joinedload(GroupSubject.teacher)
    ).filter(User.id == current_user.id).first().student_profile.attendance_records

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

    return {
        "payment_records": [{
            "amount": r.amount,
            "payment_date": r.payment_date,
            "payment_method": r.payment_method,
            "description": r.description
        } for r in student.payment_records],
        "monthly_status": [{
            "month": m.month,
            "year": m.year,
            "paid_amount": m.paid_amount,
            "is_completed": m.is_completed,
            "due_date": m.due_date
        } for m in student.monthly_payments]
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

    recent_grades = sorted(
        student.homework_grades + student.exam_grades,
        key=lambda g: g.graded_at,
        reverse=True
    )[:5]

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
        "recent_grades": [{
            "title": getattr(g.homework, 'title', None) or getattr(g.exam, 'title', None),
            "type": "homework" if hasattr(g, 'homework') else "exam",
            "points": g.points,
            "max_points": getattr(g.homework, 'max_points', None) or getattr(g.exam, 'max_points', None),
            "graded_at": g.graded_at
        } for g in recent_grades]
    }