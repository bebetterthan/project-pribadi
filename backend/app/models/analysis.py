from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.base import Base


class AIAnalysis(Base):
    __tablename__ = 'ai_analyses'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = Column(String, ForeignKey('scans.id'), unique=True)

    model_used = Column(String, nullable=False)  # 'gemini-1.5-flash-002'
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    cost_usd = Column(Float, nullable=False)  # Estimated cost

    # NEW: Store the actual prompt sent to AI
    prompt_text = Column(Text, nullable=True)  # Full prompt for transparency
    analysis_text = Column(Text, nullable=False)  # Full markdown output

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    scan = relationship("Scan", back_populates="analysis")
