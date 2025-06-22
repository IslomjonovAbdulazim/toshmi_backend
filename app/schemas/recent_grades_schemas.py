from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class RecentGradeItem(BaseModel):
    id: str
    type: str  # 'homework' or 'exam'
    title: str
    subject_name: str
    grade: float
    comment: Optional[str] = None
    graded_at: datetime

class RecentGradesResponse(BaseModel):
    student_id: str
    student_name: str
    grades: List[RecentGradeItem]