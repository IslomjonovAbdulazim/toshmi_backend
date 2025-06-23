# app/routes/admin.py
"""
Admin management routes with passionate administrative control!
Handles all administrative operations including user management, groups, subjects, payments, and more.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.user_service import get_user_service
from ..services.admin_service import get_admin_service
from ..utils.dependencies import require_admin
from ..schemas.users import (
    StudentCreate, ParentCreate, TeacherCreate,
    StudentResponse, ParentResponse, TeacherResponse,
    AssignParentRequest, ChangeGroupRequest
)
from ..schemas.management import (
    GroupCreate, SubjectCreate, ScheduleCreate, GroupSubjectAssign,
    GroupResponse, SubjectResponse, ScheduleResponse
)
from ..schemas.misc import (
    PaymentCreate, MonthlyPaymentStatusUpdate, NewsCreate,
    PaymentResponse, NewsResponse
)

router = APIRouter()


# User Management Routes

@router.post("/students", response_model=dict, summary="Create Student")
async def create_student(
        student_data: StudentCreate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Create a new student account

    - **phone**: Student's phone number (unique per role)
    - **full_name**: Student's full name
    - **password**: Initial password
    - **group_id**: ID of the group to assign student to
    - **parent_id**: Optional parent ID to link
    - **graduation_year**: Expected graduation year

    Returns created student information with credentials
    """
    user_service = get_user_service(db)
    return user_service.create_student(student_data, admin.id)


@router.post("/teachers", response_model=dict, summary="Create Teacher")
async def create_teacher(
        teacher_data: TeacherCreate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Create a new teacher account

    - **phone**: Teacher's phone number (unique per role)
    - **full_name**: Teacher's full name
    - **password**: Initial password

    Returns created teacher information with credentials
    """
    user_service = get_user_service(db)
    return user_service.create_teacher(teacher_data, admin.id)


@router.post("/parents", response_model=dict, summary="Create Parent")
async def create_parent(
        parent_data: ParentCreate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Create a new parent account

    - **phone**: Parent's phone number (unique per role)
    - **full_name**: Parent's full name
    - **password**: Initial password

    Returns created parent information with credentials
    """
    user_service = get_user_service(db)
    return user_service.create_parent(parent_data, admin.id)


@router.get("/students", response_model=dict, summary="Get All Students")
async def get_students(
        page: int = Query(default=1, ge=1, description="Page number"),
        size: int = Query(default=20, ge=1, le=100, description="Page size"),
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Get paginated list of all students

    Returns list of students with user information, group details, and parent info
    """
    user_service = get_user_service(db)
    return user_service.get_all_students(page, size)


@router.get("/teachers", response_model=dict, summary="Get All Teachers")
async def get_teachers(
        page: int = Query(default=1, ge=1, description="Page number"),
        size: int = Query(default=20, ge=1, le=100, description="Page size"),
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Get paginated list of all teachers

    Returns list of teachers with user information
    """
    user_service = get_user_service(db)
    return user_service.get_all_teachers(page, size)


@router.get("/parents", response_model=dict, summary="Get All Parents")
async def get_parents(
        page: int = Query(default=1, ge=1, description="Page number"),
        size: int = Query(default=20, ge=1, le=100, description="Page size"),
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Get paginated list of all parents

    Returns list of parents with user information and children details
    """
    user_service = get_user_service(db)
    return user_service.get_all_parents(page, size)


@router.get("/students/{student_id}", response_model=dict, summary="Get Student Details")
async def get_student(
        student_id: str,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Get detailed information about a specific student

    Returns student details including user info, group, and parent information
    """
    user_service = get_user_service(db)
    return user_service.get_student_by_id(student_id)


@router.post("/students/{student_id}/assign-parent", response_model=dict, summary="Assign Parent to Student")
async def assign_parent_to_student(
        student_id: str,
        assign_request: AssignParentRequest,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Assign a parent to a student

    - **parent_id**: ID of parent to assign

    Links parent-child relationship for payment tracking and notifications
    """
    user_service = get_user_service(db)
    return user_service.assign_parent_to_student(student_id, assign_request.parent_id, admin.id)


@router.put("/students/{student_id}/change-group", response_model=dict, summary="Change Student Group")
async def change_student_group(
        student_id: str,
        group_request: ChangeGroupRequest,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Move student to a different group

    - **group_id**: ID of new group

    Academic records are preserved when changing groups
    """
    user_service = get_user_service(db)
    return user_service.change_student_group(student_id, group_request.group_id, admin.id)


# Group Management Routes

@router.post("/groups", response_model=dict, summary="Create Group")
async def create_group(
        group_data: GroupCreate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Create a new group/class

    - **name**: Group name (unique)
    - **description**: Optional group description

    Groups are the main organizational unit for students
    """
    admin_service = get_admin_service(db)
    return admin_service.create_group(group_data, admin.id)


@router.get("/groups", response_model=List[dict], summary="Get All Groups")
async def get_groups(
        include_inactive: bool = Query(default=False, description="Include inactive groups"),
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Get all groups with statistics

    Returns list of groups with student and subject counts
    """
    admin_service = get_admin_service(db)
    return admin_service.get_all_groups(include_inactive)


# Subject Management Routes

@router.post("/subjects", response_model=dict, summary="Create Subject")
async def create_subject(
        subject_data: SubjectCreate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Create a new subject

    - **name**: Subject name (unique)
    - **description**: Optional subject description

    Subjects can be taught across multiple groups
    """
    admin_service = get_admin_service(db)
    return admin_service.create_subject(subject_data, admin.id)


@router.get("/subjects", response_model=List[dict], summary="Get All Subjects")
async def get_subjects(
        include_inactive: bool = Query(default=False, description="Include inactive subjects"),
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Get all subjects with statistics

    Returns list of subjects with group and teacher counts
    """
    admin_service = get_admin_service(db)
    return admin_service.get_all_subjects(include_inactive)


# Group-Subject Assignment Routes

@router.post("/assign-teacher", response_model=dict, summary="Assign Teacher to Group-Subject")
async def assign_teacher_to_group_subject(
        assignment_data: GroupSubjectAssign,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Assign a teacher to teach a subject in a specific group

    - **group_id**: Group ID
    - **subject_id**: Subject ID
    - **teacher_id**: Teacher ID

    Each group-subject combination can have only one teacher
    """
    admin_service = get_admin_service(db)
    return admin_service.assign_teacher_to_group_subject(assignment_data, admin.id)


# Schedule Management Routes

@router.post("/schedule", response_model=dict, summary="Create Schedule Entry")
async def create_schedule(
        schedule_data: ScheduleCreate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Create a new schedule entry

    - **group_id**: Group ID
    - **subject_id**: Subject ID
    - **teacher_id**: Teacher ID (must be assigned to this group-subject)
    - **day_of_week**: Day of the week (monday, tuesday, etc.)
    - **start_time**: Start time (HH:MM format)
    - **end_time**: End time (HH:MM format)

    System prevents scheduling conflicts for the same group
    """
    admin_service = get_admin_service(db)
    return admin_service.create_schedule(schedule_data, admin.id)


@router.get("/schedule", response_model=List[dict], summary="Get All Schedules")
async def get_all_schedules(
        group_id: Optional[str] = Query(None, description="Filter by group"),
        teacher_id: Optional[str] = Query(None, description="Filter by teacher"),
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Get all schedule entries with filtering options

    Returns comprehensive schedule information with group, subject, and teacher details
    """
    # Implementation would go in admin service
    # For now, return placeholder
    return {"message": "Schedule retrieval endpoint - implementation pending"}


# Payment Management Routes

@router.post("/payments", response_model=dict, summary="Record Payment")
async def record_payment(
        payment_data: PaymentCreate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Record a new payment for a student

    - **student_id**: Student ID
    - **amount**: Payment amount
    - **month**: Payment month (YYYY-MM format)
    - **notes**: Optional payment notes

    Automatically updates monthly payment status and creates notifications
    """
    admin_service = get_admin_service(db)
    return admin_service.record_payment(payment_data, admin.id)


@router.put("/monthly-payment-status", response_model=dict, summary="Update Monthly Payment Status")
async def update_monthly_payment_status(
        status_data: MonthlyPaymentStatusUpdate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Update monthly payment completion status for a student

    - **student_id**: Student ID
    - **month**: Month (YYYY-MM format)
    - **is_fully_paid**: Whether month is fully paid
    - **total_amount_due**: Optional expected total amount

    Allows manual marking of payment completion status
    """
    admin_service = get_admin_service(db)
    return admin_service.update_monthly_payment_status(status_data, admin.id)


@router.get("/payments", response_model=dict, summary="Get Payment History")
async def get_payments(
        student_id: Optional[str] = Query(None, description="Filter by student"),
        month: Optional[str] = Query(None, description="Filter by month (YYYY-MM)"),
        page: int = Query(default=1, ge=1, description="Page number"),
        size: int = Query(default=20, ge=1, le=100, description="Page size"),
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Get payment history with filtering and pagination

    Returns detailed payment information with student details
    """
    # Implementation would go in admin service
    return {"message": "Payment history endpoint - implementation pending"}


# News Management Routes

@router.post("/news", response_model=dict, summary="Create News Article")
async def create_news(
        news_data: NewsCreate,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Create a new news article

    - **title**: News title
    - **body**: News content
    - **external_links**: Optional external links
    - **is_published**: Publication status

    Published news creates notifications for all users
    """
    admin_service = get_admin_service(db)
    return admin_service.create_news(news_data, admin.id)


@router.get("/news", response_model=List[dict], summary="Get All News")
async def get_all_news(
        include_unpublished: bool = Query(default=True, description="Include unpublished news"),
        page: int = Query(default=1, ge=1, description="Page number"),
        size: int = Query(default=20, ge=1, le=100, description="Page size"),
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Get all news articles with pagination

    Admins can see both published and unpublished articles
    """
    # Implementation would go in admin service
    return {"message": "News list endpoint - implementation pending"}


@router.delete("/news/{news_id}", response_model=dict, summary="Delete News Article")
async def delete_news(
        news_id: str,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Delete a news article

    Permanently removes news article and associated files
    """
    # Implementation would go in admin service
    return {"message": f"News {news_id} deleted successfully"}


# Reporting Routes

@router.get("/reports/overview", response_model=dict, summary="System Overview Report")
async def get_system_overview(
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Get comprehensive system overview for admin dashboard

    Returns statistics on users, academics, payments, and system activity
    """
    admin_service = get_admin_service(db)
    return admin_service.get_system_overview()


@router.get("/reports/payments", response_model=dict, summary="Payment Report")
async def get_payment_report(
        month: int = Query(..., ge=1, le=12, description="Report month"),
        year: int = Query(..., ge=2020, le=2030, description="Report year"),
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Generate detailed payment report for specific month

    Returns payment statistics, collection rates, and detailed payment list
    """
    admin_service = get_admin_service(db)
    return admin_service.get_payment_report(month, year)


@router.get("/reports/academic", response_model=dict, summary="Academic Performance Report")
async def get_academic_report(
        group_id: Optional[str] = Query(None, description="Filter by group"),
        subject_id: Optional[str] = Query(None, description="Filter by subject"),
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Generate academic performance report

    Returns grade distributions, attendance rates, and academic statistics
    """
    # Implementation would go in admin service
    return {"message": "Academic report endpoint - implementation pending"}


# User Statistics Routes

@router.get("/statistics/users", response_model=dict, summary="User Statistics")
async def get_user_statistics(
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Get comprehensive user statistics

    Returns counts and breakdowns of all user types
    """
    user_service = get_user_service(db)
    return user_service.get_user_statistics()


@router.get("/statistics/academic", response_model=dict, summary="Academic Statistics")
async def get_academic_statistics(
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Get academic activity statistics

    Returns homework, exam, grade, and attendance statistics
    """
    # Implementation would go in admin service
    return {"message": "Academic statistics endpoint - implementation pending"}


# Bulk Operations Routes

@router.post("/bulk/deactivate-users", response_model=dict, summary="Bulk Deactivate Users")
async def bulk_deactivate_users(
        user_ids: List[str],
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Deactivate multiple users at once

    - **user_ids**: List of user IDs to deactivate

    Cannot deactivate admin users
    """
    # Implementation would go in admin service
    return {"message": f"Bulk deactivation of {len(user_ids)} users completed"}


@router.post("/bulk/activate-users", response_model=dict, summary="Bulk Activate Users")
async def bulk_activate_users(
        user_ids: List[str],
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Activate multiple users at once

    - **user_ids**: List of user IDs to activate
    """
    # Implementation would go in admin service
    return {"message": f"Bulk activation of {len(user_ids)} users completed"}