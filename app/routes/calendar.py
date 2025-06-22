from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import require_admin, require_teacher
from app.schemas import AcademicEvent
from app.crud import filter_grades
import uuid

router = APIRouter()

# Academic Calendar (simplified - could use separate model)
academic_events = []  # In production, use database

@router.post("/events")
def create_event(event: AcademicEvent, db: Session = Depends(get_db), admin = Depends(require_admin)):
    event_dict = event.dict()
    event_dict["id"] = str(uuid.uuid4())
    academic_events.append(event_dict)
    return event_dict

@router.get("/events")
def get_events(group_id: str = None):
    if group_id:
        return [e for e in academic_events if not e.get("group_ids") or group_id in e.get("group_ids", [])]
    return academic_events

@router.delete("/events/{event_id}")
def delete_event(event_id: str, admin = Depends(require_admin)):
    global academic_events
    academic_events = [e for e in academic_events if e["id"] != event_id]
    return {"deleted": True}