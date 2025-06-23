# app/routes/files.py
"""
File management routes with passionate file handling!
Handles uploads, downloads, and management of all file types in the system.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from ..database import get_db
from ..services.file_service import get_file_service
from ..utils.dependencies import (
    get_current_active_user, require_admin, require_teacher,
    get_current_teacher_profile
)

router = APIRouter()


# Profile Picture Management

@router.post("/profile-picture", response_model=dict, summary="Upload Profile Picture")
async def upload_profile_picture(
        file: UploadFile = File(..., description="Profile picture file"),
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    """
    Upload profile picture for current user

    - **file**: Image file (JPG, PNG, GIF, WEBP)
    - **Max size**: 3MB

    Replaces existing profile picture if any
    Returns new avatar URL
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )

    file_service = get_file_service(db)
    return file_service.upload_profile_picture(file, current_user.id)


# Academic File Management (Teacher Only)

@router.post("/homework/{homework_id}/upload", response_model=dict, summary="Upload Homework File")
async def upload_homework_file(
        homework_id: str,
        file: UploadFile = File(..., description="Homework file"),
        teacher=Depends(get_current_teacher_profile),
        db: Session = Depends(get_db)
):
    """
    Upload file for homework assignment (Teacher only)

    - **homework_id**: Homework assignment ID
    - **file**: Document or image file
    - **Max size**: 10MB

    Teacher can only upload files for their own homework assignments
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )

    file_service = get_file_service(db)
    return file_service.upload_homework_file(file, homework_id, teacher.user_id)


@router.post("/exams/{exam_id}/upload", response_model=dict, summary="Upload Exam File")
async def upload_exam_file(
        exam_id: str,
        file: UploadFile = File(..., description="Exam file"),
        teacher=Depends(get_current_teacher_profile),
        db: Session = Depends(get_db)
):
    """
    Upload file for exam (Teacher only)

    - **exam_id**: Exam ID
    - **file**: Document or image file
    - **Max size**: 10MB

    Teacher can only upload files for their own exams
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )

    file_service = get_file_service(db)
    return file_service.upload_exam_file(file, exam_id, teacher.user_id)


# News File Management (Admin Only)

@router.post("/news/{news_id}/upload-image", response_model=dict, summary="Upload News Image")
async def upload_news_image(
        news_id: str,
        file: UploadFile = File(..., description="News image file"),
        admin=Depends(require_admin),
        db: Session = Depends(get_db)
):
    """
    Upload image for news article (Admin only)

    - **news_id**: News article ID
    - **file**: Image file (JPG, PNG, GIF, WEBP)
    - **Max size**: 10MB

    Admin can only upload images for their own news articles
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )

    file_service = get_file_service(db)
    return file_service.upload_news_image(file, news_id, admin.id)


# File Download and Access

@router.get("/{file_id}", summary="Download/View File")
async def get_file(
        file_id: str,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    """
    Download or view a file

    - **file_id**: File ID

    Returns file content with appropriate headers
    Users can access files they have permission to view
    """
    file_service = get_file_service(db)
    file_info = file_service.get_file(file_id, current_user.id)

    file_path = Path(file_info["file_path"])

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )

    # Return file with appropriate headers
    return FileResponse(
        path=file_path,
        filename=file_info["original_filename"],
        media_type=file_info["mime_type"]
    )


@router.get("/{file_id}/info", response_model=dict, summary="Get File Information")
async def get_file_info(
        file_id: str,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    """
    Get file information without downloading

    - **file_id**: File ID

    Returns file metadata including size, type, and upload date
    """
    file_service = get_file_service(db)
    file_info = file_service.get_file(file_id, current_user.id)

    from ..utils.helpers import format_file_size

    return {
        "file_id": file_info["id"],
        "filename": file_info["original_filename"],
        "file_size": file_info["file_size"],
        "file_size_formatted": format_file_size(file_info["file_size"]),
        "file_type": file_info["file_type"],
        "mime_type": file_info["mime_type"],
        "uploaded_at": file_info["created_at"],
        "download_url": f"/files/{file_id}"
    }


# File Management

@router.delete("/{file_id}", response_model=dict, summary="Delete File")
async def delete_file(
        file_id: str,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    """
    Delete a file

    - **file_id**: File ID

    Users can only delete files they uploaded
    Admins can delete any file
    """
    file_service = get_file_service(db)
    return file_service.delete_file(file_id, current_user.id)


@router.get("/user/my-files", response_model=list, summary="Get My Files")
async def get_my_files(
        file_type: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    """
    Get all files uploaded by current user

    - **file_type**: Optional filter by file type (image, document)

    Returns list of files with download URLs and metadata
    """
    file_service = get_file_service(db)
    return file_service.get_user_files(current_user.id, file_type)


# Admin File Management

@router.get("/admin/storage-stats", response_model=dict, summary="Get Storage Statistics")
async def get_storage_statistics(
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Get file storage statistics (Admin only)

    Returns comprehensive storage usage information
    """
    file_service = get_file_service(db)
    return file_service.get_storage_statistics()


@router.get("/admin/all-files", response_model=list, summary="Get All Files")
async def get_all_files(
        file_type: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Get all files in the system (Admin only)

    - **file_type**: Optional filter by file type
    - **user_id**: Optional filter by uploader
    - **limit**: Maximum number of files to return

    Returns comprehensive file listing for administration
    """
    from ..models import File, User

    query = db.query(File).join(User, File.uploaded_by == User.id)

    if file_type:
        query = query.filter(File.file_type == file_type)

    if user_id:
        query = query.filter(File.uploaded_by == user_id)

    files = query.order_by(File.created_at.desc()).limit(limit).all()

    result = []
    for file_record in files:
        from ..utils.helpers import format_file_size

        file_data = {
            "id": file_record.id,
            "filename": file_record.original_filename,
            "file_size": file_record.file_size,
            "file_size_formatted": format_file_size(file_record.file_size),
            "file_type": file_record.file_type,
            "mime_type": file_record.mime_type,
            "uploaded_by": {
                "user_id": file_record.uploaded_by,
                "full_name": file_record.uploaded_by_user.full_name,
                "role": file_record.uploaded_by_user.role
            },
            "created_at": file_record.created_at,
            "download_url": f"/files/{file_record.id}"
        }

        # Add context information
        if file_record.homework_id:
            file_data["context"] = {
                "type": "homework",
                "homework_id": file_record.homework_id,
                "title": file_record.homework.title if file_record.homework else None
            }
        elif file_record.exam_id:
            file_data["context"] = {
                "type": "exam",
                "exam_id": file_record.exam_id,
                "title": file_record.exam.title if file_record.exam else None
            }
        elif file_record.news_id:
            file_data["context"] = {
                "type": "news",
                "news_id": file_record.news_id,
                "title": file_record.news.title if file_record.news else None
            }
        elif file_record.user_id:
            file_data["context"] = {
                "type": "profile_picture",
                "user_id": file_record.user_id
            }

        result.append(file_data)

    return result


@router.post("/admin/cleanup-orphaned", response_model=dict, summary="Cleanup Orphaned Files")
async def cleanup_orphaned_files(
        dry_run: bool = True,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Cleanup orphaned files that exist in filesystem but not in database (Admin only)

    - **dry_run**: If True, only reports what would be deleted without actually deleting

    Returns report of orphaned files found and action taken
    """
    from ..models import File
    from ..config import settings
    import os

    upload_dir = Path(settings.upload_dir)
    orphaned_files = []
    total_size = 0

    # Check all subdirectories
    for subdir in ["profiles", "documents", "news"]:
        subdir_path = upload_dir / subdir
        if not subdir_path.exists():
            continue

        for file_path in subdir_path.iterdir():
            if file_path.is_file():
                # Check if file exists in database
                file_exists = db.query(File).filter(
                    File.file_path == str(file_path)
                ).first()

                if not file_exists:
                    file_size = file_path.stat().st_size
                    orphaned_files.append({
                        "file_path": str(file_path),
                        "file_name": file_path.name,
                        "file_size": file_size,
                        "subdirectory": subdir
                    })
                    total_size += file_size

                    # Delete file if not dry run
                    if not dry_run:
                        try:
                            file_path.unlink()
                        except Exception as e:
                            # Log error but continue
                            pass

    from ..utils.helpers import format_file_size

    return {
        "orphaned_files_found": len(orphaned_files),
        "total_size_bytes": total_size,
        "total_size_formatted": format_file_size(total_size),
        "dry_run": dry_run,
        "action_taken": "Files would be deleted" if dry_run else "Files deleted",
        "files": orphaned_files[:20]  # Return first 20 for preview
    }


# File Validation and Upload Helpers

@router.post("/validate", response_model=dict, summary="Validate File Before Upload")
async def validate_file(
        file: UploadFile = File(..., description="File to validate"),
        file_type: str = "document",
        current_user=Depends(get_current_active_user)
):
    """
    Validate file before actual upload

    - **file**: File to validate
    - **file_type**: Expected file type (image, document)

    Returns validation result without actually uploading the file
    """
    from ..utils.helpers import (
        validate_file_extension, get_file_type_from_extension,
        MAX_PROFILE_IMAGE_SIZE, MAX_DOCUMENT_SIZE, format_file_size
    )

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )

    # Check file type
    detected_type = get_file_type_from_extension(file.filename)
    if not detected_type:
        return {
            "valid": False,
            "error": "Unsupported file type",
            "filename": file.filename
        }

    # Check extension
    if not validate_file_extension(file.filename, detected_type):
        return {
            "valid": False,
            "error": "Invalid file extension for file type",
            "filename": file.filename,
            "detected_type": detected_type
        }

    # Check file size
    file_content = await file.read()
    file_size = len(file_content)

    max_size = MAX_PROFILE_IMAGE_SIZE if detected_type == "image" else MAX_DOCUMENT_SIZE

    if file_size > max_size:
        return {
            "valid": False,
            "error": f"File size exceeds limit of {format_file_size(max_size)}",
            "filename": file.filename,
            "file_size": file_size,
            "file_size_formatted": format_file_size(file_size),
            "max_size_formatted": format_file_size(max_size)
        }

    # Reset file position for potential future use
    await file.seek(0)

    return {
        "valid": True,
        "filename": file.filename,
        "detected_type": detected_type,
        "file_size": file_size,
        "file_size_formatted": format_file_size(file_size),
        "max_size_formatted": format_file_size(max_size)
    }


# Bulk File Operations (Admin Only)

@router.post("/admin/bulk-delete", response_model=dict, summary="Bulk Delete Files")
async def bulk_delete_files(
        file_ids: list[str],
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """
    Delete multiple files at once (Admin only)

    - **file_ids**: List of file IDs to delete

    Returns summary of deletion results
    """
    file_service = get_file_service(db)

    deleted_count = 0
    failed_count = 0
    errors = []

    for file_id in file_ids:
        try:
            file_service.delete_file(file_id, admin.id)
            deleted_count += 1
        except Exception as e:
            failed_count += 1
            errors.append(f"File {file_id}: {str(e)}")

    return {
        "total_files": len(file_ids),
        "deleted_count": deleted_count,
        "failed_count": failed_count,
        "errors": errors[:10]  # Return first 10 errors
    }