from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AttendanceBase(BaseModel):
    student_id: str
    group_subject_id: str
    date: datetime
    status: str
    comment: Optional[str] = None


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceResponse(AttendanceBase):
    id: str

    class Config:
        from_attributes = True


class PaymentBase(BaseModel):
    student_id: str
    month: int
    year: int
    amount_paid: float
    is_fully_paid: bool = False
    comment: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentResponse(PaymentBase):
    id: str
    paid_at: datetime

    class Config:
        from_attributes = True


class NewsBase(BaseModel):
    title: str
    body: str
    media_urls: Optional[List[str]] = None
    links: Optional[List[str]] = None


class NewsCreate(NewsBase):
    pass


class NewsResponse(NewsBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True