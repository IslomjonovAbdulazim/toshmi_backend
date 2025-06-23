# app/routes/student.py
"""
Student routes with passionate educational engagement!
Handles student access to homework, exams, grades, attendance, and academic progress.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date
from sqlalchemy import func  # Add this import at top
from ..database import get_db
from ..services.academic_service import get_academic_service
from ..utils.dependencies import require_student, get_current_student_profile
from ..schemas.academic import (
    HomeworkResponse, ExamResponse, GradeResponse, AttendanceResponse,
    StudentDashboard, AcademicSummary
)

router = APIRouter()


# Student Profile and Information

@router.get("/profile", response_model=dict, summary="Get Student Profile")
async def get_student_profile(
        student=Depends(get_current_student_profile),
        db: Session = Depends(get_db)
):
    """
    Get current student's profile and academic information

    Returns student details including group, parent, and graduation year
    """
    profile_data = {
        "student_id": student.id,
        "user_id": student.user_id,
        "full_name": student.user.full_name,
        "phone": student.user.phone,
        "avatar_url": student.user.avatar_url,
        "group_id": student.group_id,
        "group_name": student.group.name if student.group else None,
        "parent_id": student.parent_id,
        "graduation_year": student.graduation_year,
        "created_at": student.created_at
    }

    # Add parent information if exists
    if student.parent and student.parent.user:
        profile_data["parent"] = {
            "parent_id": student.parent.id,
            "full_name": student.parent.user.full_name,
            "phone": student.parent.user.phone
        }

    return profile_data


@router.get("/dashboard", response_model=dict, summary="Get Student Dashboard")
async def get_student_dashboard(
        student=Depends(get_current_student_profile),
        db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard data for student

    Returns recent grades, pending homework, upcoming exams, and academic summary
    """
    academic_service = get_academic_service(db)
    return academic_service.get_student_academic_summary(student.id)


@router.get("/group", response_model=dict, summary="Get Group Information")
async def get_group_info(
        student=Depends(get_current_student_profile),
        db: Session = Depends(get_db)
):
    """
    Get information about student's current group

    Returns group details, subjects, and classmates count
    """
    if not student.group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student is not assigned to any group"
        )

    # Get group subjects and teachers
    from ..models import GroupSubject
    group_subjects = db.query(GroupSubject).filter(
        GroupSubject.group_id == student.group_id
    ).all()

    # Get classmates count
    from ..models import Student, User
    classmates_count = db.query(Student).join(User).filter(
        Student.group_id == student.group_id,
        Student.id != student.id,
        User.is_active == True
    ).count()

    subjects_info = []
    for gs in group_subjects:
        subjects_info.append({
            "subject_id": gs.subject_id,
            "subject_name": gs.subject.name,
            "teacher_id": gs.teacher_id,
            "teacher_name": gs.teacher.user.full_name
        })

    return {
        "group_id": student.group.id,
        "group_name": student.group.name,
        "group_description": student.group.description,
        "subjects": subjects_info,
        "classmates_count": classmates_count,
        "total_students": classmates_count + 1  # Including current student
    }


# Homework Management

@router.get("/homework", response_model=List[dict], summary="Get Student's Homework")
async def get_student_homework(
        include_completed: bool = Query(default=True, description="Include completed homework"),
        subject_id: Optional[str] = Query(None, description="Filter by subject"),
        student=Depends(get_current_student_profile),
        db: Session = Depends(get_db)
):
    """
    Get all homework assignments for student

    Returns homework with completion status and grades
    """
    academic_service = get_academic_service(db)
    homework_list = academic_service.get_student_homework(student.id, include_completed)

    # Filter by subject if specified
    if subject_id:
        homework_list = [hw for hw in homework_list if hw.get('subject_id') == subject_id]

    return homework_list


@router.get("/homework/{homework_id}", response_model=dict, summary="Get Homework Details")
async def get_homework_details(
        homework_id: str,
        student=Depends(get_current_student_profile),
        db: Session = Depends(get_db)
):
    """
    Get detailed information about specific homework

    Returns homework details with files, links, and grade if available
    """
    from ..models import Homework, Grade

    # Get homework and verify student has access (same group)
    homework = db.query(Homework).filter(
        Homework.id == homework_id,
        Homework.group_id == student.group_id
    ).first()

    if not homework:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Homework not found or access denied"
        )

    # Get grade if exists
    grade = db.query(Grade).filter(
        Grade.student_id == student.id,
        Grade.homework_id == homework_id
    ).first()

    # Get files associated with homework
    homework_files = []
    for file in homework.files:
        homework_files.append({
            "file_id": file.id,
            "filename": file.original_filename,
            "file_size": file.file_size,
            "download_url": f"/files/{file.id}"
        })

    homework_data = {
        "id": homework.id,
        "title": homework.title,
        "description": homework.description,
        "external_links": homework.external_links,
        "due_date": homework.due_date,
        "subject_name": homework.subject.name,
        "teacher_name": homework.teacher.user.full_name,
        "created_at": homework.created_at,
        "is_overdue": homework.due_date < db.query(func.now()).scalar(),
        "files": homework_files,
        "grade": None
    }

    if grade:
        from ..utils.helpers import calculate_grade_percentage
        homework_data["grade"] = {
            "grade": grade.grade,
            "max_grade": grade.max_grade,
            "percentage": calculate_grade_percentage(grade.grade, grade.max_grade),
            "comment": grade.comment,
            "graded_at": grade.graded_at
        }

    return homework_data


@router.get("/homework/pending", response_model=List[dict], summary="Get Pending Homework")
async def get_pending_homework(
        student=Depends(get_current_student_profile),
        db: Session = Depends(get_db)
):
    """
    Get only homework that hasn't been graded yet

    Returns ungraded homework assignments with due dates
    """
    academic_service = get_academic_service(db)
    return academic_service.get_student_homework(student.id, include_completed=False)


# Exam Management

@router.get("/exams", response_model=List[dict], summary="Get Student's Exams")
async def get_student_exams(
        include_past: bool = Query(default=True, description="Include past exams"),
        subject_id: Optional[str] = Query(None, description="Filter by subject"),
        student=Depends(get_current_student_profile),
        db: Session = Depends(get_db)
):
    """
    Get all exams for student

    Returns exams with grades and schedule information
    """
    from ..models import Exam, Grade
    from datetime import datetime

    # Get exams for student's group
    exams_query = db.query(Exam).filter(Exam.group_id == student.group_id)

    if not include_past:
        exams_query = exams_query.filter(Exam.exam_date >= datetime.utcnow())

    if subject_id:
        exams_query = exams_query.filter(Exam.subject_id == subject_id)

    exams = exams_query.order_by(Exam.exam_date.desc()).all()

    result = []
    for exam in exams:
        # Get grade if exists
        grade = db.query(Grade).filter(
            Grade.student_id == student.id,
            Grade.exam_id == exam.id
        ).first()

        exam_data = {
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "external_links": exam.external_links,
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


@router.get("/exams/{exam_id}", response_model=dict, summary="Get Exam Details")
async def get_exam_details(
        exam_id: str,
        student=Depends(get_current_student_profile),
        db: Session = Depends(get_db)
):
    """
    Get detailed information about specific exam

    Returns exam details with files, links, and grade if available
    """
    from ..models import Exam, Grade

    # Get exam and verify student has access
    exam = db.query(Exam).filter(
        Exam.id == exam_id,
        Exam.group_id == student.group_id
    ).first()

    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found or access denied"
        )

    # Get grade if exists
    grade = db.query(Grade).filter(
        Grade.student_id == student.id,
        Grade.exam_id == exam_id
    ).first()

    # Get files associated with exam
    exam_files = []
    for file in exam.files:
        exam_files.append({
            "file_id": file.id,
            "filename": file.original_filename,
            "file_size": file.file_size,
            "download_url": f"/files/{file.id}"
        })

    exam_data = {
        "id": exam.id,
        "title": exam.title,
        "description": exam.description,
        "external_links": exam.external_links,
        "exam_date": exam.exam_date,
        "subject_name": exam.subject.name,
        "teacher_name": exam.teacher.user.full_name,
        "created_at": exam.created_at,
        "files": exam_files,
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

    return exam_data


@router.get("/exams/upcoming", response_model=List[dict], summary="Get Upcoming Exams")
async def get_upcoming_exams(
        days: int = Query(default=30, ge=1, le=365, description="Days ahead to look"),
        student=Depends(get_current_student_profile),
        db: Session = Depends(get_db)
):
    """
    Get exams scheduled in the next specified days

    Returns upcoming exams to help students prepare
    """
    from ..models import Exam
    from datetime import datetime, timedelta

    future_date = datetime.utcnow() + timedelta(days=days)

    upcoming_exams = db.query(Exam).filter(
        Exam.group_id == student.group_id,
        Exam.exam_date >= datetime.utcnow(),
        Exam.exam_date <= future_date
    ).order_by(Exam.exam_date).all()

    result = []
    for exam in upcoming_exams:
        result.append({
            "id": exam.id,
            "title": exam.title,
            "subject_name": exam.subject.name,
            "teacher_name": exam.teacher.user.full_name,
            "exam_date": exam.exam_date,
            "days_until": (exam.exam_date.date() - datetime.utcnow().date()).days
        })

    return result


# Grades and Academic Performance

@router.get("/grades", response_model=List[dict], summary="Get All Grades")
async def get_student_grades(
        subject_id: Optional[str] = Query(None, description="Filter by subject"),
        grade_type: Optional[str] = Query(None, description="Filter by type (homework/exam)"),
        student=Depends(get_current_student_profile),
        db: Session = Depends(get_db)
):
    """
    Get all grades for student

    Returns comprehensive grade history with filtering options
    """
    from ..models import Grade

    grades_query = db.query(Grade).filter(Grade.student_id == student.id)

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


@router.get("/grades/summary", response_model=dict, summary="Get Grade Summary")
async def get_grade_summary(
        student=Depends(get_current_student_profile),
        db: Session = Depends(get_db)
):
    """
    Get grade summary and statistics

    Returns average grades by subject and overall performance metrics
    """
    from ..models import Grade
    from sqlalchemy import func

    # Get grade statistics by subject
    subject_stats = db.query(
        Grade.subject_id,
        func.count(Grade.id).label('total_grades'),
        func.avg(Grade.grade).label('avg_grade'),
        func.max(Grade.grade).label('max_grade_received'),
        func.min(Grade.grade).label('min_grade_received')
    ).filter(Grade.student_id == student.id).group_by(Grade.subject_id).all()

    # Get overall statistics
    overall_stats = db.query(
        func.count(Grade.id).label('total_grades'),
        func.avg(Grade.grade).label('overall_average')
    ).filter(Grade.student_id == student.id).first()

    # Format subject statistics
    subjects_summary = []
    for stat in subject_stats:
        from ..models import Subject
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
        "overall": {
            "total_grades": overall_stats.total_grades or 0,
            "overall_average": round(float(overall_stats.overall_average), 2) if overall_stats.overall_average else 0
        },
        "by_subject": subjects_summary,
        "generated_at": db.query(func.now()).scalar()
    }


# Attendance Management

@router.get("/attendance", response_model=List[dict], summary="Get Attendance Records")
async def get_student_attendance(
        subject_id: Optional[str] = Query(None, description="Filter by subject"),
        date_from: Optional[date] = Query(None, description="Filter from date"),
        date_to: Optional[date] = Query(None, description="Filter to date"),
        student=Depends(get_current_student_profile),
        db: Session = Depends(get_db)
):
    """
    Get attendance records for student

    Returns attendance history with filtering options
    """
    from ..models import Attendance

    attendance_query = db.query(Attendance).filter(Attendance.student_id == student.id)

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


@router.get("/attendance/summary", response_model=dict, summary="Get Attendance Summary")
async def get_attendance_summary(
        student=Depends(get_current_student_profile),
        db: Session = Depends(get_db)
):
    """
    Get attendance summary and statistics

    Returns attendance rates by subject and overall attendance metrics
    """
    from ..models import Attendance
    from sqlalchemy import func, case
    from ..utils.helpers import AttendanceStatus, get_attendance_percentage

    # Get attendance statistics by subject
    subject_stats = db.query(
        Attendance.subject_id,
        func.count(Attendance.id).label('total_records'),
        func.sum(case((Attendance.status == AttendanceStatus.PRESENT, 1), else_=0)).label('present_count'),
        func.sum(case((Attendance.status == AttendanceStatus.ABSENT, 1), else_=0)).label('absent_count'),
        func.sum(case((Attendance.status == AttendanceStatus.LATE, 1), else_=0)).label('late_count')
    ).filter(Attendance.student_id == student.id).group_by(Attendance.subject_id).all()

    # Get overall statistics
    overall_stats = db.query(
        func.count(Attendance.id).label('total_records'),
        func.sum(case((Attendance.status == AttendanceStatus.PRESENT, 1), else_=0)).label('present_count'),
        func.sum(case((Attendance.status == AttendanceStatus.ABSENT, 1), else_=0)).label('absent_count'),
        func.sum(case((Attendance.status == AttendanceStatus.LATE, 1), else_=0)).label('late_count')
    ).filter(Attendance.student_id == student.id).first()

    # Format subject statistics
    subjects_summary = []
    for stat in subject_stats:
        from ..models import Subject
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


# Schedule and Calendar

@router.get("/schedule", response_model=List[dict], summary="Get Class Schedule")
async def get_class_schedule(
        day: Optional[str] = Query(None, description="Filter by day of week"),
        student=Depends(get_current_student_profile),
        db: Session = Depends(get_db)
):
    """
    Get weekly class schedule for student

    Returns schedule with subjects, teachers, and time slots
    """
    from ..models import Schedule

    schedule_query = db.query(Schedule).filter(Schedule.group_id == student.group_id)

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
            "teacher_name": schedule.teacher.user.full_name,
            "duration_minutes": _calculate_duration(schedule.start_time, schedule.end_time)
        })

    return result


def _calculate_duration(start_time: str, end_time: str) -> int:
    """Calculate duration in minutes between two time strings"""
    from datetime import datetime
    start = datetime.strptime(start_time, "%H:%M")
    end = datetime.strptime(end_time, "%H:%M")
    duration = end - start
    return int(duration.total_seconds() / 60)


# Payments and Financial Information

@router.get("/payments", response_model=List[dict], summary="Get Payment History")
async def get_payment_history(
        year: Optional[int] = Query(None, description="Filter by year"),
        student=Depends(get_current_student_profile),
        db: Session = Depends(get_db)
):
    """
    Get payment history for student

    Returns payment records and monthly payment status
    """
    from ..models import Payment, MonthlyPaymentStatus

    payments_query = db.query(Payment).filter(Payment.student_id == student.id)

    if year:
        payments_query = payments_query.filter(Payment.year == year)

    payments = payments_query.order_by(Payment.payment_date.desc()).all()

    # Get monthly payment statuses
    monthly_status_query = db.query(MonthlyPaymentStatus).filter(
        MonthlyPaymentStatus.student_id == student.id
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
        "payment_history": payment_history,
        "monthly_summary": monthly_summary,
        "total_payments": len(payments),
        "total_amount_paid": sum(p.amount for p in payments)
    }


# News and Announcements

@router.get("/news", response_model=List[dict], summary="Get School News")
async def get_school_news(
        limit: int = Query(default=10, ge=1, le=50, description="Number of news articles"),
        db: Session = Depends(get_db),
        student=Depends(get_current_student_profile)
):
    """
    Get published school news and announcements

    Returns recent news articles visible to students
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

@router.get("/notifications", response_model=List[dict], summary="Get Student Notifications")
async def get_notifications(
        unread_only: bool = Query(default=False, description="Get only unread notifications"),
        limit: int = Query(default=20, ge=1, le=100, description="Number of notifications"),
        student=Depends(get_current_student_profile),
        db: Session = Depends(get_db)
):
    """
    Get notifications for student

    Returns notifications about grades, payments, news, etc.
    """
    from ..models import Notification

    notifications_query = db.query(Notification).filter(
        Notification.user_id == student.user_id
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
        student=Depends(get_current_student_profile),
        db: Session = Depends(get_db)
):
    """
    Mark a specific notification as read

    Students can only mark their own notifications as read
    """
    from ..models import Notification

    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == student.user_id
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