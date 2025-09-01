from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, UserActivity
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.max_connections = 3000
    
    async def connect(self, websocket: WebSocket, user_id: int):
        if len(self.active_connections) >= self.max_connections:
            await websocket.close(code=1008, reason="Connection limit reached")
            return False
        
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected for user {user_id}")
        return True
    
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(message)
            except:
                self.disconnect(user_id)
    
    async def broadcast_activity_data_by_role(self, role: str):
        if not self.active_connections:
            return
        
        try:
            db = next(get_db())
            
            # Query users with their activity data
            query = db.query(User, UserActivity).outerjoin(
                UserActivity, User.id == UserActivity.user_id
            ).filter(
                User.is_active == True,
                User.role == role
            )
            
            current_time = datetime.utcnow()
            activity_data = []
            
            for user, activity in query:
                # Get last_active from database
                last_active = activity.last_active if activity else None
                
                # Calculate if user is online (active within 30 seconds)
                is_online = False
                if last_active:
                    time_diff = (current_time - last_active).total_seconds()
                    is_online = time_diff <= 30
                
                activity_data.append({
                    "user_id": user.id,
                    "phone": user.phone,
                    "last_active": last_active.isoformat() if last_active else None,
                    "is_online": is_online,
                    "role": user.role,
                    "full_name": user.full_name
                })
            
            message = json.dumps({
                "type": f"{role}_activity_update",
                "data": activity_data,
                "timestamp": current_time.isoformat(),
                "total_users": len(activity_data),
                "online_users": len([u for u in activity_data if u["is_online"]])
            })
            
            disconnected_users = []
            for user_id, websocket in self.active_connections.items():
                try:
                    await websocket.send_text(message)
                except:
                    disconnected_users.append(user_id)
            
            for user_id in disconnected_users:
                self.disconnect(user_id)
                
            db.close()
            
        except Exception as e:
            logger.error(f"Error broadcasting {role} activity data: {e}")
    
    async def broadcast_activity_data(self):
        # Keep old method for compatibility
        await self.broadcast_activity_data_by_role("student")

student_manager = WebSocketManager()
teacher_manager = WebSocketManager()
parent_manager = WebSocketManager()

async def periodic_broadcast_students():
    while True:
        await student_manager.broadcast_activity_data_by_role("student")
        await asyncio.sleep(10)

async def periodic_broadcast_teachers():
    while True:
        await teacher_manager.broadcast_activity_data_by_role("teacher")
        await asyncio.sleep(10)

async def periodic_broadcast_parents():
    while True:
        await parent_manager.broadcast_activity_data_by_role("parent")
        await asyncio.sleep(10)