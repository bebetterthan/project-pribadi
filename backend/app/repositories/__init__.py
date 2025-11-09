"""
Repository Layer - Data access abstraction
"""
from app.repositories.base import BaseRepository
from app.repositories.scan_repository import ScanRepository
from app.repositories.vulnerability_repository import VulnerabilityRepository

__all__ = [
    "BaseRepository",
    "ScanRepository",
    "VulnerabilityRepository",
]

