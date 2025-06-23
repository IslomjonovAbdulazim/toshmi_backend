# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.database import create_tables

# Import simplified routers
from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router
from app.routes.teacher import router as teacher_router
from app.routes.student import router as student_router
from app.routes.parent import router as parent_router
from app.routes.schedule import router as schedule_router

# Import optional routers if they exist
try:
    from app.routes.profile import router as profile_router
except ImportError:
    profile_router = None

# Environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"

app = FastAPI(
    title="Simplified School Management System API",
    description="A streamlined school management system with role-based access",
    version="2.0.0",
    debug=DEBUG
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)


# Database initialization
@app.on_event("startup")
def startup_event():
    try:
        create_tables()
        print("✅ Database tables created successfully")
        print("🚀 Simplified School Management System is running!")
    except Exception as e:
        print(f"❌ Database error: {e}")


# Include simplified routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(admin_router, prefix="/admin", tags=["Admin Management"])
app.include_router(teacher_router, prefix="/teacher", tags=["Teacher"])
app.include_router(student_router, prefix="/student", tags=["Student"])
app.include_router(parent_router, prefix="/parent", tags=["Parent"])
app.include_router(schedule_router, prefix="/schedule", tags=["Schedule"])

# Include profile router if available
if profile_router:
    app.include_router(profile_router, prefix="/profile", tags=["Profile"])


@app.get("/")
def root():
    return {
        "message": "Simplified School Management System API",
        "version": "2.0.0",
        "environment": ENVIRONMENT,
        "features": [
            "Unique user creation endpoints",
            "Simplified parent-student relationships",
            "Streamlined authentication",
            "Role-based access control",
            "Academic management",
            "Grade tracking",
            "Reports and analytics"
        ]
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "database": "sqlite"
    }


# API documentation
@app.get("/api-info")
def api_info():
    return {
        "endpoints": {
            "auth": {
                "login": "POST /auth/login",
                "logout": "POST /auth/logout",
                "reset_password": "POST /auth/reset-password"
            },
            "admin": {
                "create_student": "POST /admin/students",
                "create_parent": "POST /admin/parents",
                "create_teacher": "POST /admin/teachers",
                "manage_groups": "POST/GET/DELETE /admin/groups",
                "manage_subjects": "POST/GET/DELETE /admin/subjects",
                "reports": "GET /admin/reports/{class|payments|overview}"
            },
            "teacher": {
                "homework": "POST/GET /teacher/homework",
                "exams": "POST/GET /teacher/exams",
                "grading": "POST /teacher/{homework|exam}-grades",
                "attendance": "POST/GET /teacher/attendance"
            },
            "student": {
                "grades": "GET /student/{homework|exam}-grades",
                "attendance": "GET /student/attendance",
                "schedule": "GET /student/schedule"
            },
            "parent": {
                "children": "GET /parent/children",
                "child_grades": "GET /parent/children/{id}/{homework|exam}-grades",
                "child_attendance": "GET /parent/children/{id}/attendance"
            }
        }
    }


@app.on_event("shutdown")
def shutdown_event():
    print("🔄 Simplified School Management System shutting down...")