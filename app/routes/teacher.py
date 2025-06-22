from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import require_teacher
from app.schemas import *
from app.crud import *

router = APIRouter()

# Homework Management
@router.post("/homework", response_model=HomeworkResponse)
def create_homework_endpoint(homework: HomeworkCreate, db: Session = Depends(get_db), teacher = Depends(require_teacher)):
    return create_homework(db, homework)

@router.get("/homework", response_model=List[HomeworkResponse])
def get_homework_endpoint(group_subject_id: str, db: Session = Depends(get_db), teacher = Depends(require_teacher)):
    return get_homework_by_group_subject(db, group_subject_id)

@router.get("/homework/{homework_id}", response_model=HomeworkResponse)
def get_homework_by_id_endpoint(homework_id: str, db: Session = Depends(get_db), teacher = Depends(require_teacher)):
    homework = get_homework(db, homework_id)
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")
    return homework

# Homework Grading
@router.post("/homework-grades", response_model=HomeworkGradeResponse)
def create_homework_grade_endpoint(grade: HomeworkGradeCreate, db: Session = Depends(get_db), teacher = Depends(require_teacher)):
    return create_homework_grade(db, grade)

@router.get("/homework-grades", response_model=List[HomeworkGradeResponse])
def get_homework_grades_endpoint(student_id: str = None, homework_id: str = None, db: Session = Depends(get_db), teacher = Depends(require_teacher)):
    if student_id:
        return get_homework_grades_by_student(db, student_id)
    elif homework_id:
        return get_homework_grades_by_homework(db, homework_id)
    else:
        raise HTTPException(status_code=400, detail="Provide either student_id or homework_id")

# Exam Management
@router.post("/exams", response_model=ExamResponse)
def create_exam_endpoint(exam: ExamCreate, db: Session = Depends(get_db), teacher = Depends(require_teacher)):
    return create_exam(db, exam)

@router.get("/exams", response_model=List[ExamResponse])
def get_exams_endpoint(group_subject_id: str, db: Session = Depends(get_db), teacher = Depends(require_teacher)):
    return get_exams_by_group_subject(db, group_subject_id)

@router.get("/exams/{exam_id}", response_model=ExamResponse)
def get_exam_by_id_endpoint(exam_id: str, db: Session = Depends(get_db), teacher = Depends(require_teacher)):
    exam = get_exam(db, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam

# Exam Grading
@router.post("/exam-grades", response_model=ExamGradeResponse)
def create_exam_grade_endpoint(grade: ExamGradeCreate, db: Session = Depends(get_db), teacher = Depends(require_teacher)):
    return create_exam_grade(db, grade)

@router.get("/exam-grades", response_model=List[ExamGradeResponse])
def get_exam_grades_endpoint(student_id: str = None, exam_id: str = None, db: Session = Depends(get_db), teacher = Depends(require_teacher)):
    if student_id:
        return get_exam_grades_by_student(db, student_id)
    elif exam_id:
        return get_exam_grades_by_exam(db, exam_id)
    else:
        raise HTTPException(status_code=400, detail="Provide either student_id or exam_id")

# Attendance Management
@router.post("/attendance", response_model=AttendanceResponse)
def create_attendance_endpoint(attendance: AttendanceCreate, db: Session = Depends(get_db), teacher = Depends(require_teacher)):
    return create_attendance(db, attendance)

@router.get("/attendance", response_model=List[AttendanceResponse])
def get_attendance_endpoint(student_id: str = None, group_subject_id: str = None, date: str = None, db: Session = Depends(get_db), teacher = Depends(require_teacher)):
    if student_id:
        return get_attendance_by_student(db, student_id)
    elif group_subject_id and date:
        return get_attendance_by_group_subject_and_date(db, group_subject_id, date)
    else:
        raise HTTPException(status_code=400, detail="Provide either student_id or (group_subject_id and date)")

# Bulk Grading - NEW ENDPOINTS
@router.get("/homework/{homework_id}/grading-table", response_model=HomeworkGradingTable)
def get_homework_grading_table_endpoint(homework_id: str, db: Session = Depends(get_db), teacher = Depends(require_teacher)):
    table = get_homework_grading_table(db, homework_id)
    if not table:
        raise HTTPException(status_code=404, detail="Homework not found")
    return table

@router.get("/exams/{exam_id}/grading-table", response_model=ExamGradingTable)
def get_exam_grading_table_endpoint(exam_id: str, db: Session = Depends(get_db), teacher = Depends(require_teacher)):
    table = get_exam_grading_table(db, exam_id)
    if not table:
        raise HTTPException(status_code=404, detail="Exam not found")
    return table

@router.post("/homework/{homework_id}/bulk-grade")
def submit_bulk_homework_grades_endpoint(homework_id: str, grades: List[dict], db: Session = Depends(get_db), teacher = Depends(require_teacher)):
    results = submit_bulk_homework_grades(db, homework_id, grades)
    return {"message": f"Graded {len(results)} students", "results": results}

@router.post("/exams/{exam_id}/bulk-grade")
def submit_bulk_exam_grades_endpoint(exam_id: str, grades: List[dict], db: Session = Depends(get_db), teacher = Depends(require_teacher)):
    results = submit_bulk_exam_grades(db, exam_id, grades)
    return {"message": f"Graded {len(results)} students", "results": results}

@router.get("/students/{student_id}/recent-grades", response_model=RecentGradesResponse)
def get_student_recent_grades(student_id: str, db: Session = Depends(get_db), teacher = Depends(require_teacher)):
    result = get_recent_grades(db, student_id)
    if not result:
        raise HTTPException(status_code=404, detail="Student not found or no grades")
    return result

# Bulk Attendance - NEW ENDPOINTS
@router.get("/attendance/table", response_model=AttendanceTable)
def get_attendance_table_endpoint(group_subject_id: str, date: str, db: Session = Depends(get_db), teacher = Depends(require_teacher)):
    table = get_attendance_table(db, group_subject_id, date)
    if not table:
        raise HTTPException(status_code=404, detail="Group subject not found")
    return table

@router.post("/attendance/bulk")
def submit_bulk_attendance_endpoint(group_subject_id: str, date: str, attendance: List[dict], db: Session = Depends(get_db), teacher = Depends(require_teacher)):
    results = submit_bulk_attendance(db, group_subject_id, date, attendance)
    return {"message": f"Marked attendance for {len(results)} students", "results": results}