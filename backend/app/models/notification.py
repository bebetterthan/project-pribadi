"""
Notification Model - Real-time notifications and alerts
FASE 5: Notification system
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, Index, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from app.db.base import Base


class NotificationType(str, enum.Enum):
    """Notification types"""
    SCAN_COMPLETED = "scan_completed"
    SCAN_FAILED = "scan_failed"
    CRITICAL_VULN = "critical_vulnerability"
    ASSIGNED = "assigned_to_vulnerability"
    MENTIONED = "mentioned_in_comment"
    STATUS_CHANGED = "vulnerability_status_changed"
    SCHEDULED_SCAN = "scheduled_scan_started"
    COMPARISON_READY = "comparison_ready"
    EXPORT_READY = "export_ready"
    SYSTEM_ALERT = "system_alert"


class NotificationChannel(str, enum.Enum):
    """Delivery channels"""
    IN_APP = "in_app"
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"


class Notification(Base):
    """User notification"""
    __tablename__ = 'notifications'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Notification details
    type = Column(Enum(NotificationType), nullable=False, index=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    
    # Associated resources
    resource_type = Column(String, nullable=True)  # scan, vulnerability, asset
    resource_id = Column(String, nullable=True, index=True)
    
    # Metadata
    data = Column(JSON, nullable=True)  # Additional context
    
    # Delivery
    channels = Column(JSON, nullable=True)  # Array of channels delivered to
    delivered_at = Column(JSON, nullable=True)  # Dict of channel: timestamp
    
    # Status
    is_read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime, nullable=True)
    
    # Priority
    priority = Column(String, default="normal")  # low, normal, high, urgent
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    
    # Indexes
    __table_args__ = (
        Index('ix_notif_user_unread', 'user_id', 'is_read', 'created_at'),
        Index('ix_notif_resource', 'resource_type', 'resource_id'),
    )
    
    def __repr__(self):
        return f"<Notification(type={self.type}, user_id={self.user_id}, read={self.is_read})>"

