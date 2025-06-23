# app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import LoginRequest, Token, PasswordReset, UserResponse
from app.crud import authenticate_user, reset_user_password
from app.auth import create_access_token, get_current_user

router = APIRouter()


@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, login_data.phone, login_data.role, login_data.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")

    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user=Depends(get_current_user)):
    """Get current authenticated user information"""
    return current_user


@router.post("/logout")
def logout():
    return {"message": "Successfully logged out"}


@router.post("/reset-password")
def reset_password(password_data: PasswordReset, db: Session = Depends(get_db)):
    user = reset_user_password(db, password_data.phone, password_data.role, password_data.new_password)
    if not user:
        raise HTTPException(404, "User not found")
    return {"message": f"Password reset successfully for {user.full_name}"}