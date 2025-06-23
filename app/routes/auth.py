# app/routes/auth.py
"""
Authentication routes with passionate security implementation!
Handles login, logout, password management, and profile operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import get_db
from ..services.auth_service import get_auth_service
from ..utils.dependencies import get_current_user, get_current_active_user
from ..schemas.auth import (
    LoginRequest, TokenResponse, ChangePasswordRequest, ResetPasswordRequest,
    UpdateProfileRequest, ProfileResponse, LogoutResponse
)

router = APIRouter()


@router.post("/login", response_model=TokenResponse, summary="User Login")
async def login(
        login_request: LoginRequest,
        db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token

    - **phone**: User's phone number
    - **role**: User role (admin, teacher, student, parent)
    - **password**: User's password

    Returns JWT token and user information
    """
    auth_service = get_auth_service(db)
    return auth_service.authenticate_user(login_request)


@router.post("/logout", response_model=LogoutResponse, summary="User Logout")
async def logout(
        current_user=Depends(get_current_user)
):
    """
    Logout current user

    Note: JWT tokens are stateless, so logout is mainly for client-side cleanup
    """
    return LogoutResponse(
        message="Successfully logged out",
        timestamp=datetime.utcnow()
    )


@router.put("/change-password", summary="Change Password")
async def change_password(
        change_request: ChangePasswordRequest,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    """
    Change current user's password

    - **current_password**: Current password for verification
    - **new_password**: New password (min 8 characters, must contain uppercase, lowercase, and digit)
    - **confirm_password**: Confirmation of new password

    Requires user authentication
    """
    auth_service = get_auth_service(db)
    return auth_service.change_password(current_user.id, change_request)


@router.post("/reset-password", summary="Reset User Password (Admin Only)")
async def reset_password(
        reset_request: ResetPasswordRequest,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    """
    Reset another user's password (Admin only)

    - **phone**: Target user's phone number
    - **role**: Target user's role
    - **new_password**: New password to set

    Only administrators can reset other users' passwords
    """
    # Check if current user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can reset other users' passwords"
        )

    auth_service = get_auth_service(db)
    return auth_service.reset_password_admin(reset_request, current_user.id)


@router.get("/profile", response_model=ProfileResponse, summary="Get Current User Profile")
async def get_profile(
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    """
    Get current user's profile information

    Returns detailed profile information including role-specific data
    """
    auth_service = get_auth_service(db)
    return auth_service.get_user_profile(current_user.id)


@router.put("/profile", response_model=ProfileResponse, summary="Update Profile")
async def update_profile(
        update_request: UpdateProfileRequest,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    """
    Update current user's profile information

    - **full_name**: Updated full name (optional)

    Users can update their basic profile information
    """
    auth_service = get_auth_service(db)
    update_data = {}

    if update_request.full_name is not None:
        update_data["full_name"] = update_request.full_name

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided"
        )

    return auth_service.update_profile(current_user.id, update_data)


@router.get("/validate-token", summary="Validate Current Token")
async def validate_token(
        current_user=Depends(get_current_active_user)
):
    """
    Validate current JWT token

    Returns user information if token is valid
    Useful for checking token validity before making other requests
    """
    return {
        "valid": True,
        "user": {
            "id": current_user.id,
            "role": current_user.role,
            "phone": current_user.phone,
            "full_name": current_user.full_name,
            "is_active": current_user.is_active
        },
        "timestamp": datetime.utcnow()
    }


@router.get("/user-info", summary="Get Basic User Info")
async def get_user_info(
        current_user=Depends(get_current_active_user)
):
    """
    Get basic user information

    Returns essential user details for UI display
    """
    return {
        "id": current_user.id,
        "role": current_user.role,
        "phone": current_user.phone,
        "full_name": current_user.full_name,
        "avatar_url": current_user.avatar_url,
        "is_active": current_user.is_active
    }


@router.post("/deactivate-account", summary="Deactivate Account (Admin Only)")
async def deactivate_account(
        target_user_id: str,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    """
    Deactivate a user account (Admin only)

    - **target_user_id**: ID of user to deactivate

    Only administrators can deactivate user accounts
    Cannot deactivate admin accounts
    """
    # Check if current user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can deactivate accounts"
        )

    auth_service = get_auth_service(db)
    return auth_service.deactivate_user(target_user_id, current_user.id)


@router.post("/reactivate-account", summary="Reactivate Account (Admin Only)")
async def reactivate_account(
        target_user_id: str,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    """
    Reactivate a user account (Admin only)

    - **target_user_id**: ID of user to reactivate

    Only administrators can reactivate user accounts
    """
    # Check if current user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can reactivate accounts"
        )

    auth_service = get_auth_service(db)
    return auth_service.reactivate_user(target_user_id, current_user.id)


@router.get("/check-phone", summary="Check Phone Number Availability")
async def check_phone_availability(
        phone: int,
        role: str,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    """
    Check if phone number is available for a specific role

    - **phone**: Phone number to check
    - **role**: Role to check for (admin, teacher, student, parent)

    Returns availability status
    Useful for user creation validation
    """
    # Only admins can check phone availability
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can check phone availability"
        )

    auth_service = get_auth_service(db)
    exists = auth_service.validate_user_exists(phone, role)

    return {
        "phone": phone,
        "role": role,
        "available": not exists,
        "exists": exists,
        "message": "Phone number is available" if not exists else "Phone number is already taken"
    }