from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import Base, SessionLocal
import json
import asyncio
from typing import Optional, Dict, Any


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    action = Column(String, index=True)  # CREATE, UPDATE, DELETE, LOGIN, etc.
    resource_type = Column(String, index=True)  # User, Student, Grade, etc.
    resource_id = Column(String, index=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    details = Column(Text, nullable=True)


class AuditLogger:
    @staticmethod
    async def log_action(
            user_id: str,
            action: str,
            resource_type: str,
            resource_id: str,
            old_values: Optional[Dict[str, Any]] = None,
            new_values: Optional[Dict[str, Any]] = None,
            ip_address: Optional[str] = None,
            user_agent: Optional[str] = None,
            details: Optional[str] = None
    ):
        """Log an action to audit trail"""
        import uuid

        db = SessionLocal()
        try:
            audit_entry = AuditLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                old_values=old_values,
                new_values=new_values,
                ip_address=ip_address,
                user_agent=user_agent,
                details=details
            )

            db.add(audit_entry)
            db.commit()
        except Exception as e:
            print(f"Audit logging failed: {e}")
        finally:
            db.close()

    @staticmethod
    def get_audit_logs(
            db: Session,
            user_id: Optional[str] = None,
            action: Optional[str] = None,
            resource_type: Optional[str] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            limit: int = 100
    ):
        """Retrieve audit logs with filters"""
        query = db.query(AuditLog)

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)

        return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()


# Decorator for automatic audit logging
def audit_action(action: str, resource_type: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract common parameters
            db = kwargs.get('db')
            current_user = kwargs.get('current_user') or kwargs.get('admin') or kwargs.get('teacher')

            # Execute the original function
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

            # Log the action
            if current_user and hasattr(result, 'id'):
                await AuditLogger.log_action(
                    user_id=current_user.id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=getattr(result, 'id', 'unknown')
                )

            return result

        return wrapper

    return decorator


# Convenience function for direct logging
async def log_action(user_id: str, action: str, resource_type: str, resource_id: str, **kwargs):
    """Simplified logging function"""
    await AuditLogger.log_action(user_id, action, resource_type, resource_id, **kwargs)


# Database change tracking middleware
class DatabaseAuditMiddleware:
    def __init__(self, db_session):
        self.db = db_session
        self._setup_event_listeners()

    def _setup_event_listeners(self):
        """Setup SQLAlchemy event listeners for automatic change tracking"""
        from sqlalchemy import event
        from app.models import User, Student, Teacher, Parent

        # Track changes to important models
        models_to_track = [User, Student, Teacher, Parent]

        for model in models_to_track:
            event.listen(model, 'after_insert', self._log_insert)
            event.listen(model, 'after_update', self._log_update)
            event.listen(model, 'after_delete', self._log_delete)

    def _log_insert(self, mapper, connection, target):
        """Log record creation"""
        asyncio.create_task(AuditLogger.log_action(
            user_id="system",
            action="CREATE",
            resource_type=target.__class__.__name__,
            resource_id=str(target.id),
            new_values=self._serialize_model(target)
        ))

    def _log_update(self, mapper, connection, target):
        """Log record updates"""
        # Get old values from session
        old_values = {}
        for attr in mapper.attrs:
            hist = attr.load_history(target)
            if hist.has_changes():
                old_values[attr.key] = hist.deleted[0] if hist.deleted else None

        asyncio.create_task(AuditLogger.log_action(
            user_id="system",
            action="UPDATE",
            resource_type=target.__class__.__name__,
            resource_id=str(target.id),
            old_values=old_values,
            new_values=self._serialize_model(target)
        ))

    def _log_delete(self, mapper, connection, target):
        """Log record deletion"""
        asyncio.create_task(AuditLogger.log_action(
            user_id="system",
            action="DELETE",
            resource_type=target.__class__.__name__,
            resource_id=str(target.id),
            old_values=self._serialize_model(target)
        ))

    def _serialize_model(self, obj):
        """Convert model instance to JSON-serializable dict"""
        result = {}
        for column in obj.__table__.columns:
            value = getattr(obj, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = str(value) if value is not None else None
        return result