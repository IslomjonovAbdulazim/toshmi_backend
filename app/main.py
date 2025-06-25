from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os

from app.core.config import settings
from app.database import get_db, engine
from app.api import auth, admin, teacher, student, parent, files
from app.models.models import Base, User, Student, Group, Subject
from app.core.security import get_password_hash

app = FastAPI(
    title="School Management System",
    description="A comprehensive education management platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/admin", tags=["Administration"])
app.include_router(teacher.router, prefix="/teacher", tags=["Teacher"])
app.include_router(student.router, prefix="/student", tags=["Student"])
app.include_router(parent.router, prefix="/parent", tags=["Parent"])
app.include_router(files.router, prefix="/files", tags=["File Management"])


@app.get("/", tags=["System"])
def root():
    return {"message": "School Management System API", "version": "1.0.0", "status": "active"}


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy"}


@app.post("/init-db", tags=["System"])
def init_database():
    try:
        Base.metadata.create_all(bind=engine)
        db = next(get_db())
        try:
            if not db.query(User).filter(User.role == "admin").first():
                admin_user = User(
                    phone=settings.ADMIN_PHONE,
                    password_hash=settings.ADMIN_PASSWORD,
                    role="admin",
                    first_name="System",
                    last_name="Administrator",
                    is_active=True
                )
                db.add(admin_user)
                db.commit()
        finally:
            db.close()
        return {"message": "Database initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database initialization failed: {str(e)}")


@app.get("/stats", tags=["System"])
def get_system_stats():
    db = next(get_db())
    try:
        stats = {
            "total_users": db.query(User).count(),
            "total_students": db.query(Student).count(),
            "total_groups": db.query(Group).count(),
            "total_subjects": db.query(Subject).count(),
            "active_users": db.query(User).filter(User.is_active == True).count(),
            "active_students": db.query(Student).join(User).filter(User.is_active == True).count(),
            "teachers": db.query(User).filter(User.role == "teacher", User.is_active == True).count(),
            "parents": db.query(User).filter(User.role == "parent", User.is_active == True).count()
        }
        return stats
    finally:
        db.close()


@app.get("/news", tags=["Public"])
def get_published_news():
    from app.models.models import News
    db = next(get_db())
    try:
        news_list = db.query(News).filter(News.is_published == True).order_by(News.created_at.desc()).limit(10).all()
        return [{
            "id": n.id,
            "title": n.title,
            "content": n.content,
            "created_at": n.created_at,
            "external_links": n.external_links,
            "image_ids": n.image_ids
        } for n in news_list]
    finally:
        db.close()