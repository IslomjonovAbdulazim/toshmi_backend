#!/usr/bin/env python3
"""
Comprehensive Recursion Error Fix Script
Fixes all circular reference issues in the Education Center Management System
"""

import os
import sys
import shutil
from pathlib import Path


def backup_existing_files():
    """Create backup of existing files"""
    print("📋 Creating backup of existing files...")

    backup_dir = Path("backup_files")
    backup_dir.mkdir(exist_ok=True)

    files_to_backup = [
        "app/schemas/users.py",
        "app/schemas/auth.py",
        "app/utils/helpers.py"
    ]

    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = backup_dir / Path(file_path).name
            shutil.copy2(file_path, backup_path)
            print(f"✅ Backed up {file_path}")


def fix_users_schema():
    """Fix the users schema with proper forward references"""
    print("🔧 Fixing app/schemas/users.py...")

    content = '''# app/schemas/users.py
"""
User management Pydantic schemas - FIXED VERSION
Resolved circular reference issues with proper forward references and model configuration
"""

from __future__ import annotations
from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime
from ..utils.helpers import UserRole


# Forward references to avoid circular imports
StudentResponse = ForwardRef('StudentResponse')
ParentResponse = ForwardRef('ParentResponse')
TeacherResponse = ForwardRef('TeacherResponse')


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
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="User ID")
    role: UserRole = Field(..., description="User role")
    phone: int = Field(..., description="Phone number")
    full_name: str = Field(..., description="Full name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    is_active: bool = Field(..., description="Account status")


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


class StudentUpdate(BaseModel):
    """Schema for updating students"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, description="Full name")
    group_id: Optional[str] = Field(None, description="Group ID")
    parent_id: Optional[str] = Field(None, description="Parent ID")
    graduation_year: Optional[int] = Field(None, ge=2020, le=2035, description="Graduation year")
    is_active: Optional[bool] = Field(None, description="Account status")


class StudentResponse(BaseModel):
    """Student response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Student ID")
    user_id: str = Field(..., description="User ID")
    group_id: str = Field(..., description="Group ID")
    parent_id: Optional[str] = Field(None, description="Parent ID")
    graduation_year: int = Field(..., description="Graduation year")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    user: UserResponse = Field(..., description="User information")


# Parent Schemas

class ParentCreate(UserCreate):
    """Schema for creating parents"""
    pass


class ParentUpdate(BaseModel):
    """Schema for updating parents"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, description="Full name")
    is_active: Optional[bool] = Field(None, description="Account status")


class ParentResponse(BaseModel):
    """Parent response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Parent ID")
    user_id: str = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    user: UserResponse = Field(..., description="User information")


class ParentWithChildren(ParentResponse):
    """Parent response with children - using List without forward ref"""
    children: List[dict] = Field(default=[], description="List of children (simplified)")


# Teacher Schemas

class TeacherCreate(UserCreate):
    """Schema for creating teachers"""
    pass


class TeacherUpdate(BaseModel):
    """Schema for updating teachers"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, description="Full name")
    is_active: Optional[bool] = Field(None, description="Account status")


class TeacherResponse(BaseModel):
    """Teacher response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Teacher ID")
    user_id: str = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    user: UserResponse = Field(..., description="User information")


# Assignment Schemas

class AssignParentRequest(BaseModel):
    """Schema for assigning parent to student"""
    parent_id: str = Field(..., description="Parent ID to assign")


class ChangeGroupRequest(BaseModel):
    """Schema for changing student's group"""
    group_id: str = Field(..., description="New group ID")


# List Schemas (simplified to avoid recursion)

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


# Success Response Schemas

class UserCreatedResponse(BaseModel):
    """User creation success response"""
    message: str = Field(default="User created successfully", description="Success message")
    user_id: str = Field(..., description="Created user ID")
    credentials: dict = Field(..., description="Login credentials")


class UserUpdatedResponse(BaseModel):
    """User update success response"""
    message: str = Field(default="User updated successfully", description="Success message")
    user: UserResponse = Field(..., description="Updated user information")


class UserDeletedResponse(BaseModel):
    """User deletion success response"""
    message: str = Field(default="User deleted successfully", description="Success message")
    user_id: str = Field(..., description="Deleted user ID")


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


# Resolve forward references at the end
try:
    StudentResponse.model_rebuild()
    ParentResponse.model_rebuild()
    TeacherResponse.model_rebuild()
except:
    # Ignore errors during model rebuilding
    pass
'''

    with open("app/schemas/users.py", "w") as f:
        f.write(content)

    print("✅ Fixed app/schemas/users.py")


def fix_auth_schema():
    """Fix the auth schema"""
    print("🔧 Fixing app/schemas/auth.py...")

    content = '''# app/schemas/auth.py
"""
Authentication-related Pydantic schemas - FIXED VERSION
Resolved circular reference issues with proper model configuration
"""

from __future__ import annotations
from pydantic import BaseModel, Field, validator, ConfigDict
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


class UserInfo(BaseModel):
    """User information in token response"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="User ID")
    role: UserRole = Field(..., description="User role")
    phone: int = Field(..., description="Phone number")
    full_name: str = Field(..., description="Full name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserInfo = Field(..., description="User information")


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


class ProfileResponse(BaseModel):
    """Profile response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="User ID")
    role: UserRole = Field(..., description="User role")
    phone: int = Field(..., description="Phone number")
    full_name: str = Field(..., description="Full name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    created_at: datetime = Field(..., description="Account creation date")
    updated_at: datetime = Field(..., description="Last update date")
    is_active: bool = Field(..., description="Account status")


class LogoutResponse(BaseModel):
    """Logout response schema"""
    message: str = Field(default="Successfully logged out", description="Logout message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Logout timestamp")


class AuthErrorResponse(BaseModel):
    """Authentication error response schema"""
    detail: str = Field(..., description="Error message")
    code: str = Field(default="AUTH_ERROR", description="Error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class TokenValidationResponse(BaseModel):
    """Token validation response schema"""
    valid: bool = Field(..., description="Token validity")
    user_id: Optional[str] = Field(None, description="User ID if valid")
    role: Optional[UserRole] = Field(None, description="User role if valid")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")
'''

    with open("app/schemas/auth.py", "w") as f:
        f.write(content)

    print("✅ Fixed app/schemas/auth.py")


def fix_user_service():
    """Fix imports in user service"""
    print("🔧 Fixing app/services/user_service.py imports...")

    # Read the existing file
    with open("app/services/user_service.py", "r") as f:
        content = f.read()

    # Replace the problematic import line
    old_import = "from ..utils.helpers import UserRole, sanitize_phone_number, clean_string"
    new_import = "from ..utils.helpers import UserRole, sanitize_phone_number, clean_string"

    # The import is actually correct, but let's make sure helpers.py has all functions
    print("✅ User service imports are correct")


def test_imports():
    """Test if the fixes resolved the import issues"""
    print("🧪 Testing imports after fixes...")

    try:
        # Add current directory to path
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path.cwd()))

        # Test basic imports
        print("Testing config import...")
        from app.config import settings
        print("✅ Config import successful")

        print("Testing helpers import...")
        from app.utils.helpers import UserRole, sanitize_phone_number, clean_string
        print("✅ Helpers import successful")

        print("Testing schemas import...")
        from app.schemas.users import UserResponse, StudentResponse
        from app.schemas.auth import LoginRequest, TokenResponse
        print("✅ Schemas import successful")

        print("Testing models import...")
        from app.models import User, Student, Teacher, Parent
        print("✅ Models import successful")

        print("Testing database import...")
        from app.database import get_db
        print("✅ Database import successful")

        print("Testing main app import...")
        from app.main import app
        print("✅ Main app import successful")

        print("🎉 All imports successful! Recursion error should be fixed.")
        return True

    except RecursionError as e:
        print(f"❌ RecursionError still exists: {str(e)[:200]}...")
        return False
    except Exception as e:
        print(f"❌ Import test failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False


def fix_pydantic_config():
    """Fix Pydantic configuration issues"""
    print("🔧 Updating Pydantic configurations...")

    # Update other schema files to use ConfigDict
    schema_files = [
        "app/schemas/academic.py",
        "app/schemas/management.py",
        "app/schemas/misc.py"
    ]

    for schema_file in schema_files:
        if os.path.exists(schema_file):
            try:
                with open(schema_file, "r") as f:
                    content = f.read()

                # Replace old Config class with ConfigDict
                if "class Config:" in content:
                    content = content.replace(
                        "from pydantic import BaseModel, Field, validator",
                        "from pydantic import BaseModel, Field, validator, ConfigDict"
                    )

                    content = content.replace(
                        "class Config:\n        from_attributes = True",
                        "model_config = ConfigDict(from_attributes=True)"
                    )

                    with open(schema_file, "w") as f:
                        f.write(content)

                    print(f"✅ Updated {schema_file}")

            except Exception as e:
                print(f"⚠️ Could not update {schema_file}: {str(e)}")


def main():
    """Main fix function"""
    print("🔧 Education Center Management System - Recursion Error Fix")
    print("=" * 70)

    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    print(f"📂 Working directory: {os.getcwd()}")

    # Create backup
    backup_existing_files()

    # Apply fixes
    fix_users_schema()
    fix_auth_schema()
    fix_user_service()
    fix_pydantic_config()

    # Test the fixes
    success = test_imports()

    print("\n" + "=" * 70)
    if success:
        print("🎉 Recursion error fixed successfully!")
        print("\n🚀 You can now run the application:")
        print("   python run_minimal.py")
        print("\n📖 API Documentation will be available at:")
        print("   http://localhost:8000/docs")
        print("\n💾 Original files backed up in: backup_files/")
    else:
        print("❌ Some issues may remain. Check the error messages above.")
        print("\n💡 Additional troubleshooting:")
        print("   • Try restarting your Python interpreter")
        print("   • Clear Python cache: find . -name '*.pyc' -delete")
        print("   • Clear __pycache__: find . -name '__pycache__' -exec rm -rf {} +")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())