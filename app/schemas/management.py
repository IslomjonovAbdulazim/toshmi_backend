# app/schemas/management.py
"""
Management Pydantic schemas for groups, subjects, and schedules
Built with passion for organized educational administration!
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, time
from ..utils.helpers import DayOfWeek


# Group Schemas

class GroupCreate(BaseModel):
    """Schema for creating groups"""
    name: str = Field(..., min_length=2, max_length=100, description="Group name")
    description: Optional[str] = Field(None, max_length=500, description="Group description")

    @validator('name')
    def validate_name(cls, v):
        """Validate and clean group name"""
        v = v.strip()
        if len(v) < 2:
            raise ValueError('Group name must be at least 2 characters long')
        return v

    @validator('description')
    def validate_description(cls, v):
        """Clean description"""
        if v:
            return v.strip()
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "Group A - Advanced Mathematics",
                "description": "Advanced mathematics group for gifted students"
            }
        }


class GroupUpdate(BaseModel):
    """Schema for updating groups"""
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Group name")
    description: Optional[str] = Field(None, max_length=500, description="Group description")
    is_active: Optional[bool] = Field(None, description="Group status")

    @validator('name')
    def validate_name(cls, v):
        """Validate and clean group name"""
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError('Group name must be at least 2 characters long')
        return v


class GroupResponse(BaseModel):
    """Group response schema"""
    id: str = Field(..., description="Group ID")
    name: str = Field(..., description="Group name")
    description: Optional[str] = Field(None, description="Group description")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    is_active: bool = Field(..., description="Group status")

    class Config:
        from_attributes = True


class GroupWithStats(GroupResponse):
    """Group response with statistics"""
    student_count: int = Field(..., description="Number of students in group")
    subject_count: int = Field(..., description="Number of subjects in group")
    teacher_count: int = Field(..., description="Number of teachers in group")


# Subject Schemas

class SubjectCreate(BaseModel):
    """Schema for creating subjects"""
    name: str = Field(..., min_length=2, max_length=100, description="Subject name")
    description: Optional[str] = Field(None, max_length=500, description="Subject description")

    @validator('name')
    def validate_name(cls, v):
        """Validate and clean subject name"""
        v = v.strip()
        if len(v) < 2:
            raise ValueError('Subject name must be at least 2 characters long')
        return v

    @validator('description')
    def validate_description(cls, v):
        """Clean description"""
        if v:
            return v.strip()
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "Advanced Mathematics",
                "description": "Calculus, algebra, and advanced mathematical concepts"
            }
        }


class SubjectUpdate(BaseModel):
    """Schema for updating subjects"""
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Subject name")
    description: Optional[str] = Field(None, max_length=500, description="Subject description")
    is_active: Optional[bool] = Field(None, description="Subject status")

    @validator('name')
    def validate_name(cls, v):
        """Validate and clean subject name"""
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError('Subject name must be at least 2 characters long')
        return v


class SubjectResponse(BaseModel):
    """Subject response schema"""
    id: str = Field(..., description="Subject ID")
    name: str = Field(..., description="Subject name")
    description: Optional[str] = Field(None, description="Subject description")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    is_active: bool = Field(..., description="Subject status")

    class Config:
        from_attributes = True


class SubjectWithStats(SubjectResponse):
    """Subject response with statistics"""
    group_count: int = Field(..., description="Number of groups teaching this subject")
    teacher_count: int = Field(..., description="Number of teachers teaching this subject")
    student_count: int = Field(..., description="Total students studying this subject")


# Group-Subject Assignment Schemas

class GroupSubjectAssign(BaseModel):
    """Schema for assigning teacher to group-subject"""
    group_id: str = Field(..., description="Group ID")
    subject_id: str = Field(..., description="Subject ID")
    teacher_id: str = Field(..., description="Teacher ID")

    class Config:
        schema_extra = {
            "example": {
                "group_id": "group-uuid",
                "subject_id": "subject-uuid",
                "teacher_id": "teacher-uuid"
            }
        }


class GroupSubjectUpdate(BaseModel):
    """Schema for updating group-subject assignment"""
    teacher_id: str = Field(..., description="New teacher ID")

    class Config:
        schema_extra = {
            "example": {
                "teacher_id": "new-teacher-uuid"
            }
        }


class GroupSubjectResponse(BaseModel):
    """Group-subject assignment response"""
    id: str = Field(..., description="Assignment ID")
    group_id: str = Field(..., description="Group ID")
    subject_id: str = Field(..., description="Subject ID")
    teacher_id: str = Field(..., description="Teacher ID")
    created_at: datetime = Field(..., description="Assignment timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class GroupSubjectDetail(GroupSubjectResponse):
    """Detailed group-subject assignment with related data"""
    group_name: str = Field(..., description="Group name")
    subject_name: str = Field(..., description="Subject name")
    teacher_name: str = Field(..., description="Teacher name")
    student_count: int = Field(..., description="Number of students")


# Schedule Schemas

class ScheduleCreate(BaseModel):
    """Schema for creating schedules"""
    group_id: str = Field(..., description="Group ID")
    subject_id: str = Field(..., description="Subject ID")
    teacher_id: str = Field(..., description="Teacher ID")
    day_of_week: DayOfWeek = Field(..., description="Day of the week")
    start_time: str = Field(..., description="Start time (HH:MM format)")
    end_time: str = Field(..., description="End time (HH:MM format)")

    @validator('start_time', 'end_time')
    def validate_time_format(cls, v):
        """Validate time format"""
        import re
        if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', v):
            raise ValueError('Time must be in HH:MM format')
        return v

    @validator('end_time')
    def validate_end_after_start(cls, v, values):
        """Validate end time is after start time"""
        if 'start_time' in values:
            from datetime import datetime
            start = datetime.strptime(values['start_time'], '%H:%M').time()
            end = datetime.strptime(v, '%H:%M').time()
            if end <= start:
                raise ValueError('End time must be after start time')
        return v

    class Config:
        schema_extra = {
            "example": {
                "group_id": "group-uuid",
                "subject_id": "subject-uuid",
                "teacher_id": "teacher-uuid",
                "day_of_week": "monday",
                "start_time": "09:00",
                "end_time": "10:30"
            }
        }


class ScheduleUpdate(BaseModel):
    """Schema for updating schedules"""
    day_of_week: Optional[DayOfWeek] = Field(None, description="Day of the week")
    start_time: Optional[str] = Field(None, description="Start time (HH:MM format)")
    end_time: Optional[str] = Field(None, description="End time (HH:MM format)")

    @validator('start_time', 'end_time')
    def validate_time_format(cls, v):
        """Validate time format"""
        if v is not None:
            import re
            if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', v):
                raise ValueError('Time must be in HH:MM format')
        return v


class ScheduleResponse(BaseModel):
    """Schedule response schema"""
    id: str = Field(..., description="Schedule ID")
    group_id: str = Field(..., description="Group ID")
    subject_id: str = Field(..., description="Subject ID")
    teacher_id: str = Field(..., description="Teacher ID")
    day_of_week: str = Field(..., description="Day of the week")
    start_time: str = Field(..., description="Start time")
    end_time: str = Field(..., description="End time")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class ScheduleDetail(ScheduleResponse):
    """Detailed schedule with related information"""
    group_name: str = Field(..., description="Group name")
    subject_name: str = Field(..., description="Subject name")
    teacher_name: str = Field(..., description="Teacher name")
    duration_minutes: int = Field(..., description="Class duration in minutes")


class WeeklySchedule(BaseModel):
    """Weekly schedule for a group"""
    group_id: str = Field(..., description="Group ID")
    group_name: str = Field(..., description="Group name")
    schedule: List[ScheduleDetail] = Field(..., description="Weekly schedule")


class DailySchedule(BaseModel):
    """Daily schedule"""
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    day_of_week: str = Field(..., description="Day of the week")
    classes: List[ScheduleDetail] = Field(..., description="Classes for the day")


# List Response Schemas

class GroupListResponse(BaseModel):
    """Group list response"""
    groups: List[GroupResponse] = Field(..., description="List of groups")
    total: int = Field(..., description="Total number of groups")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total pages")


class SubjectListResponse(BaseModel):
    """Subject list response"""
    subjects: List[SubjectResponse] = Field(..., description="List of subjects")
    total: int = Field(..., description="Total number of subjects")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total pages")


class ScheduleListResponse(BaseModel):
    """Schedule list response"""
    schedules: List[ScheduleDetail] = Field(..., description="List of schedules")
    total: int = Field(..., description="Total number of schedules")


# Management Dashboard Schemas

class ManagementStats(BaseModel):
    """Management statistics for dashboard"""
    total_groups: int = Field(..., description="Total number of groups")
    total_subjects: int = Field(..., description="Total number of subjects")
    total_assignments: int = Field(..., description="Total group-subject assignments")
    total_schedule_slots: int = Field(..., description="Total scheduled classes")
    active_groups: int = Field(..., description="Number of active groups")
    active_subjects: int = Field(..., description="Number of active subjects")


class GroupManagementInfo(BaseModel):
    """Comprehensive group management information"""
    group: GroupResponse = Field(..., description="Group information")
    subjects: List[GroupSubjectDetail] = Field(..., description="Assigned subjects")
    schedule: List[ScheduleDetail] = Field(..., description="Group schedule")
    student_count: int = Field(..., description="Number of students")


# Conflict Check Schemas

class ScheduleConflict(BaseModel):
    """Schedule conflict information"""
    existing_schedule_id: str = Field(..., description="Conflicting schedule ID")
    conflict_type: str = Field(..., description="Type of conflict")
    message: str = Field(..., description="Conflict description")


class ConflictCheckRequest(BaseModel):
    """Schedule conflict check request"""
    teacher_id: str = Field(..., description="Teacher ID")
    day_of_week: DayOfWeek = Field(..., description="Day of the week")
    start_time: str = Field(..., description="Start time")
    end_time: str = Field(..., description="End time")
    exclude_schedule_id: Optional[str] = Field(None, description="Schedule ID to exclude from check")


class ConflictCheckResponse(BaseModel):
    """Schedule conflict check response"""
    has_conflict: bool = Field(..., description="Whether there is a conflict")
    conflicts: List[ScheduleConflict] = Field(default=[], description="List of conflicts")


# Bulk Operations Schemas

class BulkGroupUpdate(BaseModel):
    """Schema for bulk group operations"""
    group_ids: List[str] = Field(..., min_items=1, description="List of group IDs")
    is_active: bool = Field(..., description="New active status")


class BulkSubjectUpdate(BaseModel):
    """Schema for bulk subject operations"""
    subject_ids: List[str] = Field(..., min_items=1, description="List of subject IDs")
    is_active: bool = Field(..., description="New active status")


class BulkOperationResponse(BaseModel):
    """Bulk operation response"""
    success: bool = Field(..., description="Operation success")
    updated_count: int = Field(..., description="Number of items updated")
    failed_count: int = Field(..., description="Number of items failed")
    errors: List[str] = Field(default=[], description="List of errors")


# Import/Export Schemas

class GroupImport(BaseModel):
    """Schema for importing groups"""
    name: str = Field(..., description="Group name")
    description: Optional[str] = Field(None, description="Group description")


class SubjectImport(BaseModel):
    """Schema for importing subjects"""
    name: str = Field(..., description="Subject name")
    description: Optional[str] = Field(None, description="Subject description")


class ScheduleImport(BaseModel):
    """Schema for importing schedules"""
    group_name: str = Field(..., description="Group name")
    subject_name: str = Field(..., description="Subject name")
    teacher_phone: int = Field(..., description="Teacher phone number")
    day_of_week: DayOfWeek = Field(..., description="Day of the week")
    start_time: str = Field(..., description="Start time")
    end_time: str = Field(..., description="End time")


class ImportResponse(BaseModel):
    """Import operation response"""
    success: bool = Field(..., description="Import success")
    created_count: int = Field(..., description="Number of items created")
    skipped_count: int = Field(..., description="Number of items skipped")
    error_count: int = Field(..., description="Number of errors")
    errors: List[str] = Field(default=[], description="List of import errors")


# Success Response Schemas

class GroupCreatedResponse(BaseModel):
    """Group creation success response"""
    message: str = Field(default="Group created successfully", description="Success message")
    group: GroupResponse = Field(..., description="Created group")


class SubjectCreatedResponse(BaseModel):
    """Subject creation success response"""
    message: str = Field(default="Subject created successfully", description="Success message")
    subject: SubjectResponse = Field(..., description="Created subject")


class ScheduleCreatedResponse(BaseModel):
    """Schedule creation success response"""
    message: str = Field(default="Schedule created successfully", description="Success message")
    schedule: ScheduleDetail = Field(..., description="Created schedule")


class AssignmentCreatedResponse(BaseModel):
    """Assignment creation success response"""
    message: str = Field(default="Teacher assigned successfully", description="Success message")
    assignment: GroupSubjectDetail = Field(..., description="Created assignment")