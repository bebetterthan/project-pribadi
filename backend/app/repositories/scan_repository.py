"""
Scan Repository - Specialized operations for scans
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from datetime import datetime
from app.models import Scan, ScanStatus
from app.repositories.base import BaseRepository


class ScanRepository(BaseRepository[Scan]):
    """Repository for Scan operations"""
    
    def __init__(self, db: Session):
        super().__init__(Scan, db)
    
    def get_with_relations(self, scan_id: str) -> Optional[Scan]:
        """Get scan with all relationships loaded"""
        return (
            self.db.query(Scan)
            .filter(Scan.id == scan_id)
            .options(
                joinedload(Scan.user),
                joinedload(Scan.asset),
                joinedload(Scan.results),
                joinedload(Scan.analysis),
            )
            .first()
        )
    
    def get_user_scans(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
        status: Optional[ScanStatus] = None
    ) -> List[Scan]:
        """Get scans for specific user"""
        query = self.db.query(Scan).filter(Scan.user_id == user_id)
        
        if status:
            query = query.filter(Scan.status == status)
        
        return query.order_by(desc(Scan.created_at)).offset(skip).limit(limit).all()
    
    def get_asset_scans(
        self,
        asset_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Scan]:
        """Get scans for specific asset"""
        return (
            self.db.query(Scan)
            .filter(Scan.asset_id == asset_id)
            .order_by(desc(Scan.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_running_scans(self) -> List[Scan]:
        """Get all currently running scans"""
        return (
            self.db.query(Scan)
            .filter(Scan.status == ScanStatus.RUNNING)
            .order_by(Scan.started_at)
            .all()
        )
    
    def get_latest_completed_scan(self, asset_id: str, before_scan_id: Optional[str] = None) -> Optional[Scan]:
        """Get most recent completed scan for an asset (optionally before a specific scan)"""
        query = (
            self.db.query(Scan)
            .filter(Scan.asset_id == asset_id)
            .filter(Scan.status == ScanStatus.COMPLETED)
        )
        
        if before_scan_id:
            # Get the created_at of the reference scan
            ref_scan = self.get(before_scan_id)
            if ref_scan:
                query = query.filter(Scan.created_at < ref_scan.created_at)
        
        return query.order_by(desc(Scan.completed_at)).first()
    
    def update_status(self, scan_id: str, status: ScanStatus, **kwargs) -> Optional[Scan]:
        """Update scan status and optional fields"""
        scan = self.get(scan_id)
        if not scan:
            return None
        
        scan.status = status
        
        # Update timestamps based on status
        if status == ScanStatus.RUNNING and not scan.started_at:
            scan.started_at = datetime.utcnow()
        elif status in [ScanStatus.COMPLETED, ScanStatus.FAILED]:
            scan.completed_at = datetime.utcnow()
            if scan.started_at:
                scan.duration_seconds = int((scan.completed_at - scan.started_at).total_seconds())
        
        # Update additional fields
        for key, value in kwargs.items():
            if hasattr(scan, key):
                setattr(scan, key, value)
        
        self.db.commit()
        self.db.refresh(scan)
        return scan
    
    def update_summary(self, scan_id: str, summary: Dict[str, Any]) -> Optional[Scan]:
        """Update scan summary (denormalized stats)"""
        scan = self.get(scan_id)
        if not scan:
            return None
        
        scan.summary = summary
        self.db.commit()
        self.db.refresh(scan)
        return scan
    
    def get_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get scan statistics"""
        query = self.db.query(Scan)
        
        if user_id:
            query = query.filter(Scan.user_id == user_id)
        
        total = query.count()
        completed = query.filter(Scan.status == ScanStatus.COMPLETED).count()
        running = query.filter(Scan.status == ScanStatus.RUNNING).count()
        failed = query.filter(Scan.status == ScanStatus.FAILED).count()
        
        # Average duration for completed scans
        avg_duration = self.db.query(func.avg(Scan.duration_seconds)).filter(
            Scan.status == ScanStatus.COMPLETED,
            Scan.duration_seconds.isnot(None)
        )
        
        if user_id:
            avg_duration = avg_duration.filter(Scan.user_id == user_id)
        
        avg_duration_result = avg_duration.scalar()
        
        return {
            "total_scans": total,
            "completed": completed,
            "running": running,
            "failed": failed,
            "pending": total - completed - running - failed,
            "average_duration_seconds": int(avg_duration_result) if avg_duration_result else 0,
        }

