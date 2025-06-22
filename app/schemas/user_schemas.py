from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    role: str
    phone: int
    full_name: str
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    password: str  # Plain password for creation


class UserResponse(UserBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class StudentBase(BaseModel):
    user_id: str
    group_id: str
    parent_id: str
    graduation_year: int


class StudentCreate(StudentBase):
    pass


class StudentResponse(StudentBase):
    id: str

    class Config:
        from_attributes = True


class ParentBase(BaseModel):
    user_id: str
    student_ids: List[str]


class ParentCreate(ParentBase):
    pass


class ParentResponse(ParentBase):
    id: str

    class Config:
        from_attributes = True


class TeacherBase(BaseModel):
    user_id: str
    group_subject_ids: List[str]


class TeacherCreate(TeacherBase):
    pass


class TeacherResponse(TeacherBase):
    id: str

    class Config:
        from_attributes = True