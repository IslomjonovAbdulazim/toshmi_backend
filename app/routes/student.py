from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import require_student
from app.schemas import *
from app.crud import *
from app.models import Student

router = APIRouter()


@router.get("/students/{student_id}", response_model=StudentResponse)
def get_student_info(student_id: str, db: Session = Depends(get_db), student=Depends(require_student)):
    student_data = get_student(db, student_id)
    if not student_data:
        raise HTTPException(status_code=404, detail="Student not found")
    return student_data


@router.get("/homework-grades", response_model=List[HomeworkGradeResponse])
def get_my_homework_grades(db: Session = Depends(get_db), current_student=Depends(require_student)):
    # Get student record from user
    student_record = db.query(Student).filter(Student.user_id == current_student.id).first()
    if not student_record:
        raise HTTPException(status_code=404, detail="Student record not found")
    return get_homework_grades_by_student(db, student_record.id)


@router.get("/exam-grades", response_model=List[ExamGradeResponse])
def get_my_exam_grades(db: Session = Depends(get_db), current_student=Depends(require_student)):
    # Get student record from user
    student_record = db.query(Student).filter(Student.user_id == current_student.id).first()
    if not student_record:
        raise HTTPException(status_code=404, detail="Student record not found")
    return get_exam_grades_by_student(db, student_record.id)


@router.get("/attendance", response_model=List[AttendanceResponse])
def get_my_attendance(db: Session = Depends(get_db), current_student=Depends(require_student)):
    # Get student record from user
    student_record = db.query(Student).filter(Student.user_id == current_student.id).first()
    if not student_record:
        raise HTTPException(status_code=404, detail="Student record not found")
    return get_attendance_by_student(db, student_record.id)


@router.get("/schedule", response_model=List[ScheduleResponse])
def get_my_schedule(db: Session = Depends(get_db), current_student=Depends(require_student)):
    # Get student record from user
    student_record = db.query(Student).filter(Student.user_id == current_student.id).first()
    if not student_record:
        raise HTTPException(status_code=404, detail="Student record not found")
    return get_schedule_by_group(db, student_record.group_id)


@router.get("/news", response_model=List[NewsResponse])
def get_news_for_students(db: Session = Depends(get_db), student=Depends(require_student)):
    return get_all_news(db)


@router.get("/recent-grades", response_model=RecentGradesResponse)
def get_my_recent_grades(db: Session = Depends(get_db), current_student=Depends(require_student)):
    # Get student record from user
    student_record = db.query(Student).filter(Student.user_id == current_student.id).first()
    if not student_record:
        raise HTTPException(status_code=404, detail="Student record not found")

    result = get_recent_grades(db, student_record.id)
    if not result:
        raise HTTPException(status_code=404, detail="No grades found")
    return result