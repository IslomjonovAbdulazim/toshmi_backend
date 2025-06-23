# app/schemas/users.py
"""
User management Pydantic schemas
Created with passion for comprehensive user data validation!
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from ..utils.helpers import UserRole


# Base User Schemas

class UserBase(BaseModel):
    """Base user schema with common fields"""
    phone: int = Field(..., ge=100000000, le=999999999999, description="Phone number")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name")

    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format"""
        phone_str = str(v)
        if len(phone_str) < 9 or len(phone_str) > 15:
            raise ValueError("Phone number must be between 9-15 digits")
        return v

    @validator('full_name')
    def validate_full_name(cls, v):
        """Validate and clean full name"""
        v = v.strip()
        if len(v) < 2:
            raise ValueError('Full name must be at least 2 characters long')
        return v


class UserCreate(UserBase):
    """Schema for creating users"""
    password: str = Field(..., min_length=8, description="Password")

    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserResponse(BaseModel):
    """User response schema"""
    id: str = Field(..., description="User ID")
    role: UserRole = Field(..., description="User role")
    phone: int = Field(..., description="Phone number")
    full_name: str = Field(..., description="Full name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    is_active: bool = Field(..., description="Account status")

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating users"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, description="Full name")
    is_active: Optional[bool] = Field(None, description="Account status")

    @validator('full_name')
    def validate_full_name(cls, v):
        """Validate and clean full name"""
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError('Full name must be at least 2 characters long')
        return v


# Student Schemas

class StudentCreate(UserCreate):
    """Schema for creating students"""
    group_id: str = Field(..., min_length=1, description="Group ID")
    parent_id: Optional[str] = Field(None, description="Parent ID (optional)")
    graduation_year: int = Field(..., ge=2020, le=2035, description="Expected graduation year")

    @validator('graduation_year')
    def validate_graduation_year(cls, v):
        """Validate graduation year"""
        current_year = datetime.now().year
        if v < current_year or v > current_year + 10:
            raise ValueError(f'Graduation year must be between {current_year} and {current_year + 10}')
        return v

    class Config:
        schema_extra = {
            "example": {
                "phone": 998901234567,
                "full_name": "John Doe",
                "password": "password123",
                "group_id": "group-uuid",
                "parent_id": "parent-uuid",
                "graduation_year": 2025
            }
        }


class StudentUpdate(BaseModel):
    """Schema for updating students"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, description="Full name")
    group_id: Optional[str] = Field(None, description="Group ID")
    parent_id: Optional[str] = Field(None, description="Parent ID")
    graduation_year: Optional[int] = Field(None, ge=2020, le=2035, description="Graduation year")
    is_active: Optional[bool] = Field(None, description="Account status")


class StudentResponse(BaseModel):
    """Student response schema"""
    id: str = Field(..., description="Student ID")
    user_id: str = Field(..., description="User ID")
    group_id: str = Field(..., description="Group ID")
    parent_id: Optional[str] = Field(None, description="Parent ID")
    graduation_year: int = Field(..., description="Graduation year")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    user: UserResponse = Field(..., description="User information")

    class Config:
        from_attributes = True


# Parent Schemas

class ParentCreate(UserCreate):
    """Schema for creating parents"""

    class Config:
        schema_extra = {
            "example": {
                "phone": 998907654321,
                "full_name": "Jane Smith",
                "password": "password123"
            }
        }


class ParentUpdate(BaseModel):
    """Schema for updating parents"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, description="Full name")
    is_active: Optional[bool] = Field(None, description="Account status")


class ParentResponse(BaseModel):
    """Parent response schema"""
    id: str = Field(..., description="Parent ID")
    user_id: str = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    user: UserResponse = Field(..., description="User information")

    class Config:
        from_attributes = True


class ParentWithChildren(ParentResponse):
    """Parent response with children"""
    children: List[StudentResponse] = Field(default=[], description="List of children")


# Teacher Schemas

class TeacherCreate(UserCreate):
    """Schema for creating teachers"""

    class Config:
        schema_extra = {
            "example": {
                "phone": 998905555555,
                "full_name": "Dr. Emily Johnson",
                "password": "password123"
            }
        }


class TeacherUpdate(BaseModel):
    """Schema for updating teachers"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, description="Full name")
    is_active: Optional[bool] = Field(None, description="Account status")


class TeacherResponse(BaseModel):
    """Teacher response schema"""
    id: str = Field(..., description="Teacher ID")
    user_id: str = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    user: UserResponse = Field(..., description="User information")

    class Config:
        from_attributes = True


# Assignment Schemas

class AssignParentRequest(BaseModel):
    """Schema for assigning parent to student"""
    parent_id: str = Field(..., description="Parent ID to assign")

    class Config:
        schema_extra = {
            "example": {
                "parent_id": "parent-uuid"
            }
        }


class ChangeGroupRequest(BaseModel):
    """Schema for changing student's group"""
    group_id: str = Field(..., description="New group ID")

    class Config:
        schema_extra = {
            "example": {
                "group_id": "new-group-uuid"
            }
        }


# List Schemas

class UserListResponse(BaseModel):
    """Paginated user list response"""
    users: List[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total pages")


class StudentListResponse(BaseModel):
    """Paginated student list response"""
    students: List[StudentResponse] = Field(..., description="List of students")
    total: int = Field(..., description="Total number of students")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total pages")


class ParentListResponse(BaseModel):
    """Paginated parent list response"""
    parents: List[ParentResponse] = Field(..., description="List of parents")
    total: int = Field(..., description="Total number of parents")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total pages")


class TeacherListResponse(BaseModel):
    """Paginated teacher list response"""
    teachers: List[TeacherResponse] = Field(..., description="List of teachers")
    total: int = Field(..., description="Total number of teachers")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total pages")


# Search Schemas

class UserSearchRequest(BaseModel):
    """User search request schema"""
    query: Optional[str] = Field(None, description="Search query (name or phone)")
    role: Optional[UserRole] = Field(None, description="Filter by role")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")


class StudentSearchRequest(BaseModel):
    """Student search request schema"""
    query: Optional[str] = Field(None, description="Search query (name or phone)")
    group_id: Optional[str] = Field(None, description="Filter by group")
    graduation_year: Optional[int] = Field(None, description="Filter by graduation year")
    has_parent: Optional[bool] = Field(None, description="Filter by parent assignment")
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")


# Profile Management Schemas

class ProfilePictureResponse(BaseModel):
    """Profile picture upload response"""
    avatar_url: str = Field(..., description="New avatar URL")
    message: str = Field(default="Profile picture updated successfully", description="Success message")


class UserStatsResponse(BaseModel):
    """User statistics response"""
    total_users: int = Field(..., description="Total number of users")
    total_students: int = Field(..., description="Total number of students")
    total_teachers: int = Field(..., description="Total number of teachers")
    total_parents: int = Field(..., description="Total number of parents")
    active_users: int = Field(..., description="Number of active users")

    class Config:
        schema_extra = {
            "example": {
                "total_users": 150,
                "total_students": 100,
                "total_teachers": 20,
                "total_parents": 80,
                "active_users": 145
            }
        }


# Success Response Schemas

class UserCreatedResponse(BaseModel):
    """User creation success response"""
    message: str = Field(default="User created successfully", description="Success message")
    user_id: str = Field(..., description="Created user ID")
    credentials: dict = Field(..., description="Login credentials")

    class Config:
        schema_extra = {
            "example": {
                "message": "Student created successfully",
                "user_id": "uuid-string",
                "credentials": {
                    "phone": 998901234567,
                    "password": "generated-password",
                    "role": "student"
                }
            }
        }


class UserUpdatedResponse(BaseModel):
    """User update success response"""
    message: str = Field(default="User updated successfully", description="Success message")
    user: UserResponse = Field(..., description="Updated user information")


class UserDeletedResponse(BaseModel):
    """User deletion success response"""
    message: str = Field(default="User deleted successfully", description="Success message")
    user_id: str = Field(..., description="Deleted user ID")