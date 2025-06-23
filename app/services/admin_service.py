# app/services/admin_service.py
"""
Admin operations service with passionate system management!
Handles groups, subjects, schedules, payments, news, and comprehensive reporting.
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, extract
from fastapi import HTTPException, status
from datetime import datetime, date

from ..models import (
    Group, Subject, GroupSubject, Schedule, Student, Teacher, Parent, User,
    Payment, MonthlyPaymentStatus, News, Notification, Grade, Attendance
)
from ..utils.helpers import (
    DayOfWeek, clean_string, serialize_external_links, parse_external_links,
    NotificationType, generate_notification_message, get_current_academic_year
)
from ..schemas.management import (
    GroupCreate, SubjectCreate, ScheduleCreate, GroupSubjectAssign
)
from ..schemas.misc import (
    PaymentCreate, MonthlyPaymentStatusUpdate, NewsCreate
)


class AdminService:
    """
    Comprehensive admin service handling all administrative operations
    with passionate attention to institutional excellence!
    """

    def __init__(self, db: Session):
        self.db = db

    # Group Management

    def create_group(self, group_data: GroupCreate, admin_id: str) -> Dict[str, Any]:
        """
        Create a new group

        Args:
            group_data: Group creation data
            admin_id: Admin creating the group

        Returns:
            Created group information

        Raises:
            HTTPException: If creation fails
        """
        try:
            # Check if group name already exists
            existing_group = self.db.query(Group).filter(
                Group.name == group_data.name.strip(),
                Group.is_active == True
            ).first()

            if existing_group:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Group with this name already exists"
                )

            # Create group
            group = Group(
                name=clean_string(group_data.name),
                description=clean_string(group_data.description) if group_data.description else None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_active=True
            )

            self.db.add(group)
            self.db.commit()
            self.db.refresh(group)

            return {
                "id": group.id,
                "name": group.name,
                "description": group.description,
                "created_at": group.created_at,
                "is_active": group.is_active,
                "message": "Group created successfully",
                "created_by": admin_id
            }

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Group creation error: {str(e)}"
            )

    def get_all_groups(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        Get all groups with statistics

        Args:
            include_inactive: Include inactive groups

        Returns:
            List of groups with statistics
        """
        try:
            query = self.db.query(Group)

            if not include_inactive:
                query = query.filter(Group.is_active == True)

            groups = query.order_by(Group.name).all()

            result = []
            for group in groups:
                # Get statistics
                student_count = self.db.query(Student).filter(Student.group_id == group.id).count()
                subject_count = self.db.query(GroupSubject).filter(GroupSubject.group_id == group.id).count()

                group_data = {
                    "id": group.id,
                    "name": group.name,
                    "description": group.description,
                    "created_at": group.created_at,
                    "updated_at": group.updated_at,
                    "is_active": group.is_active,
                    "statistics": {
                        "student_count": student_count,
                        "subject_count": subject_count
                    }
                }

                result.append(group_data)

            return result

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving groups: {str(e)}"
            )

    # Subject Management

    def create_subject(self, subject_data: SubjectCreate, admin_id: str) -> Dict[str, Any]:
        """
        Create a new subject

        Args:
            subject_data: Subject creation data
            admin_id: Admin creating the subject

        Returns:
            Created subject information

        Raises:
            HTTPException: If creation fails
        """
        try:
            # Check if subject name already exists
            existing_subject = self.db.query(Subject).filter(
                Subject.name == subject_data.name.strip(),
                Subject.is_active == True
            ).first()

            if existing_subject:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Subject with this name already exists"
                )

            # Create subject
            subject = Subject(
                name=clean_string(subject_data.name),
                description=clean_string(subject_data.description) if subject_data.description else None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_active=True
            )

            self.db.add(subject)
            self.db.commit()
            self.db.refresh(subject)

            return {
                "id": subject.id,
                "name": subject.name,
                "description": subject.description,
                "created_at": subject.created_at,
                "is_active": subject.is_active,
                "message": "Subject created successfully",
                "created_by": admin_id
            }

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Subject creation error: {str(e)}"
            )

    def get_all_subjects(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        Get all subjects with statistics

        Args:
            include_inactive: Include inactive subjects

        Returns:
            List of subjects with statistics
        """
        try:
            query = self.db.query(Subject)

            if not include_inactive:
                query = query.filter(Subject.is_active == True)

            subjects = query.order_by(Subject.name).all()

            result = []
            for subject in subjects:
                # Get statistics
                group_count = self.db.query(GroupSubject).filter(GroupSubject.subject_id == subject.id).count()
                teacher_count = self.db.query(GroupSubject.teacher_id).filter(
                    GroupSubject.subject_id == subject.id
                ).distinct().count()

                subject_data = {
                    "id": subject.id,
                    "name": subject.name,
                    "description": subject.description,
                    "created_at": subject.created_at,
                    "updated_at": subject.updated_at,
                    "is_active": subject.is_active,
                    "statistics": {
                        "group_count": group_count,
                        "teacher_count": teacher_count
                    }
                }

                result.append(subject_data)

            return result

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving subjects: {str(e)}"
            )

    # Group-Subject Assignment

    def assign_teacher_to_group_subject(self, assignment_data: GroupSubjectAssign, admin_id: str) -> Dict[str, Any]:
        """
        Assign teacher to group-subject combination

        Args:
            assignment_data: Assignment data
            admin_id: Admin performing assignment

        Returns:
            Assignment result

        Raises:
            HTTPException: If assignment fails
        """
        try:
            # Validate group exists and is active
            group = self.db.query(Group).filter(
                Group.id == assignment_data.group_id,
                Group.is_active == True
            ).first()

            if not group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Group not found or inactive"
                )

            # Validate subject exists and is active
            subject = self.db.query(Subject).filter(
                Subject.id == assignment_data.subject_id,
                Subject.is_active == True
            ).first()

            if not subject:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Subject not found or inactive"
                )

            # Validate teacher exists and is active
            teacher = self.db.query(Teacher).join(User).filter(
                Teacher.id == assignment_data.teacher_id,
                User.is_active == True
            ).first()

            if not teacher:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Teacher not found or inactive"
                )

            # Check if assignment already exists
            existing_assignment = self.db.query(GroupSubject).filter(
                GroupSubject.group_id == assignment_data.group_id,
                GroupSubject.subject_id == assignment_data.subject_id
            ).first()

            if existing_assignment:
                # Update existing assignment
                existing_assignment.teacher_id = assignment_data.teacher_id
                existing_assignment.updated_at = datetime.utcnow()
                message = "Teacher assignment updated successfully"
            else:
                # Create new assignment
                assignment = GroupSubject(
                    group_id=assignment_data.group_id,
                    subject_id=assignment_data.subject_id,
                    teacher_id=assignment_data.teacher_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )

                self.db.add(assignment)
                message = "Teacher assigned successfully"

            self.db.commit()

            return {
                "message": message,
                "group_id": assignment_data.group_id,
                "group_name": group.name,
                "subject_id": assignment_data.subject_id,
                "subject_name": subject.name,
                "teacher_id": assignment_data.teacher_id,
                "teacher_name": teacher.user.full_name,
                "assigned_by": admin_id,
                "timestamp": datetime.utcnow()
            }

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Assignment error: {str(e)}"
            )

    # Schedule Management

    def create_schedule(self, schedule_data: ScheduleCreate, admin_id: str) -> Dict[str, Any]:
        """
        Create a new schedule entry

        Args:
            schedule_data: Schedule creation data
            admin_id: Admin creating the schedule

        Returns:
            Created schedule information

        Raises:
            HTTPException: If creation fails
        """
        try:
            # Validate group-subject assignment exists
            group_subject = self.db.query(GroupSubject).filter(
                GroupSubject.group_id == schedule_data.group_id,
                GroupSubject.subject_id == schedule_data.subject_id,
                GroupSubject.teacher_id == schedule_data.teacher_id
            ).first()

            if not group_subject:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Teacher is not assigned to this group-subject combination"
                )

            # Check for schedule conflicts
            conflict = self.db.query(Schedule).filter(
                Schedule.group_id == schedule_data.group_id,
                Schedule.day_of_week == schedule_data.day_of_week,
                or_(
                    and_(
                        Schedule.start_time <= schedule_data.start_time,
                        Schedule.end_time > schedule_data.start_time
                    ),
                    and_(
                        Schedule.start_time < schedule_data.end_time,
                        Schedule.end_time >= schedule_data.end_time
                    ),
                    and_(
                        Schedule.start_time >= schedule_data.start_time,
                        Schedule.end_time <= schedule_data.end_time
                    )
                )
            ).first()

            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Schedule conflict detected for this group and time slot"
                )

            # Create schedule
            schedule = Schedule(
                group_id=schedule_data.group_id,
                subject_id=schedule_data.subject_id,
                teacher_id=schedule_data.teacher_id,
                day_of_week=schedule_data.day_of_week,
                start_time=schedule_data.start_time,
                end_time=schedule_data.end_time,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(schedule)
            self.db.commit()
            self.db.refresh(schedule)

            return {
                "id": schedule.id,
                "group_id": schedule.group_id,
                "group_name": schedule.group.name,
                "subject_id": schedule.subject_id,
                "subject_name": schedule.subject.name,
                "teacher_id": schedule.teacher_id,
                "teacher_name": schedule.teacher.user.full_name,
                "day_of_week": schedule.day_of_week,
                "start_time": schedule.start_time,
                "end_time": schedule.end_time,
                "created_at": schedule.created_at,
                "message": "Schedule created successfully",
                "created_by": admin_id
            }

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Schedule creation error: {str(e)}"
            )

    # Payment Management

    def record_payment(self, payment_data: PaymentCreate, admin_id: str) -> Dict[str, Any]:
        """
        Record a new payment for student

        Args:
            payment_data: Payment data
            admin_id: Admin recording the payment

        Returns:
            Payment information and updated monthly status

        Raises:
            HTTPException: If recording fails
        """
        try:
            # Validate student exists
            student = self.db.query(Student).join(User).filter(
                Student.id == payment_data.student_id,
                User.is_active == True
            ).first()

            if not student:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Student not found or inactive"
                )

            # Parse month and year
            year, month = map(int, payment_data.month.split('-'))

            # Create payment record
            payment = Payment(
                student_id=payment_data.student_id,
                amount=payment_data.amount,
                month=payment_data.month,
                year=year,
                payment_date=datetime.utcnow(),
                notes=payment_data.notes,
                recorded_by=admin_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(payment)
            self.db.flush()  # Get payment ID

            # Update or create monthly payment status
            monthly_status = self.db.query(MonthlyPaymentStatus).filter(
                MonthlyPaymentStatus.student_id == payment_data.student_id,
                MonthlyPaymentStatus.month == payment_data.month,
                MonthlyPaymentStatus.year == year
            ).first()

            if not monthly_status:
                monthly_status = MonthlyPaymentStatus(
                    student_id=payment_data.student_id,
                    month=payment_data.month,
                    year=year,
                    is_fully_paid=False,
                    total_amount_paid=0.0,
                    updated_by=admin_id,
                    updated_at=datetime.utcnow()
                )
                self.db.add(monthly_status)
                self.db.flush()

            # Update total amount paid
            monthly_status.total_amount_paid += payment_data.amount
            monthly_status.updated_by = admin_id
            monthly_status.updated_at = datetime.utcnow()

            self.db.commit()

            # Create payment notification
            self._create_payment_notification(payment_data.student_id, payment_data.amount)

            return {
                "payment": {
                    "id": payment.id,
                    "student_id": payment.student_id,
                    "amount": payment.amount,
                    "month": payment.month,
                    "payment_date": payment.payment_date,
                    "notes": payment.notes,
                    "recorded_by": admin_id
                },
                "monthly_status": {
                    "month": monthly_status.month,
                    "is_fully_paid": monthly_status.is_fully_paid,
                    "total_amount_paid": monthly_status.total_amount_paid,
                    "total_amount_due": monthly_status.total_amount_due
                },
                "message": "Payment recorded successfully"
            }

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment recording error: {str(e)}"
            )

    def update_monthly_payment_status(self, status_data: MonthlyPaymentStatusUpdate, admin_id: str) -> Dict[str, Any]:
        """
        Update monthly payment status for student

        Args:
            status_data: Payment status data
            admin_id: Admin updating the status

        Returns:
            Updated status information

        Raises:
            HTTPException: If update fails
        """
        try:
            year, month = map(int, status_data.month.split('-'))

            # Get or create monthly status
            monthly_status = self.db.query(MonthlyPaymentStatus).filter(
                MonthlyPaymentStatus.student_id == status_data.student_id,
                MonthlyPaymentStatus.month == status_data.month,
                MonthlyPaymentStatus.year == year
            ).first()

            if not monthly_status:
                monthly_status = MonthlyPaymentStatus(
                    student_id=status_data.student_id,
                    month=status_data.month,
                    year=year,
                    total_amount_paid=0.0,
                    updated_by=admin_id,
                    updated_at=datetime.utcnow()
                )
                self.db.add(monthly_status)

            # Update status
            monthly_status.is_fully_paid = status_data.is_fully_paid
            if status_data.total_amount_due is not None:
                monthly_status.total_amount_due = status_data.total_amount_due
            monthly_status.updated_by = admin_id
            monthly_status.updated_at = datetime.utcnow()

            self.db.commit()

            return {
                "message": "Monthly payment status updated successfully",
                "student_id": status_data.student_id,
                "month": status_data.month,
                "is_fully_paid": monthly_status.is_fully_paid,
                "total_amount_due": monthly_status.total_amount_due,
                "total_amount_paid": monthly_status.total_amount_paid,
                "updated_by": admin_id,
                "timestamp": datetime.utcnow()
            }

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Status update error: {str(e)}"
            )

    # News Management

    def create_news(self, news_data: NewsCreate, admin_id: str) -> Dict[str, Any]:
        """
        Create a new news article

        Args:
            news_data: News creation data
            admin_id: Admin creating the news

        Returns:
            Created news information

        Raises:
            HTTPException: If creation fails
        """
        try:
            # Create news article
            news = News(
                title=clean_string(news_data.title),
                body=clean_string(news_data.body),
                external_links=serialize_external_links(news_data.external_links or []),
                published_by=admin_id,
                published_at=datetime.utcnow() if news_data.is_published else None,
                is_published=news_data.is_published,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(news)
            self.db.commit()
            self.db.refresh(news)

            # Create notifications if published
            if news_data.is_published:
                self._create_news_notifications(news.id, news.title)

            return {
                "id": news.id,
                "title": news.title,
                "body": news.body,
                "external_links": parse_external_links(news.external_links),
                "published_by": admin_id,
                "published_at": news.published_at,
                "is_published": news.is_published,
                "created_at": news.created_at,
                "message": "News article created successfully"
            }

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"News creation error: {str(e)}"
            )

    # Reporting and Analytics

    def get_system_overview(self) -> Dict[str, Any]:
        """
        Get comprehensive system overview for admin dashboard

        Returns:
            System statistics and metrics
        """
        try:
            current_date = datetime.now()
            current_month = current_date.month
            current_year = current_date.year

            # User statistics
            total_users = self.db.query(User).count()
            active_users = self.db.query(User).filter(User.is_active == True).count()
            total_students = self.db.query(User).filter(User.role == 'student').count()
            total_teachers = self.db.query(User).filter(User.role == 'teacher').count()
            total_parents = self.db.query(User).filter(User.role == 'parent').count()

            # Academic statistics
            total_groups = self.db.query(Group).filter(Group.is_active == True).count()
            total_subjects = self.db.query(Subject).filter(Subject.is_active == True).count()

            # Payment statistics for current month
            monthly_payments = self.db.query(Payment).filter(
                extract('month', Payment.payment_date) == current_month,
                extract('year', Payment.payment_date) == current_year
            ).all()

            total_revenue_this_month = sum(payment.amount for payment in monthly_payments)
            total_payments_this_month = len(monthly_payments)

            # Academic activity statistics
            active_homework = self.db.query(func.count(Homework.id)).filter(
                Homework.due_date > current_date
            ).scalar()

            upcoming_exams = self.db.query(func.count(Exam.id)).filter(
                Exam.exam_date > current_date,
                Exam.exam_date <= current_date.replace(day=current_date.day + 7)
            ).scalar()

            # Recent news count
            recent_news_count = self.db.query(func.count(News.id)).filter(
                News.published_at >= current_date.replace(day=current_date.day - 30),
                News.is_published == True
            ).scalar()

            # Unread notifications
            unread_notifications = self.db.query(func.count(Notification.id)).filter(
                Notification.is_read == False
            ).scalar()

            return {
                "user_statistics": {
                    "total_users": total_users,
                    "active_users": active_users,
                    "total_students": total_students,
                    "total_teachers": total_teachers,
                    "total_parents": total_parents
                },
                "academic_statistics": {
                    "total_groups": total_groups,
                    "total_subjects": total_subjects,
                    "active_homework": active_homework,
                    "upcoming_exams": upcoming_exams
                },
                "payment_statistics": {
                    "total_revenue_this_month": total_revenue_this_month,
                    "total_payments_this_month": total_payments_this_month
                },
                "activity_statistics": {
                    "recent_news_count": recent_news_count,
                    "unread_notifications": unread_notifications
                },
                "generated_at": datetime.utcnow()
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating system overview: {str(e)}"
            )

    def get_payment_report(self, month: int, year: int) -> Dict[str, Any]:
        """
        Generate payment report for specific month

        Args:
            month: Report month
            year: Report year

        Returns:
            Payment report with statistics
        """
        try:
            # Get all payments for the month
            payments = self.db.query(Payment).filter(
                Payment.month == f"{year}-{month:02d}"
            ).all()

            # Get all students
            total_students = self.db.query(Student).join(User).filter(User.is_active == True).count()

            # Calculate statistics
            total_collected = sum(payment.amount for payment in payments)
            unique_paying_students = len(set(payment.student_id for payment in payments))

            # Get monthly statuses
            monthly_statuses = self.db.query(MonthlyPaymentStatus).filter(
                MonthlyPaymentStatus.month == f"{year}-{month:02d}"
            ).all()

            fully_paid_students = len([status for status in monthly_statuses if status.is_fully_paid])
            pending_students = total_students - fully_paid_students

            payment_percentage = (fully_paid_students / total_students * 100) if total_students > 0 else 0

            return {
                "month": f"{year}-{month:02d}",
                "total_students": total_students,
                "paying_students": unique_paying_students,
                "fully_paid_students": fully_paid_students,
                "pending_students": pending_students,
                "total_collected": total_collected,
                "payment_percentage": round(payment_percentage, 2),
                "payment_details": [
                    {
                        "student_name": payment.student.user.full_name,
                        "amount": payment.amount,
                        "payment_date": payment.payment_date,
                        "notes": payment.notes
                    }
                    for payment in payments
                ],
                "generated_at": datetime.utcnow()
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating payment report: {str(e)}"
            )

    # Helper methods for notifications

    def _create_payment_notification(self, student_id: str, amount: float):
        """Create payment notification for student and parents"""
        try:
            student = self.db.query(Student).filter(Student.id == student_id).first()
            if not student:
                return

            message = generate_notification_message(
                NotificationType.PAYMENT,
                amount=amount
            )

            # Notification for student
            student_notification = Notification(
                user_id=student.user_id,
                title="Yangi to'lov",
                message=message,
                type=NotificationType.PAYMENT,
                created_at=datetime.utcnow()
            )
            self.db.add(student_notification)

            # Notification for parent if exists
            if student.parent:
                parent_notification = Notification(
                    user_id=student.parent.user_id,
                    title="Farzandingiz uchun yangi to'lov",
                    message=f"{student.user.full_name}: {message}",
                    type=NotificationType.PAYMENT,
                    created_at=datetime.utcnow()
                )
                self.db.add(parent_notification)

            self.db.commit()

        except Exception:
            # Don't fail main operation if notification fails
            self.db.rollback()

    def _create_news_notifications(self, news_id: str, title: str):
        """Create news notifications for all users"""
        try:
            # Get all active users
            users = self.db.query(User).filter(User.is_active == True).all()

            message = generate_notification_message(
                NotificationType.NEWS,
                title=title
            )

            for user in users:
                notification = Notification(
                    user_id=user.id,
                    title="Yangi e'lon",
                    message=message,
                    type=NotificationType.NEWS,
                    created_at=datetime.utcnow()
                )
                self.db.add(notification)

            self.db.commit()

        except Exception:
            # Don't fail main operation if notification fails
            self.db.rollback()


# Service factory function
def get_admin_service(db: Session) -> AdminService:
    """Create admin service instance"""
    return AdminService(db)