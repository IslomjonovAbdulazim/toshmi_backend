# app/schemas/misc.py
"""
Miscellaneous Pydantic schemas for payments, news, notifications, and files
Crafted with passion for comprehensive system functionality!
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Union
from datetime import datetime, date
from ..utils.helpers import NotificationType, FileType


# Payment Schemas

class PaymentCreate(BaseModel):
    """Schema for creating payments"""
    student_id: str = Field(..., description="Student ID")
    amount: float = Field(..., gt=0, description="Payment amount")
    month: str = Field(..., description="Payment month (YYYY-MM format)")
    notes: Optional[str] = Field(None, max_length=500, description="Payment notes")

    @validator('amount')
    def validate_amount(cls, v):
        """Validate payment amount"""
        if v <= 0:
            raise ValueError('Payment amount must be greater than 0')
        if v > 10000000:  # 10 million limit
            raise ValueError('Payment amount is too large')
        return round(v, 2)

    @validator('month')
    def validate_month_format(cls, v):
        """Validate month format"""
        import re
        if not re.match(r'^\d{4}-\d{2}$', v):
            raise ValueError('Month must be in YYYY-MM format')

        # Parse and validate the date
        try:
            year, month = map(int, v.split('-'))
            if month < 1 or month > 12:
                raise ValueError('Invalid month')
            if year < 2020 or year > 2030:
                raise ValueError('Year must be between 2020 and 2030')
        except ValueError:
            raise ValueError('Invalid month format')

        return v

    class Config:
        schema_extra = {
            "example": {
                "student_id": "student-uuid",
                "amount": 150000.0,
                "month": "2024-01",
                "notes": "Monthly tuition payment"
            }
        }


class PaymentUpdate(BaseModel):
    """Schema for updating payments"""
    amount: Optional[float] = Field(None, gt=0, description="Payment amount")
    notes: Optional[str] = Field(None, max_length=500, description="Payment notes")


class PaymentResponse(BaseModel):
    """Payment response schema"""
    id: str = Field(..., description="Payment ID")
    student_id: str = Field(..., description="Student ID")
    amount: float = Field(..., description="Payment amount")
    month: str = Field(..., description="Payment month")
    year: int = Field(..., description="Payment year")
    payment_date: datetime = Field(..., description="Payment date")
    notes: Optional[str] = Field(None, description="Payment notes")
    recorded_by: str = Field(..., description="Admin who recorded payment")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class MonthlyPaymentStatusUpdate(BaseModel):
    """Schema for updating monthly payment status"""
    student_id: str = Field(..., description="Student ID")
    month: str = Field(..., description="Month (YYYY-MM format)")
    is_fully_paid: bool = Field(..., description="Payment completion status")
    total_amount_due: Optional[float] = Field(None, gt=0, description="Expected total amount")

    @validator('month')
    def validate_month_format(cls, v):
        """Validate month format"""
        import re
        if not re.match(r'^\d{4}-\d{2}$', v):
            raise ValueError('Month must be in YYYY-MM format')
        return v


class MonthlyPaymentStatusResponse(BaseModel):
    """Monthly payment status response"""
    id: str = Field(..., description="Status ID")
    student_id: str = Field(..., description="Student ID")
    month: str = Field(..., description="Month")
    year: int = Field(..., description="Year")
    is_fully_paid: bool = Field(..., description="Payment completion status")
    total_amount_due: Optional[float] = Field(None, description="Expected total amount")
    total_amount_paid: float = Field(..., description="Total amount paid")
    updated_by: str = Field(..., description="Admin who updated status")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class StudentPaymentSummary(BaseModel):
    """Student payment summary"""
    student_id: str = Field(..., description="Student ID")
    student_name: str = Field(..., description="Student name")
    total_paid: float = Field(..., description="Total amount paid")
    total_due: float = Field(..., description="Total amount due")
    months_paid: int = Field(..., description="Number of months fully paid")
    months_pending: int = Field(..., description="Number of months with pending payments")
    last_payment_date: Optional[datetime] = Field(None, description="Last payment date")


# News Schemas

class NewsCreate(BaseModel):
    """Schema for creating news"""
    title: str = Field(..., min_length=5, max_length=200, description="News title")
    body: str = Field(..., min_length=10, max_length=5000, description="News content")
    external_links: Optional[List[str]] = Field(default=[], description="External links")
    is_published: bool = Field(default=True, description="Publication status")

    @validator('title', 'body')
    def validate_content(cls, v):
        """Validate and clean content"""
        return v.strip()

    @validator('external_links')
    def validate_links(cls, v):
        """Validate external links"""
        if not v:
            return []

        import re
        url_pattern = re.compile(
            r'^https?://'
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
                "title": "Winter Break Announcement",
                "body": "Dear students and parents, we are pleased to announce that winter break will begin on December 25th...",
                "external_links": ["https://school.edu/calendar"],
                "is_published": True
            }
        }


class NewsUpdate(BaseModel):
    """Schema for updating news"""
    title: Optional[str] = Field(None, min_length=5, max_length=200, description="News title")
    body: Optional[str] = Field(None, min_length=10, max_length=5000, description="News content")
    external_links: Optional[List[str]] = Field(None, description="External links")
    is_published: Optional[bool] = Field(None, description="Publication status")


class NewsResponse(BaseModel):
    """News response schema"""
    id: str = Field(..., description="News ID")
    title: str = Field(..., description="News title")
    body: str = Field(..., description="News content")
    external_links: List[str] = Field(default=[], description="External links")
    published_by: str = Field(..., description="Publisher ID")
    published_at: datetime = Field(..., description="Publication timestamp")
    is_published: bool = Field(..., description="Publication status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class NewsWithAuthor(NewsResponse):
    """News response with author information"""
    author_name: str = Field(..., description="Author's full name")


class NewsSummary(BaseModel):
    """News summary for lists"""
    id: str = Field(..., description="News ID")
    title: str = Field(..., description="News title")
    summary: str = Field(..., description="News summary (first 150 characters)")
    published_at: datetime = Field(..., description="Publication timestamp")
    author_name: str = Field(..., description="Author's name")
    is_published: bool = Field(..., description="Publication status")


# Notification Schemas

class NotificationCreate(BaseModel):
    """Schema for creating notifications"""
    user_id: str = Field(..., description="User ID to notify")
    title: str = Field(..., min_length=3, max_length=200, description="Notification title")
    message: str = Field(..., min_length=5, max_length=1000, description="Notification message")
    type: NotificationType = Field(..., description="Notification type")

    @validator('title', 'message')
    def validate_content(cls, v):
        """Validate and clean content"""
        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "user_id": "user-uuid",
                "title": "New Grade Posted",
                "message": "Your Mathematics homework has been graded. Grade: 85/100",
                "type": "grade"
            }
        }


class NotificationUpdate(BaseModel):
    """Schema for updating notifications"""
    is_read: bool = Field(..., description="Read status")


class NotificationResponse(BaseModel):
    """Notification response schema"""
    id: str = Field(..., description="Notification ID")
    user_id: str = Field(..., description="User ID")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    type: NotificationType = Field(..., description="Notification type")
    is_read: bool = Field(..., description="Read status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class BulkNotificationCreate(BaseModel):
    """Schema for creating bulk notifications"""
    user_ids: List[str] = Field(..., min_items=1, description="List of user IDs")
    title: str = Field(..., min_length=3, max_length=200, description="Notification title")
    message: str = Field(..., min_length=5, max_length=1000, description="Notification message")
    type: NotificationType = Field(..., description="Notification type")


class NotificationStats(BaseModel):
    """Notification statistics"""
    total_notifications: int = Field(..., description="Total notifications")
    unread_notifications: int = Field(..., description="Unread notifications")
    read_notifications: int = Field(..., description="Read notifications")


# File Schemas

class FileUploadResponse(BaseModel):
    """File upload response schema"""
    id: str = Field(..., description="File ID")
    filename: str = Field(..., description="File name")
    original_filename: str = Field(..., description="Original file name")
    file_path: str = Field(..., description="File path")
    file_size: int = Field(..., description="File size in bytes")
    file_type: FileType = Field(..., description="File type")
    mime_type: str = Field(..., description="MIME type")
    upload_url: str = Field(..., description="File access URL")
    created_at: datetime = Field(..., description="Upload timestamp")

    class Config:
        from_attributes = True


class FileResponse(BaseModel):
    """File response schema"""
    id: str = Field(..., description="File ID")
    filename: str = Field(..., description="File name")
    original_filename: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size in bytes")
    file_type: FileType = Field(..., description="File type")
    mime_type: str = Field(..., description="MIME type")
    uploaded_by: str = Field(..., description="Uploader ID")
    created_at: datetime = Field(..., description="Upload timestamp")

    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """File list response"""
    files: List[FileResponse] = Field(..., description="List of files")
    total: int = Field(..., description="Total file count")


# Report Schemas

class PaymentReport(BaseModel):
    """Payment report schema"""
    month: str = Field(..., description="Report month")
    total_students: int = Field(..., description="Total students")
    paid_students: int = Field(..., description="Students who paid")
    pending_students: int = Field(..., description="Students with pending payments")
    total_collected: float = Field(..., description="Total amount collected")
    total_pending: float = Field(..., description="Total pending amount")
    payment_percentage: float = Field(..., description="Payment completion percentage")


class RevenueReport(BaseModel):
    """Revenue report schema"""
    period: str = Field(..., description="Report period")
    total_revenue: float = Field(..., description="Total revenue")
    monthly_breakdown: List[dict] = Field(..., description="Monthly revenue breakdown")
    payment_methods: List[dict] = Field(..., description="Payment method breakdown")


class SystemOverview(BaseModel):
    """System overview for admin dashboard"""
    total_users: int = Field(..., description="Total users")
    total_students: int = Field(..., description="Total students")
    total_teachers: int = Field(..., description="Total teachers")
    total_parents: int = Field(..., description="Total parents")
    total_groups: int = Field(..., description="Total groups")
    total_subjects: int = Field(..., description="Total subjects")
    total_revenue_this_month: float = Field(..., description="Revenue this month")
    total_payments_this_month: int = Field(..., description="Payments this month")
    active_homework: int = Field(..., description="Active homework assignments")
    upcoming_exams: int = Field(..., description="Upcoming exams")
    recent_news_count: int = Field(..., description="Recent news articles")
    unread_notifications: int = Field(..., description="System-wide unread notifications")


# List Response Schemas

class PaymentListResponse(BaseModel):
    """Payment list response"""
    payments: List[PaymentResponse] = Field(..., description="List of payments")
    total: int = Field(..., description="Total payment count")
    total_amount: float = Field(..., description="Total payment amount")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total pages")


class NewsListResponse(BaseModel):
    """News list response"""
    news: List[NewsSummary] = Field(..., description="List of news articles")
    total: int = Field(..., description="Total news count")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total pages")


class NotificationListResponse(BaseModel):
    """Notification list response"""
    notifications: List[NotificationResponse] = Field(..., description="List of notifications")
    total: int = Field(..., description="Total notification count")
    unread_count: int = Field(..., description="Unread notification count")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total pages")


# Search and Filter Schemas

class PaymentSearchRequest(BaseModel):
    """Payment search request"""
    student_id: Optional[str] = Field(None, description="Filter by student")
    month: Optional[str] = Field(None, description="Filter by month (YYYY-MM)")
    year: Optional[int] = Field(None, description="Filter by year")
    min_amount: Optional[float] = Field(None, description="Minimum amount")
    max_amount: Optional[float] = Field(None, description="Maximum amount")
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")


class NewsSearchRequest(BaseModel):
    """News search request"""
    query: Optional[str] = Field(None, description="Search in title and content")
    is_published: Optional[bool] = Field(None, description="Filter by publication status")
    date_from: Optional[date] = Field(None, description="Filter from date")
    date_to: Optional[date] = Field(None, description="Filter to date")
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")


class NotificationSearchRequest(BaseModel):
    """Notification search request"""
    type: Optional[NotificationType] = Field(None, description="Filter by type")
    is_read: Optional[bool] = Field(None, description="Filter by read status")
    date_from: Optional[date] = Field(None, description="Filter from date")
    date_to: Optional[date] = Field(None, description="Filter to date")
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")


# Success Response Schemas

class PaymentCreatedResponse(BaseModel):
    """Payment creation success response"""
    message: str = Field(default="Payment recorded successfully", description="Success message")
    payment: PaymentResponse = Field(..., description="Created payment")
    monthly_status: MonthlyPaymentStatusResponse = Field(..., description="Updated monthly status")


class NewsCreatedResponse(BaseModel):
    """News creation success response"""
    message: str = Field(default="News article created successfully", description="Success message")
    news: NewsResponse = Field(..., description="Created news article")


class NotificationCreatedResponse(BaseModel):
    """Notification creation success response"""
    message: str = Field(default="Notification sent successfully", description="Success message")
    notification_count: int = Field(..., description="Number of notifications sent")


class BulkNotificationResponse(BaseModel):
    """Bulk notification response"""
    message: str = Field(default="Bulk notifications sent successfully", description="Success message")
    total_sent: int = Field(..., description="Total notifications sent")
    successful: int = Field(..., description="Successfully sent")
    failed: int = Field(..., description="Failed to send")
    errors: List[str] = Field(default=[], description="List of errors")