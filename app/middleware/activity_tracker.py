from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

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
        
        # Update activity in database after successful request
        if user_id:
            try:
                from app.database import get_db
                from app.models.models import UserActivity, User
                
                db = next(get_db())
                
                # Get user info
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    # Update or create activity record
                    activity = db.query(UserActivity).filter(UserActivity.user_id == user_id).first()
                    if activity:
                        activity.last_active = datetime.utcnow()
                        activity.phone = user.phone
                    else:
                        activity = UserActivity(
                            user_id=user_id,
                            phone=user.phone,
                            last_active=datetime.utcnow()
                        )
                        db.add(activity)
                    
                    db.commit()
                db.close()
                
            except Exception as e:
                logger.error(f"Failed to update user activity for user {user_id}: {e}")
        
        return response