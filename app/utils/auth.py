# app/utils/auth.py
"""
Authentication utilities with passion for security and simplicity!
JWT token handling, password hashing, and verification functions.
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from ..config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hashed password

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with user data

    Args:
        data: Dictionary containing user data (user_id, role, etc.)
        expires_delta: Optional custom expiration time

    Returns:
        JWT token string
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})

    # Create JWT token
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")

        if user_id is None or role is None:
            raise credentials_exception

        return {
            "user_id": user_id,
            "role": role,
            "phone": payload.get("phone"),
            "full_name": payload.get("full_name")
        }

    except JWTError:
        raise credentials_exception


def create_user_token_data(user_id: str, role: str, phone: int, full_name: str) -> dict:
    """
    Create token data dictionary for a user

    Args:
        user_id: User's unique ID
        role: User's role (admin, teacher, student, parent)
        phone: User's phone number
        full_name: User's full name

    Returns:
        Dictionary containing token data
    """
    return {
        "sub": user_id,
        "role": role,
        "phone": phone,
        "full_name": full_name,
        "iat": datetime.utcnow()
    }


def validate_role(user_role: str, required_roles: list) -> bool:
    """
    Validate if user has required role

    Args:
        user_role: User's current role
        required_roles: List of acceptable roles

    Returns:
        True if user has required role, False otherwise
    """
    return user_role in required_roles


def check_admin_role(user_role: str) -> bool:
    """Check if user is admin"""
    return user_role == "admin"


def check_teacher_role(user_role: str) -> bool:
    """Check if user is teacher"""
    return user_role == "teacher"


def check_student_role(user_role: str) -> bool:
    """Check if user is student"""
    return user_role == "student"


def check_parent_role(user_role: str) -> bool:
    """Check if user is parent"""
    return user_role == "parent"


def check_academic_roles(user_role: str) -> bool:
    """Check if user has academic access (teacher, student, parent)"""
    return user_role in ["teacher", "student", "parent"]


def get_role_permissions(role: str) -> dict:
    """
    Get permissions for a specific role

    Args:
        role: User role

    Returns:
        Dictionary containing permission flags
    """
    permissions = {
        "admin": {
            "can_create_users": True,
            "can_manage_groups": True,
            "can_manage_subjects": True,
            "can_manage_payments": True,
            "can_view_all_data": True,
            "can_create_news": True,
            "can_reset_passwords": True,
        },
        "teacher": {
            "can_create_homework": True,
            "can_create_exams": True,
            "can_grade_students": True,
            "can_record_attendance": True,
            "can_view_group_data": True,
            "can_upload_files": True,
        },
        "student": {
            "can_view_own_data": True,
            "can_view_homework": True,
            "can_view_exams": True,
            "can_view_grades": True,
            "can_view_attendance": True,
            "can_update_profile": True,
        },
        "parent": {
            "can_view_children_data": True,
            "can_view_children_grades": True,
            "can_view_children_attendance": True,
            "can_view_payment_history": True,
            "can_update_profile": True,
        }
    }

    return permissions.get(role, {})


def generate_secure_password(length: int = 12) -> str:
    """
    Generate a secure random password

    Args:
        length: Length of password to generate

    Returns:
        Randomly generated password
    """
    import secrets
    import string

    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def validate_password_strength(password: str) -> tuple[bool, list]:
    """
    Validate password strength

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")

    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")

    return len(errors) == 0, errors


def sanitize_phone_number(phone: Union[str, int]) -> int:
    """
    Sanitize and validate phone number

    Args:
        phone: Phone number as string or int

    Returns:
        Cleaned phone number as integer

    Raises:
        ValueError: If phone number is invalid
    """
    # Convert to string and remove all non-digits
    phone_str = str(phone).strip()
    phone_digits = ''.join(filter(str.isdigit, phone_str))

    # Validate length (should be between 9-15 digits)
    if len(phone_digits) < 9 or len(phone_digits) > 15:
        raise ValueError("Phone number must be between 9-15 digits")

    return int(phone_digits)


def create_login_response(user, token: str) -> dict:
    """
    Create standardized login response

    Args:
        user: User object from database
        token: JWT token

    Returns:
        Login response dictionary
    """
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,  # Convert to seconds
        "user": {
            "id": user.id,
            "role": user.role,
            "phone": user.phone,
            "full_name": user.full_name,
            "avatar_url": user.avatar_url
        }
    }