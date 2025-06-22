from sqlalchemy.orm import Session
from app.models import *
from app.schemas import *
from app.crud import create_homework_grade, create_exam_grade, create_attendance
import uuid


def get_homework_grading_table(db: Session, homework_id: str):
    # Get homework info
    homework = db.query(Homework).filter(Homework.id == homework_id).first()
    if not homework:
        return None

    # Get group from group_subject
    group_subject = db.query(GroupSubject).filter(GroupSubject.id == homework.group_subject_id).first()
    if not group_subject:
        return None

    # Get students in the group
    students = db.query(Student).filter(Student.group_id == group_subject.group_id).all()

    student_rows = []
    for student in students:
        # Get user info for student name
        user = db.query(User).filter(User.id == student.user_id).first()

        # Get existing grade if any
        existing_grade = db.query(HomeworkGrade).filter(
            HomeworkGrade.homework_id == homework_id,
            HomeworkGrade.student_id == student.id
        ).first()

        student_rows.append(StudentGradeRow(
            student_id=student.id,
            student_name=user.full_name if user else "Unknown",
            current_grade=existing_grade.grade if existing_grade else None,
            current_comment=existing_grade.comment if existing_grade else None
        ))

    return HomeworkGradingTable(
        homework_id=homework_id,
        homework_title=homework.title,
        students=student_rows
    )


def get_exam_grading_table(db: Session, exam_id: str):
    # Get exam info
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        return None

    # Get group from group_subject
    group_subject = db.query(GroupSubject).filter(GroupSubject.id == exam.group_subject_id).first()
    if not group_subject:
        return None

    # Get students in the group
    students = db.query(Student).filter(Student.group_id == group_subject.group_id).all()

    student_rows = []
    for student in students:
        # Get user info for student name
        user = db.query(User).filter(User.id == student.user_id).first()

        # Get existing grade if any
        existing_grade = db.query(ExamGrade).filter(
            ExamGrade.exam_id == exam_id,
            ExamGrade.student_id == student.id
        ).first()

        student_rows.append(StudentGradeRow(
            student_id=student.id,
            student_name=user.full_name if user else "Unknown",
            current_grade=existing_grade.grade if existing_grade else None,
            current_comment=existing_grade.comment if existing_grade else None
        ))

    return ExamGradingTable(
        exam_id=exam_id,
        exam_title=exam.title,
        students=student_rows
    )


def submit_bulk_homework_grades(db: Session, homework_id: str, grades: list):
    results = []
    for grade_data in grades:
        # Check if grade already exists
        existing = db.query(HomeworkGrade).filter(
            HomeworkGrade.homework_id == homework_id,
            HomeworkGrade.student_id == grade_data["student_id"]
        ).first()

        if existing:
            # Update existing grade
            existing.grade = grade_data["grade"]
            existing.comment = grade_data.get("comment")
            db.commit()
            results.append(existing)
        else:
            # Create new grade
            grade_create = HomeworkGradeCreate(
                homework_id=homework_id,
                student_id=grade_data["student_id"],
                grade=grade_data["grade"],
                comment=grade_data.get("comment")
            )
            new_grade = create_homework_grade(db, grade_create)
            results.append(new_grade)

    return results


def submit_bulk_exam_grades(db: Session, exam_id: str, grades: list):
    results = []
    for grade_data in grades:
        # Check if grade already exists
        existing = db.query(ExamGrade).filter(
            ExamGrade.exam_id == exam_id,
            ExamGrade.student_id == grade_data["student_id"]
        ).first()

        if existing:
            # Update existing grade
            existing.grade = grade_data["grade"]
            existing.comment = grade_data.get("comment")
            db.commit()
            results.append(existing)
        else:
            # Create new grade
            grade_create = ExamGradeCreate(
                exam_id=exam_id,
                student_id=grade_data["student_id"],
                grade=grade_data["grade"],
                comment=grade_data.get("comment")
            )
            new_grade = create_exam_grade(db, grade_create)
            results.append(new_grade)

    return results


# Bulk Attendance Functions
def get_attendance_table(db: Session, group_subject_id: str, date: str):
    # Get group_subject info
    group_subject = db.query(GroupSubject).filter(GroupSubject.id == group_subject_id).first()
    if not group_subject:
        return None

    group = db.query(Group).filter(Group.id == group_subject.group_id).first()
    subject = db.query(Subject).filter(Subject.id == group_subject.subject_id).first()

    # Get students in the group
    students = db.query(Student).filter(Student.group_id == group_subject.group_id).all()

    student_rows = []
    for student in students:
        # Get user info for student name
        user = db.query(User).filter(User.id == student.user_id).first()

        # Get existing attendance if any
        existing_attendance = db.query(Attendance).filter(
            Attendance.student_id == student.id,
            Attendance.group_subject_id == group_subject_id,
            Attendance.date == date
        ).first()

        student_rows.append(StudentAttendanceRow(
            student_id=student.id,
            student_name=user.full_name if user else "Unknown",
            current_status=existing_attendance.status if existing_attendance else None,
            current_comment=existing_attendance.comment if existing_attendance else None
        ))

    return AttendanceTable(
        group_subject_id=group_subject_id,
        subject_name=subject.name if subject else "Unknown",
        group_name=group.name if group else "Unknown",
        date=date,
        students=student_rows
    )


def submit_bulk_attendance(db: Session, group_subject_id: str, date: str, attendance_data: list):
    from datetime import datetime

    date_obj = datetime.fromisoformat(date) if isinstance(date, str) else date
    results = []

    for attendance_item in attendance_data:
        # Check if attendance already exists
        existing = db.query(Attendance).filter(
            Attendance.student_id == attendance_item["student_id"],
            Attendance.group_subject_id == group_subject_id,
            Attendance.date == date_obj
        ).first()

        if existing:
            # Update existing attendance
            existing.status = attendance_item["status"]
            existing.comment = attendance_item.get("comment")
            db.commit()
            results.append(existing)
        else:
            # Create new attendance
            attendance_create = AttendanceCreate(
                student_id=attendance_item["student_id"],
                group_subject_id=group_subject_id,
                date=date_obj,
                status=attendance_item["status"],
                comment=attendance_item.get("comment")
            )
            new_attendance = create_attendance(db, attendance_create)
            results.append(new_attendance)

    return results