# app/services/file_service.py
"""
File operations service with passionate file management!
Handles uploads, downloads, validation, and secure file operations.
"""

import os
import uuid
import shutil
from typing import Optional, Dict, Any, BinaryIO, List
from sqlalchemy import func
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from datetime import datetime

from ..models import File, User, Homework, Exam, News
from ..utils.helpers import (
    FileType, validate_file_extension, get_file_type_from_extension,
    format_file_size, MAX_PROFILE_IMAGE_SIZE, MAX_DOCUMENT_SIZE
)
from ..config import settings


class FileService:
    """
    Comprehensive file service handling all file operations
    with passionate attention to security and user experience!
    """

    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path(settings.upload_dir)
        self._ensure_upload_directories()

    def _ensure_upload_directories(self):
        """Ensure all upload directories exist"""
        directories = [
            self.upload_dir / "profiles",
            self.upload_dir / "documents",
            self.upload_dir / "news"
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _generate_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename while preserving extension"""
        file_extension = Path(original_filename).suffix.lower()
        unique_name = str(uuid.uuid4())
        return f"{unique_name}{file_extension}"

    def _validate_file_size(self, file_size: int, file_type: str) -> bool:
        """Validate file size based on type"""
        if file_type == FileType.IMAGE:
            return file_size <= MAX_PROFILE_IMAGE_SIZE
        elif file_type == FileType.DOCUMENT:
            return file_size <= MAX_DOCUMENT_SIZE
        return False

    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type of file"""
        try:
            import magic
            mime = magic.Magic(mime=True)
            return mime.from_file(file_path)
        except ImportError:
            # Fallback to basic detection if python-magic is not available
            return self._get_mime_type_fallback(file_path)
        except Exception:
            # Fallback to basic detection if magic fails
            return self._get_mime_type_fallback(file_path)

    def _get_mime_type_fallback(self, file_path: str) -> str:
        """Fallback MIME type detection based on file extension"""
        extension = Path(file_path).suffix.lower()
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.rtf': 'application/rtf'
        }
        return mime_map.get(extension, 'application/octet-stream')

    def upload_profile_picture(self, file: UploadFile, user_id: str) -> Dict[str, Any]:
        """
        Upload profile picture for user

        Args:
            file: Uploaded file
            user_id: User ID

        Returns:
            Upload result with file information

        Raises:
            HTTPException: If upload fails
        """
        try:
            # Validate user exists
            user = self.db.query(User).filter(
                User.id == user_id,
                User.is_active == True
            ).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Validate file type
            file_type = get_file_type_from_extension(file.filename)
            if file_type != FileType.IMAGE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only image files are allowed for profile pictures"
                )

            # Validate file extension
            if not validate_file_extension(file.filename, FileType.IMAGE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid file extension for image"
                )

            # Read file content to get size
            file_content = file.file.read()
            file_size = len(file_content)

            # Validate file size
            if not self._validate_file_size(file_size, FileType.IMAGE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File size exceeds limit of {format_file_size(MAX_PROFILE_IMAGE_SIZE)}"
                )

            # Generate unique filename
            unique_filename = self._generate_unique_filename(file.filename)
            file_path = self.upload_dir / "profiles" / unique_filename

            # Save file
            with open(file_path, "wb") as f:
                f.write(file_content)

            # Get MIME type
            mime_type = self._get_mime_type(str(file_path))

            # Delete existing profile picture file record
            existing_file = self.db.query(File).filter(
                File.user_id == user_id,
                File.file_type == FileType.IMAGE
            ).first()

            if existing_file:
                # Delete old file from filesystem
                old_file_path = Path(existing_file.file_path)
                if old_file_path.exists():
                    old_file_path.unlink()
                # Delete old file record
                self.db.delete(existing_file)

            # Create file record
            file_record = File(
                filename=unique_filename,
                original_filename=file.filename,
                file_path=str(file_path),
                file_size=file_size,
                file_type=FileType.IMAGE,
                mime_type=mime_type,
                uploaded_by=user_id,
                user_id=user_id,  # For profile pictures
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(file_record)

            # Update user avatar URL
            avatar_url = f"/files/{file_record.id}"
            user.avatar_url = avatar_url
            user.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(file_record)

            return {
                "id": file_record.id,
                "filename": file_record.filename,
                "original_filename": file_record.original_filename,
                "file_size": file_record.file_size,
                "file_type": file_record.file_type,
                "mime_type": file_record.mime_type,
                "avatar_url": avatar_url,
                "upload_url": f"/files/{file_record.id}",
                "created_at": file_record.created_at,
                "message": "Profile picture uploaded successfully"
            }

        except HTTPException:
            self.db.rollback()
            # Clean up file if it was created
            if 'file_path' in locals() and Path(file_path).exists():
                Path(file_path).unlink()
            raise
        except Exception as e:
            self.db.rollback()
            # Clean up file if it was created
            if 'file_path' in locals() and Path(file_path).exists():
                Path(file_path).unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Profile picture upload error: {str(e)}"
            )

    def upload_homework_file(self, file: UploadFile, homework_id: str, user_id: str) -> Dict[str, Any]:
        """
        Upload file for homework

        Args:
            file: Uploaded file
            homework_id: Homework ID
            user_id: User uploading the file

        Returns:
            Upload result with file information

        Raises:
            HTTPException: If upload fails
        """
        try:
            # Validate homework exists and user has permission
            homework = self.db.query(Homework).filter(
                Homework.id == homework_id,
                Homework.teacher_id == user_id
            ).first()

            if not homework:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Homework not found or access denied"
                )

            return self._upload_academic_file(file, user_id, homework_id=homework_id)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Homework file upload error: {str(e)}"
            )

    def upload_exam_file(self, file: UploadFile, exam_id: str, user_id: str) -> Dict[str, Any]:
        """
        Upload file for exam

        Args:
            file: Uploaded file
            exam_id: Exam ID
            user_id: User uploading the file

        Returns:
            Upload result with file information

        Raises:
            HTTPException: If upload fails
        """
        try:
            # Validate exam exists and user has permission
            exam = self.db.query(Exam).filter(
                Exam.id == exam_id,
                Exam.teacher_id == user_id
            ).first()

            if not exam:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Exam not found or access denied"
                )

            return self._upload_academic_file(file, user_id, exam_id=exam_id)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Exam file upload error: {str(e)}"
            )

    def upload_news_image(self, file: UploadFile, news_id: str, user_id: str) -> Dict[str, Any]:
        """
        Upload image for news article

        Args:
            file: Uploaded file
            news_id: News ID
            user_id: User uploading the file

        Returns:
            Upload result with file information

        Raises:
            HTTPException: If upload fails
        """
        try:
            # Validate news exists and user has permission (admin only)
            news = self.db.query(News).filter(
                News.id == news_id,
                News.published_by == user_id
            ).first()

            if not news:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="News article not found or access denied"
                )

            # Validate file type (images only for news)
            file_type = get_file_type_from_extension(file.filename)
            if file_type != FileType.IMAGE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only image files are allowed for news articles"
                )

            return self._upload_academic_file(file, user_id, news_id=news_id)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"News image upload error: {str(e)}"
            )

    def _upload_academic_file(
            self,
            file: UploadFile,
            user_id: str,
            homework_id: Optional[str] = None,
            exam_id: Optional[str] = None,
            news_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload academic file (homework, exam, or news)

        Args:
            file: Uploaded file
            user_id: User uploading the file
            homework_id: Optional homework ID
            exam_id: Optional exam ID
            news_id: Optional news ID

        Returns:
            Upload result
        """
        try:
            # Determine file type
            file_type = get_file_type_from_extension(file.filename)
            if not file_type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported file type"
                )

            # Validate file extension
            if not validate_file_extension(file.filename, file_type):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid file extension"
                )

            # Read file content
            file_content = file.file.read()
            file_size = len(file_content)

            # Validate file size
            if not self._validate_file_size(file_size, file_type):
                max_size = MAX_PROFILE_IMAGE_SIZE if file_type == FileType.IMAGE else MAX_DOCUMENT_SIZE
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File size exceeds limit of {format_file_size(max_size)}"
                )

            # Generate unique filename and path
            unique_filename = self._generate_unique_filename(file.filename)
            file_path = self.upload_dir / "documents" / unique_filename

            # For news images, use news directory
            if news_id and file_type == FileType.IMAGE:
                file_path = self.upload_dir / "news" / unique_filename

            # Save file
            with open(file_path, "wb") as f:
                f.write(file_content)

            # Get MIME type
            mime_type = self._get_mime_type(str(file_path))

            # Create file record
            file_record = File(
                filename=unique_filename,
                original_filename=file.filename,
                file_path=str(file_path),
                file_size=file_size,
                file_type=file_type,
                mime_type=mime_type,
                uploaded_by=user_id,
                homework_id=homework_id,
                exam_id=exam_id,
                news_id=news_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(file_record)
            self.db.commit()
            self.db.refresh(file_record)

            return {
                "id": file_record.id,
                "filename": file_record.filename,
                "original_filename": file_record.original_filename,
                "file_size": file_record.file_size,
                "file_type": file_record.file_type,
                "mime_type": file_record.mime_type,
                "upload_url": f"/files/{file_record.id}",
                "created_at": file_record.created_at,
                "message": "File uploaded successfully"
            }

        except HTTPException:
            self.db.rollback()
            # Clean up file if it was created
            if 'file_path' in locals() and Path(file_path).exists():
                Path(file_path).unlink()
            raise
        except Exception as e:
            self.db.rollback()
            # Clean up file if it was created
            if 'file_path' in locals() and Path(file_path).exists():
                Path(file_path).unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"File upload error: {str(e)}"
            )

    def get_file(self, file_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get file information and path for download

        Args:
            file_id: File ID
            user_id: Optional user ID for permission check

        Returns:
            File information and path

        Raises:
            HTTPException: If file not found or access denied
        """
        try:
            file_record = self.db.query(File).filter(File.id == file_id).first()

            if not file_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found"
                )

            # Check if file exists on filesystem
            file_path = Path(file_record.file_path)
            if not file_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found on server"
                )

            # Basic access control (can be enhanced based on requirements)
            # For now, allow access to all files for authenticated users

            return {
                "id": file_record.id,
                "filename": file_record.filename,
                "original_filename": file_record.original_filename,
                "file_path": str(file_path),
                "file_size": file_record.file_size,
                "file_type": file_record.file_type,
                "mime_type": file_record.mime_type,
                "created_at": file_record.created_at
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"File retrieval error: {str(e)}"
            )

    def delete_file(self, file_id: str, user_id: str) -> Dict[str, Any]:
        """
        Delete file (admin or file owner only)

        Args:
            file_id: File ID
            user_id: User requesting deletion

        Returns:
            Deletion result

        Raises:
            HTTPException: If deletion fails
        """
        try:
            file_record = self.db.query(File).filter(File.id == file_id).first()

            if not file_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found"
                )

            # Check permission (file owner or admin)
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            if file_record.uploaded_by != user_id and user.role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied to delete this file"
                )

            # Delete file from filesystem
            file_path = Path(file_record.file_path)
            if file_path.exists():
                file_path.unlink()

            # Delete file record
            self.db.delete(file_record)
            self.db.commit()

            return {
                "message": "File deleted successfully",
                "file_id": file_id,
                "deleted_by": user_id,
                "timestamp": datetime.utcnow()
            }

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"File deletion error: {str(e)}"
            )

    def get_user_files(self, user_id: str, file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get files uploaded by user

        Args:
            user_id: User ID
            file_type: Optional file type filter

        Returns:
            List of user files
        """
        try:
            query = self.db.query(File).filter(File.uploaded_by == user_id)

            if file_type:
                query = query.filter(File.file_type == file_type)

            files = query.order_by(File.created_at.desc()).all()

            result = []
            for file_record in files:
                file_data = {
                    "id": file_record.id,
                    "filename": file_record.filename,
                    "original_filename": file_record.original_filename,
                    "file_size": file_record.file_size,
                    "file_type": file_record.file_type,
                    "mime_type": file_record.mime_type,
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

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving user files: {str(e)}"
            )

    def get_storage_statistics(self) -> Dict[str, Any]:
        """
        Get file storage statistics

        Returns:
            Storage statistics
        """
        try:
            # Count files by type
            total_files = self.db.query(File).count()
            image_files = self.db.query(File).filter(File.file_type == FileType.IMAGE).count()
            document_files = self.db.query(File).filter(File.file_type == FileType.DOCUMENT).count()

            # Calculate total storage used
            total_size = self.db.query(func.sum(File.file_size)).scalar() or 0
            image_size = self.db.query(func.sum(File.file_size)).filter(
                File.file_type == FileType.IMAGE
            ).scalar() or 0
            document_size = self.db.query(func.sum(File.file_size)).filter(
                File.file_type == FileType.DOCUMENT
            ).scalar() or 0

            return {
                "total_files": total_files,
                "image_files": image_files,
                "document_files": document_files,
                "total_storage_bytes": total_size,
                "total_storage_formatted": format_file_size(total_size),
                "image_storage_bytes": image_size,
                "image_storage_formatted": format_file_size(image_size),
                "document_storage_bytes": document_size,
                "document_storage_formatted": format_file_size(document_size),
                "generated_at": datetime.utcnow()
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving storage statistics: {str(e)}"
            )


# Service factory function
def get_file_service(db: Session) -> FileService:
    """Create file service instance"""
    return FileService(db)