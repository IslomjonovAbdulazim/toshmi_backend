from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.schemas import UserUpdate, FileUpload
from app.crud import update_user_profile

router = APIRouter()


@router.patch("/profile")
def update_my_profile(user_update: UserUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return update_user_profile(db, current_user.id, user_update)


@router.post("/upload-avatar")
def upload_avatar(file: UploadFile = File(...), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    # In production, upload to cloud storage (AWS S3, etc.)
    file_url = f"/uploads/avatars/{current_user.id}_{file.filename}"

    user_update = UserUpdate(avatar_url=file_url)
    return update_user_profile(db, current_user.id, user_update)


@router.post("/upload-file")
def upload_file(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    # In production, upload to cloud storage
    file_url = f"/uploads/files/{current_user.id}_{file.filename}"

    return FileUpload(
        file_url=file_url,
        file_type=file.content_type.split('/')[0],
        file_name=file.filename
    )