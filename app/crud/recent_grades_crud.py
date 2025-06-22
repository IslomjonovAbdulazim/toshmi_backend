from sqlalchemy.orm import Session
from app.models import Student, User, HomeworkGrade, ExamGrade, Homework, Exam, GroupSubject, Subject
from app.schemas import RecentGradesResponse, RecentGradeItem


def get_recent_grades(db: Session, student_id: str, limit: int = 20):
    # Get student info
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return None

    user = db.query(User).filter(User.id == student.user_id).first()
    student_name = user.full_name if user else "Unknown"

    recent_grades = []

    # Get homework grades
    homework_grades = (
        db.query(HomeworkGrade, Homework, GroupSubject, Subject)
        .join(Homework, HomeworkGrade.homework_id == Homework.id)
        .join(GroupSubject, Homework.group_subject_id == GroupSubject.id)
        .join(Subject, GroupSubject.subject_id == Subject.id)
        .filter(HomeworkGrade.student_id == student_id)
        .order_by(HomeworkGrade.graded_at.desc())
        .limit(limit)
        .all()
    )

    for hw_grade, homework, group_subject, subject in homework_grades:
        recent_grades.append(RecentGradeItem(
            id=hw_grade.id,
            type="homework",
            title=homework.title,
            subject_name=subject.name,
            grade=hw_grade.grade,
            comment=hw_grade.comment,
            graded_at=hw_grade.graded_at
        ))

    # Get exam grades
    exam_grades = (
        db.query(ExamGrade, Exam, GroupSubject, Subject)
        .join(Exam, ExamGrade.exam_id == Exam.id)
        .join(GroupSubject, Exam.group_subject_id == GroupSubject.id)
        .join(Subject, GroupSubject.subject_id == Subject.id)
        .filter(ExamGrade.student_id == student_id)
        .order_by(ExamGrade.graded_at.desc())
        .limit(limit)
        .all()
    )

    for exam_grade, exam, group_subject, subject in exam_grades:
        recent_grades.append(RecentGradeItem(
            id=exam_grade.id,
            type="exam",
            title=exam.title,
            subject_name=subject.name,
            grade=exam_grade.grade,
            comment=exam_grade.comment,
            graded_at=exam_grade.graded_at
        ))

    # Sort all grades by graded_at date (most recent first)
    recent_grades.sort(key=lambda x: x.graded_at, reverse=True)

    # Limit to requested number
    recent_grades = recent_grades[:limit]

    return RecentGradesResponse(
        student_id=student_id,
        student_name=student_name,
        grades=recent_grades
    )