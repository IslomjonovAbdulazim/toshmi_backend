from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models.models import User, Student, Homework, Exam, HomeworkGrade, ExamGrade, Attendance, PaymentRecord, \
    MonthlyPayment, GroupSubject
from app.core.security import require_role

router = APIRouter()


def get_children(current_user: User, db: Session):
    children = db.query(Student).join(User).filter(
        Student.parent_phone == current_user.phone
    ).all()
    return children


@router.get("/children")
def list_children(current_user: User = Depends(require_role(["parent"])), db: Session = Depends(get_db)):
    children = get_children(current_user, db)
    return [
        {
            "id": child.id,
            "name": f"{child.user.first_name} {child.user.last_name}",
            "group_id": child.group_id,
            "graduation_year": child.graduation_year
        } for child in children
    ]


@router.get("/children/{child_id}/homework")
def get_child_homework(child_id: int, current_user: User = Depends(require_role(["parent"])),
                       db: Session = Depends(get_db)):
    child = db.query(Student).join(User).filter(
        Student.id == child_id,
        Student.parent_phone == current_user.phone
    ).first()

    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    homework = db.query(Homework).join(GroupSubject).filter(
        GroupSubject.group_id == child.group_id
    ).all()

    grades = db.query(HomeworkGrade).filter(HomeworkGrade.student_id == child.id).all()
    grade_map = {g.homework_id: g for g in grades}

    return [
        {
            "id": h.id,
            "title": h.title,
            "description": h.description,
            "due_date": h.due_date,
            "max_points": h.max_points,
            "grade": {
                "points": grade_map[h.id].points if h.id in grade_map else None,
                "comment": grade_map[h.id].comment if h.id in grade_map else ""
            }
        } for h in homework
    ]


@router.get("/children/{child_id}/grades")
def get_child_grades(child_id: int, current_user: User = Depends(require_role(["parent"])),
                     db: Session = Depends(get_db)):
    child = db.query(Student).join(User).filter(
        Student.id == child_id,
        Student.parent_phone == current_user.phone
    ).first()

    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    homework_grades = db.query(HomeworkGrade).join(Homework).filter(
        HomeworkGrade.student_id == child.id
    ).all()

    exam_grades = db.query(ExamGrade).join(Exam).filter(
        ExamGrade.student_id == child.id
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


@router.get("/children/{child_id}/attendance")
def get_child_attendance(child_id: int, current_user: User = Depends(require_role(["parent"])),
                         db: Session = Depends(get_db)):
    child = db.query(Student).join(User).filter(
        Student.id == child_id,
        Student.parent_phone == current_user.phone
    ).first()

    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    attendance = db.query(Attendance).filter(
        Attendance.student_id == child.id
    ).all()

    return [
        {
            "date": a.date,
            "status": a.status
        } for a in attendance
    ]


@router.get("/children/{child_id}/payments")
def get_child_payments(child_id: int, current_user: User = Depends(require_role(["parent"])),
                       db: Session = Depends(get_db)):
    child = db.query(Student).join(User).filter(
        Student.id == child_id,
        Student.parent_phone == current_user.phone
    ).first()

    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    records = db.query(PaymentRecord).filter(
        PaymentRecord.student_id == child.id
    ).all()

    monthly = db.query(MonthlyPayment).filter(
        MonthlyPayment.student_id == child.id
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
def get_dashboard(current_user: User = Depends(require_role(["parent"])), db: Session = Depends(get_db)):
    children = get_children(current_user, db)

    dashboard_data = []
    for child in children:
        upcoming_homework = db.query(Homework).join(GroupSubject).filter(
            GroupSubject.group_id == child.group_id,
            Homework.due_date > datetime.utcnow()
        ).count()

        pending_payments = db.query(MonthlyPayment).filter(
            MonthlyPayment.student_id == child.id,
            MonthlyPayment.is_completed == False
        ).count()

        dashboard_data.append({
            "child_id": child.id,
            "child_name": f"{child.user.first_name} {child.user.last_name}",
            "upcoming_homework_count": upcoming_homework,
            "pending_payments_count": pending_payments
        })

    return {"children_summary": dashboard_data}