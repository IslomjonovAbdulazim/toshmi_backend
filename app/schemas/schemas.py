# app/schemas/schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


# AUTH
class LoginRequest(BaseModel):
    phone: int
    role: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class PasswordReset(BaseModel):
    phone: int
    role: str
    new_password: str = Field(..., min_length=8)


# USER CREATION - Simplified with unique endpoints
class StudentCreate(BaseModel):
    phone: int = Field(..., ge=100000000, le=999999999999)
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8)
    group_id: str = Field(..., min_length=1)
    parent_id: Optional[str] = None
    graduation_year: int = Field(..., ge=2020, le=2035)


class ParentCreate(BaseModel):
    phone: int = Field(..., ge=100000000, le=999999999999)
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8)


class TeacherCreate(BaseModel):
    phone: int = Field(..., ge=100000000, le=999999999999)
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8)


# RESPONSES
class UserResponse(BaseModel):
    id: str
    role: str
    phone: int
    full_name: str
    avatar_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class StudentResponse(BaseModel):
    id: str
    user_id: str
    group_id: str
    parent_id: Optional[str] = None
    graduation_year: int
    user: UserResponse

    class Config:
        from_attributes = True


class ParentResponse(BaseModel):
    id: str
    user_id: str
    user: UserResponse
    students: Optional[List[StudentResponse]] = None

    class Config:
        from_attributes = True


class TeacherResponse(BaseModel):
    id: str
    user_id: str
    user: UserResponse

    class Config:
        from_attributes = True


# ACADEMIC
class GroupCreate(BaseModel):
    name: str


class GroupResponse(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True


class SubjectCreate(BaseModel):
    name: str


class SubjectResponse(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True


class GroupSubjectCreate(BaseModel):
    group_id: str
    subject_id: str


class GroupSubjectResponse(BaseModel):
    id: str
    group_id: str
    subject_id: str

    class Config:
        from_attributes = True


class ScheduleCreate(BaseModel):
    group_id: str
    group_subject_id: str
    day_of_week: str
    start_time: str
    end_time: str
    room: Optional[str] = None


class ScheduleResponse(BaseModel):
    id: str
    group_id: str
    group_subject_id: str
    day_of_week: str
    start_time: str
    end_time: str
    room: Optional[str] = None

    class Config:
        from_attributes = True


# GRADES
class HomeworkCreate(BaseModel):
    group_subject_id: str
    title: str
    description: str
    due_date: datetime


class HomeworkResponse(BaseModel):
    id: str
    group_subject_id: str
    title: str
    description: str
    due_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class HomeworkGradeCreate(BaseModel):
    homework_id: str
    student_id: str
    grade: float
    comment: Optional[str] = None


class HomeworkGradeResponse(BaseModel):
    id: str
    homework_id: str
    student_id: str
    grade: float
    comment: Optional[str] = None
    graded_at: datetime

    class Config:
        from_attributes = True


class ExamCreate(BaseModel):
    group_subject_id: str
    title: str
    exam_date: datetime


class ExamResponse(BaseModel):
    id: str
    group_subject_id: str
    title: str
    exam_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class ExamGradeCreate(BaseModel):
    exam_id: str
    student_id: str
    grade: float
    comment: Optional[str] = None


class ExamGradeResponse(BaseModel):
    id: str
    exam_id: str
    student_id: str
    grade: float
    comment: Optional[str] = None
    graded_at: datetime

    class Config:
        from_attributes = True


# MISC
class AttendanceCreate(BaseModel):
    student_id: str
    group_subject_id: str
    date: datetime
    status: str
    comment: Optional[str] = None


class AttendanceResponse(BaseModel):
    id: str
    student_id: str
    group_subject_id: str
    date: datetime
    status: str
    comment: Optional[str] = None

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    student_id: str
    month: int
    year: int
    amount_paid: float
    is_fully_paid: bool = False
    comment: Optional[str] = None


class PaymentResponse(BaseModel):
    id: str
    student_id: str
    month: int
    year: int
    amount_paid: float
    is_fully_paid: bool
    paid_at: datetime
    comment: Optional[str] = None

    class Config:
        from_attributes = True


class NewsCreate(BaseModel):
    title: str
    body: str
    media_urls: Optional[List[str]] = None
    links: Optional[List[str]] = None


class NewsResponse(BaseModel):
    id: str
    title: str
    body: str
    media_urls: Optional[List[str]] = None
    links: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# BULK GRADING
class StudentGradeRow(BaseModel):
    student_id: str
    student_name: str
    current_grade: Optional[float] = None
    current_comment: Optional[str] = None


class HomeworkGradingTable(BaseModel):
    homework_id: str
    homework_title: str
    students: List[StudentGradeRow]


class ExamGradingTable(BaseModel):
    exam_id: str
    exam_title: str
    students: List[StudentGradeRow]


class StudentAttendanceRow(BaseModel):
    student_id: str
    student_name: str
    current_status: Optional[str] = None
    current_comment: Optional[str] = None


class AttendanceTable(BaseModel):
    group_subject_id: str
    subject_name: str
    group_name: str
    date: str
    students: List[StudentAttendanceRow]


# RECENT GRADES
class RecentGradeItem(BaseModel):
    id: str
    type: str
    title: str
    subject_name: str
    grade: float
    comment: Optional[str] = None
    graded_at: datetime


class RecentGradesResponse(BaseModel):
    student_id: str
    student_name: str
    grades: List[RecentGradeItem]


# REPORTS (keeping these as requested)
class ClassReport(BaseModel):
    group_id: str
    subject_id: str
    average_grade: float = Field(..., ge=0, le=100)
    total_students: int = Field(..., ge=0)
    assignments_count: int = Field(..., ge=0)


class PaymentReport(BaseModel):
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020, le=2035)
    total_paid: float = Field(..., ge=0)
    total_unpaid: float = Field(..., ge=0)
    students_paid: int = Field(..., ge=0)
    students_unpaid: int = Field(..., ge=0)


# PROFILE UPDATE
class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    avatar_url: Optional[str] = None


class FileUpload(BaseModel):
    file_url: str = Field(..., min_length=1)
    file_type: str = Field(..., pattern="^(image|document|video)$")
    file_name: str = Field(..., min_length=1)