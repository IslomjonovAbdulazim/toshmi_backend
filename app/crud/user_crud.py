# app/crud/user_crud.py
from sqlalchemy.orm import Session
from app.models import User, Student, Parent, Teacher
from app.schemas import StudentCreate, ParentCreate, TeacherCreate
from app.utils.password import hash_password, verify_password
import uuid


def authenticate_user(db: Session, phone: int, role: str, password: str):
    user = db.query(User).filter(User.phone == phone, User.role == role).first()
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user


def get_user(db: Session, user_id: str):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_phone(db: Session, phone: int, role: str):
    return db.query(User).filter(User.phone == phone, User.role == role).first()


def reset_user_password(db: Session, phone: int, role: str, new_password: str):
    user = db.query(User).filter(User.phone == phone, User.role == role).first()
    if user:
        user.password_hash = hash_password(new_password)
        db.commit()
        db.refresh(user)
        return user
    return None


# STUDENT CRUD
def create_student(db: Session, student_data: StudentCreate):
    # Create user first
    user = User(
        id=str(uuid.uuid4()),
        role="student",
        phone=student_data.phone,
        password_hash=hash_password(student_data.password),
        full_name=student_data.full_name
    )
    db.add(user)
    db.flush()

    # Create student profile
    student = Student(
        id=str(uuid.uuid4()),
        user_id=user.id,
        group_id=student_data.group_id,
        parent_id=student_data.parent_id,
        graduation_year=student_data.graduation_year
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def get_student(db: Session, student_id: str):
    return db.query(Student).filter(Student.id == student_id).first()


def get_students_by_group(db: Session, group_id: str):
    return db.query(Student).filter(Student.group_id == group_id).all()


def get_all_students(db: Session):
    return db.query(Student).all()


def delete_student(db: Session, student_id: str):
    student = db.query(Student).filter(Student.id == student_id).first()
    if student:
        user = db.query(User).filter(User.id == student.user_id).first()
        if user:
            db.delete(user)
        db.delete(student)
        db.commit()
        return True
    return False


# PARENT CRUD
def create_parent(db: Session, parent_data: ParentCreate):
    # Create user first
    user = User(
        id=str(uuid.uuid4()),
        role="parent",
        phone=parent_data.phone,
        password_hash=hash_password(parent_data.password),
        full_name=parent_data.full_name
    )
    db.add(user)
    db.flush()

    # Create parent profile
    parent = Parent(
        id=str(uuid.uuid4()),
        user_id=user.id
    )
    db.add(parent)
    db.commit()
    db.refresh(parent)
    return parent


def get_parent(db: Session, parent_id: str):
    return db.query(Parent).filter(Parent.id == parent_id).first()


def get_all_parents(db: Session):
    return db.query(Parent).all()


def delete_parent(db: Session, parent_id: str):
    parent = db.query(Parent).filter(Parent.id == parent_id).first()
    if parent:
        user = db.query(User).filter(User.id == parent.user_id).first()
        if user:
            db.delete(user)
        db.delete(parent)
        db.commit()
        return True
    return False


# TEACHER CRUD
def create_teacher(db: Session, teacher_data: TeacherCreate):
    # Create user first
    user = User(
        id=str(uuid.uuid4()),
        role="teacher",
        phone=teacher_data.phone,
        password_hash=hash_password(teacher_data.password),
        full_name=teacher_data.full_name
    )
    db.add(user)
    db.flush()

    # Create teacher profile
    teacher = Teacher(
        id=str(uuid.uuid4()),
        user_id=user.id
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


def get_teacher(db: Session, teacher_id: str):
    return db.query(Teacher).filter(Teacher.id == teacher_id).first()


def get_all_teachers(db: Session):
    return db.query(Teacher).all()


def delete_teacher(db: Session, teacher_id: str):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if teacher:
        user = db.query(User).filter(User.id == teacher.user_id).first()
        if user:
            db.delete(user)
        db.delete(teacher)
        db.commit()
        return True
    return False


# PROFILE UPDATES
def update_user_profile(db: Session, user_id: str, user_update):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        if user_update.full_name:
            user.full_name = user_update.full_name
        if user_update.avatar_url:
            user.avatar_url = user_update.avatar_url
        db.commit()
        db.refresh(user)
    return user