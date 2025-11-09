"""
Database model for Scan Context storage
Phase 1, Day 1: Database Schema for Tool Chaining
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Index, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.db.base import Base


class FindingType(str, enum.Enum):
    """Types of findings that can be stored in scan context"""
    SUBDOMAIN = "subdomain"
    HTTP_SERVICE = "http_service"  
    PORT = "port"
    VULNERABILITY = "vulnerability"
    TECHNOLOGY = "technology"
    DIRECTORY = "directory"
    CREDENTIAL = "credential"
    SSL_INFO = "ssl_info"
    DNS_RECORD = "dns_record"
    METADATA = "metadata"  # For system/scan metadata


class ScanContext(Base):
    """
    Stores individual findings from tools for tool chaining.
    Each row is ONE finding (not batched) for granular querying.
    """
    __tablename__ = 'scan_contexts'
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key to scan
    scan_id = Column(String, ForeignKey('scans.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Tool that generated this finding
    tool_name = Column(String, nullable=False, index=True)
    
    # Type of finding
    finding_type = Column(Enum(FindingType), nullable=False, index=True)
    
    # Actual finding data (single finding as JSON)
    finding_data = Column(JSON, nullable=False)
    
    # Optional metadata about this finding (renamed from 'metadata' - SQLAlchemy reserved name)
    finding_metadata = Column(JSON, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship back to scan
    scan = relationship("Scan", back_populates="contexts")
    
    # Composite indexes for efficient tool chaining queries
    __table_args__ = (
        Index('idx_scan_tool_type', 'scan_id', 'tool_name', 'finding_type'),
        Index('idx_scan_finding_type', 'scan_id', 'finding_type'),
        Index('idx_tool_type_created', 'tool_name', 'finding_type', 'created_at'),
    )
    
    def __repr__(self):
        return (
            f"<ScanContext("
            f"scan_id={self.scan_id[:8]}..., "
            f"tool={self.tool_name}, "
            f"type={self.finding_type.value}"
            f")>"
        )

