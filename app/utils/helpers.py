# app/utils/helpers.py
"""
Helper functions and constants for the Education Center Management System
Crafted with passion for clean, reusable, and efficient code!
"""

import json
import re
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Union
from enum import Enum


# Constants
class UserRole(str, Enum):
    """User roles in the system"""
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"


class AttendanceStatus(str, Enum):
    """Attendance status options"""
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"


class NotificationType(str, Enum):
    """Notification types"""
    PAYMENT = "payment"
    GRADE = "grade"
    HOMEWORK = "homework"
    EXAM = "exam"
    NEWS = "news"
    GENERAL = "general"


class FileType(str, Enum):
    """File types"""
    IMAGE = "image"
    DOCUMENT = "document"


class DayOfWeek(str, Enum):
    """Days of the week"""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


# File size constants (in bytes)
MAX_PROFILE_IMAGE_SIZE = 3 * 1024 * 1024  # 3MB
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB

# Supported file extensions
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.rtf'}


def sanitize_phone_number(phone: Union[str, int]) -> int:
    """
    Sanitize and validate phone number

    Args:
        phone: Phone number as string or int

    Returns:
        Cleaned phone number as integer

    Raises:
        ValueError: If phone number is invalid
    """
    # Convert to string and remove all non-digits
    phone_str = str(phone).strip()
    phone_digits = ''.join(filter(str.isdigit, phone_str))

    # Validate length (should be between 9-15 digits)
    if len(phone_digits) < 9 or len(phone_digits) > 15:
        raise ValueError("Phone number must be between 9-15 digits")

    return int(phone_digits)


def clean_string(text: str) -> str:
    """
    Clean and normalize string

    Args:
        text: Input text

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove extra whitespace and normalize
    return ' '.join(text.strip().split())


def format_phone_number(phone: int) -> str:
    """
    Format phone number for display

    Args:
        phone: Phone number as integer

    Returns:
        Formatted phone number string
    """
    phone_str = str(phone)

    # Add country code if not present (assuming Uzbekistan +998)
    if len(phone_str) == 9:
        phone_str = "998" + phone_str

    # Format as +998 XX XXX XX XX
    if len(phone_str) == 12:
        return f"+{phone_str[:3]} {phone_str[3:5]} {phone_str[5:8]} {phone_str[8:10]} {phone_str[10:12]}"

    return f"+{phone_str}"


def parse_external_links(links_str: Optional[str]) -> List[str]:
    """
    Parse external links from JSON string

    Args:
        links_str: JSON string containing links array

    Returns:
        List of links
    """
    if not links_str:
        return []

    try:
        links = json.loads(links_str)
        return links if isinstance(links, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def serialize_external_links(links: List[str]) -> str:
    """
    Serialize external links to JSON string

    Args:
        links: List of links

    Returns:
        JSON string
    """
    if not links:
        return "[]"

    # Validate URLs
    valid_links = []
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    for link in links:
        if isinstance(link, str) and url_pattern.match(link):
            valid_links.append(link)

    return json.dumps(valid_links)


def get_month_name_uzbek(month: int) -> str:
    """
    Get Uzbek month name

    Args:
        month: Month number (1-12)

    Returns:
        Uzbek month name
    """
    months = {
        1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel",
        5: "May", 6: "Iyun", 7: "Iyul", 8: "Avgust",
        9: "Sentabr", 10: "Oktabr", 11: "Noyabr", 12: "Dekabr"
    }
    return months.get(month, "Noma'lum")


def get_day_name_uzbek(day: str) -> str:
    """
    Get Uzbek day name

    Args:
        day: English day name

    Returns:
        Uzbek day name
    """
    days = {
        "monday": "Dushanba",
        "tuesday": "Seshanba",
        "wednesday": "Chorshanba",
        "thursday": "Payshanba",
        "friday": "Juma",
        "saturday": "Shanba",
        "sunday": "Yakshanba"
    }
    return days.get(day.lower(), day)


def format_date_uzbek(date_obj: Union[date, datetime]) -> str:
    """
    Format date in Uzbek style

    Args:
        date_obj: Date or datetime object

    Returns:
        Formatted date string
    """
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()

    day = date_obj.day
    month = get_month_name_uzbek(date_obj.month)
    year = date_obj.year

    return f"{day} {month} {year}"


def format_time_12hour(time_str: str) -> str:
    """
    Convert 24-hour time to 12-hour format

    Args:
        time_str: Time in HH:MM format

    Returns:
        Time in 12-hour format
    """
    try:
        time_obj = datetime.strptime(time_str, "%H:%M").time()
        return time_obj.strftime("%I:%M %p")
    except ValueError:
        return time_str


def get_grade_letter(percentage: float) -> str:
    """
    Convert percentage to letter grade

    Args:
        percentage: Grade percentage

    Returns:
        Letter grade
    """
    if percentage >= 90:
        return "A"
    elif percentage >= 80:
        return "B"
    elif percentage >= 70:
        return "C"
    elif percentage >= 60:
        return "D"
    else:
        return "F"


def calculate_grade_percentage(grade: float, max_grade: float) -> float:
    """
    Calculate grade percentage

    Args:
        grade: Received grade
        max_grade: Maximum possible grade

    Returns:
        Percentage
    """
    if max_grade == 0:
        return 0.0
    return round((grade / max_grade) * 100, 2)


def get_attendance_percentage(present_days: int, total_days: int) -> float:
    """
    Calculate attendance percentage

    Args:
        present_days: Number of days present
        total_days: Total number of days

    Returns:
        Attendance percentage
    """
    if total_days == 0:
        return 0.0
    return round((present_days / total_days) * 100, 2)


def validate_file_extension(filename: str, file_type: str) -> bool:
    """
    Validate file extension based on type

    Args:
        filename: File name
        file_type: Type of file (image or document)

    Returns:
        True if extension is valid
    """
    extension = '.' + filename.split('.')[-1].lower()

    if file_type == FileType.IMAGE:
        return extension in ALLOWED_IMAGE_EXTENSIONS
    elif file_type == FileType.DOCUMENT:
        return extension in ALLOWED_DOCUMENT_EXTENSIONS

    return False


def get_file_type_from_extension(filename: str) -> Optional[str]:
    """
    Determine file type from extension

    Args:
        filename: File name

    Returns:
        File type or None if unknown
    """
    extension = '.' + filename.split('.')[-1].lower()

    if extension in ALLOWED_IMAGE_EXTENSIONS:
        return FileType.IMAGE
    elif extension in ALLOWED_DOCUMENT_EXTENSIONS:
        return FileType.DOCUMENT

    return None


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format

    Args:
        size_bytes: File size in bytes

    Returns:
        Formatted file size
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)

    return f"{s} {size_names[i]}"


def generate_month_list(start_year: int, end_year: int) -> List[Dict[str, Any]]:
    """
    Generate list of months for payment tracking

    Args:
        start_year: Starting year
        end_year: Ending year

    Returns:
        List of month dictionaries
    """
    months = []

    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            month_str = f"{year}-{month:02d}"
            months.append({
                "value": month_str,
                "label": f"{get_month_name_uzbek(month)} {year}",
                "year": year,
                "month": month
            })

    return months


def get_current_academic_year() -> Dict[str, int]:
    """
    Get current academic year (September to June)

    Returns:
        Dictionary with start and end years
    """
    current_date = datetime.now()

    if current_date.month >= 9:  # September or later
        start_year = current_date.year
        end_year = current_date.year + 1
    else:  # Before September
        start_year = current_date.year - 1
        end_year = current_date.year

    return {
        "start_year": start_year,
        "end_year": end_year,
        "label": f"{start_year}/{end_year}"
    }


def validate_graduation_year(year: int) -> bool:
    """
    Validate graduation year

    Args:
        year: Graduation year

    Returns:
        True if valid
    """
    current_year = datetime.now().year
    return current_year <= year <= current_year + 10


def parse_time_string(time_str: str) -> bool:
    """
    Validate time string format (HH:MM)

    Args:
        time_str: Time string

    Returns:
        True if valid format
    """
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


def get_week_days() -> List[Dict[str, str]]:
    """
    Get list of week days

    Returns:
        List of day dictionaries with English and Uzbek names
    """
    return [
        {"value": "monday", "label": "Dushanba", "english": "Monday"},
        {"value": "tuesday", "label": "Seshanba", "english": "Tuesday"},
        {"value": "wednesday", "label": "Chorshanba", "english": "Wednesday"},
        {"value": "thursday", "label": "Payshanba", "english": "Thursday"},
        {"value": "friday", "label": "Juma", "english": "Friday"},
        {"value": "saturday", "label": "Shanba", "english": "Saturday"},
        {"value": "sunday", "label": "Yakshanba", "english": "Sunday"},
    ]


def create_success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
    """
    Create standardized success response

    Args:
        data: Response data
        message: Success message

    Returns:
        Standardized response
    """
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }


def create_error_response(message: str, code: str = "ERROR") -> Dict[str, Any]:
    """
    Create standardized error response

    Args:
        message: Error message
        code: Error code

    Returns:
        Standardized error response
    """
    return {
        "success": False,
        "message": message,
        "code": code,
        "timestamp": datetime.utcnow().isoformat()
    }


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to specified length

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - 3] + "..."


def generate_notification_message(notification_type: str, **kwargs) -> str:
    """
    Generate notification message based on type

    Args:
        notification_type: Type of notification
        **kwargs: Additional data for message

    Returns:
        Generated message
    """
    templates = {
        NotificationType.PAYMENT: "Yangi to'lov qayd etildi: {amount} so'm",
        NotificationType.GRADE: "{subject} fani bo'yicha yangi baho: {grade}",
        NotificationType.HOMEWORK: "{subject} fani bo'yicha yangi uy vazifasi berildi",
        NotificationType.EXAM: "{subject} fani bo'yicha imtihon e'lon qilindi",
        NotificationType.NEWS: "Yangi e'lon: {title}",
        NotificationType.GENERAL: "{message}"
    }

    template = templates.get(notification_type, "{message}")

    try:
        return template.format(**kwargs)
    except KeyError:
        return kwargs.get("message", "Yangi bildirishnoma")


def get_uzbek_role_name(role: str) -> str:
    """
    Get Uzbek role name

    Args:
        role: English role name

    Returns:
        Uzbek role name
    """
    roles = {
        UserRole.ADMIN: "Administrator",
        UserRole.TEACHER: "O'qituvchi",
        UserRole.STUDENT: "O'quvchi",
        UserRole.PARENT: "Ota-ona"
    }
    return roles.get(role, role)