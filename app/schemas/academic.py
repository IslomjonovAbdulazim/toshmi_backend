# app/schemas/academic.py
"""
Academic activity Pydantic schemas for homework, exams, grades, and attendance
Crafted with passion for educational excellence!
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from ..utils.helpers import AttendanceStatus


# Homework Schemas

class HomeworkCreate(BaseModel):
    """Schema for creating homework"""
    group_id: str = Field(..., description="Group ID")
    subject_id: str = Field(..., description="Subject ID")
    title: str = Field(..., min_length=3, max_length=200, description="Homework title")
    description: Optional[str] = Field(None, max_length=2000, description="Homework description")
    external_links: Optional[List[str]] = Field(default=[], description="External links")
    due_date: datetime = Field(..., description="Due date and time")

    @validator('title')
    def validate_title(cls, v):
        """Validate and clean title"""
        return v.strip()

    @validator('description')
    def validate_description(cls, v):
        """Validate and clean description"""
        if v:
            return v.strip()
        return v

    @validator('due_date')
    def validate_due_date(cls, v):
        """Validate due date is in the future"""
        if v <= datetime.now():
            raise ValueError('Due date must be in the future')
        return v

    @validator('external_links')
    def validate_links(cls, v):
        """Validate external links format"""
        if not v:
            return []

        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        valid_links = []
        for link in v:
            if isinstance(link, str) and url_pattern.match(link.strip()):
                valid_links.append(link.strip())

        return valid_links

    class Config:
        schema_extra = {
            "example": {
                "group_id": "group-uuid",
                "subject_id": "subject-uuid",
                "title": "Algebra Problems Chapter 5",
                "description": "Complete exercises 1-20 from textbook",
                "external_links": ["https://mathbook.com/chapter5"],
                "due_date": "2024-02-01T23:59:00"
            }
        }


class HomeworkUpdate(BaseModel):
    """Schema for updating homework"""
    title: Optional[str] = Field(None, min_length=3, max_length=200, description="Homework title")
    description: Optional[str] = Field(None, max_length=2000, description="Homework description")
    external_links: Optional[List[str]] = Field(None, description="External links")
    due_date: Optional[datetime] = Field(None, description="Due date and time")


class HomeworkResponse(BaseModel):
    """Homework response schema"""
    id: str = Field(..., description="Homework ID")
    group_id: str = Field(..., description="Group ID")
    subject_id: str = Field(..., description="Subject ID")
    teacher_id: str = Field(..., description="Teacher ID")
    title: str = Field(..., description="Homework title")
    description: Optional[str] = Field(None, description="Homework description")
    external_links: List[str] = Field(default=[], description="External links")
    due_date: datetime = Field(..., description="Due date")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


# Exam Schemas

class ExamCreate(BaseModel):
    """Schema for creating exams"""
    group_id: str = Field(..., description="Group ID")
    subject_id: str = Field(..., description="Subject ID")
    title: str = Field(..., min_length=3, max_length=200, description="Exam title")
    description: Optional[str] = Field(None, max_length=2000, description="Exam description")
    external_links: Optional[List[str]] = Field(default=[], description="External links")
    exam_date: datetime = Field(..., description="Exam date and time")

    @validator('title')
    def validate_title(cls, v):
        """Validate and clean title"""
        return v.strip()

    @validator('description')
    def validate_description(cls, v):
        """Validate and clean description"""
        if v:
            return v.strip()
        return v

    @validator('exam_date')
    def validate_exam_date(cls, v):
        """Validate exam date is in the future"""
        if v <= datetime.now():
            raise ValueError('Exam date must be in the future')
        return v

    class Config:
        schema_extra = {
            "example": {
                "group_id": "group-uuid",
                "subject_id": "subject-uuid",
                "title": "Midterm Exam - Mathematics",
                "description": "Covers chapters 1-5",
                "external_links": ["https://studyguide.com/math"],
                "exam_date": "2024-02-15T09:00:00"
            }
        }


class ExamUpdate(BaseModel):
    """Schema for updating exams"""
    title: Optional[str] = Field(None, min_length=3, max_length=200, description="Exam title")
    description: Optional[str] = Field(None, max_length=2000, description="Exam description")
    external_links: Optional[List[str]] = Field(None, description="External links")
    exam_date: Optional[datetime] = Field(None, description="Exam date and time")


class ExamResponse(BaseModel):
    """Exam response schema"""
    id: str = Field(..., description="Exam ID")
    group_id: str = Field(..., description="Group ID")
    subject_id: str = Field(..., description="Subject ID")
    teacher_id: str = Field(..., description="Teacher ID")
    title: str = Field(..., description="Exam title")
    description: Optional[str] = Field(None, description="Exam description")
    external_links: List[str] = Field(default=[], description="External links")
    exam_date: datetime = Field(..., description="Exam date")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


# Grade Schemas

class GradeCreate(BaseModel):
    """Schema for creating individual grades"""
    student_id: str = Field(..., description="Student ID")
    homework_id: Optional[str] = Field(None, description="Homework ID (if grading homework)")
    exam_id: Optional[str] = Field(None, description="Exam ID (if grading exam)")
    grade: float = Field(..., ge=0, description="Grade received")
    max_grade: float = Field(default=100.0, gt=0, description="Maximum possible grade")
    comment: Optional[str] = Field(None, max_length=500, description="Teacher comment")

    @validator('grade')
    def validate_grade(cls, v, values):
        """Validate grade doesn't exceed max_grade"""
        max_grade = values.get('max_grade', 100.0)
        if v > max_grade:
            raise ValueError('Grade cannot exceed maximum grade')
        return v

    class Config:
        schema_extra = {
            "example": {
                "student_id": "student-uuid",
                "homework_id": "homework-uuid",
                "grade": 85.5,
                "max_grade": 100.0,
                "comment": "Good work, but check calculation in problem 3"
            }
        }


class BulkGradeItem(BaseModel):
    """Schema for bulk grading individual items"""
    student_id: str = Field(..., description="Student ID")
    grade: float = Field(..., ge=0, description="Grade received")
    comment: Optional[str] = Field(None, max_length=500, description="Teacher comment")


class BulkGradeRequest(BaseModel):
    """Schema for bulk grading"""
    homework_id: Optional[str] = Field(None, description="Homework ID (if grading homework)")
    exam_id: Optional[str] = Field(None, description="Exam ID (if grading exam)")
    max_grade: float = Field(default=100.0, gt=0, description="Maximum possible grade")
    grades: List[BulkGradeItem] = Field(..., min_items=1, description="List of grades")

    @validator('grades')
    def validate_unique_students(cls, v):
        """Ensure no duplicate students in bulk grading"""
        student_ids = [item.student_id for item in v]
        if len(student_ids) != len(set(student_ids)):
            raise ValueError('Duplicate students found in grade list')
        return v

    class Config:
        schema_extra = {
            "example": {
                "homework_id": "homework-uuid",
                "max_grade": 100.0,
                "grades": [
                    {"student_id": "student1-uuid", "grade": 85.0, "comment": "Great work!"},
                    {"student_id": "student2-uuid", "grade": 92.5, "comment": "Excellent!"}
                ]
            }
        }


class GradeResponse(BaseModel):
    """Grade response schema"""
    id: str = Field(..., description="Grade ID")
    student_id: str = Field(..., description="Student ID")
    group_id: str = Field(..., description="Group ID")
    subject_id: str = Field(..., description="Subject ID")
    homework_id: Optional[str] = Field(None, description="Homework ID")
    exam_id: Optional[str] = Field(None, description="Exam ID")
    teacher_id: str = Field(..., description="Teacher ID")
    grade: float = Field(..., description="Grade received")
    max_grade: float = Field(..., description="Maximum possible grade")
    percentage: float = Field(..., description="Grade percentage")
    comment: Optional[str] = Field(None, description="Teacher comment")
    graded_at: datetime = Field(..., description="Grading timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


# Attendance Schemas

class AttendanceCreate(BaseModel):
    """Schema for creating individual attendance"""
    student_id: str = Field(..., description="Student ID")
    group_id: str = Field(..., description="Group ID")
    subject_id: str = Field(..., description="Subject ID")
    date: date = Field(..., description="Attendance date")
    status: AttendanceStatus = Field(..., description="Attendance status")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")

    @validator('date')
    def validate_date(cls, v):
        """Validate attendance date is not in the future"""
        if v > date.today():
            raise ValueError('Attendance date cannot be in the future')
        return v

    class Config:
        schema_extra = {
            "example": {
                "student_id": "student-uuid",
                "group_id": "group-uuid",
                "subject_id": "subject-uuid",
                "date": "2024-01-15",
                "status": "present",
                "notes": ""
            }
        }


class BulkAttendanceItem(BaseModel):
    """Schema for bulk attendance individual items"""
    student_id: str = Field(..., description="Student ID")
    status: AttendanceStatus = Field(..., description="Attendance status")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")


class BulkAttendanceRequest(BaseModel):
    """Schema for bulk attendance recording"""
    group_id: str = Field(..., description="Group ID")
    subject_id: str = Field(..., description="Subject ID")
    date: date = Field(..., description="Attendance date")
    attendance: List[BulkAttendanceItem] = Field(..., min_items=1, description="List of attendance records")

    @validator('date')
    def validate_date(cls, v):
        """Validate attendance date is not in the future"""
        if v > date.today():
            raise ValueError('Attendance date cannot be in the future')
        return v

    @validator('attendance')
    def validate_unique_students(cls, v):
        """Ensure no duplicate students in bulk attendance"""
        student_ids = [item.student_id for item in v]
        if len(student_ids) != len(set(student_ids)):
            raise ValueError('Duplicate students found in attendance list')
        return v

    class Config:
        schema_extra = {
            "example": {
                "group_id": "group-uuid",
                "subject_id": "subject-uuid",
                "date": "2024-01-15",
                "attendance": [
                    {"student_id": "student1-uuid", "status": "present"},
                    {"student_id": "student2-uuid", "status": "late", "notes": "Arrived 10 minutes late"}
                ]
            }
        }


class AttendanceResponse(BaseModel):
    """Attendance response schema"""
    id: str = Field(..., description="Attendance ID")
    student_id: str = Field(..., description="Student ID")
    group_id: str = Field(..., description="Group ID")
    subject_id: str = Field(..., description="Subject ID")
    teacher_id: str = Field(..., description="Teacher ID")
    date: date = Field(..., description="Attendance date")
    status: AttendanceStatus = Field(..., description="Attendance status")
    notes: Optional[str] = Field(None, description="Notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


# Academic Records Schemas

class StudentAcademicRecord(BaseModel):
    """Student's academic record summary"""
    student_id: str = Field(..., description="Student ID")
    student_name: str = Field(..., description="Student name")
    grades: List[GradeResponse] = Field(default=[], description="Student grades")
    attendance: List[AttendanceResponse] = Field(default=[], description="Attendance records")


class GroupAcademicTable(BaseModel):
    """Academic table for a group"""
    group_id: str = Field(..., description="Group ID")
    group_name: str = Field(..., description="Group name")
    subject_id: str = Field(..., description="Subject ID")
    subject_name: str = Field(..., description="Subject name")
    students: List[StudentAcademicRecord] = Field(..., description="Student records")


# Summary Schemas

class AcademicSummary(BaseModel):
    """Academic summary for dashboards"""
    total_homework: int = Field(..., description="Total homework count")
    total_exams: int = Field(..., description="Total exam count")
    total_grades: int = Field(..., description="Total grade count")
    average_grade: Optional[float] = Field(None, description="Average grade")
    attendance_percentage: Optional[float] = Field(None, description="Attendance percentage")


class StudentDashboard(BaseModel):
    """Student dashboard data"""
    recent_grades: List[GradeResponse] = Field(default=[], description="Recent grades")
    pending_homework: List[HomeworkResponse] = Field(default=[], description="Pending homework")
    upcoming_exams: List[ExamResponse] = Field(default=[], description="Upcoming exams")
    recent_attendance: List[AttendanceResponse] = Field(default=[], description="Recent attendance")
    summary: AcademicSummary = Field(..., description="Academic summary")


# Grading Table Schemas

class GradingTableStudent(BaseModel):
    """Student info for grading table"""
    student_id: str = Field(..., description="Student ID")
    student_name: str = Field(..., description="Student name")
    current_grade: Optional[float] = Field(None, description="Current grade if exists")
    current_comment: Optional[str] = Field(None, description="Current comment if exists")


class HomeworkGradingTable(BaseModel):
    """Homework grading table"""
    homework_id: str = Field(..., description="Homework ID")
    homework_title: str = Field(..., description="Homework title")
    max_grade: float = Field(default=100.0, description="Maximum grade")
    students: List[GradingTableStudent] = Field(..., description="Students to grade")


class ExamGradingTable(BaseModel):
    """Exam grading table"""
    exam_id: str = Field(..., description="Exam ID")
    exam_title: str = Field(..., description="Exam title")
    max_grade: float = Field(default=100.0, description="Maximum grade")
    students: List[GradingTableStudent] = Field(..., description="Students to grade")


# List Response Schemas

class HomeworkListResponse(BaseModel):
    """Homework list response"""
    homework: List[HomeworkResponse] = Field(..., description="Homework list")
    total: int = Field(..., description="Total count")


class ExamListResponse(BaseModel):
    """Exam list response"""
    exams: List[ExamResponse] = Field(..., description="Exam list")
    total: int = Field(..., description="Total count")


class GradeListResponse(BaseModel):
    """Grade list response"""
    grades: List[GradeResponse] = Field(..., description="Grade list")
    total: int = Field(..., description="Total count")


class AttendanceListResponse(BaseModel):
    """Attendance list response"""
    attendance: List[AttendanceResponse] = Field(..., description="Attendance list")
    total: int = Field(..., description="Total count")