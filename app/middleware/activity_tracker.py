from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User
import logging

logger = logging.getLogger(__name__)

class ActivityTrackingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Only track activity for authenticated requests
        if hasattr(request.state, 'user_id'):
            try:
                db = next(get_db())
                db.query(User).filter(User.id == request.state.user_id).update({
                    'last_active': datetime.utcnow()
                })
                db.commit()
                db.close()
            except Exception as e:
                logger.error(f"Failed to update user activity: {e}")
        
        return response

def get_user_from_token(request: Request) -> int:
    """Extract user ID from JWT token in request headers"""
    try:
        from jose import jwt
        from app.core.config import settings
        
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
            
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return int(payload.get("sub"))
    except:
        return None

class EnhancedActivityTrackingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Try to get user ID from token before processing request
        user_id = get_user_from_token(request)
        if user_id:
            request.state.user_id = user_id
        
        response = await call_next(request)
        
        # Update last_active time after successful request
        if user_id:
            try:
                db = next(get_db())
                db.query(User).filter(User.id == user_id).update({
                    'last_active': datetime.utcnow()
                })
                db.commit()
                db.close()
            except Exception as e:
                logger.error(f"Failed to update user activity for user {user_id}: {e}")
        
        return response