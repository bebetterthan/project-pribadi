"""
Notification Endpoints - In-app notifications and alerts
FASE 5: Real-time notification system
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.notification_manager import NotificationManager
from app.models import NotificationType
from app.utils.logger import logger

router = APIRouter()


@router.get("/")
async def get_notifications(
    unread_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get notifications for current user
    
    - **unread_only**: Only show unread notifications
    - **skip**: Pagination offset
    - **limit**: Max results to return
    """
    # TODO: Get current user from auth
    # For now, use default admin user
    from app.models import User
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    notification_manager = NotificationManager(db)
    notifications = notification_manager.get_notifications(
        user_id=user.id,
        unread_only=unread_only,
        skip=skip,
        limit=limit
    )
    
    unread_count = notification_manager.get_unread_count(user.id)
    
    return {
        "notifications": [
            {
                "id": n.id,
                "type": n.type.value,
                "title": n.title,
                "message": n.message,
                "resource_type": n.resource_type,
                "resource_id": n.resource_id,
                "data": n.data,
                "priority": n.priority,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
                "read_at": n.read_at.isoformat() if n.read_at else None
            }
            for n in notifications
        ],
        "total_unread": unread_count,
        "skip": skip,
        "limit": limit
    }


@router.get("/unread/count")
async def get_unread_count(db: Session = Depends(get_db)):
    """Get count of unread notifications"""
    from app.models import User
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    notification_manager = NotificationManager(db)
    count = notification_manager.get_unread_count(user.id)
    
    return {"unread_count": count}


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db)
):
    """Mark specific notification as read"""
    notification_manager = NotificationManager(db)
    notification = notification_manager.mark_as_read(notification_id)
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"success": True, "notification_id": notification_id}


@router.post("/read-all")
async def mark_all_read(db: Session = Depends(get_db)):
    """Mark all notifications as read"""
    from app.models import User
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    notification_manager = NotificationManager(db)
    count = notification_manager.mark_all_as_read(user.id)
    
    return {"success": True, "marked_read": count}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    db: Session = Depends(get_db)
):
    """Delete notification"""
    notification_manager = NotificationManager(db)
    success = notification_manager.delete_notification(notification_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"success": True, "notification_id": notification_id}

