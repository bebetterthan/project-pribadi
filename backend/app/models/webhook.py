"""
Webhook Model - Event-driven integrations
FASE 5: Webhook system for external integrations
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, Index, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.base import Base


class Webhook(Base):
    """Webhook configuration"""
    __tablename__ = 'webhooks'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Webhook details
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)  # Target URL
    secret = Column(String, nullable=True)  # HMAC signature secret
    
    # Events to trigger on
    events = Column(JSON, nullable=False)  # Array of event types
    
    # Filtering
    filters = Column(JSON, nullable=True)  # Optional filters (e.g., only critical vulns)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Delivery settings
    retry_count = Column(Integer, default=3)
    timeout_seconds = Column(Integer, default=30)
    
    # Statistics
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    last_triggered_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_failure_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Webhook(name={self.name}, url={self.url})>"


class WebhookDelivery(Base):
    """Webhook delivery attempt log"""
    __tablename__ = 'webhook_deliveries'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    webhook_id = Column(String, ForeignKey('webhooks.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Delivery details
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    
    # Response
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Attempt tracking
    attempt_number = Column(Integer, default=1)
    success = Column(Boolean, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    delivered_at = Column(DateTime, nullable=True)
    
    # Relationships
    webhook = relationship("Webhook", back_populates="deliveries")
    
    # Indexes
    __table_args__ = (
        Index('ix_delivery_webhook_created', 'webhook_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<WebhookDelivery(webhook_id={self.webhook_id}, success={self.success})>"

