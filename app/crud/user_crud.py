from sqlalchemy.orm import Session
from app.models import User, Student, Parent, Teacher
from app.schemas import UserCreate, StudentCreate, ParentCreate, TeacherCreate
import uuid

def create_user(db: Session, user: UserCreate):
    db_user = User(
        id=str(uuid.uuid4()),
        role=user.role,
        phone=user.phone,
        full_name=user.full_name,
        avatar_url=user.avatar_url
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: str):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_phone(db: Session, phone: int, role: str):
    return db.query(User).filter(User.phone == phone, User.role == role).first()

def get_users_by_role(db: Session, role: str):
    return db.query(User).filter(User.role == role).all()

def create_student(db: Session, student: StudentCreate):
    db_student = Student(
        id=str(uuid.uuid4()),
        user_id=student.user_id,
        group_id=student.group_id,
        parent_id=student.parent_id,
        graduation_year=student.graduation_year
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

def get_student(db: Session, student_id: str):
    return db.query(Student).filter(Student.id == student_id).first()

def get_students_by_group(db: Session, group_id: str):
    return db.query(Student).filter(Student.group_id == group_id).all()

def create_parent(db: Session, parent: ParentCreate):
    db_parent = Parent(
        id=str(uuid.uuid4()),
        user_id=parent.user_id,
        student_ids=parent.student_ids
    )
    db.add(db_parent)
    db.commit()
    db.refresh(db_parent)
    return db_parent

def get_parent(db: Session, parent_id: str):
    return db.query(Parent).filter(Parent.id == parent_id).first()

def create_teacher(db: Session, teacher: TeacherCreate):
    db_teacher = Teacher(
        id=str(uuid.uuid4()),
        user_id=teacher.user_id,
        group_subject_ids=teacher.group_subject_ids
    )
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher

def get_teacher(db: Session, teacher_id: str):
    return db.query(Teacher).filter(Teacher.id == teacher_id).first()