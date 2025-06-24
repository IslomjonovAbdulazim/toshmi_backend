from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.models import User
from app.core.security import verify_password, create_access_token, get_current_user, hash_password, \
    verify_admin_password

router = APIRouter()


class LoginRequest(BaseModel):
    phone: str
    password: str
    role: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.phone == request.phone,
        User.role == request.role
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.role == "admin":
        if not verify_admin_password(request.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
    else:
        if not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account disabled")

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer", "role": user.role}


@router.put("/change-password")
def change_password(request: ChangePasswordRequest, current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if current_user.role == "admin":
        if not verify_admin_password(request.old_password):
            raise HTTPException(status_code=400, detail="Invalid old password")
    else:
        if not verify_password(request.old_password, current_user.password_hash):
            raise HTTPException(status_code=400, detail="Invalid old password")
        current_user.password_hash = hash_password(request.new_password)

    db.commit()
    return {"message": "Password changed"}


@router.get("/profile")
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "phone": current_user.phone,
        "role": current_user.role,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "profile_image_id": current_user.profile_image_id
    }


class UpdateProfileRequest(BaseModel):
    first_name: str
    last_name: str


@router.put("/profile")
def update_profile(request: UpdateProfileRequest, current_user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    current_user.first_name = request.first_name
    current_user.last_name = request.last_name
    db.commit()
    return {"message": "Profile updated"}