from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class HomeworkBase(BaseModel):
    group_subject_id: str
    title: str
    description: str
    due_date: datetime


class HomeworkCreate(HomeworkBase):
    pass


class HomeworkResponse(HomeworkBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class HomeworkGradeBase(BaseModel):
    homework_id: str
    student_id: str
    grade: float
    comment: Optional[str] = None


class HomeworkGradeCreate(HomeworkGradeBase):
    pass


class HomeworkGradeResponse(HomeworkGradeBase):
    id: str
    graded_at: datetime

    class Config:
        from_attributes = True


class ExamBase(BaseModel):
    group_subject_id: str
    title: str
    exam_date: datetime


class ExamCreate(ExamBase):
    pass


class ExamResponse(ExamBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ExamGradeBase(BaseModel):
    exam_id: str
    student_id: str
    grade: float
    comment: Optional[str] = None


class ExamGradeCreate(ExamGradeBase):
    pass


class ExamGradeResponse(ExamGradeBase):
    id: str
    graded_at: datetime

    class Config:
        from_attributes = True