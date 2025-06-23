# app/utils/permissions.py
from functools import wraps
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import Student, Parent, Teacher


def get_student_record(db: Session, user_id: str):
    """Get student record by user_id"""
    student = db.query(Student).filter(Student.user_id == user_id).first()
    if not student:
        raise HTTPException(404, "Student record not found")
    return student


def get_parent_record(db: Session, user_id: str):
    """Get parent record by user_id"""
    parent = db.query(Parent).filter(Parent.user_id == user_id).first()
    if not parent:
        raise HTTPException(404, "Parent record not found")
    return parent


def get_teacher_record(db: Session, user_id: str):
    """Get teacher record by user_id"""
    teacher = db.query(Teacher).filter(Teacher.user_id == user_id).first()
    if not teacher:
        raise HTTPException(404, "Teacher record not found")
    return teacher


def verify_student_access(current_user, student_id: str, db: Session):
    """Verify user can access student data"""
    if current_user.role == "admin":
        return True
    elif current_user.role == "student":
        student = get_student_record(db, current_user.id)
        if student.id != student_id:
            raise HTTPException(403, "Access denied")
    elif current_user.role == "parent":
        parent = get_parent_record(db, current_user.id)
        # Check if student belongs to this parent
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student or student.parent_id != parent.id:
            raise HTTPException(403, "Access denied")
    else:
        raise HTTPException(403, "Access denied")
    return True


def inject_student_record(func):
    """Decorator to inject current user's student record"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        current_user = kwargs.get("current_user") or kwargs.get("current_student")
        db = kwargs.get("db")

        if current_user and current_user.role == "student":
            kwargs["student_record"] = get_student_record(db, current_user.id)
        return func(*args, **kwargs)
    return wrapper


def inject_parent_record(func):
    """Decorator to inject current user's parent record"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        current_user = kwargs.get("current_user") or kwargs.get("current_parent")
        db = kwargs.get("db")

        if current_user and current_user.role == "parent":
            kwargs["parent_record"] = get_parent_record(db, current_user.id)
        return func(*args, **kwargs)
    return wrapper


def student_access_required(student_id_param: str = "student_id"):
    """Decorator to verify student access"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user") or kwargs.get("current_parent")
            student_id = kwargs.get(student_id_param)
            db = kwargs.get("db")

            verify_student_access(current_user, student_id, db)
            return func(*args, **kwargs)
        return wrapper
    return decorator