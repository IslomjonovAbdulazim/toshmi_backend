# app/models/__init__.py
from .user_models import User, Student, Parent, Teacher
from .academic_models import Group, Subject, GroupSubject, Schedule
from .grade_models import Homework, HomeworkGrade, Exam, ExamGrade
from .misc_models import Attendance, Payment, News

__all__ = [
    "User", "Student", "Parent", "Teacher",
    "Group", "Subject", "GroupSubject", "Schedule",
    "Homework", "HomeworkGrade", "Exam", "ExamGrade",
    "Attendance", "Payment", "News"
]