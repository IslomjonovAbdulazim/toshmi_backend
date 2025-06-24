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


class AttendanceRecord(BaseModel):
    student_id: int
    status: str


class BulkAttendanceRequest(BaseModel):
    group_subject_id: int
    date: date
    records: List[AttendanceRecord]


def verify_teacher_assignment(group_subject_id: int, teacher_id: int, db: Session):
    assignment = db.query(GroupSubject).filter(
        GroupSubject.id == group_subject_id,
        GroupSubject.teacher_id == teacher_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=403, detail="Not assigned to this group-subject")
    return assignment


def verify_teacher_homework(homework_id: int, teacher_id: int, db: Session):
    homework = db.query(Homework).join(Homework.group_subject).filter(
        Homework.id == homework_id,
        Homework.group_subject.has(teacher_id=teacher_id)
    ).first()
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")
    return homework


def verify_teacher_exam(exam_id: int, teacher_id: int, db: Session):
    exam = db.query(Exam).join(Exam.group_subject).filter(
        Exam.id == exam_id,
        Exam.group_subject.has(teacher_id=teacher_id)
    ).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam


@router.post("/homework")
def create_homework(request: HomeworkRequest, current_user: User = Depends(require_role(["teacher"])),
                    db: Session = Depends(get_db)):
    verify_teacher_assignment(request.group_subject_id, current_user.id, db)

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


@router.put("/homework/{homework_id}")
def update_homework(homework_id: int, request: HomeworkRequest,
                    current_user: User = Depends(require_role(["teacher"])), db: Session = Depends(get_db)):
    homework = verify_teacher_homework(homework_id, current_user.id, db)

    homework.title = request.title
    homework.description = request.description
    homework.due_date = request.due_date
    homework.max_points = request.max_points
    homework.external_links = request.external_links
    db.commit()
    return {"message": "Homework updated"}


@router.post("/exams")
def create_exam(request: ExamRequest, current_user: User = Depends(require_role(["teacher"])),
                db: Session = Depends(get_db)):
    verify_teacher_assignment(request.group_subject_id, current_user.id, db)

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


@router.put("/exams/{exam_id}")
def update_exam(exam_id: int, request: ExamRequest, current_user: User = Depends(require_role(["teacher"])),
                db: Session = Depends(get_db)):
    exam = verify_teacher_exam(exam_id, current_user.id, db)

    exam.title = request.title
    exam.description = request.description
    exam.exam_date = request.exam_date
    exam.max_points = request.max_points
    exam.external_links = request.external_links
    db.commit()
    return {"message": "Exam updated"}


@router.get("/homework")
def get_my_homework(current_user: User = Depends(require_role(["teacher"])), db: Session = Depends(get_db)):
    return [
        {
            "id": h.id,
            "title": h.title,
            "due_date": h.due_date,
            "max_points": h.max_points,
            "subject": h.group_subject.subject.name,
            "group": h.group_subject.group.name,
            "group_subject_id": h.group_subject_id
        } for h in current_user.group_subjects for h in h.homework
    ]


@router.get("/exams")
def get_my_exams(current_user: User = Depends(require_role(["teacher"])), db: Session = Depends(get_db)):
    return [
        {
            "id": e.id,
            "title": e.title,
            "exam_date": e.exam_date,
            "max_points": e.max_points,
            "subject": e.group_subject.subject.name,
            "group": e.group_subject.group.name,
            "group_subject_id": e.group_subject_id
        } for gs in current_user.group_subjects for e in gs.exams
    ]


@router.get("/homework/{homework_id}/grading-table")
def get_grading_table(homework_id: int, current_user: User = Depends(require_role(["teacher"])),
                      db: Session = Depends(get_db)):
    homework = verify_teacher_homework(homework_id, current_user.id, db)

    students = homework.group_subject.group.students
    grade_map = {g.student_id: g for g in homework.grades}

    return {
        "homework": {
            "id": homework.id,
            "title": homework.title,
            "max_points": homework.max_points
        },
        "students": [
            {
                "student_id": s.id,
                "name": s.user.full_name,
                "grade": {
                    "points": grade_map[s.id].points if s.id in grade_map else None,
                    "comment": grade_map[s.id].comment if s.id in grade_map else ""
                }
            } for s in students
        ]
    }


@router.get("/exams/{exam_id}/grading-table")
def get_exam_grading_table(exam_id: int, current_user: User = Depends(require_role(["teacher"])),
                           db: Session = Depends(get_db)):
    exam = verify_teacher_exam(exam_id, current_user.id, db)

    students = exam.group_subject.group.students
    grade_map = {g.student_id: g for g in exam.grades}

    return {
        "exam": {
            "id": exam.id,
            "title": exam.title,
            "max_points": exam.max_points
        },
        "students": [
            {
                "student_id": s.id,
                "name": s.user.full_name,
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
        homework = verify_teacher_homework(request.homework_id, current_user.id, db)
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
        exam = verify_teacher_exam(request.exam_id, current_user.id, db)
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


@router.post("/bulk-attendance")
def bulk_attendance(request: BulkAttendanceRequest, current_user: User = Depends(require_role(["teacher"])),
                    db: Session = Depends(get_db)):
    verify_teacher_assignment(request.group_subject_id, current_user.id, db)

    for record in request.records:
        existing = db.query(Attendance).filter(
            Attendance.student_id == record.student_id,
            Attendance.group_subject_id == request.group_subject_id,
            Attendance.date == request.date
        ).first()

        if existing:
            existing.status = record.status
        else:
            attendance = Attendance(
                student_id=record.student_id,
                group_subject_id=request.group_subject_id,
                date=request.date,
                status=record.status
            )
            db.add(attendance)

    db.commit()
    return {"message": "Attendance recorded"}


@router.delete("/homework/{homework_id}")
def delete_homework(homework_id: int, current_user: User = Depends(require_role(["teacher"])),
                    db: Session = Depends(get_db)):
    homework = verify_teacher_homework(homework_id, current_user.id, db)

    if homework.grades:
        raise HTTPException(status_code=400, detail="Cannot delete homework with existing grades")

    db.delete(homework)
    db.commit()
    return {"message": "Homework deleted"}


@router.delete("/exams/{exam_id}")
def delete_exam(exam_id: int, current_user: User = Depends(require_role(["teacher"])),
                db: Session = Depends(get_db)):
    exam = verify_teacher_exam(exam_id, current_user.id, db)

    if exam.grades:
        raise HTTPException(status_code=400, detail="Cannot delete exam with existing grades")

    db.delete(exam)
    db.commit()
    return {"message": "Exam deleted"}


@router.get("/groups/{group_id}/students")
def get_group_students(group_id: int, current_user: User = Depends(require_role(["teacher"])),
                       db: Session = Depends(get_db)):
    assignment = db.query(GroupSubject).filter(
        GroupSubject.group_id == group_id,
        GroupSubject.teacher_id == current_user.id
    ).first()

    if not assignment:
        raise HTTPException(status_code=403, detail="Not assigned to this group")

    return [
        {
            "id": s.id,
            "name": s.user.full_name,
            "phone": s.user.phone
        } for s in assignment.group.students
    ]