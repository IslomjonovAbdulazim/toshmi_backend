from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
import os
import logging
import asyncio

from app.core.config import settings
from app.database import get_db, engine
from app.api import auth, admin, teacher, student, parent, files
from app.models.models import User, Student, Group, Subject
from app.core.security import hash_password, get_current_user
from app.services.websocket_manager import student_manager, teacher_manager, parent_manager, periodic_broadcast_students, periodic_broadcast_teachers, periodic_broadcast_parents
from app.middleware.activity_tracker import EnhancedActivityTrackingMiddleware

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="School Management System",
    description="Education management platform",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(EnhancedActivityTrackingMiddleware)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/admin", tags=["Administration"])
app.include_router(teacher.router, prefix="/teacher", tags=["Teacher"])
app.include_router(student.router, prefix="/student", tags=["Student"])
app.include_router(parent.router, prefix="/parent", tags=["Parent"])
app.include_router(files.router, prefix="/files", tags=["File Management"])


# Database Management Functions
def verify_database_connection():
    """Verify database connection is working"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.fetchone()[0] == 1
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False




def create_initial_admin():
    """Create initial admin user"""
    db = next(get_db())
    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.role == "admin").first()
        if existing_admin:
            logger.info("Admin user already exists")
            return existing_admin

        # Create admin user
        admin_user = User(
            phone="+998990330919",
            password_hash=hash_password("admin123"),
            role="admin",
            first_name="System",
            last_name="Administrator",
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        logger.info(f"Admin user created with ID: {admin_user.id}")
        return admin_user

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating admin user: {str(e)}")
        raise
    finally:
        db.close()


def create_sample_data():
    """Create sample groups and subjects for testing"""
    db = next(get_db())
    try:
        # Create sample groups
        groups_data = [
            {"name": "10-A", "academic_year": "2024-2025"},
            {"name": "10-B", "academic_year": "2024-2025"},
            {"name": "11-A", "academic_year": "2024-2025"},
            {"name": "11-B", "academic_year": "2024-2025"},
        ]

        for group_data in groups_data:
            existing_group = db.query(Group).filter(Group.name == group_data["name"]).first()
            if not existing_group:
                group = Group(**group_data)
                db.add(group)
                logger.info(f"Created group: {group_data['name']}")

        # Create sample subjects
        subjects_data = [
            {"name": "Matematika", "code": "MATH"},
            {"name": "Fizika", "code": "PHYS"},
            {"name": "Kimyo", "code": "CHEM"},
            {"name": "Biologiya", "code": "BIO"},
            {"name": "Ingliz tili", "code": "ENG"},
            {"name": "O'zbek tili", "code": "UZB"},
            {"name": "Tarix", "code": "HIST"},
            {"name": "Geografiya", "code": "GEO"},
        ]

        for subject_data in subjects_data:
            existing_subject = db.query(Subject).filter(Subject.code == subject_data["code"]).first()
            if not existing_subject:
                subject = Subject(**subject_data)
                db.add(subject)
                logger.info(f"Created subject: {subject_data['name']}")

        db.commit()
        logger.info("Sample data created successfully")

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating sample data: {str(e)}")
        raise
    finally:
        db.close()


def get_database_stats():
    """Get current database statistics"""
    db = next(get_db())
    try:
        stats = {}

        # Get table counts
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        stats["total_tables"] = len(tables)
        stats["table_names"] = tables

        # Get record counts for main tables
        try:
            stats["users"] = db.query(User).count()
            stats["groups"] = db.query(Group).count()
            stats["subjects"] = db.query(Subject).count()
        except:
            stats["users"] = 0
            stats["groups"] = 0
            stats["subjects"] = 0

        return stats

    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        return {"error": str(e)}
    finally:
        db.close()




# API Endpoints
@app.get("/", tags=["System"])
def root():
    return {"message": "School Management System API", "version": "2.0.0", "status": "active"}


@app.get("/health", tags=["System"])
def health_check():
    db_status = verify_database_connection()

    return {
        "status": "healthy" if db_status else "unhealthy",
        "database_connected": db_status,
        "version": "2.0.0"
    }


@app.post("/create-admin", tags=["Database Management"])
def create_admin_user():
    """
    Create admin user without wiping database:
    Phone: +998990330919
    Password: admin123
    """
    try:
        logger.info("Creating admin user...")
        admin_user = create_initial_admin()

        return {
            "message": "Admin user created successfully",
            "admin_user": {
                "id": admin_user.id,
                "phone": admin_user.phone,
                "role": admin_user.role,
                "name": admin_user.full_name
            },
            "login_credentials": {
                "phone": "+998990330919",
                "password": "admin123",
                "role": "admin"
            }
        }

    except Exception as e:
        logger.error(f"Admin creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Admin creation failed: {str(e)}")






@app.get("/db-stats", tags=["Database Management"])
def get_database_stats_endpoint():
    """Get current database statistics and table information"""
    try:
        stats = get_database_stats()
        return {
            "database_stats": stats,
            "timestamp": "now"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database stats: {str(e)}")


@app.post("/create-sample-data", tags=["Database Management"])
def create_sample_data_endpoint():
    """Create sample groups and subjects (useful for testing)"""
    try:
        create_sample_data()
        return {"message": "Sample data created successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create sample data: {str(e)}")


@app.get("/stats", tags=["System"])
def get_system_stats():
    """Get general system statistics"""
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
            "parents": db.query(User).filter(User.role == "parent", User.is_active == True).count(),
            "admins": db.query(User).filter(User.role == "admin", User.is_active == True).count()
        }
        return stats
    finally:
        db.close()


@app.get("/news", tags=["Public"])
def get_published_news():
    """Get published news articles"""
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


@app.websocket("/ws/students")
async def students_websocket(websocket: WebSocket):
    await websocket.accept()
    
    try:
        connected = await student_manager.connect(websocket, 0)  # Use 0 as dummy ID for broadcast
        if not connected:
            return
        
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            student_manager.disconnect(0)
    
    except Exception as e:
        logger.error(f"Students WebSocket error: {e}")
        student_manager.disconnect(0)


@app.websocket("/ws/teachers")
async def teachers_websocket(websocket: WebSocket):
    await websocket.accept()
    
    try:
        connected = await teacher_manager.connect(websocket, 0)
        if not connected:
            return
        
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            teacher_manager.disconnect(0)
    
    except Exception as e:
        logger.error(f"Teachers WebSocket error: {e}")
        teacher_manager.disconnect(0)


@app.websocket("/ws/parents")
async def parents_websocket(websocket: WebSocket):
    await websocket.accept()
    
    try:
        connected = await parent_manager.connect(websocket, 0)
        if not connected:
            return
        
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            parent_manager.disconnect(0)
    
    except Exception as e:
        logger.error(f"Parents WebSocket error: {e}")
        parent_manager.disconnect(0)


@app.get("/activity/status", tags=["Activity Tracking"])
async def get_activity_status(current_user: User = Depends(get_current_user)):
    """Get current activity tracking status"""
    from app.models.models import UserActivity
    
    db = next(get_db())
    try:
        # Get recent activity from database
        recent_activity = db.query(User, UserActivity).outerjoin(
            UserActivity, User.id == UserActivity.user_id
        ).filter(User.is_active == True).limit(50).all()
        
        activity_list = []
        for user, activity in recent_activity:
            last_active = activity.last_active if activity else None
            activity_list.append({
                "user_id": user.id,
                "phone": user.phone,
                "full_name": user.full_name,
                "role": user.role,
                "last_active": last_active.isoformat() if last_active else None
            })
        
        return {
            "student_connections": len(student_manager.active_connections),
            "teacher_connections": len(teacher_manager.active_connections),
            "parent_connections": len(parent_manager.active_connections),
            "recent_activity": activity_list,
            "max_connections": 3000
        }
    finally:
        db.close()


@app.on_event("startup")
async def startup_event():
    """Start the periodic activity broadcast tasks for all roles"""
    asyncio.create_task(periodic_broadcast_students())
    asyncio.create_task(periodic_broadcast_teachers())
    asyncio.create_task(periodic_broadcast_parents())