import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.models import User, File, Homework, Exam, News
from app.core.security import get_current_user, require_role
from app.core.config import settings

router = APIRouter()


def validate_file_size(file: UploadFile, file_type: str):
    max_size = settings.MAX_IMAGE_SIZE if file_type == "profile" else settings.MAX_FILE_SIZE
    if file.size > max_size:
        raise HTTPException(status_code=413, detail="File too large")


def get_file_path(file_type: str, filename: str):
    subfolder = "images" if file_type == "profile" else "documents"
    file_path = os.path.join(settings.UPLOAD_DIR, subfolder, filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    return file_path


def save_file(file: UploadFile, file_type: str, related_id: int, current_user: User, db: Session):
    validate_file_size(file, file_type)
    file_extension = file.filename.split(".")[-1] if "." in file.filename else ""
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = get_file_path(file_type, unique_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    db_file = File(
        filename=unique_filename,
        file_path=file_path,
        file_size=file.size,
        uploaded_by=current_user.id,
        related_id=related_id,
        file_type=file_type
    )
    db.add(db_file)
    db.commit()
    return db_file


def delete_old_file(file_id: int, db: Session):
    if file_id:
        old_file = db.query(File).filter(File.id == file_id).first()
        if old_file:
            if os.path.exists(old_file.file_path):
                os.remove(old_file.file_path)
            db.delete(old_file)


def update_file_list(entity, file_id: int, field_name: str, operation: str, max_count: int = None):
    file_list = getattr(entity, field_name) or []

    if operation == "add":
        if max_count and len(file_list) >= max_count:
            raise HTTPException(status_code=400, detail=f"Maximum {max_count} files allowed")
        file_list.append(file_id)
    elif operation == "remove" and file_id in file_list:
        file_list.remove(file_id)

    setattr(entity, field_name, file_list)


@router.post("/profile-picture")
def upload_profile_picture(file: UploadFile = FastAPIFile(...), current_user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    delete_old_file(current_user.profile_image_id, db)
    new_file = save_file(file, "profile", current_user.id, current_user, db)
    current_user.profile_image_id = new_file.id
    db.commit()
    return {"message": "Profile picture updated", "file_id": new_file.id}


@router.post("/homework/{homework_id}/upload")
def upload_homework_file(homework_id: int, file: UploadFile = FastAPIFile(...),
                         current_user: User = Depends(require_role(["teacher"])), db: Session = Depends(get_db)):
    homework = db.query(Homework).options(
        joinedload(Homework.group_subject)
    ).filter(
        Homework.id == homework_id,
        Homework.group_subject.has(teacher_id=current_user.id)
    ).first()

    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")

    new_file = save_file(file, "homework", homework_id, current_user, db)
    update_file_list(homework, new_file.id, "document_ids", "add", 3)
    db.commit()
    return {"message": "File uploaded", "file_id": new_file.id}


@router.post("/exam/{exam_id}/upload")
def upload_exam_file(exam_id: int, file: UploadFile = FastAPIFile(...),
                     current_user: User = Depends(require_role(["teacher"])), db: Session = Depends(get_db)):
    exam = db.query(Exam).options(
        joinedload(Exam.group_subject)
    ).filter(
        Exam.id == exam_id,
        Exam.group_subject.has(teacher_id=current_user.id)
    ).first()

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    new_file = save_file(file, "exam", exam_id, current_user, db)
    update_file_list(exam, new_file.id, "document_ids", "add", 3)
    db.commit()
    return {"message": "File uploaded", "file_id": new_file.id}


@router.post("/news/{news_id}/upload-image")
def upload_news_image(news_id: int, file: UploadFile = FastAPIFile(...),
                      current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    new_file = save_file(file, "news", news_id, current_user, db)
    update_file_list(news, new_file.id, "image_ids", "add", 3)
    db.commit()
    return {"message": "Image uploaded", "file_id": new_file.id}


@router.get("/{file_id}")
def get_file(file_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    if not os.path.exists(file.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(file.file_path, filename=file.filename)


@router.delete("/{file_id}")
def delete_file(file_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    if file.uploaded_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    if file.file_type == "homework":
        homework = db.query(Homework).filter(Homework.id == file.related_id).first()
        if homework:
            update_file_list(homework, file_id, "document_ids", "remove")
    elif file.file_type == "exam":
        exam = db.query(Exam).filter(Exam.id == file.related_id).first()
        if exam:
            update_file_list(exam, file_id, "document_ids", "remove")
    elif file.file_type == "news":
        news = db.query(News).filter(News.id == file.related_id).first()
        if news:
            update_file_list(news, file_id, "image_ids", "remove")

    if os.path.exists(file.file_path):
        os.remove(file.file_path)

    db.delete(file)
    db.commit()
    return {"message": "File deleted"}