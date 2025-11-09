from sqlalchemy import Column, String, DateTime, Enum, JSON, ForeignKey, Integer, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from app.db.base import Base


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Scan(Base):
    __tablename__ = 'scans'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Multi-tenancy (link to user and asset)
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)  # Nullable for backward compat
    asset_id = Column(String, ForeignKey('assets.id', ondelete='CASCADE'), nullable=True, index=True)  # Nullable for backward compat
    
    # Target (snapshot at scan time for historical accuracy)
    target = Column(String, nullable=False, index=True)
    target_snapshot = Column(String, nullable=True)  # Preserved target value

    # AI Agent fields
    user_prompt = Column(String, nullable=True)  # User's objective/instruction
    ai_strategy = Column(JSON, nullable=True)  # AI's tool selection & reasoning
    agent_thoughts = Column(JSON, nullable=True)  # AI's thought process (ReAct chain)

    tools = Column(JSON, nullable=False)  # ["nmap", "nuclei", "whatweb"]
    profile = Column(String, nullable=False)  # "quick", "normal", "aggressive"

    status = Column(Enum(ScanStatus), default=ScanStatus.PENDING, index=True)
    current_tool = Column(String, nullable=True)  # For progress tracking
    progress_message = Column(String, nullable=True)  # Real-time progress updates for SSE
    progress_metadata = Column(JSON, nullable=True)  # Additional progress data

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)  # Calculated duration
    error_message = Column(String, nullable=True)
    
    # Summary (denormalized for list performance)
    summary = Column(JSON, nullable=True)  # Quick stats for list views

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="scans")
    asset = relationship("Asset", back_populates="scans")
    results = relationship("ScanResult", back_populates="scan", cascade="all, delete-orphan")
    analysis = relationship("AIAnalysis", back_populates="scan", uselist=False, cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="scan", cascade="all, delete-orphan", order_by="ChatMessage.sequence")
    vulnerabilities = relationship("Vulnerability", back_populates="scan", cascade="all, delete-orphan")
    contexts = relationship("ScanContext", back_populates="scan", cascade="all, delete-orphan")  # NEW: For tool chaining
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_scan_user_created', 'user_id', 'created_at'),
        Index('ix_scan_asset_created', 'asset_id', 'created_at'),
    )
