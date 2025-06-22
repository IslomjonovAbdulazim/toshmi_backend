from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
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

# Environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"

app = FastAPI(
    title="School Management System API",
    description="A comprehensive school management system with role-based access",
    version="1.0.0",
    debug=DEBUG
)

# CORS configuration based on environment
if ENVIRONMENT == "production":
    # Production CORS - replace with your actual domain
    allowed_origins = [
        "*"
    ]
else:
    # Development CORS
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

# Database initialization
@app.on_event("startup")
def startup_event():
    if ENVIRONMENT == "production":
        # Run Alembic migrations in production
        try:
            import alembic.config
            import alembic.command
            alembic_cfg = alembic.config.Config("alembic.ini")
            alembic.command.upgrade(alembic_cfg, "head")
            print("✅ Database migrations applied successfully")
        except Exception as e:
            print(f"❌ Migration error: {e}")
            # Fallback to create_tables if migrations fail
            create_tables()
    else:
        # Development: create tables directly
        create_tables()
        print("✅ Development database tables created")

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
    return {
        "message": "School Management System API is running!",
        "environment": ENVIRONMENT,
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "environment": ENVIRONMENT
    }

# Graceful shutdown
@app.on_event("shutdown")
def shutdown_event():
    print("🔄 Application shutting down...")