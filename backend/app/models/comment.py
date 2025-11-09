"""
Comment Model - Team collaboration on vulnerabilities
FASE 5: Team collaboration features
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.base import Base


class VulnerabilityComment(Base):
    """Comment on vulnerability for team collaboration"""
    __tablename__ = 'vulnerability_comments'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    vulnerability_id = Column(String, ForeignKey('vulnerabilities.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Comment content
    content = Column(Text, nullable=False)
    
    # Mentions (for notifications)
    mentions = Column(Text, nullable=True)  # JSON array of user_ids
    
    # Thread support
    parent_id = Column(String, ForeignKey('vulnerability_comments.id', ondelete='CASCADE'), nullable=True)
    
    # Edit tracking
    edited_at = Column(DateTime, nullable=True)
    is_edited = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    vulnerability = relationship("Vulnerability", back_populates="comments")
    user = relationship("User", back_populates="comments")
    replies = relationship("VulnerabilityComment", backref="parent", remote_side=[id])
    
    # Indexes
    __table_args__ = (
        Index('ix_comment_vuln_created', 'vulnerability_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<VulnerabilityComment(vuln_id={self.vulnerability_id}, user_id={self.user_id})>"

