"""
Chat Message Model - Store all SSE stream messages for replay
Allows users to see complete conversation history even after page refresh
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.base import Base


class ChatMessage(Base):
    """
    Stores every message sent via SSE during scan
    Enables chat history replay and debugging
    """
    __tablename__ = 'chat_messages'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = Column(String, ForeignKey('scans.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Message metadata
    message_type = Column(String, nullable=False, index=True)  # system, thought, plan, tool, output, analysis, decision
    content = Column(Text, nullable=False)  # The actual message content
    sequence = Column(Integer, nullable=False)  # Order of messages (1, 2, 3...)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Optional metadata (JSON stored as text)
    metadata_json = Column(Text, nullable=True)  # Additional context
    
    # Relationship
    scan = relationship("Scan", back_populates="chat_messages")
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('ix_chat_scan_sequence', 'scan_id', 'sequence'),
        Index('ix_chat_scan_created', 'scan_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ChatMessage(scan_id={self.scan_id}, type={self.message_type}, seq={self.sequence})>"
    
    def to_dict(self):
        """Convert to dict for API response"""
        return {
            'id': self.id,
            'scan_id': self.scan_id,
            'message_type': self.message_type,
            'content': self.content,
            'sequence': self.sequence,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'metadata': self.metadata_json
        }

