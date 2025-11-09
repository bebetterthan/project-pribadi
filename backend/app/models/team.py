"""
Team/Workspace Model - Team collaboration and multi-tenancy
FASE 5: Team collaboration infrastructure
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Index, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.base import Base


class Team(Base):
    """Team/Workspace for multi-user collaboration"""
    __tablename__ = 'teams'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)  # URL-friendly identifier
    description = Column(Text, nullable=True)
    
    # Settings
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="team")
    
    def __repr__(self):
        return f"<Team(name={self.name}, slug={self.slug})>"


class TeamMember(Base):
    """Team membership with role-based access"""
    __tablename__ = 'team_members'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    team_id = Column(String, ForeignKey('teams.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Role in team
    role = Column(String, nullable=False, default="member")  # owner, admin, member, viewer
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")
    
    # Indexes
    __table_args__ = (
        Index('ix_team_member_unique', 'team_id', 'user_id', unique=True),
    )
    
    def __repr__(self):
        return f"<TeamMember(team_id={self.team_id}, user_id={self.user_id}, role={self.role})>"

