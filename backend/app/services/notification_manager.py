"""
Notification Manager - Complete notification delivery system
FASE 5: Real-time notifications and alerts
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import Notification, NotificationType, NotificationChannel, User
from app.utils.logger import logger
from datetime import datetime
import json
import uuid


class NotificationManager:
    """
    Centralized notification management
    Handles creation, delivery, and tracking across multiple channels
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def send_notification(
        self,
        user_id: str,
        type: NotificationType,
        title: str,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        channels: Optional[List[NotificationChannel]] = None
    ) -> Notification:
        """
        Send notification to user across specified channels
        
        Args:
            user_id: Target user ID
            type: Notification type enum
            title: Notification title
            message: Notification message body
            resource_type: Optional resource type (scan, vulnerability, etc.)
            resource_id: Optional resource ID
            data: Optional additional data
            priority: Priority level (low, normal, high, urgent)
            channels: Channels to deliver to (default: in_app only)
        
        Returns:
            Created Notification object
        """
        # Default to in-app only if not specified
        if channels is None:
            channels = [NotificationChannel.IN_APP]
        
        # Create notification record
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            resource_type=resource_type,
            resource_id=resource_id,
            data=data,
            priority=priority,
            channels=[c.value for c in channels],
            delivered_at={}
        )
        
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        
        logger.info(f"[Notification] Created {type.value} for user {user_id}")
        
        # Deliver to each channel
        for channel in channels:
            try:
                await self._deliver_to_channel(notification, channel)
            except Exception as e:
                logger.error(f"[Notification] Failed to deliver to {channel.value}: {e}")
        
        return notification
    
    async def _deliver_to_channel(self, notification: Notification, channel: NotificationChannel):
        """Deliver notification to specific channel"""
        if channel == NotificationChannel.IN_APP:
            # In-app is already created in database
            notification.delivered_at[channel.value] = datetime.utcnow().isoformat()
            self.db.commit()
            logger.debug(f"[Notification] Delivered to in-app: {notification.id}")
        
        elif channel == NotificationChannel.EMAIL:
            await self._send_email(notification)
        
        elif channel == NotificationChannel.SLACK:
            await self._send_slack(notification)
        
        elif channel == NotificationChannel.WEBHOOK:
            await self._send_webhook(notification)
    
    async def _send_email(self, notification: Notification):
        """Send email notification"""
        # Get user email
        user = self.db.query(User).filter(User.id == notification.user_id).first()
        if not user or not user.email:
            logger.warning(f"[Notification] No email for user {notification.user_id}")
            return
        
        # TODO: Integrate with email service (SMTP, SendGrid, etc.)
        # For now, just log
        logger.info(f"[Notification] Email to {user.email}: {notification.title}")
        
        # Mark as delivered
        if notification.delivered_at is None:
            notification.delivered_at = {}
        notification.delivered_at[NotificationChannel.EMAIL.value] = datetime.utcnow().isoformat()
        self.db.commit()
    
    async def _send_slack(self, notification: Notification):
        """Send Slack notification"""
        # TODO: Integrate with Slack webhook
        logger.info(f"[Notification] Slack: {notification.title}")
        
        if notification.delivered_at is None:
            notification.delivered_at = {}
        notification.delivered_at[NotificationChannel.SLACK.value] = datetime.utcnow().isoformat()
        self.db.commit()
    
    async def _send_webhook(self, notification: Notification):
        """Send webhook notification"""
        # TODO: Integrate with webhook system
        logger.info(f"[Notification] Webhook: {notification.title}")
        
        if notification.delivered_at is None:
            notification.delivered_at = {}
        notification.delivered_at[NotificationChannel.WEBHOOK.value] = datetime.utcnow().isoformat()
        self.db.commit()
    
    def mark_as_read(self, notification_id: str) -> Optional[Notification]:
        """Mark notification as read"""
        notification = self.db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            return None
        
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(notification)
        
        logger.debug(f"[Notification] Marked as read: {notification_id}")
        return notification
    
    def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications as read for user"""
        count = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .update({"is_read": True, "read_at": datetime.utcnow()})
        )
        self.db.commit()
        
        logger.info(f"[Notification] Marked {count} notifications as read for user {user_id}")
        return count
    
    def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications"""
        return (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .count()
        )
    
    def get_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50
    ) -> List[Notification]:
        """Get notifications for user"""
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    
    def delete_notification(self, notification_id: str) -> bool:
        """Delete notification"""
        notification = self.db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            return False
        
        self.db.delete(notification)
        self.db.commit()
        
        logger.debug(f"[Notification] Deleted: {notification_id}")
        return True
    
    # === Convenience methods for common notification types ===
    
    async def notify_scan_completed(
        self,
        user_id: str,
        scan_id: str,
        target: str,
        findings_count: int,
        critical_count: int = 0
    ):
        """Notify user that scan completed"""
        message = f"Scan of {target} completed. Found {findings_count} findings"
        if critical_count > 0:
            message += f" ({critical_count} critical)"
        
        await self.send_notification(
            user_id=user_id,
            type=NotificationType.SCAN_COMPLETED,
            title=f"Scan Completed: {target}",
            message=message,
            resource_type="scan",
            resource_id=scan_id,
            data={
                "target": target,
                "findings_count": findings_count,
                "critical_count": critical_count
            },
            priority="normal" if critical_count == 0 else "high"
        )
    
    async def notify_critical_vulnerability(
        self,
        user_id: str,
        vuln_id: str,
        cve_id: Optional[str],
        title: str,
        affected_url: str
    ):
        """Notify user of critical vulnerability"""
        message = f"Critical vulnerability discovered: {title}"
        if cve_id:
            message = f"{cve_id}: {message}"
        
        await self.send_notification(
            user_id=user_id,
            type=NotificationType.CRITICAL_VULN,
            title="⚠️ Critical Vulnerability Detected",
            message=message,
            resource_type="vulnerability",
            resource_id=vuln_id,
            data={
                "cve_id": cve_id,
                "title": title,
                "affected_url": affected_url
            },
            priority="urgent",
            channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL]
        )
    
    async def notify_assigned(
        self,
        user_id: str,
        vuln_id: str,
        title: str,
        assigned_by_username: str
    ):
        """Notify user they were assigned a vulnerability"""
        await self.send_notification(
            user_id=user_id,
            type=NotificationType.ASSIGNED,
            title="Assigned to Vulnerability",
            message=f"{assigned_by_username} assigned you to: {title}",
            resource_type="vulnerability",
            resource_id=vuln_id,
            data={
                "assigned_by": assigned_by_username,
                "title": title
            },
            priority="normal"
        )
    
    async def notify_status_changed(
        self,
        user_id: str,
        vuln_id: str,
        title: str,
        old_status: str,
        new_status: str,
        changed_by_username: str
    ):
        """Notify user of vulnerability status change"""
        await self.send_notification(
            user_id=user_id,
            type=NotificationType.STATUS_CHANGED,
            title="Vulnerability Status Changed",
            message=f"{changed_by_username} changed status of '{title}' from {old_status} to {new_status}",
            resource_type="vulnerability",
            resource_id=vuln_id,
            data={
                "old_status": old_status,
                "new_status": new_status,
                "changed_by": changed_by_username
            },
            priority="low"
        )

