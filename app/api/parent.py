from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from app.database import get_db
from app.models.models import User, Student, Homework, Exam, GroupSubject, HomeworkGrade, ExamGrade, Attendance
from app.core.security import require_role

router = APIRouter()


def get_children(current_user: User, db: Session):
    return db.query(Student).options(
        joinedload(Student.user),
        joinedload(Student.group)
    ).filter(Student.parent_phone == current_user.phone).all()


def get_child_or_404(child_id: int, current_user: User, db: Session):
    child = db.query(Student).options(
        joinedload(Student.user),
        joinedload(Student.group)
    ).filter(
        Student.id == child_id,
        Student.parent_phone == current_user.phone
    ).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    return child


@router.get("/children")
def list_children(current_user: User = Depends(require_role(["parent"])), db: Session = Depends(get_db)):
    children = get_children(current_user, db)
    return [{
        "id": child.id,
        "name": child.user.full_name,
        "group_name": child.group.name,
        "graduation_year": child.graduation_year
    } for child in children]


@router.get("/children/{child_id}/homework")
def get_child_homework(child_id: int, current_user: User = Depends(require_role(["parent"])),
                       db: Session = Depends(get_db)):
    child = get_child_or_404(child_id, current_user, db)

    homework = db.query(Homework).options(
        joinedload(Homework.group_subject).joinedload(GroupSubject.subject),
        joinedload(Homework.group_subject).joinedload(GroupSubject.teacher)
    ).filter(
        Homework.group_subject.has(group_id=child.group_id)
    ).all()

    # Get child's grades for this homework
    homework_grades = db.query(HomeworkGrade).filter(
        HomeworkGrade.student_id == child_id
    ).all()
    grade_map = {g.homework_id: g for g in homework_grades}

    return [{
        "id": h.id,
        "title": h.title,
        "description": h.description,
        "due_date": h.due_date,
        "max_points": h.max_points,
        "subject": h.group_subject.subject.name,
        "teacher": h.group_subject.teacher.full_name,
        "grade": {
            "points": grade_map[h.id].points if h.id in grade_map else None,
            "comment": grade_map[h.id].comment if h.id in grade_map else ""
        }
    } for h in homework]


@router.get("/children/{child_id}/grades")
def get_child_grades(child_id: int, current_user: User = Depends(require_role(["parent"])),
                     db: Session = Depends(get_db)):
    child = get_child_or_404(child_id, current_user, db)

    # Fixed: Use direct queries instead of selectinload with strings
    homework_grades = db.query(HomeworkGrade).options(
        joinedload(HomeworkGrade.homework).joinedload(Homework.group_subject).joinedload(GroupSubject.subject)
    ).filter(HomeworkGrade.student_id == child_id).all()

    exam_grades = db.query(ExamGrade).options(
        joinedload(ExamGrade.exam).joinedload(Exam.group_subject).joinedload(GroupSubject.subject)
    ).filter(ExamGrade.student_id == child_id).all()

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


@router.get("/children/{child_id}/attendance")
def get_child_attendance(child_id: int, current_user: User = Depends(require_role(["parent"])),
                         db: Session = Depends(get_db)):
    child = get_child_or_404(child_id, current_user, db)

    # Fixed: Use direct query instead of selectinload with strings
    attendance = db.query(Attendance).options(
        joinedload(Attendance.group_subject).joinedload(GroupSubject.subject),
        joinedload(Attendance.group_subject).joinedload(GroupSubject.teacher)
    ).filter(Attendance.student_id == child_id).all()

    return [{
        "date": a.date,
        "status": a.status,
        "subject": a.group_subject.subject.name,
        "teacher": a.group_subject.teacher.full_name
    } for a in attendance]


@router.get("/children/{child_id}/payments")
def get_child_payments(child_id: int, current_user: User = Depends(require_role(["parent"])),
                       db: Session = Depends(get_db)):
    child = get_child_or_404(child_id, current_user, db)

    # Fixed: Removed non-existent monthly_payments reference
    return {
        "payment_records": [{
            "amount": r.amount,
            "payment_date": r.payment_date,
            "payment_method": r.payment_method,
            "description": r.description,
            "created_at": r.created_at
        } for r in child.payment_records]
    }


@router.get("/dashboard")
def get_dashboard(current_user: User = Depends(require_role(["parent"])), db: Session = Depends(get_db)):
    children = get_children(current_user, db)

    dashboard_data = []
    for child in children:
        upcoming_homework = db.query(Homework).filter(
            Homework.group_subject.has(group_id=child.group_id),
            Homework.due_date > datetime.utcnow()
        ).count()

        # Fixed: Removed reference to non-existent monthly_payments
        # For now, just count unpaid payment records or set to 0
        pending_payments_count = 0  # You can implement proper logic here if needed

        dashboard_data.append({
            "child_id": child.id,
            "child_name": child.user.full_name,
            "upcoming_homework_count": upcoming_homework,
            "pending_payments_count": pending_payments_count
        })

    return {"children_summary": dashboard_data}