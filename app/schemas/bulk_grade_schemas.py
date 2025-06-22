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