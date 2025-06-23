# app/routes/student.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import require_student
from app.schemas import *
from app.crud import *
from app.utils.permissions import inject_student_record

router = APIRouter()


@router.get("/homework-grades", response_model=List[HomeworkGradeResponse])
@inject_student_record
def get_my_homework_grades(student_record=None, db: Session = Depends(get_db), current_student=Depends(require_student)):
    """Get my homework grades"""
    if not student_record:
        raise HTTPException(404, "Student record not found")
    return get_homework_grades_by_student(db, student_record.id)


@router.get("/exam-grades", response_model=List[ExamGradeResponse])
@inject_student_record
def get_my_exam_grades(student_record=None, db: Session = Depends(get_db), current_student=Depends(require_student)):
    """Get my exam grades"""
    if not student_record:
        raise HTTPException(404, "Student record not found")
    return get_exam_grades_by_student(db, student_record.id)


@router.get("/attendance", response_model=List[AttendanceResponse])
@inject_student_record
def get_my_attendance(student_record=None, db: Session = Depends(get_db), current_student=Depends(require_student)):
    """Get my attendance records"""
    if not student_record:
        raise HTTPException(404, "Student record not found")
    return get_attendance_by_student(db, student_record.id)


@router.get("/schedule", response_model=List[ScheduleResponse])
@inject_student_record
def get_my_schedule(student_record=None, db: Session = Depends(get_db), current_student=Depends(require_student)):
    """Get my class schedule"""
    if not student_record:
        raise HTTPException(404, "Student record not found")
    return get_schedule_by_group(db, student_record.group_id)


@router.get("/recent-grades", response_model=RecentGradesResponse)
@inject_student_record
def get_my_recent_grades(student_record=None, db: Session = Depends(get_db), current_student=Depends(require_student)):
    """Get my recent grades"""
    if not student_record:
        raise HTTPException(404, "Student record not found")
    result = get_recent_grades(db, student_record.id)
    if not result:
        raise HTTPException(404, "No grades found")
    return result


@router.get("/payments", response_model=List[PaymentResponse])
@inject_student_record
def get_my_payments(student_record=None, db: Session = Depends(get_db), current_student=Depends(require_student)):
    """Get my payment records"""
    if not student_record:
        raise HTTPException(404, "Student record not found")
    return get_payments_by_student(db, student_record.id)


@router.get("/news", response_model=List[NewsResponse])
def get_news_for_students(db: Session = Depends(get_db), student=Depends(require_student)):
    """Get school news"""
    return get_all_news(db)