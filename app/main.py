"""
Education Center Management System - Main Application - MINIMAL FIXED VERSION
Removes circular import issues by deferring route imports
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime

from .config import settings
from .database import engine, create_tables

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Education Center Management System",
    description="A comprehensive API for managing educational institutions",
    version="1.0.0",
    debug=settings.debug
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else ["https://yourdomain.com"],
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
    if settings.debug:
        logger.error(f"Unexpected error on {request.url}: {str(exc)}", exc_info=True)
    else:
        logger.error(f"Unexpected error on {request.url}: {str(exc)}")

    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred" if not settings.debug else str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Root endpoints
@app.get("/", tags=["System"])
def root():
    """Welcome endpoint with system information"""
    return {
        "message": "🎓 Education Center Management System API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment,
        "debug": settings.debug,
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
    """System health check endpoint"""
    try:
        # Test database connection
        from .database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        database_status = "healthy"
    except Exception as e:
        logger.error(f"Health check database error: {str(e)}")
        database_status = "unhealthy"

    return {
        "status": "healthy" if database_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.environment,
        "components": {
            "database": database_status,
            "api": "healthy"
        }
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and perform startup tasks"""
    try:
        logger.info("🚀 Starting Education Center Management System...")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Debug mode: {settings.debug}")

        # Create database tables
        logger.info("📊 Creating database tables...")
        create_tables()
        logger.info("✅ Database tables created successfully")

        # Create upload directories
        import os
        upload_dirs = [
            settings.upload_dir,
            os.path.join(settings.upload_dir, "profiles"),
            os.path.join(settings.upload_dir, "documents"),
            os.path.join(settings.upload_dir, "news")
        ]

        for upload_dir in upload_dirs:
            os.makedirs(upload_dir, exist_ok=True)

        logger.info("📁 Upload directories created successfully")

        # Setup routes AFTER everything else is initialized
        setup_routes()

        logger.info("🎓 Education Center Management System started successfully!")

    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}")
        raise


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup tasks on shutdown"""
    logger.info("🔄 Education Center Management System shutting down...")


def setup_routes():
    """Setup all routes with lazy imports to avoid circular dependencies"""
    try:
        logger.info("🔗 Setting up routes...")

        # Import routes only when needed to avoid circular imports
        from .routes import auth
        app.include_router(
            auth.router,
            prefix="/auth",
            tags=["Authentication"]
        )
        logger.info("✅ Auth routes added")

        from .routes import admin
        app.include_router(
            admin.router,
            prefix="/admin",
            tags=["Admin Management"]
        )
        logger.info("✅ Admin routes added")

        from .routes import teacher
        app.include_router(
            teacher.router,
            prefix="/teacher",
            tags=["Teacher Operations"]
        )
        logger.info("✅ Teacher routes added")

        from .routes import student
        app.include_router(
            student.router,
            prefix="/student",
            tags=["Student Information"]
        )
        logger.info("✅ Student routes added")

        from .routes import parent
        app.include_router(
            parent.router,
            prefix="/parent",
            tags=["Parent Access"]
        )
        logger.info("✅ Parent routes added")

        from .routes import files
        app.include_router(
            files.router,
            prefix="/files",
            tags=["File Management"]
        )
        logger.info("✅ File routes added")

        logger.info("✅ All routes setup successfully")

    except Exception as e:
        logger.error(f"❌ Route setup failed: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        # Don't raise - allow app to start with basic endpoints


# For running with uvicorn directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )