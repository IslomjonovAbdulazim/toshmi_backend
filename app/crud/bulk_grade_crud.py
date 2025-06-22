from sqlalchemy.orm import Session
from app.models import Homework, Exam, Student, User, HomeworkGrade, ExamGrade, GroupSubject
from app.schemas import StudentGradeRow, HomeworkGradingTable, ExamGradingTable, BulkGradeSubmission, \
    HomeworkGradeCreate, ExamGradeCreate
from app.crud import create_homework_grade, create_exam_grade
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