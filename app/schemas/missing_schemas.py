from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Profile Updates
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

# Student Management
class StudentEnrollment(BaseModel):
    student_id: str
    group_id: str

class GroupTransfer(BaseModel):
    student_ids: List[str]
    from_group_id: str
    to_group_id: str

# Bulk Operations
class BulkStudentCreate(BaseModel):
    students: List[dict]  # [{phone, full_name, group_id, parent_phone, graduation_year}]

# Search/Filter
class StudentSearch(BaseModel):
    name: Optional[str] = None
    group_id: Optional[str] = None
    graduation_year: Optional[int] = None

class GradeFilter(BaseModel):
    student_id: Optional[str] = None
    subject_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

# Reports
class ClassReport(BaseModel):
    group_id: str
    subject_id: str
    average_grade: float
    total_students: int
    assignments_count: int

class PaymentReport(BaseModel):
    month: int
    year: int
    total_paid: float
    total_unpaid: float
    students_paid: int
    students_unpaid: int

# File Upload
class FileUpload(BaseModel):
    file_url: str
    file_type: str  # 'image', 'document', 'video'
    file_name: str

# Password Management
class PasswordChange(BaseModel):
    current_password: str
    new_password: str

# Calendar
class AcademicEvent(BaseModel):
    title: str
    description: str
    event_date: datetime
    event_type: str  # 'exam', 'holiday', 'meeting'
    group_ids: Optional[List[str]] = None