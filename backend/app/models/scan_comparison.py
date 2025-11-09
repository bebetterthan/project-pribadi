"""
Scan Comparison Model - Track changes between scans
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, JSON, Index, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.base import Base


class ScanComparison(Base):
    """Comparison between two scan runs"""
    __tablename__ = 'scan_comparisons'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(String, ForeignKey('assets.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Scans being compared
    baseline_scan_id = Column(String, ForeignKey('scans.id', ondelete='CASCADE'), nullable=False)
    current_scan_id = Column(String, ForeignKey('scans.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Comparison metadata
    comparison_type = Column(String, default="auto")  # auto, manual
    changes_detected = Column(Boolean, default=False)
    
    # Comparison results (JSON structure)
    summary = Column(JSON, nullable=False)  # Detailed changes
    
    # Creator
    created_by = Column(String, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    asset = relationship("Asset")
    baseline_scan = relationship("Scan", foreign_keys=[baseline_scan_id])
    current_scan = relationship("Scan", foreign_keys=[current_scan_id])
    creator = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('ix_comparison_asset_created', 'asset_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ScanComparison(asset_id={self.asset_id}, changes={self.changes_detected})>"

