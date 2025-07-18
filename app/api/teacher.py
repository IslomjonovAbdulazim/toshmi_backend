from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload, selectinload
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
from app.database import get_db
from app.models.models import User, Student, Group, Homework, Exam, HomeworkGrade, ExamGrade, Attendance, GroupSubject, \
    Subject, Schedule
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


class BulkHomeworkGradeRequest(BaseModel):
    homework_id: int
    grades: List[GradeRequest]


class BulkExamGradeRequest(BaseModel):
    exam_id: int
    grades: List[GradeRequest]


class AttendanceRecord(BaseModel):
    student_id: int
    status: str


class BulkAttendanceRequest(BaseModel):
    group_subject_id: int
    date: date
    records: List[AttendanceRecord]


# NEW RESPONSE MODELS FOR THE NEW ENDPOINTS
class GroupSubjectResponse(BaseModel):
    id: int
    group_id: int
    subject_id: int
    teacher_id: int
    group_name: str
    subject_name: str
    subject_code: str

    class Config:
        from_attributes = True


class ScheduleResponse(BaseModel):
    id: int
    day: int
    day_name: str
    start_time: str  # HH:MM:SS format
    end_time: str  # HH:MM:SS format
    room: str

    class Config:
        from_attributes = True


def verify_teacher_assignment(group_subject_id: int, teacher_id: int, db: Session):
    assignment = db.query(GroupSubject).options(
        joinedload(GroupSubject.group),
        joinedload(GroupSubject.subject)
    ).filter(
        GroupSubject.id == group_subject_id,
        GroupSubject.teacher_id == teacher_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=403, detail="Not assigned to this group-subject")
    return assignment


def verify_teacher_homework(homework_id: int, teacher_id: int, db: Session):
    homework = db.query(Homework).options(
        joinedload(Homework.group_subject).joinedload(GroupSubject.group),
        joinedload(Homework.group_subject).joinedload(GroupSubject.subject),
        selectinload(Homework.grades)
    ).filter(
        Homework.id == homework_id,
        Homework.group_subject.has(teacher_id=teacher_id)
    ).first()
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")
    return homework


def verify_teacher_exam(exam_id: int, teacher_id: int, db: Session):
    exam = db.query(Exam).options(
        joinedload(Exam.group_subject).joinedload(GroupSubject.group),
        joinedload(Exam.group_subject).joinedload(GroupSubject.subject),
        selectinload(Exam.grades)
    ).filter(
        Exam.id == exam_id,
        Exam.group_subject.has(teacher_id=teacher_id)
    ).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam


# NEW ENDPOINT 1: Get teacher's group-subjects
@router.get("/group-subjects", response_model=List[GroupSubjectResponse])
def get_teacher_group_subjects(
        current_user: User = Depends(require_role(["teacher"])),
        db: Session = Depends(get_db)
):
    """
    Get all group-subjects assigned to the current teacher.
    Teacher can use this to see which groups they teach and what subjects.
    """
    try:
        # Query group-subjects for this teacher with joined data
        group_subjects = db.query(GroupSubject).options(
            joinedload(GroupSubject.group),
            joinedload(GroupSubject.subject)
        ).filter(GroupSubject.teacher_id == current_user.id).order_by(
            GroupSubject.group_id, GroupSubject.subject_id
        ).all()

        # Format response
        response_data = []
        for gs in group_subjects:
            response_data.append(GroupSubjectResponse(
                id=gs.id,
                group_id=gs.group_id,
                subject_id=gs.subject_id,
                teacher_id=gs.teacher_id,
                group_name=gs.group.name,
                subject_name=gs.subject.name,
                subject_code=gs.subject.code
            ))

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving group-subjects")


# NEW ENDPOINT 2: Get schedule for a specific group-subject
@router.get("/group-subjects/{group_subject_id}/schedule", response_model=List[ScheduleResponse])
def get_group_subject_schedule(
        group_subject_id: int,
        current_user: User = Depends(require_role(["teacher"])),
        db: Session = Depends(get_db)
):
    """
    Get schedule (dates and times) for a specific group-subject.
    Teacher uses this for attendance - first selects group-subject, then gets times.
    """
    try:
        # Verify this group-subject belongs to the teacher
        group_subject = db.query(GroupSubject).filter(
            GroupSubject.id == group_subject_id,
            GroupSubject.teacher_id == current_user.id
        ).first()

        if not group_subject:
            raise HTTPException(status_code=404, detail="Group-subject not found or not assigned to you")

        # Get schedule for this group-subject
        schedules = db.query(Schedule).filter(
            Schedule.group_subject_id == group_subject_id
        ).order_by(Schedule.day, Schedule.start_time).all()

        # Format response with day names
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        response_data = []
        for schedule in schedules:
            response_data.append(ScheduleResponse(
                id=schedule.id,
                day=schedule.day,
                day_name=day_names[schedule.day],
                start_time=str(schedule.start_time),
                end_time=str(schedule.end_time),
                room=schedule.room or ""
            ))

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving schedule")


@router.post("/homework")
def create_homework(request: HomeworkRequest, current_user: User = Depends(require_role(["teacher"])),
                    db: Session = Depends(get_db)):
    assignment = verify_teacher_assignment(request.group_subject_id, current_user.id, db)

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
    assignment = verify_teacher_assignment(request.group_subject_id, current_user.id, db)

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
    homework_list = db.query(Homework).options(
        joinedload(Homework.group_subject).joinedload(GroupSubject.group),
        joinedload(Homework.group_subject).joinedload(GroupSubject.subject)
    ).join(GroupSubject).filter(GroupSubject.teacher_id == current_user.id).all()

    result = []
    for h in homework_list:
        # Count graded students
        graded_count = db.query(HomeworkGrade).filter(HomeworkGrade.homework_id == h.id).count()

        # Count total students in group
        total_students = db.query(Student).filter(Student.group_id == h.group_subject.group_id).count()

        result.append({
            "id": h.id,
            "title": h.title,
            "description": h.description,
            "due_date": h.due_date,
            "max_points": h.max_points,
            "external_links": h.external_links,
            "subject": h.group_subject.subject.name,
            "group": h.group_subject.group.name,
            "group_subject_id": h.group_subject_id,
            "graded_count": graded_count,
            "total_students": total_students
        })

    return result


@router.get("/exams")
def get_my_exams(current_user: User = Depends(require_role(["teacher"])), db: Session = Depends(get_db)):
    exam_list = db.query(Exam).options(
        joinedload(Exam.group_subject).joinedload(GroupSubject.group),
        joinedload(Exam.group_subject).joinedload(GroupSubject.subject)
    ).join(GroupSubject).filter(GroupSubject.teacher_id == current_user.id).all()

    result = []
    for e in exam_list:
        # Count graded students
        graded_count = db.query(ExamGrade).filter(ExamGrade.exam_id == e.id).count()

        # Count total students in group
        total_students = db.query(Student).filter(Student.group_id == e.group_subject.group_id).count()

        result.append({
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "exam_date": e.exam_date,
            "max_points": e.max_points,
            "external_links": e.external_links,
            "subject": e.group_subject.subject.name,
            "group": e.group_subject.group.name,
            "group_subject_id": e.group_subject_id,
            "graded_count": graded_count,
            "total_students": total_students
        })

    return result

@router.get("/homework/{homework_id}/grading-table")
def get_grading_table(homework_id: int, current_user: User = Depends(require_role(["teacher"])),
                      db: Session = Depends(get_db)):
    homework = verify_teacher_homework(homework_id, current_user.id, db)
    students = db.query(Student).options(joinedload(Student.user)).filter(
        Student.group_id == homework.group_subject.group_id
    ).all()
    grade_map = {g.student_id: g for g in homework.grades}

    return {
        "homework": {"id": homework.id, "title": homework.title, "max_points": homework.max_points},
        "students": [{
            "student_id": s.id,
            "name": s.user.full_name,
            "grade": {
                "points": grade_map[s.id].points if s.id in grade_map else None,
                "comment": grade_map[s.id].comment if s.id in grade_map else ""
            }
        } for s in students]
    }


@router.get("/exams/{exam_id}/grading-table")
def get_exam_grading_table(exam_id: int, current_user: User = Depends(require_role(["teacher"])),
                           db: Session = Depends(get_db)):
    exam = verify_teacher_exam(exam_id, current_user.id, db)
    students = db.query(Student).options(joinedload(Student.user)).filter(
        Student.group_id == exam.group_subject.group_id
    ).all()
    grade_map = {g.student_id: g for g in exam.grades}

    return {
        "exam": {"id": exam.id, "title": exam.title, "max_points": exam.max_points},
        "students": [{
            "student_id": s.id,
            "name": s.user.full_name,
            "grade": {
                "points": grade_map[s.id].points if s.id in grade_map else None,
                "comment": grade_map[s.id].comment if s.id in grade_map else ""
            }
        } for s in students]
    }


@router.get("/attendance-table")
def get_attendance_table(group_subject_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None,
                         current_user: User = Depends(require_role(["teacher"])), db: Session = Depends(get_db)):
    assignment = verify_teacher_assignment(group_subject_id, current_user.id, db)

    students = db.query(Student).options(joinedload(Student.user)).filter(
        Student.group_id == assignment.group_id
    ).all()

    attendance_query = db.query(Attendance).filter(
        Attendance.group_subject_id == group_subject_id
    )

    if start_date:
        attendance_query = attendance_query.filter(Attendance.date >= start_date)
    if end_date:
        attendance_query = attendance_query.filter(Attendance.date <= end_date)

    attendance_records = attendance_query.all()

    attendance_map = {}
    dates_set = set()

    for record in attendance_records:
        dates_set.add(record.date)
        if record.student_id not in attendance_map:
            attendance_map[record.student_id] = {}
        attendance_map[record.student_id][record.date] = record.status

    sorted_dates = sorted(list(dates_set))

    student_attendance = []
    for student in students:
        student_data = {
            "student_id": student.id,
            "name": student.user.full_name,
            "attendance_by_date": {},
            "summary": {"present": 0, "absent": 0, "late": 0, "excused": 0, "total_days": len(sorted_dates)}
        }

        for date in sorted_dates:
            status = attendance_map.get(student.id, {}).get(date, "not_recorded")
            student_data["attendance_by_date"][str(date)] = status

            if status in student_data["summary"]:
                student_data["summary"][status] += 1

        student_attendance.append(student_data)

    return {
        "group_subject": {
            "id": assignment.id,
            "group_name": assignment.group.name,
            "subject_name": assignment.subject.name
        },
        "date_range": {
            "start_date": start_date,
            "end_date": end_date,
            "total_dates": len(sorted_dates)
        },
        "dates": [str(d) for d in sorted_dates],
        "students": student_attendance
    }


@router.post("/bulk-homework-grades")
def bulk_homework_grades(request: BulkHomeworkGradeRequest, current_user: User = Depends(require_role(["teacher"])),
                         db: Session = Depends(get_db)):
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

    db.commit()
    return {"message": "Homework grades recorded"}


@router.post("/bulk-exam-grades")
def bulk_exam_grades(request: BulkExamGradeRequest, current_user: User = Depends(require_role(["teacher"])),
                     db: Session = Depends(get_db)):
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
    return {"message": "Exam grades recorded"}


@router.post("/bulk-attendance")
def bulk_attendance(request: BulkAttendanceRequest, current_user: User = Depends(require_role(["teacher"])),
                    db: Session = Depends(get_db)):
    assignment = verify_teacher_assignment(request.group_subject_id, current_user.id, db)

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
    assignment = db.query(GroupSubject).options(
        joinedload(GroupSubject.group).selectinload(Group.students).joinedload(Student.user)
    ).filter(
        GroupSubject.group_id == group_id,
        GroupSubject.teacher_id == current_user.id
    ).first()

    if not assignment:
        raise HTTPException(status_code=403, detail="Not assigned to this group")

    return [{"id": s.id, "name": s.user.full_name, "phone": s.user.phone} for s in assignment.group.students]