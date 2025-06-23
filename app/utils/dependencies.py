# app/utils/dependencies.py
"""
FastAPI dependencies for authentication and authorization
Built with passion for clean, secure, and efficient request handling!
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Student, Parent, Teacher
from .auth import verify_token

# HTTP Bearer security scheme
security = HTTPBearer()


def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: If authentication fails
    """
    # Verify token and get user data
    token_data = verify_token(credentials.credentials)

    # Get user from database
    user = db.query(User).filter(
        User.id == token_data["user_id"],
        User.is_active == True
    ).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user (additional check for user status)

    Args:
        current_user: Current user from get_current_user

    Returns:
        Active user object

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Require admin role

    Args:
        current_user: Current authenticated user

    Returns:
        Admin user object

    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_teacher(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Require teacher role

    Args:
        current_user: Current authenticated user

    Returns:
        Teacher user object

    Raises:
        HTTPException: If user is not teacher
    """
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher access required"
        )
    return current_user


def require_student(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Require student role

    Args:
        current_user: Current authenticated user

    Returns:
        Student user object

    Raises:
        HTTPException: If user is not student
    """
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required"
        )
    return current_user


def require_parent(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Require parent role

    Args:
        current_user: Current authenticated user

    Returns:
        Parent user object

    Raises:
        HTTPException: If user is not parent
    """
    if current_user.role != "parent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Parent access required"
        )
    return current_user


def require_academic_access(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Require academic access (teacher, student, or parent)

    Args:
        current_user: Current authenticated user

    Returns:
        User object with academic access

    Raises:
        HTTPException: If user doesn't have academic access
    """
    if current_user.role not in ["teacher", "student", "parent"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Academic access required"
        )
    return current_user


def require_teacher_or_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Require teacher or admin role

    Args:
        current_user: Current authenticated user

    Returns:
        User object with teacher or admin access

    Raises:
        HTTPException: If user is not teacher or admin
    """
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher or admin access required"
        )
    return current_user


def get_current_student_profile(
        current_user: User = Depends(require_student),
        db: Session = Depends(get_db)
) -> Student:
    """
    Get current student's profile

    Args:
        current_user: Current authenticated student user
        db: Database session

    Returns:
        Student profile object

    Raises:
        HTTPException: If student profile not found
    """
    student = db.query(Student).filter(Student.user_id == current_user.id).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )

    return student


def get_current_parent_profile(
        current_user: User = Depends(require_parent),
        db: Session = Depends(get_db)
) -> Parent:
    """
    Get current parent's profile

    Args:
        current_user: Current authenticated parent user
        db: Database session

    Returns:
        Parent profile object

    Raises:
        HTTPException: If parent profile not found
    """
    parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()

    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent profile not found"
        )

    return parent


def get_current_teacher_profile(
        current_user: User = Depends(require_teacher),
        db: Session = Depends(get_db)
) -> Teacher:
    """
    Get current teacher's profile

    Args:
        current_user: Current authenticated teacher user
        db: Database session

    Returns:
        Teacher profile object

    Raises:
        HTTPException: If teacher profile not found
    """
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()

    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )

    return teacher


def get_optional_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
        db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None
    Useful for endpoints that work for both authenticated and anonymous users

    Args:
        credentials: Optional HTTP Bearer credentials
        db: Database session

    Returns:
        User object if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        token_data = verify_token(credentials.credentials)
        user = db.query(User).filter(
            User.id == token_data["user_id"],
            User.is_active == True
        ).first()
        return user
    except:
        return None


def validate_student_access(
        student_id: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
) -> Student:
    """
    Validate access to student data
    - Admins can access any student
    - Teachers can access students in their groups
    - Students can only access their own data
    - Parents can access their children's data

    Args:
        student_id: Student ID to check access for
        current_user: Current authenticated user
        db: Database session

    Returns:
        Student object if access is valid

    Raises:
        HTTPException: If access is denied
    """
    student = db.query(Student).filter(Student.id == student_id).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    # Admin has access to all students
    if current_user.role == "admin":
        return student

    # Student can only access their own data
    if current_user.role == "student":
        if student.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to student data"
            )
        return student

    # Parent can access their children's data
    if current_user.role == "parent":
        parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()
        if not parent or student.parent_id != parent.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to student data"
            )
        return student

    # Teacher can access students in their groups (this would need more complex logic)
    if current_user.role == "teacher":
        # For now, allow teachers to access all students in the system
        # In a real implementation, you'd check if the teacher teaches this student
        return student

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied to student data"
    )


def validate_parent_children_access(
        current_user: User = Depends(require_parent),
        db: Session = Depends(get_db)
) -> list[Student]:
    """
    Get list of children for current parent

    Args:
        current_user: Current authenticated parent user
        db: Database session

    Returns:
        List of student objects (children)

    Raises:
        HTTPException: If parent profile not found
    """
    parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()

    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent profile not found"
        )

    children = db.query(Student).filter(Student.parent_id == parent.id).all()
    return children