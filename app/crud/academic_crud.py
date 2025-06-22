from sqlalchemy.orm import Session
from app.models import Group, Subject, GroupSubject, Schedule
from app.schemas import GroupCreate, SubjectCreate, GroupSubjectCreate, ScheduleCreate
import uuid

def create_group(db: Session, group: GroupCreate):
    db_group = Group(
        id=str(uuid.uuid4()),
        name=group.name,
        student_ids=group.student_ids
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

def get_group(db: Session, group_id: str):
    return db.query(Group).filter(Group.id == group_id).first()

def get_all_groups(db: Session):
    return db.query(Group).all()

def create_subject(db: Session, subject: SubjectCreate):
    db_subject = Subject(
        id=str(uuid.uuid4()),
        name=subject.name
    )
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject

def get_subject(db: Session, subject_id: str):
    return db.query(Subject).filter(Subject.id == subject_id).first()

def get_all_subjects(db: Session):
    return db.query(Subject).all()

def create_group_subject(db: Session, group_subject: GroupSubjectCreate):
    db_group_subject = GroupSubject(
        id=str(uuid.uuid4()),
        group_id=group_subject.group_id,
        subject_id=group_subject.subject_id,
        teacher_id=group_subject.teacher_id
    )
    db.add(db_group_subject)
    db.commit()
    db.refresh(db_group_subject)
    return db_group_subject

def get_group_subject(db: Session, group_subject_id: str):
    return db.query(GroupSubject).filter(GroupSubject.id == group_subject_id).first()

def get_all_group_subjects(db: Session):
    return db.query(GroupSubject).all()

def create_schedule(db: Session, schedule: ScheduleCreate):
    db_schedule = Schedule(
        id=str(uuid.uuid4()),
        group_id=schedule.group_id,
        group_subject_id=schedule.group_subject_id,
        day_of_week=schedule.day_of_week,
        start_time=schedule.start_time,
        end_time=schedule.end_time,
        room=schedule.room
    )
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

def get_schedule_by_group(db: Session, group_id: str):
    return db.query(Schedule).filter(Schedule.group_id == group_id).all()

def get_schedule_by_day(db: Session, group_id: str, day_of_week: str):
    return db.query(Schedule).filter(
        Schedule.group_id == group_id,
        Schedule.day_of_week == day_of_week
    ).all()