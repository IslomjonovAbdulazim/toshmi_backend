from sqlalchemy.orm import Session
from app.models import Homework, HomeworkGrade, Exam, ExamGrade
from app.schemas import HomeworkCreate, HomeworkGradeCreate, ExamCreate, ExamGradeCreate
import uuid

def create_homework(db: Session, homework: HomeworkCreate):
    db_homework = Homework(
        id=str(uuid.uuid4()),
        group_subject_id=homework.group_subject_id,
        title=homework.title,
        description=homework.description,
        due_date=homework.due_date
    )
    db.add(db_homework)
    db.commit()
    db.refresh(db_homework)
    return db_homework

def get_homework_by_group_subject(db: Session, group_subject_id: str):
    return db.query(Homework).filter(Homework.group_subject_id == group_subject_id).all()

def get_homework(db: Session, homework_id: str):
    return db.query(Homework).filter(Homework.id == homework_id).first()

def create_homework_grade(db: Session, grade: HomeworkGradeCreate):
    db_grade = HomeworkGrade(
        id=str(uuid.uuid4()),
        homework_id=grade.homework_id,
        student_id=grade.student_id,
        grade=grade.grade,
        comment=grade.comment
    )
    db.add(db_grade)
    db.commit()
    db.refresh(db_grade)
    return db_grade

def get_homework_grades_by_student(db: Session, student_id: str):
    return db.query(HomeworkGrade).filter(HomeworkGrade.student_id == student_id).all()

def get_homework_grades_by_homework(db: Session, homework_id: str):
    return db.query(HomeworkGrade).filter(HomeworkGrade.homework_id == homework_id).all()

def create_exam(db: Session, exam: ExamCreate):
    db_exam = Exam(
        id=str(uuid.uuid4()),
        group_subject_id=exam.group_subject_id,
        title=exam.title,
        exam_date=exam.exam_date
    )
    db.add(db_exam)
    db.commit()
    db.refresh(db_exam)
    return db_exam

def get_exams_by_group_subject(db: Session, group_subject_id: str):
    return db.query(Exam).filter(Exam.group_subject_id == group_subject_id).all()

def get_exam(db: Session, exam_id: str):
    return db.query(Exam).filter(Exam.id == exam_id).first()

def create_exam_grade(db: Session, grade: ExamGradeCreate):
    db_grade = ExamGrade(
        id=str(uuid.uuid4()),
        exam_id=grade.exam_id,
        student_id=grade.student_id,
        grade=grade.grade,
        comment=grade.comment
    )
    db.add(db_grade)
    db.commit()
    db.refresh(db_grade)
    return db_grade

def get_exam_grades_by_student(db: Session, student_id: str):
    return db.query(ExamGrade).filter(ExamGrade.student_id == student_id).all()

def get_exam_grades_by_exam(db: Session, exam_id: str):
    return db.query(ExamGrade).filter(ExamGrade.exam_id == exam_id).all()