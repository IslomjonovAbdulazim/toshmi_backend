# app/routes/parent.py
"""
Parent routes with passionate family engagement!
Handles parent access to their children's academic information and progress monitoring.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date

from ..database import get_db
from ..utils.dependencies import require_parent, get_current_parent_profile, validate_parent_children_access
from ..schemas.academic import GradeResponse, AttendanceResponse

router = APIRouter()


# Parent Profile and Children

@router.get("/profile", response_model=dict, summary="Get Parent Profile")
async def get_parent_profile(
        parent=Depends(get_current_parent_profile),
        children=Depends(validate_parent_children_access),
        db: Session = Depends(get_db)
):
    """
    Get current parent's profile and children information

    Returns parent details and list of all children
    """
    children_info = []
    for child in children:
        children_info.append({
            "student_id": child.id,
            "full_name": child.user.full_name,
            "group_id": child.group_id,
            "group_name": child.group.name if child.group else None,
            "graduation_year": child.graduation_year,
            "phone": child.user.phone,
            "avatar_url": child.user.avatar_url,
            "is_active": child.user.is_active
        })

    return {
        "parent_id": parent.id,
        "user_id": parent.user_id,
        "full_name": parent.user.full_name,
        "phone": parent.user.phone,
        "avatar_url": parent.user.avatar_url,
        "created_at": parent.created_at,
        "children_count": len(children),
        "children": children_info
    }


@router.get("/children", response_model=List[dict], summary="Get All Children")
async def get_children(
        children=Depends(validate_parent_children_access),
        db: Session = Depends(get_db)
):
    """
    Get detailed information about all children

    Returns comprehensive information about each child including academic status
    """
    from ..models import Grade, Attendance, Payment
    from sqlalchemy import func, case
    from ..utils.helpers import AttendanceStatus, get_attendance_percentage

    children_details = []

    for child in children:
        # Get recent academic statistics
        recent_grades_count = db.query(func.count(Grade.id)).filter(
            Grade.student_id == child.id
        ).scalar() or 0

        average_grade = db.query(func.avg(Grade.grade)).filter(
            Grade.student_id == child.id
        ).scalar()

        # Get attendance statistics
        attendance_stats = db.query(
            func.count(Attendance.id).label('total_classes'),
            func.sum(case((Attendance.status == AttendanceStatus.PRESENT, 1), else_=0)).label('present_count')
        ).filter(Attendance.student_id == child.id).first()

        attendance_percentage = get_attendance_percentage(
            int(attendance_stats.present_count or 0),
            int(attendance_stats.total_classes or 0)
        )

        # Get recent payment information
        recent_payment = db.query(Payment).filter(
            Payment.student_id == child.id
        ).order_by(Payment.payment_date.desc()).first()

        child_data = {
            "student_id": child.id,
            "full_name": child.user.full_name,
            "phone": child.user.phone,
            "avatar_url": child.user.avatar_url,
            "group_id": child.group_id,
            "group_name": child.group.name if child.group else None,
            "graduation_year": child.graduation_year,
            "is_active": child.user.is_active,
            "academic_summary": {
                "total_grades": recent_grades_count,
                "average_grade": round(float(average_grade), 2) if average_grade else 0,
                "attendance_percentage": attendance_percentage,
                "total_classes": int(attendance_stats.total_classes or 0)
            },
            "recent_payment": {
                "amount": recent_payment.amount if recent_payment else None,
                "date": recent_payment.payment_date if recent_payment else None,
                "month": recent_payment.month if recent_payment else None
            } if recent_payment else None
        }

        children_details.append(child_data)

    return children_details


@router.get("/children/{child_id}/profile", response_model=dict, summary="Get Child Profile")
async def get_child_profile(
        child_id: str,
        parent=Depends(get_current_parent_profile),
        db: Session = Depends(get_db)
):
    """
    Get detailed profile of a specific child

    Returns comprehensive child information including group and academic details
    """
    from ..models import Student, User

    # Verify child belongs to parent
    child = db.query(Student).join(User).filter(
        Student.id == child_id,
        Student.parent_id == parent.id,
        User.is_active == True
    ).first()

    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found or access denied"
        )

    # Get group subjects and teachers
    from ..models import GroupSubject
    group_subjects = []
    if child.group:
        subjects = db.query(GroupSubject).filter(
            GroupSubject.group_id == child.group_id
        ).all()

        for gs in subjects:
            group_subjects.append({
                "subject_id": gs.subject_id,
                "subject_name": gs.subject.name,
                "teacher_id": gs.teacher_id,
                "teacher_name": gs.teacher.user.full_name
            })

    return {
        "student_id": child.id,
        "full_name": child.user.full_name,
        "phone": child.user.phone,
        "avatar_url": child.user.avatar_url,
        "group": {
            "group_id": child.group_id,
            "group_name": child.group.name if child.group else None,
            "subjects": group_subjects
        } if child.group else None,
        "graduation_year": child.graduation_year,
        "created_at": child.created_at,
        "is_active": child.user.is_active
    }


# Academic Information for Children

@router.get("/children/{child_id}/homework", response_model=List[dict], summary="Get Child's Homework")
async def get_child_homework(
        child_id: str,
        include_completed: bool = Query(default=True, description="Include completed homework"),
        subject_id: Optional[str] = Query(None, description="Filter by subject"),
        parent=Depends(get_current_parent_profile),
        db: Session = Depends(get_db)
):
    """
    Get homework assignments for specific child

    Returns homework with completion status and grades
    """
    # Verify child belongs to parent
    from ..models import Student
    child = db.query(Student).filter(
        Student.id == child_id,
        Student.parent_id == parent.id
    ).first()

    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found or access denied"
        )

    from ..services.academic_service import get_academic_service
    academic_service = get_academic_service(db)
    homework_list = academic_service.get_student_homework(child_id, include_completed)

    # Filter by subject if specified
    if subject_id:
        homework_list = [hw for hw in homework_list if hw.get('subject_id') == subject_id]

    return homework_list


@router.get("/children/{child_id}/exams", response_model=List[dict], summary="Get Child's Exams")
async def get_child_exams(
        child_id: str,
        include_past: bool = Query(default=True, description="Include past exams"),
        subject_id: Optional[str] = Query(None, description="Filter by subject"),
        parent=Depends(get_current_parent_profile),
        db: Session = Depends(get_db)
):
    """
    Get exams for specific child

    Returns exams with grades and schedule information
    """
    # Verify child belongs to parent
    from ..models import Student
    child = db.query(Student).filter(
        Student.id == child_id,
        Student.parent_id == parent.id
    ).first()

    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found or access denied"
        )

    from ..models import Exam, Grade
    from datetime import datetime

    # Get exams for child's group
    exams_query = db.query(Exam).filter(Exam.group_id == child.group_id)

    if not include_past:
        exams_query = exams_query.filter(Exam.exam_date >= datetime.utcnow())

    if subject_id:
        exams_query = exams_query.filter(Exam.subject_id == subject_id)

    exams = exams_query.order_by(Exam.exam_date.desc()).all()

    result = []
    for exam in exams:
        # Get grade if exists
        grade = db.query(Grade).filter(
            Grade.student_id == child_id,
            Grade.exam_id == exam.id
        ).first()

        exam_data = {
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "exam_date": exam.exam_date,
            "subject_name": exam.subject.name,
            "teacher_name": exam.teacher.user.full_name,
            "is_upcoming": exam.exam_date > datetime.utcnow(),
            "grade": None
        }

        if grade:
            from ..utils.helpers import calculate_grade_percentage
            exam_data["grade"] = {
                "grade": grade.grade,
                "max_grade": grade.max_grade,
                "percentage": calculate_grade_percentage(grade.grade, grade.max_grade),
                "comment": grade.comment,
                "graded_at": grade.graded_at
            }

        result.append(exam_data)

    return result


@router.get("/children/{child_id}/grades", response_model=List[dict], summary="Get Child's Grades")
async def get_child_grades(
        child_id: str,
        subject_id: Optional[str] = Query(None, description="Filter by subject"),
        grade_type: Optional[str] = Query(None, description="Filter by type (homework/exam)"),
        parent=Depends(get_current_parent_profile),
        db: Session = Depends(get_db)
):
    """
    Get all grades for specific child

    Returns comprehensive grade history with filtering options
    """
    # Verify child belongs to parent
    from ..models import Student
    child = db.query(Student).filter(
        Student.id == child_id,
        Student.parent_id == parent.id
    ).first()

    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found or access denied"
        )

    from ..models import Grade

    grades_query = db.query(Grade).filter(Grade.student_id == child_id)

    if subject_id:
        grades_query = grades_query.filter(Grade.subject_id == subject_id)

    if grade_type == "homework":
        grades_query = grades_query.filter(Grade.homework_id.isnot(None))
    elif grade_type == "exam":
        grades_query = grades_query.filter(Grade.exam_id.isnot(None))

    grades = grades_query.order_by(Grade.graded_at.desc()).all()

    result = []
    for grade in grades:
        from ..utils.helpers import calculate_grade_percentage

        grade_data = {
            "id": grade.id,
            "subject_name": grade.homework.subject.name if grade.homework else grade.exam.subject.name,
            "type": "homework" if grade.homework_id else "exam",
            "title": grade.homework.title if grade.homework else grade.exam.title,
            "grade": grade.grade,
            "max_grade": grade.max_grade,
            "percentage": calculate_grade_percentage(grade.grade, grade.max_grade),
            "comment": grade.comment,
            "teacher_name": grade.graded_by_teacher.user.full_name,
            "graded_at": grade.graded_at
        }

        result.append(grade_data)

    return result


@router.get("/children/{child_id}/grades/summary", response_model=dict, summary="Get Child's Grade Summary")
async def get_child_grade_summary(
        child_id: str,
        parent=Depends(get_current_parent_profile),
        db: Session = Depends(get_db)
):
    """
    Get grade summary and statistics for specific child

    Returns average grades by subject and overall performance metrics
    """
    # Verify child belongs to parent
    from ..models import Student
    child = db.query(Student).filter(
        Student.id == child_id,
        Student.parent_id == parent.id
    ).first()

    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found or access denied"
        )

    from ..models import Grade, Subject
    from sqlalchemy import func

    # Get grade statistics by subject
    subject_stats = db.query(
        Grade.subject_id,
        func.count(Grade.id).label('total_grades'),
        func.avg(Grade.grade).label('avg_grade'),
        func.max(Grade.grade).label('max_grade_received'),
        func.min(Grade.grade).label('min_grade_received')
    ).filter(Grade.student_id == child_id).group_by(Grade.subject_id).all()

    # Get overall statistics
    overall_stats = db.query(
        func.count(Grade.id).label('total_grades'),
        func.avg(Grade.grade).label('overall_average')
    ).filter(Grade.student_id == child_id).first()

    # Format subject statistics
    subjects_summary = []
    for stat in subject_stats:
        subject = db.query(Subject).filter(Subject.id == stat.subject_id).first()

        subjects_summary.append({
            "subject_id": stat.subject_id,
            "subject_name": subject.name if subject else "Unknown",
            "total_grades": stat.total_grades,
            "average_grade": round(float(stat.avg_grade), 2) if stat.avg_grade else 0,
            "highest_grade": float(stat.max_grade_received) if stat.max_grade_received else 0,
            "lowest_grade": float(stat.min_grade_received) if stat.min_grade_received else 0
        })

    return {
        "child_id": child_id,
        "child_name": child.user.full_name,
        "overall": {
            "total_grades": overall_stats.total_grades or 0,
            "overall_average": round(float(overall_stats.overall_average), 2) if overall_stats.overall_average else 0
        },
        "by_subject": subjects_summary,
        "generated_at": db.query(func.now()).scalar()
    }


@router.get("/children/{child_id}/attendance", response_model=List[dict], summary="Get Child's Attendance")
async def get_child_attendance(
        child_id: str,
        subject_id: Optional[str] = Query(None, description="Filter by subject"),
        date_from: Optional[date] = Query(None, description="Filter from date"),
        date_to: Optional[date] = Query(None, description="Filter to date"),
        parent=Depends(get_current_parent_profile),
        db: Session = Depends(get_db)
):
    """
    Get attendance records for specific child

    Returns attendance history with filtering options
    """
    # Verify child belongs to parent
    from ..models import Student
    child = db.query(Student).filter(
        Student.id == child_id,
        Student.parent_id == parent.id
    ).first()

    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found or access denied"
        )

    from ..models import Attendance

    attendance_query = db.query(Attendance).filter(Attendance.student_id == child_id)

    if subject_id:
        attendance_query = attendance_query.filter(Attendance.subject_id == subject_id)

    if date_from:
        attendance_query = attendance_query.filter(Attendance.date >= date_from)

    if date_to:
        attendance_query = attendance_query.filter(Attendance.date <= date_to)

    attendance_records = attendance_query.order_by(Attendance.date.desc()).all()

    result = []
    for record in attendance_records:
        result.append({
            "id": record.id,
            "subject_name": record.subject.name,
            "date": record.date,
            "status": record.status,
            "notes": record.notes,
            "teacher_name": record.teacher.user.full_name,
            "created_at": record.created_at
        })

    return result


@router.get("/children/{child_id}/attendance/summary", response_model=dict, summary="Get Child's Attendance Summary")
async def get_child_attendance_summary(
        child_id: str,
        parent=Depends(get_current_parent_profile),
        db: Session = Depends(get_db)
):
    """
    Get attendance summary and statistics for specific child

    Returns attendance rates by subject and overall attendance metrics
    """
    # Verify child belongs to parent
    from ..models import Student
    child = db.query(Student).filter(
        Student.id == child_id,
        Student.parent_id == parent.id
    ).first()

    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found or access denied"
        )

    from ..models import Attendance, Subject
    from sqlalchemy import func, case
    from ..utils.helpers import AttendanceStatus, get_attendance_percentage

    # Get attendance statistics by subject
    subject_stats = db.query(
        Attendance.subject_id,
        func.count(Attendance.id).label('total_records'),
        func.sum(case((Attendance.status == AttendanceStatus.PRESENT, 1), else_=0)).label('present_count'),
        func.sum(case((Attendance.status == AttendanceStatus.ABSENT, 1), else_=0)).label('absent_count'),
        func.sum(case((Attendance.status == AttendanceStatus.LATE, 1), else_=0)).label('late_count')
    ).filter(Attendance.student_id == child_id).group_by(Attendance.subject_id).all()

    # Get overall statistics
    overall_stats = db.query(
        func.count(Attendance.id).label('total_records'),
        func.sum(case((Attendance.status == AttendanceStatus.PRESENT, 1), else_=0)).label('present_count'),
        func.sum(case((Attendance.status == AttendanceStatus.ABSENT, 1), else_=0)).label('absent_count'),
        func.sum(case((Attendance.status == AttendanceStatus.LATE, 1), else_=0)).label('late_count')
    ).filter(Attendance.student_id == child_id).first()

    # Format subject statistics
    subjects_summary = []
    for stat in subject_stats:
        subject = db.query(Subject).filter(Subject.id == stat.subject_id).first()

        attendance_percentage = get_attendance_percentage(
            int(stat.present_count or 0),
            int(stat.total_records or 0)
        )

        subjects_summary.append({
            "subject_id": stat.subject_id,
            "subject_name": subject.name if subject else "Unknown",
            "total_classes": int(stat.total_records or 0),
            "present_count": int(stat.present_count or 0),
            "absent_count": int(stat.absent_count or 0),
            "late_count": int(stat.late_count or 0),
            "attendance_percentage": attendance_percentage
        })

    overall_attendance_percentage = get_attendance_percentage(
        int(overall_stats.present_count or 0),
        int(overall_stats.total_records or 0)
    )

    return {
        "child_id": child_id,
        "child_name": child.user.full_name,
        "overall": {
            "total_classes": int(overall_stats.total_records or 0),
            "present_count": int(overall_stats.present_count or 0),
            "absent_count": int(overall_stats.absent_count or 0),
            "late_count": int(overall_stats.late_count or 0),
            "attendance_percentage": overall_attendance_percentage
        },
        "by_subject": subjects_summary,
        "generated_at": db.query(func.now()).scalar()
    }


@router.get("/children/{child_id}/schedule", response_model=List[dict], summary="Get Child's Schedule")
async def get_child_schedule(
        child_id: str,
        day: Optional[str] = Query(None, description="Filter by day of week"),
        parent=Depends(get_current_parent_profile),
        db: Session = Depends(get_db)
):
    """
    Get weekly class schedule for specific child

    Returns schedule with subjects, teachers, and time slots
    """
    # Verify child belongs to parent
    from ..models import Student
    child = db.query(Student).filter(
        Student.id == child_id,
        Student.parent_id == parent.id
    ).first()

    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found or access denied"
        )

    from ..models import Schedule

    schedule_query = db.query(Schedule).filter(Schedule.group_id == child.group_id)

    if day:
        schedule_query = schedule_query.filter(Schedule.day_of_week == day.lower())

    schedules = schedule_query.order_by(Schedule.day_of_week, Schedule.start_time).all()

    result = []
    for schedule in schedules:
        from ..utils.helpers import get_day_name_uzbek, format_time_12hour

        result.append({
            "id": schedule.id,
            "day_of_week": schedule.day_of_week,
            "day_name_uzbek": get_day_name_uzbek(schedule.day_of_week),
            "start_time": schedule.start_time,
            "end_time": schedule.end_time,
            "start_time_12h": format_time_12hour(schedule.start_time),
            "end_time_12h": format_time_12hour(schedule.end_time),
            "subject_name": schedule.subject.name,
            "teacher_name": schedule.teacher.user.full_name
        })

    return result


# Payment Information for Children

@router.get("/children/{child_id}/payments", response_model=dict, summary="Get Child's Payment History")
async def get_child_payments(
        child_id: str,
        year: Optional[int] = Query(None, description="Filter by year"),
        parent=Depends(get_current_parent_profile),
        db: Session = Depends(get_db)
):
    """
    Get payment history for specific child

    Returns payment records and monthly payment status
    """
    # Verify child belongs to parent
    from ..models import Student
    child = db.query(Student).filter(
        Student.id == child_id,
        Student.parent_id == parent.id
    ).first()

    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found or access denied"
        )

    from ..models import Payment, MonthlyPaymentStatus

    payments_query = db.query(Payment).filter(Payment.student_id == child_id)

    if year:
        payments_query = payments_query.filter(Payment.year == year)

    payments = payments_query.order_by(Payment.payment_date.desc()).all()

    # Get monthly payment statuses
    monthly_status_query = db.query(MonthlyPaymentStatus).filter(
        MonthlyPaymentStatus.student_id == child_id
    )

    if year:
        monthly_status_query = monthly_status_query.filter(MonthlyPaymentStatus.year == year)

    monthly_statuses = monthly_status_query.order_by(
        MonthlyPaymentStatus.year.desc(),
        MonthlyPaymentStatus.month.desc()
    ).all()

    # Format payment history
    payment_history = []
    for payment in payments:
        payment_history.append({
            "id": payment.id,
            "amount": payment.amount,
            "month": payment.month,
            "payment_date": payment.payment_date,
            "notes": payment.notes
        })

    # Format monthly statuses
    monthly_summary = []
    for status in monthly_statuses:
        from ..utils.helpers import get_month_name_uzbek
        month_num = int(status.month.split('-')[1])

        monthly_summary.append({
            "month": status.month,
            "month_name": get_month_name_uzbek(month_num),
            "year": status.year,
            "is_fully_paid": status.is_fully_paid,
            "total_amount_due": status.total_amount_due,
            "total_amount_paid": status.total_amount_paid,
            "updated_at": status.updated_at
        })

    return {
        "child_id": child_id,
        "child_name": child.user.full_name,
        "payment_history": payment_history,
        "monthly_summary": monthly_summary,
        "total_payments": len(payments),
        "total_amount_paid": sum(p.amount for p in payments)
    }


# News and Communication

@router.get("/news", response_model=List[dict], summary="Get School News")
async def get_school_news(
        limit: int = Query(default=10, ge=1, le=50, description="Number of news articles"),
        db: Session = Depends(get_db),
        parent=Depends(get_current_parent_profile)
):
    """
    Get published school news and announcements

    Returns recent news articles visible to parents
    """
    from ..models import News

    news_articles = db.query(News).filter(
        News.is_published == True
    ).order_by(News.published_at.desc()).limit(limit).all()

    result = []
    for article in news_articles:
        from ..utils.helpers import parse_external_links, truncate_text

        result.append({
            "id": article.id,
            "title": article.title,
            "summary": truncate_text(article.body, 200),
            "external_links": parse_external_links(article.external_links),
            "published_at": article.published_at,
            "author_name": article.published_by  # Would need to join with User table for actual name
        })

    return result


# Notifications

@router.get("/notifications", response_model=List[dict], summary="Get Parent Notifications")
async def get_notifications(
        unread_only: bool = Query(default=False, description="Get only unread notifications"),
        limit: int = Query(default=20, ge=1, le=100, description="Number of notifications"),
        parent=Depends(get_current_parent_profile),
        db: Session = Depends(get_db)
):
    """
    Get notifications for parent

    Returns notifications about children's grades, payments, news, etc.
    """
    from ..models import Notification

    notifications_query = db.query(Notification).filter(
        Notification.user_id == parent.user_id
    )

    if unread_only:
        notifications_query = notifications_query.filter(Notification.is_read == False)

    notifications = notifications_query.order_by(
        Notification.created_at.desc()
    ).limit(limit).all()

    result = []
    for notification in notifications:
        result.append({
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "type": notification.type,
            "is_read": notification.is_read,
            "created_at": notification.created_at
        })

    return result


@router.put("/notifications/{notification_id}/mark-read", response_model=dict, summary="Mark Notification as Read")
async def mark_notification_read(
        notification_id: str,
        parent=Depends(get_current_parent_profile),
        db: Session = Depends(get_db)
):
    """
    Mark a specific notification as read

    Parents can only mark their own notifications as read
    """
    from ..models import Notification

    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == parent.user_id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    notification.is_read = True
    notification.updated_at = db.query(func.now()).scalar()

    db.commit()

    return {
        "message": "Notification marked as read",
        "notification_id": notification_id
    }


# Family Dashboard

@router.get("/dashboard", response_model=dict, summary="Get Family Dashboard")
async def get_family_dashboard(
        parent=Depends(get_current_parent_profile),
        children=Depends(validate_parent_children_access),
        db: Session = Depends(get_db)
):
    """
    Get comprehensive family dashboard with all children's information

    Returns overview of all children's academic performance and recent activities
    """
    from ..models import Grade, Attendance, Payment, Homework, Exam
    from sqlalchemy import func
    from datetime import datetime, timedelta

    dashboard_data = {
        "parent_info": {
            "full_name": parent.user.full_name,
            "children_count": len(children)
        },
        "children_overview": [],
        "recent_activities": [],
        "upcoming_events": []
    }

    for child in children:
        # Get recent grades
        recent_grades = db.query(Grade).filter(
            Grade.student_id == child.id
        ).order_by(Grade.graded_at.desc()).limit(3).all()

        # Get attendance summary
        from sqlalchemy import case
        from ..utils.helpers import AttendanceStatus
        attendance_stats = db.query(
            func.count(Attendance.id).label('total_classes'),
            func.sum(case((Attendance.status == AttendanceStatus.PRESENT, 1), else_=0)).label('present_count')
        ).filter(Attendance.student_id == child.id).first()

        attendance_percentage = 0
        if attendance_stats.total_classes and attendance_stats.total_classes > 0:
            attendance_percentage = (attendance_stats.present_count / attendance_stats.total_classes) * 100

        # Get pending homework
        pending_homework_count = db.query(func.count(Homework.id)).filter(
            Homework.group_id == child.group_id,
            Homework.due_date > datetime.utcnow(),
            ~Homework.id.in_(
                db.query(Grade.homework_id).filter(
                    Grade.student_id == child.id,
                    Grade.homework_id.isnot(None)
                )
            )
        ).scalar() or 0

        child_overview = {
            "student_id": child.id,
            "full_name": child.user.full_name,
            "group_name": child.group.name if child.group else None,
            "recent_grades_count": len(recent_grades),
            "average_grade": sum(g.grade for g in recent_grades) / len(recent_grades) if recent_grades else 0,
            "attendance_percentage": round(attendance_percentage, 1),
            "pending_homework_count": pending_homework_count
        }

        dashboard_data["children_overview"].append(child_overview)

        # Add recent activities for this child
        for grade in recent_grades:
            dashboard_data["recent_activities"].append({
                "type": "grade",
                "child_name": child.user.full_name,
                "subject": grade.homework.subject.name if grade.homework else grade.exam.subject.name,
                "activity": f"Yangi baho: {grade.grade}/{grade.max_grade}",
                "date": grade.graded_at
            })

        # Get upcoming exams
        upcoming_exams = db.query(Exam).filter(
            Exam.group_id == child.group_id,
            Exam.exam_date > datetime.utcnow(),
            Exam.exam_date <= datetime.utcnow() + timedelta(days=7)
        ).all()

        for exam in upcoming_exams:
            dashboard_data["upcoming_events"].append({
                "type": "exam",
                "child_name": child.user.full_name,
                "subject": exam.subject.name,
                "title": exam.title,
                "date": exam.exam_date
            })

    # Sort activities by date
    dashboard_data["recent_activities"].sort(key=lambda x: x["date"], reverse=True)
    dashboard_data["recent_activities"] = dashboard_data["recent_activities"][:10]  # Latest 10

    # Sort upcoming events by date
    dashboard_data["upcoming_events"].sort(key=lambda x: x["date"])

    return dashboard_data