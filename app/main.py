from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.api import auth, admin, teacher, student, parent, files

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
    return {
        "message": "School Management System API",
        "version": "1.0.0",
        "status": "active"
    }


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy"}


@app.post("/init-db", tags=["System"])
def init_database():
    try:
        from app.database import engine
        from app.models.models import Base
        Base.metadata.create_all(bind=engine)
        return {"message": "Database initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database initialization failed: {str(e)}")


@app.get("/stats", tags=["System"])
def get_system_stats():
    from app.database import get_db
    from app.models.models import User, Student, Group, Subject

    db = next(get_db())
    try:
        return {
            "total_users": db.query(User).count(),
            "total_students": db.query(Student).count(),
            "total_groups": db.query(Group).count(),
            "total_subjects": db.query(Subject).count(),
            "active_users": db.query(User).filter(User.is_active == True).count()
        }
    finally:
        db.close()