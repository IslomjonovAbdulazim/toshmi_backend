# app/schemas/auth.py
"""
Authentication-related Pydantic schemas
Built with passion for secure and validated data handling!
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from ..utils.helpers import UserRole


class LoginRequest(BaseModel):
    """Login request schema"""
    phone: int = Field(..., ge=100000000, le=999999999999, description="Phone number")
    role: UserRole = Field(..., description="User role")
    password: str = Field(..., min_length=1, description="Password")

    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format"""
        phone_str = str(v)
        if len(phone_str) < 9 or len(phone_str) > 15:
            raise ValueError("Phone number must be between 9-15 digits")
        return v

    class Config:
        schema_extra = {
            "example": {
                "phone": 998901234567,
                "role": "student",
                "password": "password123"
            }
        }


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: "UserInfo" = Field(..., description="User information")

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": "uuid-string",
                    "role": "student",
                    "phone": 998901234567,
                    "full_name": "John Doe",
                    "avatar_url": None
                }
            }
        }


class UserInfo(BaseModel):
    """User information in token response"""
    id: str = Field(..., description="User ID")
    role: UserRole = Field(..., description="User role")
    phone: int = Field(..., description="Phone number")
    full_name: str = Field(..., description="Full name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., min_length=8, description="Confirm new password")

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Validate that passwords match"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

    @validator('new_password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)

        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain uppercase, lowercase, and digit')

        return v

    class Config:
        schema_extra = {
            "example": {
                "current_password": "oldpassword123",
                "new_password": "NewPassword123",
                "confirm_password": "NewPassword123"
            }
        }


class ResetPasswordRequest(BaseModel):
    """Reset password request schema (admin only)"""
    phone: int = Field(..., ge=100000000, le=999999999999, description="User phone number")
    role: UserRole = Field(..., description="User role")
    new_password: str = Field(..., min_length=8, description="New password")

    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format"""
        phone_str = str(v)
        if len(phone_str) < 9 or len(phone_str) > 15:
            raise ValueError("Phone number must be between 9-15 digits")
        return v

    @validator('new_password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

    class Config:
        schema_extra = {
            "example": {
                "phone": 998901234567,
                "role": "student",
                "new_password": "NewPassword123"
            }
        }


class UpdateProfileRequest(BaseModel):
    """Update profile request schema"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, description="Full name")

    @validator('full_name')
    def validate_full_name(cls, v):
        """Validate full name"""
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError('Full name must be at least 2 characters long')
        return v

    class Config:
        schema_extra = {
            "example": {
                "full_name": "John Smith"
            }
        }


class ProfileResponse(BaseModel):
    """Profile response schema"""
    id: str = Field(..., description="User ID")
    role: UserRole = Field(..., description="User role")
    phone: int = Field(..., description="Phone number")
    full_name: str = Field(..., description="Full name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    created_at: datetime = Field(..., description="Account creation date")
    updated_at: datetime = Field(..., description="Last update date")
    is_active: bool = Field(..., description="Account status")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "uuid-string",
                "role": "student",
                "phone": 998901234567,
                "full_name": "John Doe",
                "avatar_url": "/uploads/profiles/uuid.jpg",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "is_active": True
            }
        }


class LogoutResponse(BaseModel):
    """Logout response schema"""
    message: str = Field(default="Successfully logged out", description="Logout message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Logout timestamp")

    class Config:
        schema_extra = {
            "example": {
                "message": "Successfully logged out",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class AuthErrorResponse(BaseModel):
    """Authentication error response schema"""
    detail: str = Field(..., description="Error message")
    code: str = Field(default="AUTH_ERROR", description="Error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

    class Config:
        schema_extra = {
            "example": {
                "detail": "Invalid credentials",
                "code": "INVALID_CREDENTIALS",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class TokenValidationResponse(BaseModel):
    """Token validation response schema"""
    valid: bool = Field(..., description="Token validity")
    user_id: Optional[str] = Field(None, description="User ID if valid")
    role: Optional[UserRole] = Field(None, description="User role if valid")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")

    class Config:
        schema_extra = {
            "example": {
                "valid": True,
                "user_id": "uuid-string",
                "role": "student",
                "expires_at": "2024-01-15T11:00:00Z"
            }
        }


# Forward reference resolution
TokenResponse.model_rebuild()