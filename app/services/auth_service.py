# app/services/auth_service.py
"""
Authentication service with passionate security implementation!
Handles login, password management, and token operations.
"""

from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from ..models import User, Student, Parent, Teacher
from ..utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_user_token_data,
    create_login_response
)
from ..utils.helpers import UserRole, sanitize_phone_number
from ..schemas.auth import LoginRequest, ChangePasswordRequest, ResetPasswordRequest


class AuthenticationService:
    """
    Comprehensive authentication service handling all auth operations
    with robust security and user-friendly error handling!
    """

    def __init__(self, db: Session):
        self.db = db

    def authenticate_user(self, login_request: LoginRequest) -> dict:
        """
        Authenticate user and return login response with token

        Args:
            login_request: Login credentials

        Returns:
            Login response with token and user info

        Raises:
            HTTPException: If authentication fails
        """
        try:
            # Sanitize phone number
            phone = sanitize_phone_number(login_request.phone)

            # Find user by phone and role
            user = self.db.query(User).filter(
                User.phone == phone,
                User.role == login_request.role,
                User.is_active == True
            ).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid phone number or role"
                )

            # Verify password
            if not verify_password(login_request.password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid password"
                )

            # Create JWT token
            token_data = create_user_token_data(
                user_id=user.id,
                role=user.role,
                phone=user.phone,
                full_name=user.full_name
            )

            access_token = create_access_token(token_data)

            # Update last login (if you want to track this)
            user.updated_at = datetime.utcnow()
            self.db.commit()

            return create_login_response(user, access_token)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Authentication error: {str(e)}"
            )

    def change_password(self, user_id: str, change_request: ChangePasswordRequest) -> dict:
        """
        Change user password with proper validation

        Args:
            user_id: User's ID
            change_request: Password change request

        Returns:
            Success response

        Raises:
            HTTPException: If validation fails
        """
        try:
            # Find user
            user = self.db.query(User).filter(
                User.id == user_id,
                User.is_active == True
            ).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Verify current password
            if not verify_password(change_request.current_password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )

            # Check if new password is different from current
            if verify_password(change_request.new_password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New password must be different from current password"
                )

            # Hash and update password
            user.password_hash = hash_password(change_request.new_password)
            user.updated_at = datetime.utcnow()

            self.db.commit()

            return {
                "message": "Password changed successfully",
                "timestamp": datetime.utcnow()
            }

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Password change error: {str(e)}"
            )

    def reset_password_admin(self, reset_request: ResetPasswordRequest, admin_id: str) -> dict:
        """
        Reset user password (admin only)

        Args:
            reset_request: Password reset request
            admin_id: Admin user ID performing the reset

        Returns:
            Success response with new credentials

        Raises:
            HTTPException: If validation fails
        """
        try:
            # Sanitize phone number
            phone = sanitize_phone_number(reset_request.phone)

            # Find target user
            user = self.db.query(User).filter(
                User.phone == phone,
                User.role == reset_request.role
            ).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found with specified phone and role"
                )

            # Hash new password
            new_password_hash = hash_password(reset_request.new_password)

            # Update user password
            user.password_hash = new_password_hash
            user.updated_at = datetime.utcnow()

            self.db.commit()

            return {
                "message": "Password reset successfully",
                "user_id": user.id,
                "credentials": {
                    "phone": user.phone,
                    "role": user.role,
                    "new_password": reset_request.new_password,
                    "full_name": user.full_name
                },
                "reset_by": admin_id,
                "timestamp": datetime.utcnow()
            }

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Password reset error: {str(e)}"
            )

    def get_user_profile(self, user_id: str) -> dict:
        """
        Get user profile information

        Args:
            user_id: User ID

        Returns:
            User profile data

        Raises:
            HTTPException: If user not found
        """
        try:
            user = self.db.query(User).filter(
                User.id == user_id,
                User.is_active == True
            ).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Get role-specific profile data
            profile_data = {
                "id": user.id,
                "role": user.role,
                "phone": user.phone,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "is_active": user.is_active
            }

            # Add role-specific information
            if user.role == UserRole.STUDENT:
                student = self.db.query(Student).filter(Student.user_id == user.id).first()
                if student:
                    profile_data["student_info"] = {
                        "student_id": student.id,
                        "group_id": student.group_id,
                        "parent_id": student.parent_id,
                        "graduation_year": student.graduation_year
                    }

            elif user.role == UserRole.PARENT:
                parent = self.db.query(Parent).filter(Parent.user_id == user.id).first()
                if parent:
                    children = self.db.query(Student).filter(Student.parent_id == parent.id).all()
                    profile_data["parent_info"] = {
                        "parent_id": parent.id,
                        "children_count": len(children),
                        "children_ids": [child.id for child in children]
                    }

            elif user.role == UserRole.TEACHER:
                teacher = self.db.query(Teacher).filter(Teacher.user_id == user.id).first()
                if teacher:
                    profile_data["teacher_info"] = {
                        "teacher_id": teacher.id
                    }

            return profile_data

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Profile retrieval error: {str(e)}"
            )

    def update_profile(self, user_id: str, update_data: dict) -> dict:
        """
        Update user profile information

        Args:
            user_id: User ID
            update_data: Data to update

        Returns:
            Updated user profile

        Raises:
            HTTPException: If update fails
        """
        try:
            user = self.db.query(User).filter(
                User.id == user_id,
                User.is_active == True
            ).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Update allowed fields
            if "full_name" in update_data and update_data["full_name"]:
                user.full_name = update_data["full_name"].strip()

            user.updated_at = datetime.utcnow()
            self.db.commit()

            return self.get_user_profile(user_id)

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Profile update error: {str(e)}"
            )

    def update_avatar(self, user_id: str, avatar_url: str) -> dict:
        """
        Update user avatar URL

        Args:
            user_id: User ID
            avatar_url: New avatar URL

        Returns:
            Success response

        Raises:
            HTTPException: If update fails
        """
        try:
            user = self.db.query(User).filter(
                User.id == user_id,
                User.is_active == True
            ).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            user.avatar_url = avatar_url
            user.updated_at = datetime.utcnow()
            self.db.commit()

            return {
                "message": "Avatar updated successfully",
                "avatar_url": avatar_url,
                "timestamp": datetime.utcnow()
            }

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Avatar update error: {str(e)}"
            )

    def validate_user_exists(self, phone: int, role: str) -> bool:
        """
        Check if user exists with given phone and role

        Args:
            phone: Phone number
            role: User role

        Returns:
            True if user exists
        """
        try:
            phone = sanitize_phone_number(phone)
            user = self.db.query(User).filter(
                User.phone == phone,
                User.role == role
            ).first()
            return user is not None
        except:
            return False

    def deactivate_user(self, user_id: str, admin_id: str) -> dict:
        """
        Deactivate user account (admin only)

        Args:
            user_id: User ID to deactivate
            admin_id: Admin performing the action

        Returns:
            Success response

        Raises:
            HTTPException: If operation fails
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            if user.role == UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot deactivate admin users"
                )

            user.is_active = False
            user.updated_at = datetime.utcnow()
            self.db.commit()

            return {
                "message": "User deactivated successfully",
                "user_id": user_id,
                "deactivated_by": admin_id,
                "timestamp": datetime.utcnow()
            }

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"User deactivation error: {str(e)}"
            )

    def reactivate_user(self, user_id: str, admin_id: str) -> dict:
        """
        Reactivate user account (admin only)

        Args:
            user_id: User ID to reactivate
            admin_id: Admin performing the action

        Returns:
            Success response

        Raises:
            HTTPException: If operation fails
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            user.is_active = True
            user.updated_at = datetime.utcnow()
            self.db.commit()

            return {
                "message": "User reactivated successfully",
                "user_id": user_id,
                "reactivated_by": admin_id,
                "timestamp": datetime.utcnow()
            }

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"User reactivation error: {str(e)}"
            )


# Service factory function
def get_auth_service(db: Session) -> AuthenticationService:
    """Create authentication service instance"""
    return AuthenticationService(db)