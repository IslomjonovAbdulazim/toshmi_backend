from pydantic import BaseModel
from typing import Optional, List

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
    grades: List[dict]  # [{"student_id": "123", "grade": 85.5, "comment": "Good work"}]

# Bulk Attendance
class StudentAttendanceRow(BaseModel):
    student_id: str
    student_name: str
    current_status: Optional[str] = None  # 'present', 'absent', 'late'
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
    attendance: List[dict]  # [{"student_id": "123", "status": "present", "comment": ""}]