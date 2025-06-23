"""
Education Center Management System - Main Application
Built with passion for educational excellence and comprehensive system management!
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime

from .config import settings
from .database import engine, create_tables
from .routes import auth, admin, teacher, student, parent, files

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Education Center Management System",
    description="""
    A comprehensive API for managing educational institutions with passionate attention to detail!

    ## Features

    * **User Management** - Admin, Teachers, Students, Parents with role-based access
    * **Academic Management** - Homework, Exams, Grades, Attendance tracking
    * **Group & Subject Management** - Flexible group structures and subject assignments
    * **Payment Tracking** - Monthly payment management with notifications
    * **File Management** - Profile pictures, academic files, news images
    * **News & Communication** - Announcements and notifications system
    * **Comprehensive Reporting** - Analytics and performance tracking

    ## Authentication

    All endpoints require JWT token authentication. Use `/auth/login` to obtain a token.

    ## Roles

    * **Admin** - Full system management access
    * **Teacher** - Academic content management and grading
    * **Student** - Personal academic information access
    * **Parent** - Children's academic information monitoring
    """,
    version="1.0.0",
    contact={
        "name": "Education Center Support",
        "email": "support@educationcenter.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database-related exceptions"""
    logger.error(f"Database error on {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Database error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unexpected error on {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and perform startup tasks"""
    try:
        logger.info("🚀 Starting Education Center Management System...")

        # Create database tables
        logger.info("📊 Creating database tables...")
        create_tables()
        logger.info("✅ Database tables created successfully")

        logger.info("🎓 Education Center Management System started successfully!")

    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}")
        raise


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup tasks on shutdown"""
    logger.info("🔄 Education Center Management System shutting down...")


# Include routers with comprehensive API organization
app.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Authentication failed"},
        403: {"description": "Access forbidden"}
    }
)

app.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin Management"],
    responses={
        403: {"description": "Admin access required"},
        404: {"description": "Resource not found"}
    }
)

app.include_router(
    teacher.router,
    prefix="/teacher",
    tags=["Teacher Operations"],
    responses={
        403: {"description": "Teacher access required"},
        404: {"description": "Resource not found"}
    }
)

app.include_router(
    student.router,
    prefix="/student",
    tags=["Student Information"],
    responses={
        403: {"description": "Student access required"},
        404: {"description": "Resource not found"}
    }
)

app.include_router(
    parent.router,
    prefix="/parent",
    tags=["Parent Access"],
    responses={
        403: {"description": "Parent access required"},
        404: {"description": "Child not found or access denied"}
    }
)

app.include_router(
    files.router,
    prefix="/files",
    tags=["File Management"],
    responses={
        404: {"description": "File not found"},
        413: {"description": "File too large"}
    }
)


# Root endpoints
@app.get("/", tags=["System"])
def root():
    """
    Welcome endpoint with system information

    Returns basic system information and available features
    """
    return {
        "message": "🎓 Education Center Management System API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment,
        "features": [
            "User Management (Admin, Teacher, Student, Parent)",
            "Academic Management (Homework, Exams, Grades, Attendance)",
            "Group & Subject Management",
            "Payment Tracking & Notifications",
            "File Management & Storage",
            "News & Communication System",
            "Comprehensive Reporting & Analytics"
        ],
        "api_documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json"
        },
        "authentication": {
            "login_endpoint": "/auth/login",
            "token_type": "Bearer JWT"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health", tags=["System"])
def health_check():
    """
    System health check endpoint

    Returns system health status and basic metrics
    """
    try:
        # Test database connection
        from .database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        database_status = "healthy"
    except Exception:
        database_status = "unhealthy"

    return {
        "status": "healthy" if database_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.environment,
        "components": {
            "database": database_status,
            "api": "healthy"
        },
        "uptime": "System running"
    }


@app.get("/api-info", tags=["System"])
def api_info():
    """
    Comprehensive API information

    Returns detailed information about available endpoints and features
    """
    return {
        "api_name": "Education Center Management System",
        "version": "1.0.0",
        "description": "Comprehensive educational institution management platform",
        "endpoints": {
            "authentication": {
                "login": "POST /auth/login",
                "logout": "POST /auth/logout",
                "change_password": "PUT /auth/change-password",
                "profile": "GET /auth/profile"
            },
            "admin_management": {
                "create_users": "POST /admin/{students|teachers|parents}",
                "manage_groups": "POST/GET/PUT/DELETE /admin/groups",
                "manage_subjects": "POST/GET/PUT/DELETE /admin/subjects",
                "assign_teachers": "POST /admin/assign-teacher",
                "record_payments": "POST /admin/payments",
                "create_news": "POST /admin/news",
                "reports": "GET /admin/reports/{overview|payments|academic}"
            },
            "teacher_operations": {
                "homework": "POST/GET /teacher/homework",
                "exams": "POST/GET /teacher/exams",
                "bulk_grading": "POST /teacher/bulk-grade",
                "attendance": "POST /teacher/attendance",
                "performance": "GET /teacher/performance/{group|student}"
            },
            "student_access": {
                "dashboard": "GET /student/dashboard",
                "homework": "GET /student/homework",
                "exams": "GET /student/exams",
                "grades": "GET /student/grades",
                "attendance": "GET /student/attendance",
                "schedule": "GET /student/schedule",
                "payments": "GET /student/payments"
            },
            "parent_access": {
                "children": "GET /parent/children",
                "child_grades": "GET /parent/children/{id}/grades",
                "child_attendance": "GET /parent/children/{id}/attendance",
                "child_payments": "GET /parent/children/{id}/payments",
                "dashboard": "GET /parent/dashboard"
            },
            "file_management": {
                "upload_profile": "POST /files/profile-picture",
                "upload_academic": "POST /files/{homework|exams}/{id}/upload",
                "download": "GET /files/{file_id}",
                "file_info": "GET /files/{file_id}/info"
            }
        },
        "authentication": {
            "type": "JWT Bearer Token",
            "header": "Authorization: Bearer <token>",
            "expiration": f"{settings.access_token_expire_minutes} minutes"
        },
        "roles_and_permissions": {
            "admin": [
                "Full system access",
                "User management",
                "Payment recording",
                "News creation",
                "System reporting"
            ],
            "teacher": [
                "Academic content management",
                "Homework and exam creation",
                "Student grading",
                "Attendance recording",
                "Group performance viewing"
            ],
            "student": [
                "Personal academic data access",
                "Homework and exam viewing",
                "Grade checking",
                "Payment history",
                "Profile management"
            ],
            "parent": [
                "Children's academic monitoring",
                "Grade and attendance viewing",
                "Payment history access",
                "School communication"
            ]
        },
        "file_support": {
            "profile_pictures": {
                "formats": ["JPG", "PNG", "GIF", "WEBP"],
                "max_size": "3MB"
            },
            "academic_files": {
                "formats": ["PDF", "DOC", "DOCX", "TXT", "JPG", "PNG"],
                "max_size": "10MB"
            }
        },
        "generated_at": datetime.utcnow().isoformat()
    }


@app.get("/system-status", tags=["System"])
def system_status():
    """
    Detailed system status for monitoring

    Returns comprehensive system status information
    """
    try:
        from .database import SessionLocal
        from .models import User, Student, Teacher, Parent, Group, Subject

        db = SessionLocal()

        # Get basic statistics
        stats = {
            "total_users": db.query(User).count(),
            "active_users": db.query(User).filter(User.is_active == True).count(),
            "total_students": db.query(Student).count(),
            "total_teachers": db.query(Teacher).count(),
            "total_parents": db.query(Parent).count(),
            "total_groups": db.query(Group).filter(Group.is_active == True).count(),
            "total_subjects": db.query(Subject).filter(Subject.is_active == True).count()
        }

        db.close()

        return {
            "system_status": "operational",
            "database_status": "connected",
            "api_status": "healthy",
            "statistics": stats,
            "environment": settings.environment,
            "debug_mode": settings.debug,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"System status check failed: {str(e)}")
        return {
            "system_status": "degraded",
            "database_status": "error",
            "api_status": "limited",
            "error": "Database connection failed",
            "timestamp": datetime.utcnow().isoformat()
        }