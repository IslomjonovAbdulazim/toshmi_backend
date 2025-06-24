import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, File, Homework, Exam, News
from app.core.security import get_current_user, require_role
from app.core.config import settings

router = APIRouter()


def save_file(file: UploadFile, file_type: str, related_id: int, current_user: User, db: Session):
    if file_type == "profile" and file.size > settings.MAX_IMAGE_SIZE:
        raise HTTPException(status_code=413, detail="Profile image too large")
    elif file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    file_extension = file.filename.split(".")[-1] if "." in file.filename else ""
    unique_filename = f"{uuid.uuid4()}.{file_extension}"

    if file_type == "profile":
        file_path = os.path.join(settings.UPLOAD_DIR, "images", unique_filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
    else:
        file_path = os.path.join(settings.UPLOAD_DIR, "documents", unique_filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

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


@router.post("/profile-picture")
def upload_profile_picture(file: UploadFile = FastAPIFile(...), current_user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    if current_user.profile_image_id:
        old_file = db.query(File).filter(File.id == current_user.profile_image_id).first()
        if old_file and os.path.exists(old_file.file_path):
            os.remove(old_file.file_path)
        db.delete(old_file)

    new_file = save_file(file, "profile", current_user.id, current_user, db)
    current_user.profile_image_id = new_file.id
    db.commit()

    return {"message": "Profile picture updated", "file_id": new_file.id}


@router.post("/homework/{homework_id}/upload")
def upload_homework_file(homework_id: int, file: UploadFile = FastAPIFile(...),
                         current_user: User = Depends(require_role(["teacher"])), db: Session = Depends(get_db)):
    homework = db.query(Homework).filter(Homework.id == homework_id).first()
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")

    if len(homework.document_ids) >= 3:
        raise HTTPException(status_code=400, detail="Maximum 3 documents allowed")

    new_file = save_file(file, "homework", homework_id, current_user, db)

    document_ids = homework.document_ids or []
    document_ids.append(new_file.id)
    homework.document_ids = document_ids
    db.commit()

    return {"message": "File uploaded", "file_id": new_file.id}


@router.post("/exam/{exam_id}/upload")
def upload_exam_file(exam_id: int, file: UploadFile = FastAPIFile(...),
                     current_user: User = Depends(require_role(["teacher"])), db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    if len(exam.document_ids) >= 3:
        raise HTTPException(status_code=400, detail="Maximum 3 documents allowed")

    new_file = save_file(file, "exam", exam_id, current_user, db)

    document_ids = exam.document_ids or []
    document_ids.append(new_file.id)
    exam.document_ids = document_ids
    db.commit()

    return {"message": "File uploaded", "file_id": new_file.id}


@router.post("/news/{news_id}/upload-image")
def upload_news_image(news_id: int, file: UploadFile = FastAPIFile(...),
                      current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    if len(news.image_ids) >= 3:
        raise HTTPException(status_code=400, detail="Maximum 3 images allowed")

    new_file = save_file(file, "news", news_id, current_user, db)

    image_ids = news.image_ids or []
    image_ids.append(new_file.id)
    news.image_ids = image_ids
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
        if homework and file_id in homework.document_ids:
            homework.document_ids.remove(file_id)
    elif file.file_type == "exam":
        exam = db.query(Exam).filter(Exam.id == file.related_id).first()
        if exam and file_id in exam.document_ids:
            exam.document_ids.remove(file_id)
    elif file.file_type == "news":
        news = db.query(News).filter(News.id == file.related_id).first()
        if news and file_id in news.image_ids:
            news.image_ids.remove(file_id)

    if os.path.exists(file.file_path):
        os.remove(file.file_path)

    db.delete(file)
    db.commit()

    return {"message": "File deleted"}