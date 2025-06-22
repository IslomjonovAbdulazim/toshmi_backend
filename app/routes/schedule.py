from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import require_admin
from app.schemas import *
from app.crud import *

router = APIRouter()


@router.post("/schedule", response_model=ScheduleResponse)
def create_schedule_endpoint(schedule: ScheduleCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return create_schedule(db, schedule)


@router.get("/schedule", response_model=List[ScheduleResponse])
def get_schedule_endpoint(group_id: str, day_of_week: str = None, db: Session = Depends(get_db)):
    if day_of_week:
        return get_schedule_by_day(db, group_id, day_of_week)
    return get_schedule_by_group(db, group_id)


@router.delete("/schedule/{schedule_id}")
def delete_schedule_endpoint(schedule_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    db.delete(schedule)
    db.commit()
    return {"message": "Schedule deleted successfully"}


@router.patch("/schedule/{schedule_id}", response_model=ScheduleResponse)
def update_schedule_endpoint(schedule_id: str, schedule_update: ScheduleCreate, db: Session = Depends(get_db),
                             admin=Depends(require_admin)):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    schedule.group_id = schedule_update.group_id
    schedule.group_subject_id = schedule_update.group_subject_id
    schedule.day_of_week = schedule_update.day_of_week
    schedule.start_time = schedule_update.start_time
    schedule.end_time = schedule_update.end_time
    schedule.room = schedule_update.room

    db.commit()
    db.refresh(schedule)
    return schedule