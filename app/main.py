from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api import auth, admin, teacher, student, parent, files

app = FastAPI(title="Education System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Tables will be created on first API call instead
# Base.metadata.create_all(bind=engine)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(teacher.router, prefix="/teacher", tags=["teacher"])
app.include_router(student.router, prefix="/student", tags=["student"])
app.include_router(parent.router, prefix="/parent", tags=["parent"])
app.include_router(files.router, prefix="/files", tags=["files"])

@app.get("/")
def root():
    return {"message": "Education System API"}

@app.get("/init-db")
def init_database():
    from app.database import engine
    from app.models.models import Base
    Base.metadata.create_all(bind=engine)
    return {"message": "Database initialized"}