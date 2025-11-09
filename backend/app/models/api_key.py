"""
API Key Model - Authentication for programmatic access
FASE 5: Public API with authentication
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Index, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid
import secrets
from app.db.base import Base


class APIKey(Base):
    """API Key for programmatic access"""
    __tablename__ = 'api_keys'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Key details
    name = Column(String, nullable=False)  # User-friendly name
    key_prefix = Column(String, nullable=False, index=True)  # First 8 chars (for display)
    key_hash = Column(String, nullable=False, unique=True, index=True)  # SHA256 hash
    
    # Permissions
    scopes = Column(Text, nullable=True)  # JSON array of permissions
    
    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=60)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Usage tracking
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Expiry
    expires_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    # Indexes
    __table_args__ = (
        Index('ix_apikey_user_active', 'user_id', 'is_active'),
    )
    
    @staticmethod
    def generate_key() -> tuple[str, str]:
        """
        Generate new API key
        Returns: (raw_key, key_hash)
        """
        # Generate random key
        raw_key = f"agp_{secrets.token_urlsafe(32)}"  # agp = Agent-P prefix
        
        # Hash for storage
        import hashlib
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        return raw_key, key_hash
    
    def is_expired(self) -> bool:
        """Check if key is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f"<APIKey(name={self.name}, prefix={self.key_prefix})>"

