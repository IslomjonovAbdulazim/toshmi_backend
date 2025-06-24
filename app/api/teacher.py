from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime, date
from app.database import get_db
from app.models.models import User, Student, Homework, Exam, HomeworkGrade, ExamGrade, Attendance, GroupSubject
from app.core.security import require_role

router = APIRouter()


class HomeworkRequest(BaseModel):
    group_subject_id: int
    title: str
    description: str
    due_date: datetime
    max_points: int = 100
    external_links: List[str] = []


class ExamRequest(BaseModel):
    group_subject_id: int
    title: str
    description: str
    exam_date: datetime
    max_points: int = 100
    external_links: List[str] = []


class GradeRequest(BaseModel):
    student_id: int
    points: int
    comment: str = ""


class BulkGradeRequest(BaseModel):
    homework_id: int = None
    exam_id: int = None
    grades: List[GradeRequest]


class AttendanceRequest(BaseModel):
    group_subject_id: int
    date: date
    records: List[dict]  # [{"student_id": 1, "status": "present"}]


@router.post("/homework")
def create_homework(request: HomeworkRequest, current_user: User = Depends(require_role(["teacher"])),
                    db: Session = Depends(get_db)):
    assignment = db.query(GroupSubject).filter(
        GroupSubject.id == request.group_subject_id,
        GroupSubject.teacher_id == current_user.id
    ).first()

    if not assignment:
        raise HTTPException(status_code=403, detail="Not assigned to this group-subject")

    homework = Homework(
        group_subject_id=request.group_subject_id,
        title=request.title,
        description=request.description,
        due_date=request.due_date,
        max_points=request.max_points,
        external_links=request.external_links
    )
    db.add(homework)
    db.commit()
    return {"message": "Homework created", "id": homework.id}


@router.post("/exams")
def create_exam(request: ExamRequest, current_user: User = Depends(require_role(["teacher"])),
                db: Session = Depends(get_db)):
    assignment = db.query(GroupSubject).filter(
        GroupSubject.id == request.group_subject_id,
        GroupSubject.teacher_id == current_user.id
    ).first()

    if not assignment:
        raise HTTPException(status_code=403, detail="Not assigned to this group-subject")

    exam = Exam(
        group_subject_id=request.group_subject_id,
        title=request.title,
        description=request.description,
        exam_date=request.exam_date,
        max_points=request.max_points,
        external_links=request.external_links
    )
    db.add(exam)
    db.commit()
    return {"message": "Exam created", "id": exam.id}


@router.get("/homework")
def get_my_homework(current_user: User = Depends(require_role(["teacher"])), db: Session = Depends(get_db)):
    homework = db.query(Homework).join(GroupSubject).filter(
        GroupSubject.teacher_id == current_user.id
    ).all()

    return [
        {
            "id": h.id,
            "title": h.title,
            "due_date": h.due_date,
            "max_points": h.max_points,
            "group_subject_id": h.group_subject_id
        } for h in homework
    ]


@router.get("/homework/{homework_id}/grading-table")
def get_grading_table(homework_id: int, current_user: User = Depends(require_role(["teacher"])),
                      db: Session = Depends(get_db)):
    homework = db.query(Homework).join(GroupSubject).filter(
        Homework.id == homework_id,
        GroupSubject.teacher_id == current_user.id
    ).first()

    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")

    students = db.query(Student).join(User).filter(
        Student.group_id == homework.group_subject.group_id
    ).all()

    grades = db.query(HomeworkGrade).filter(
        HomeworkGrade.homework_id == homework_id
    ).all()

    grade_map = {g.student_id: g for g in grades}

    return {
        "homework": {
            "id": homework.id,
            "title": homework.title,
            "max_points": homework.max_points
        },
        "students": [
            {
                "student_id": s.id,
                "name": f"{s.user.first_name} {s.user.last_name}",
                "grade": {
                    "points": grade_map[s.id].points if s.id in grade_map else None,
                    "comment": grade_map[s.id].comment if s.id in grade_map else ""
                }
            } for s in students
        ]
    }


@router.post("/bulk-grade")
def bulk_grade(request: BulkGradeRequest, current_user: User = Depends(require_role(["teacher"])),
               db: Session = Depends(get_db)):
    if request.homework_id:
        homework = db.query(Homework).join(GroupSubject).filter(
            Homework.id == request.homework_id,
            GroupSubject.teacher_id == current_user.id
        ).first()
        if not homework:
            raise HTTPException(status_code=404, detail="Homework not found")

        for grade_data in request.grades:
            existing = db.query(HomeworkGrade).filter(
                HomeworkGrade.homework_id == request.homework_id,
                HomeworkGrade.student_id == grade_data.student_id
            ).first()

            if existing:
                existing.points = grade_data.points
                existing.comment = grade_data.comment
                existing.graded_at = datetime.utcnow()
            else:
                grade = HomeworkGrade(
                    student_id=grade_data.student_id,
                    homework_id=request.homework_id,
                    points=grade_data.points,
                    comment=grade_data.comment
                )
                db.add(grade)

    elif request.exam_id:
        exam = db.query(Exam).join(GroupSubject).filter(
            Exam.id == request.exam_id,
            GroupSubject.teacher_id == current_user.id
        ).first()
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")

        for grade_data in request.grades:
            existing = db.query(ExamGrade).filter(
                ExamGrade.exam_id == request.exam_id,
                ExamGrade.student_id == grade_data.student_id
            ).first()

            if existing:
                existing.points = grade_data.points
                existing.comment = grade_data.comment
                existing.graded_at = datetime.utcnow()
            else:
                grade = ExamGrade(
                    student_id=grade_data.student_id,
                    exam_id=request.exam_id,
                    points=grade_data.points,
                    comment=grade_data.comment
                )
                db.add(grade)

    db.commit()
    return {"message": "Grades recorded"}


@router.post("/attendance")
def record_attendance(request: AttendanceRequest, current_user: User = Depends(require_role(["teacher"])),
                      db: Session = Depends(get_db)):
    assignment = db.query(GroupSubject).filter(
        GroupSubject.id == request.group_subject_id,
        GroupSubject.teacher_id == current_user.id
    ).first()

    if not assignment:
        raise HTTPException(status_code=403, detail="Not assigned to this group-subject")

    for record in request.records:
        existing = db.query(Attendance).filter(
            Attendance.student_id == record["student_id"],
            Attendance.group_subject_id == request.group_subject_id,
            Attendance.date == request.date
        ).first()

        if existing:
            existing.status = record["status"]
        else:
            attendance = Attendance(
                student_id=record["student_id"],
                group_subject_id=request.group_subject_id,
                date=request.date,
                status=record["status"]
            )
            db.add(attendance)

    db.commit()
    return {"message": "Attendance recorded"}