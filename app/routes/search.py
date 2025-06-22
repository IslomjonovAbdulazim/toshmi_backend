from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.schemas import GradeFilter, PaginationParams
from app.crud import filter_grades, search_students
from app.crud.base_crud import paginate
from datetime import datetime

router = APIRouter()


@router.get("/students")
def search_students_endpoint(
    name: str = Query(None, min_length=2),
    group_id: str = None,
    graduation_year: int = Query(None, ge=2020, le=2035),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    results = search_students(db, name, group_id, graduation_year)
    # Apply pagination
    query = db.query(type(results[0])) if results else db.query(db.query(type(results[0])).model)
    return paginate(query, page, size)


@router.get("/grades")
def filter_grades_endpoint(
    student_id: str = None,
    subject_id: str = None,
    date_from: str = None,
    date_to: str = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    date_from_dt = datetime.fromisoformat(date_from) if date_from else None
    date_to_dt = datetime.fromisoformat(date_to) if date_to else None

    results = filter_grades(db, student_id, subject_id, date_from_dt, date_to_dt)
    return {"results": results[:size], "total": len(results)}