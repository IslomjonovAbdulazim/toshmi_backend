from pydantic import BaseModel
from typing import List, Optional


class GroupBase(BaseModel):
    name: str
    student_ids: List[str]


class GroupCreate(GroupBase):
    pass


class GroupResponse(GroupBase):
    id: str

    class Config:
        from_attributes = True


class SubjectBase(BaseModel):
    name: str


class SubjectCreate(SubjectBase):
    pass


class SubjectResponse(SubjectBase):
    id: str

    class Config:
        from_attributes = True


class GroupSubjectBase(BaseModel):
    group_id: str
    subject_id: str
    teacher_id: str


class GroupSubjectCreate(GroupSubjectBase):
    pass


class GroupSubjectResponse(GroupSubjectBase):
    id: str

    class Config:
        from_attributes = True


class ScheduleBase(BaseModel):
    group_id: str
    group_subject_id: str
    day_of_week: str
    start_time: str
    end_time: str
    room: Optional[str] = None


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleResponse(ScheduleBase):
    id: str

    class Config:
        from_attributes = True