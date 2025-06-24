from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models.models import User, Student, Homework, Exam, HomeworkGrade, ExamGrade, Attendance, GroupSubject, \
    Schedule, PaymentRecord, MonthlyPayment
from app.core.security import require_role

router = APIRouter()


def get_student(current_user: User, db: Session):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return student


@router.get("/homework")
def get_homework(current_user: User = Depends(require_role(["student"])), db: Session = Depends(get_db)):
    student = get_student(current_user, db)

    homework = db.query(Homework).join(GroupSubject).filter(
        GroupSubject.group_id == student.group_id
    ).all()

    grades = db.query(HomeworkGrade).filter(HomeworkGrade.student_id == student.id).all()
    grade_map = {g.homework_id: g for g in grades}

    return [
        {
            "id": h.id,
            "title": h.title,
            "description": h.description,
            "due_date": h.due_date,
            "max_points": h.max_points,
            "external_links": h.external_links,
            "document_ids": h.document_ids,
            "grade": {
                "points": grade_map[h.id].points if h.id in grade_map else None,
                "comment": grade_map[h.id].comment if h.id in grade_map else ""
            }
        } for h in homework
    ]


@router.get("/exams")
def get_exams(current_user: User = Depends(require_role(["student"])), db: Session = Depends(get_db)):
    student = get_student(current_user, db)

    exams = db.query(Exam).join(GroupSubject).filter(
        GroupSubject.group_id == student.group_id
    ).all()

    grades = db.query(ExamGrade).filter(ExamGrade.student_id == student.id).all()
    grade_map = {g.exam_id: g for g in grades}

    return [
        {
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "exam_date": e.exam_date,
            "max_points": e.max_points,
            "external_links": e.external_links,
            "document_ids": e.document_ids,
            "grade": {
                "points": grade_map[e.id].points if e.id in grade_map else None,
                "comment": grade_map[e.id].comment if e.id in grade_map else ""
            }
        } for e in exams
    ]


@router.get("/grades")
def get_grades(current_user: User = Depends(require_role(["student"])), db: Session = Depends(get_db)):
    student = get_student(current_user, db)

    homework_grades = db.query(HomeworkGrade).join(Homework).filter(
        HomeworkGrade.student_id == student.id
    ).all()

    exam_grades = db.query(ExamGrade).join(Exam).filter(
        ExamGrade.student_id == student.id
    ).all()

    return {
        "homework_grades": [
            {
                "homework_title": g.homework.title,
                "points": g.points,
                "max_points": g.homework.max_points,
                "comment": g.comment,
                "graded_at": g.graded_at
            } for g in homework_grades
        ],
        "exam_grades": [
            {
                "exam_title": g.exam.title,
                "points": g.points,
                "max_points": g.exam.max_points,
                "comment": g.comment,
                "graded_at": g.graded_at
            } for g in exam_grades
        ]
    }


@router.get("/attendance")
def get_attendance(current_user: User = Depends(require_role(["student"])), db: Session = Depends(get_db)):
    student = get_student(current_user, db)

    attendance = db.query(Attendance).filter(
        Attendance.student_id == student.id
    ).all()

    return [
        {
            "date": a.date,
            "status": a.status,
            "group_subject_id": a.group_subject_id
        } for a in attendance
    ]


@router.get("/schedule")
def get_schedule(current_user: User = Depends(require_role(["student"])), db: Session = Depends(get_db)):
    student = get_student(current_user, db)

    schedule = db.query(Schedule).join(GroupSubject).filter(
        GroupSubject.group_id == student.group_id
    ).all()

    return [
        {
            "day": s.day,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "room": s.room,
            "subject": s.group_subject.subject.name,
            "teacher": f"{s.group_subject.teacher.first_name} {s.group_subject.teacher.last_name}"
        } for s in schedule
    ]


@router.get("/payments")
def get_payments(current_user: User = Depends(require_role(["student"])), db: Session = Depends(get_db)):
    student = get_student(current_user, db)

    records = db.query(PaymentRecord).filter(
        PaymentRecord.student_id == student.id
    ).all()

    monthly = db.query(MonthlyPayment).filter(
        MonthlyPayment.student_id == student.id
    ).all()

    return {
        "payment_records": [
            {
                "amount": r.amount,
                "payment_date": r.payment_date,
                "payment_method": r.payment_method,
                "description": r.description
            } for r in records
        ],
        "monthly_status": [
            {
                "month": m.month,
                "year": m.year,
                "paid_amount": m.paid_amount,
                "is_completed": m.is_completed,
                "due_date": m.due_date
            } for m in monthly
        ]
    }


@router.get("/dashboard")
def get_dashboard(current_user: User = Depends(require_role(["student"])), db: Session = Depends(get_db)):
    student = get_student(current_user, db)

    upcoming_homework = db.query(Homework).join(GroupSubject).filter(
        GroupSubject.group_id == student.group_id,
        Homework.due_date > datetime.utcnow()
    ).order_by(Homework.due_date).limit(5).all()

    upcoming_exams = db.query(Exam).join(GroupSubject).filter(
        GroupSubject.group_id == student.group_id,
        Exam.exam_date > datetime.utcnow()
    ).order_by(Exam.exam_date).limit(5).all()

    recent_grades = db.query(HomeworkGrade).filter(
        HomeworkGrade.student_id == student.id
    ).order_by(HomeworkGrade.graded_at.desc()).limit(5).all()

    return {
        "upcoming_homework": [
            {
                "id": h.id,
                "title": h.title,
                "due_date": h.due_date
            } for h in upcoming_homework
        ],
        "upcoming_exams": [
            {
                "id": e.id,
                "title": e.title,
                "exam_date": e.exam_date
            } for e in upcoming_exams
        ],
        "recent_grades": [
            {
                "homework_title": g.homework.title,
                "points": g.points,
                "max_points": g.homework.max_points,
                "graded_at": g.graded_at
            } for g in recent_grades
        ]
    }