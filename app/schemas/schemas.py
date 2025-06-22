from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any
from datetime import datetime


# AUTH
class LoginRequest(BaseModel):
    phone: int
    role: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: str = None


class PasswordChange(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class AdminPasswordChange(BaseModel):
    new_password: str = Field(..., min_length=8)

    @validator('new_password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain number')
        return v


# USERS
class UserBase(BaseModel):
    role: str = Field(..., pattern="^(student|parent|teacher|admin)$")
    phone: int = Field(..., ge=100000000, le=999999999999)
    full_name: str = Field(..., min_length=2, max_length=100)
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    avatar_url: Optional[str] = None


# STUDENTS/PARENTS/TEACHERS
class StudentBase(BaseModel):
    user_id: str = Field(..., min_length=1)
    group_id: str = Field(..., min_length=1)
    graduation_year: int = Field(..., ge=2020, le=2035)


class StudentCreate(StudentBase):
    pass


class StudentResponse(StudentBase):
    id: str

    class Config:
        from_attributes = True


class ParentBase(BaseModel):
    user_id: str = Field(..., min_length=1)


class ParentCreate(ParentBase):
    pass


class ParentResponse(ParentBase):
    id: str

    class Config:
        from_attributes = True


class TeacherBase(BaseModel):
    user_id: str = Field(..., min_length=1)


class TeacherCreate(TeacherBase):
    pass


class TeacherResponse(TeacherBase):
    id: str

    class Config:
        from_attributes = True


# ACADEMIC
class GroupBase(BaseModel):
    name: str


class GroupCreate(GroupBase):
    pass


class GroupResponse(GroupBase):
    id: str

    class Config:
        from_attributes = True


class SubjectBase(BaseModel):
    name: str


class SubjectCreate(SubjectBase):
    pass


class SubjectResponse(SubjectBase):
    id: str

    class Config:
        from_attributes = True


class GroupSubjectBase(BaseModel):
    group_id: str
    subject_id: str


class GroupSubjectCreate(GroupSubjectBase):
    pass


class GroupSubjectResponse(GroupSubjectBase):
    id: str

    class Config:
        from_attributes = True


class ScheduleBase(BaseModel):
    group_id: str
    group_subject_id: str
    day_of_week: str
    start_time: str
    end_time: str
    room: Optional[str] = None


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleResponse(ScheduleBase):
    id: str

    class Config:
        from_attributes = True


# GRADES
class HomeworkBase(BaseModel):
    group_subject_id: str
    title: str
    description: str
    due_date: datetime


class HomeworkCreate(HomeworkBase):
    pass


class HomeworkResponse(HomeworkBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class HomeworkGradeBase(BaseModel):
    homework_id: str
    student_id: str
    grade: float
    comment: Optional[str] = None


class HomeworkGradeCreate(HomeworkGradeBase):
    pass


class HomeworkGradeResponse(HomeworkGradeBase):
    id: str
    graded_at: datetime

    class Config:
        from_attributes = True


class ExamBase(BaseModel):
    group_subject_id: str
    title: str
    exam_date: datetime


class ExamCreate(ExamBase):
    pass


class ExamResponse(ExamBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ExamGradeBase(BaseModel):
    exam_id: str
    student_id: str
    grade: float
    comment: Optional[str] = None


class ExamGradeCreate(ExamGradeBase):
    pass


class ExamGradeResponse(ExamGradeBase):
    id: str
    graded_at: datetime

    class Config:
        from_attributes = True


# MISC
class AttendanceBase(BaseModel):
    student_id: str
    group_subject_id: str
    date: datetime
    status: str
    comment: Optional[str] = None


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceResponse(AttendanceBase):
    id: str

    class Config:
        from_attributes = True


class PaymentBase(BaseModel):
    student_id: str
    month: int
    year: int
    amount_paid: float
    is_fully_paid: bool = False
    comment: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentResponse(PaymentBase):
    id: str
    paid_at: datetime

    class Config:
        from_attributes = True


class NewsBase(BaseModel):
    title: str
    body: str
    media_urls: Optional[List[str]] = None
    links: Optional[List[str]] = None


class NewsCreate(NewsBase):
    pass


class NewsResponse(NewsBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


# BULK OPERATIONS
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


class BulkGradeSubmission(BaseModel):
    homework_id: Optional[str] = None
    exam_id: Optional[str] = None
    grades: List[dict]


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


class BulkAttendanceSubmission(BaseModel):
    group_subject_id: str
    date: str
    attendance: List[dict]


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


# REPORTS & OPERATIONS
class StudentEnrollment(BaseModel):
    student_id: str = Field(..., min_length=1)
    group_id: str = Field(..., min_length=1)


class GroupTransfer(BaseModel):
    student_ids: List[str] = Field(..., min_items=1)
    from_group_id: str = Field(..., min_length=1)
    to_group_id: str = Field(..., min_length=1)


class BulkStudentCreate(BaseModel):
    students: List[dict] = Field(..., min_items=1)


class StudentSearch(BaseModel):
    name: Optional[str] = Field(None, min_length=2)
    group_id: Optional[str] = None
    graduation_year: Optional[int] = Field(None, ge=2020, le=2035)


class GradeFilter(BaseModel):
    student_id: Optional[str] = None
    subject_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


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


class FileUpload(BaseModel):
    file_url: str = Field(..., min_length=1)
    file_type: str = Field(..., pattern="^(image|document|video)$")
    file_name: str = Field(..., min_length=1)


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)