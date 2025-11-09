from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.base import Base


class ScanResult(Base):
    __tablename__ = 'scan_results'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = Column(String, ForeignKey('scans.id'), nullable=False)

    tool_name = Column(String, nullable=False)  # "nmap", "nuclei", etc.

    raw_output = Column(Text, nullable=False)  # Full stdout
    parsed_output = Column(JSON, nullable=True)  # Structured data

    exit_code = Column(Integer, nullable=False)
    execution_time = Column(Float, nullable=False)  # Seconds
    error_message = Column(Text, nullable=True)  # stderr if failed

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    scan = relationship("Scan", back_populates="results")
