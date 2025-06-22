from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import require_parent
from app.schemas import *
from app.crud import *
from app.models import Parent, Student

router = APIRouter()


@router.get("/children", response_model=List[StudentResponse])
def get_children(db: Session = Depends(get_db), current_parent=Depends(require_parent)):
    # Get parent record from user
    parent_record = db.query(Parent).filter(Parent.user_id == current_parent.id).first()
    if not parent_record:
        raise HTTPException(status_code=404, detail="Parent record not found")

    children = []
    for student_id in parent_record.student_ids:
        student = get_student(db, student_id)
        if student:
            children.append(student)
    return children


@router.get("/children/{student_id}/homework-grades", response_model=List[HomeworkGradeResponse])
def get_child_homework_grades(student_id: str, db: Session = Depends(get_db), current_parent=Depends(require_parent)):
    # Verify this student belongs to the parent
    parent_record = db.query(Parent).filter(Parent.user_id == current_parent.id).first()
    if not parent_record or student_id not in parent_record.student_ids:
        raise HTTPException(status_code=403, detail="Access denied")

    return get_homework_grades_by_student(db, student_id)


@router.get("/children/{student_id}/exam-grades", response_model=List[ExamGradeResponse])
def get_child_exam_grades(student_id: str, db: Session = Depends(get_db), current_parent=Depends(require_parent)):
    # Verify this student belongs to the parent
    parent_record = db.query(Parent).filter(Parent.user_id == current_parent.id).first()
    if not parent_record or student_id not in parent_record.student_ids:
        raise HTTPException(status_code=403, detail="Access denied")

    return get_exam_grades_by_student(db, student_id)


@router.get("/children/{student_id}/attendance", response_model=List[AttendanceResponse])
def get_child_attendance(student_id: str, db: Session = Depends(get_db), current_parent=Depends(require_parent)):
    # Verify this student belongs to the parent
    parent_record = db.query(Parent).filter(Parent.user_id == current_parent.id).first()
    if not parent_record or student_id not in parent_record.student_ids:
        raise HTTPException(status_code=403, detail="Access denied")

    return get_attendance_by_student(db, student_id)


@router.get("/children/{student_id}/payments", response_model=List[PaymentResponse])
def get_child_payments(student_id: str, db: Session = Depends(get_db), current_parent=Depends(require_parent)):
    # Verify this student belongs to the parent
    parent_record = db.query(Parent).filter(Parent.user_id == current_parent.id).first()
    if not parent_record or student_id not in parent_record.student_ids:
        raise HTTPException(status_code=403, detail="Access denied")

    return get_payments_by_student(db, student_id)


@router.get("/children/{student_id}/recent-grades", response_model=RecentGradesResponse)
def get_child_recent_grades(student_id: str, db: Session = Depends(get_db), current_parent=Depends(require_parent)):
    # Verify this student belongs to the parent
    parent_record = db.query(Parent).filter(Parent.user_id == current_parent.id).first()
    if not parent_record or student_id not in parent_record.student_ids:
        raise HTTPException(status_code=403, detail="Access denied")

    result = get_recent_grades(db, student_id)
    if not result:
        raise HTTPException(status_code=404, detail="No grades found")
    return result