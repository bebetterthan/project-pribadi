"""
Asset Model - Registered targets for scanning
"""
from sqlalchemy import Column, String, DateTime, Integer, Enum, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from app.db.base import Base


class TargetType(str, enum.Enum):
    """Type of scan target"""
    DOMAIN = "domain"
    IP = "ip"
    CIDR = "cidr"


class AssetCriticality(str, enum.Enum):
    """Business criticality of asset"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Asset(Base):
    """Registered asset (target) for scanning"""
    __tablename__ = 'assets'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    team_id = Column(String, ForeignKey('teams.id', ondelete='SET NULL'), nullable=True, index=True)  # Optional team ownership
    
    # Target information
    target = Column(String, nullable=False, index=True)  # domain/IP/CIDR
    target_type = Column(Enum(TargetType), nullable=False)
    display_name = Column(String, nullable=True)  # Human-friendly name
    description = Column(Text, nullable=True)
    
    # Classification
    criticality = Column(Enum(AssetCriticality), default=AssetCriticality.MEDIUM)
    tags = Column(String, nullable=True)  # Comma-separated tags
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    verification_status = Column(String, default="unverified")  # unverified, pending, verified
    
    # Statistics (denormalized for performance)
    scan_count = Column(Integer, default=0)
    last_scanned_at = Column(DateTime, nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="assets")
    team = relationship("Team", back_populates="assets")
    scans = relationship("Scan", back_populates="asset")
    
    # Indexes
    __table_args__ = (
        Index('ix_asset_user_created', 'user_id', 'created_at'),
        Index('ix_asset_target_type', 'target', 'target_type'),
    )
    
    def __repr__(self):
        return f"<Asset(target={self.target}, type={self.target_type})>"

