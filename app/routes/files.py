from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
import shutil
from pathlib import Path
from app.database import get_db
from app.auth import get_current_user
from app.schemas import *
from app.models import User
from app.utils.audit import log_action

router = APIRouter()

# File storage settings
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
    'document': ['.pdf', '.doc', '.docx', '.txt', '.csv', '.xlsx'],
    'video': ['.mp4', '.avi', '.mov', '.webm']
}


class FileManager:
    @staticmethod
    def get_file_type(filename: str) -> str:
        ext = Path(filename).suffix.lower()
        for file_type, extensions in ALLOWED_EXTENSIONS.items():
            if ext in extensions:
                return file_type
        return 'unknown'

    @staticmethod
    def validate_file(file: UploadFile) -> str:
        if file.size > MAX_FILE_SIZE:
            raise HTTPException(413, "File too large")

        file_type = FileManager.get_file_type(file.filename)
        if file_type == 'unknown':
            raise HTTPException(400, "File type not allowed")

        return file_type

    @staticmethod
    def save_file(file: UploadFile, user_id: str, file_type: str) -> str:
        file_id = str(uuid.uuid4())
        ext = Path(file.filename).suffix
        filename = f"{file_id}{ext}"

        # Create user directory
        user_dir = UPLOAD_DIR / user_id / file_type
        user_dir.mkdir(parents=True, exist_ok=True)

        file_path = user_dir / filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return str(file_path)


# File upload endpoints
@router.post("/upload")
async def upload_file(
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    """Upload a file"""
    file_type = FileManager.validate_file(file)
    file_path = FileManager.save_file(file, current_user.id, file_type)

    await log_action(current_user.id, "UPLOAD", "File", file.filename)

    return {
        "file_id": str(uuid.uuid4()),
        "filename": file.filename,
        "file_type": file_type,
        "file_path": file_path,
        "size": file.size
    }


@router.post("/upload-avatar")
async def upload_avatar(
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    """Upload user avatar"""
    if FileManager.get_file_type(file.filename) != 'image':
        raise HTTPException(400, "Avatar must be an image")

    file_path = FileManager.save_file(file, current_user.id, 'image')

    # Update user avatar URL
    user = db.query(User).filter(User.id == current_user.id).first()
    user.avatar_url = f"/files/serve/{file_path}"
    db.commit()

    await log_action(current_user.id, "UPDATE", "Avatar", file.filename)

    return {"avatar_url": user.avatar_url}


@router.get("/serve/{file_path:path}")
async def serve_file(file_path: str, current_user=Depends(get_current_user)):
    """Serve uploaded files"""
    full_path = Path(file_path)

    if not full_path.exists():
        raise HTTPException(404, "File not found")

    # Check if user can access this file
    if not str(full_path).startswith(f"uploads/{current_user.id}") and current_user.role != "admin":
        raise HTTPException(403, "Access denied")

    return FileResponse(full_path)


@router.get("/my-files")
async def list_my_files(current_user=Depends(get_current_user)):
    """List user's uploaded files"""
    user_dir = UPLOAD_DIR / current_user.id

    if not user_dir.exists():
        return {"files": []}

    files = []
    for file_path in user_dir.rglob("*"):
        if file_path.is_file():
            files.append({
                "filename": file_path.name,
                "type": FileManager.get_file_type(file_path.name),
                "size": file_path.stat().st_size,
                "created": file_path.stat().st_ctime,
                "path": str(file_path)
            })

    return {"files": files}


@router.delete("/delete/{file_path:path}")
async def delete_file(
        file_path: str,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    """Delete uploaded file"""
    full_path = Path(file_path)

    # Security check
    if not str(full_path).startswith(f"uploads/{current_user.id}") and current_user.role != "admin":
        raise HTTPException(403, "Access denied")

    if full_path.exists():
        full_path.unlink()
        await log_action(current_user.id, "DELETE", "File", str(full_path))
        return {"deleted": True}

    raise HTTPException(404, "File not found")


@router.post("/bulk-upload")
async def bulk_upload_files(
        files: List[UploadFile] = File(...),
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    """Upload multiple files"""
    if len(files) > 10:
        raise HTTPException(400, "Maximum 10 files per upload")

    uploaded_files = []
    errors = []

    for file in files:
        try:
            file_type = FileManager.validate_file(file)
            file_path = FileManager.save_file(file, current_user.id, file_type)

            uploaded_files.append({
                "filename": file.filename,
                "file_type": file_type,
                "file_path": file_path
            })
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")

    await log_action(current_user.id, "BULK_UPLOAD", "Files", f"Uploaded {len(uploaded_files)}")

    return {
        "uploaded": len(uploaded_files),
        "files": uploaded_files,
        "errors": errors
    }