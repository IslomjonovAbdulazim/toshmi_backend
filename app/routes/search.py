from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.schemas import GradeFilter
from app.crud import filter_grades, search_students
from datetime import datetime

router = APIRouter()


@router.get("/students")
def search_students_endpoint(name: str = None, group_id: str = None, graduation_year: int = None,
                             db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return search_students(db, name, group_id, graduation_year)


@router.get("/grades")
def filter_grades_endpoint(
        student_id: str = None,
        subject_id: str = None,
        date_from: str = None,
        date_to: str = None,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    date_from_dt = datetime.fromisoformat(date_from) if date_from else None
    date_to_dt = datetime.fromisoformat(date_to) if date_to else None

    return filter_grades(db, student_id, subject_id, date_from_dt, date_to_dt)