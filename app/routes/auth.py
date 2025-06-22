from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.schemas import LoginRequest, Token, PasswordChange
from app.crud import authenticate_user, get_user, get_user_by_phone
from app.auth import create_access_token, get_current_user

router = APIRouter()


@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, login_data.phone, login_data.role, login_data.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")

    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout():
    return {"message": "Successfully logged out"}


@router.get("/me")
def get_current_user_info(current_user=Depends(get_current_user)):
    return current_user


@router.post("/change-password")
def change_password(password_data: PasswordChange, current_user=Depends(get_current_user)):
    return {"message": "Password changed successfully"}


@router.post("/reset-password")
def reset_password(phone: int, role: str, db: Session = Depends(get_db)):
    user = get_user_by_phone(db, phone, role)
    if not user:
        raise HTTPException(404, "User not found")
    return {"message": "Password reset link sent"}