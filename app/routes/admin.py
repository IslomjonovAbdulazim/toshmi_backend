from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import require_admin
from app.schemas import *
from app.crud import *

router = APIRouter()

# User Management
@router.post("/users", response_model=UserResponse)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    return create_user(db, user)

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user_endpoint(user_id: str, db: Session = Depends(get_db), admin = Depends(require_admin)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/users", response_model=List[UserResponse])
def get_users_by_role_endpoint(role: str = None, db: Session = Depends(get_db), admin = Depends(require_admin)):
    if role:
        return get_users_by_role(db, role)
    return get_users_by_role(db, "student")  # Default

# Group Management
@router.post("/groups", response_model=GroupResponse)
def create_group_endpoint(group: GroupCreate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    return create_group(db, group)

@router.get("/groups", response_model=List[GroupResponse])
def get_groups_endpoint(db: Session = Depends(get_db), admin = Depends(require_admin)):
    return get_all_groups(db)

@router.get("/groups/{group_id}", response_model=GroupResponse)
def get_group_endpoint(group_id: str, db: Session = Depends(get_db), admin = Depends(require_admin)):
    group = get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

# Subject Management
@router.post("/subjects", response_model=SubjectResponse)
def create_subject_endpoint(subject: SubjectCreate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    return create_subject(db, subject)

@router.get("/subjects", response_model=List[SubjectResponse])
def get_subjects_endpoint(db: Session = Depends(get_db), admin = Depends(require_admin)):
    return get_all_subjects(db)

# Payment Management
@router.post("/payments", response_model=PaymentResponse)
def create_payment_endpoint(payment: PaymentCreate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    return create_payment(db, payment)

@router.patch("/payments/{payment_id}")
def update_payment_endpoint(payment_id: str, is_fully_paid: bool, comment: str = None, db: Session = Depends(get_db), admin = Depends(require_admin)):
    return update_payment(db, payment_id, is_fully_paid, comment)

# News Management
@router.post("/news", response_model=NewsResponse)
def create_news_endpoint(news: NewsCreate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    return create_news(db, news)

@router.get("/news", response_model=List[NewsResponse])
def get_news_endpoint(db: Session = Depends(get_db)):
    return get_all_news(db)