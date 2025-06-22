from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_tables
from app.routes import (
    auth_router,
    admin_router,
    teacher_router,
    student_router,
    parent_router,
    schedule_router,
    profile_router,
    search_router
)

# Import bulk router
try:
    from app.routes.bulk import router as bulk_router
except ImportError:
    bulk_router = None

app = FastAPI(
    title="School Management System API",
    description="A comprehensive school management system with role-based access",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables on startup
@app.on_event("startup")
def startup_event():
    create_tables()

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(teacher_router, prefix="/teacher", tags=["Teacher"])
app.include_router(student_router, prefix="/student", tags=["Student"])
app.include_router(parent_router, prefix="/parent", tags=["Parent"])
app.include_router(schedule_router, prefix="/schedule", tags=["Schedule"])

# Include optional routers if they loaded successfully
if profile_router:
    app.include_router(profile_router, prefix="/profile", tags=["Profile"])
if search_router:
    app.include_router(search_router, prefix="/search", tags=["Search"])
if bulk_router:
    app.include_router(bulk_router, prefix="/bulk", tags=["Bulk Operations"])

@app.get("/")
def root():
    return {"message": "School Management System API is running!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}