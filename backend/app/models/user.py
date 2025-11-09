"""
User Model - Authentication and multi-tenancy
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.base import Base


class User(Base):
    """User account for authentication and multi-tenancy"""
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    
    # Password hash (bcrypt or Argon2)
    hashed_password = Column(String, nullable=True)  # Nullable for now (add auth later)
    
    # Status & Role
    is_active = Column(Boolean, default=True, index=True)
    is_superuser = Column(Boolean, default=False)
    role = Column(String, default="user")  # admin, user, viewer
    
    # Preferences (JSON as text)
    notification_preferences = Column(Text, nullable=True)  # JSON string
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    
    # Relationships
    assets = relationship("Asset", back_populates="owner", cascade="all, delete-orphan")
    scans = relationship("Scan", back_populates="user")
    team_memberships = relationship("TeamMember", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("VulnerabilityComment", back_populates="user")
    
    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"

