from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import require_parent
from app.schemas import *
from app.crud import *
from app.utils.permissions import inject_parent_record, student_access_required

router = APIRouter()


@router.get("/children", response_model=List[StudentResponse])
@inject_parent_record
def get_children(parent_record=None, db: Session = Depends(get_db), current_parent=Depends(require_parent)):
    return parent_record.students


@router.get("/children/{student_id}/homework-grades", response_model=List[HomeworkGradeResponse])
@student_access_required()
def get_child_homework_grades(student_id: str, db: Session = Depends(get_db), current_parent=Depends(require_parent)):
    return get_homework_grades_by_student(db, student_id)


@router.get("/children/{student_id}/exam-grades", response_model=List[ExamGradeResponse])
@student_access_required()
def get_child_exam_grades(student_id: str, db: Session = Depends(get_db), current_parent=Depends(require_parent)):
    return get_exam_grades_by_student(db, student_id)


@router.get("/children/{student_id}/attendance", response_model=List[AttendanceResponse])
@student_access_required()
def get_child_attendance(student_id: str, db: Session = Depends(get_db), current_parent=Depends(require_parent)):
    return get_attendance_by_student(db, student_id)


@router.get("/children/{student_id}/payments", response_model=List[PaymentResponse])
@student_access_required()
def get_child_payments(student_id: str, db: Session = Depends(get_db), current_parent=Depends(require_parent)):
    return get_payments_by_student(db, student_id)


@router.get("/children/{student_id}/recent-grades", response_model=RecentGradesResponse)
@student_access_required()
def get_child_recent_grades(student_id: str, db: Session = Depends(get_db), current_parent=Depends(require_parent)):
    result = get_recent_grades(db, student_id)
    if not result:
        raise HTTPException(404, "No grades found")
    return result