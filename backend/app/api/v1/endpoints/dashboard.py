"""
Dashboard Endpoints - Rich statistics and activity feeds
FASE 5: Production-grade dashboard APIs
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.db.session import get_db
from app.models import (
    Scan, ScanStatus, Vulnerability, VulnerabilitySeverity, VulnerabilityStatus,
    Asset, User, ScanResult
)
from app.utils.logger import logger
from datetime import datetime, timedelta
from typing import Optional

router = APIRouter()


@router.get("/overview")
async def get_dashboard_overview(db: Session = Depends(get_db)):
    """
    Get complete dashboard overview with all key metrics
    
    Returns comprehensive statistics for dashboard display
    """
    # === SCAN STATISTICS ===
    total_scans = db.query(Scan).count()
    completed_scans = db.query(Scan).filter(Scan.status == ScanStatus.COMPLETED).count()
    running_scans = db.query(Scan).filter(Scan.status == ScanStatus.RUNNING).count()
    failed_scans = db.query(Scan).filter(Scan.status == ScanStatus.FAILED).count()
    
    # Scans in last 24 hours
    last_24h = datetime.utcnow() - timedelta(hours=24)
    scans_last_24h = db.query(Scan).filter(Scan.created_at >= last_24h).count()
    
    # Scans in last 7 days
    last_7d = datetime.utcnow() - timedelta(days=7)
    scans_last_7d = db.query(Scan).filter(Scan.created_at >= last_7d).count()
    
    # === VULNERABILITY STATISTICS ===
    total_vulns = db.query(Vulnerability).count()
    
    # By severity
    critical_vulns = db.query(Vulnerability).filter(
        Vulnerability.severity == VulnerabilitySeverity.CRITICAL
    ).count()
    high_vulns = db.query(Vulnerability).filter(
        Vulnerability.severity == VulnerabilitySeverity.HIGH
    ).count()
    medium_vulns = db.query(Vulnerability).filter(
        Vulnerability.severity == VulnerabilitySeverity.MEDIUM
    ).count()
    low_vulns = db.query(Vulnerability).filter(
        Vulnerability.severity == VulnerabilitySeverity.LOW
    ).count()
    
    # By status
    open_vulns = db.query(Vulnerability).filter(
        Vulnerability.status == VulnerabilityStatus.OPEN
    ).count()
    fixing_vulns = db.query(Vulnerability).filter(
        Vulnerability.status == VulnerabilityStatus.FIXING
    ).count()
    fixed_vulns = db.query(Vulnerability).filter(
        Vulnerability.status == VulnerabilityStatus.FIXED
    ).count()
    
    # === ASSET STATISTICS ===
    total_assets = db.query(Asset).count()
    active_assets = db.query(Asset).filter(Asset.is_active == True).count()
    
    # === TOP VULNERABLE ASSETS ===
    top_vulnerable_assets = (
        db.query(
            Asset.id,
            Asset.target,
            Asset.display_name,
            func.count(Vulnerability.id).label('vuln_count')
        )
        .join(Scan, Asset.id == Scan.asset_id)
        .join(Vulnerability, Scan.id == Vulnerability.scan_id)
        .filter(Vulnerability.status != VulnerabilityStatus.FIXED)
        .group_by(Asset.id, Asset.target, Asset.display_name)
        .order_by(desc('vuln_count'))
        .limit(5)
        .all()
    )
    
    # === RECENT ACTIVITY ===
    recent_scans = (
        db.query(Scan)
        .order_by(Scan.created_at.desc())
        .limit(10)
        .all()
    )
    
    return {
        "scans": {
            "total": total_scans,
            "completed": completed_scans,
            "running": running_scans,
            "failed": failed_scans,
            "last_24h": scans_last_24h,
            "last_7d": scans_last_7d,
            "success_rate": round(completed_scans / total_scans * 100, 1) if total_scans > 0 else 0
        },
        "vulnerabilities": {
            "total": total_vulns,
            "by_severity": {
                "critical": critical_vulns,
                "high": high_vulns,
                "medium": medium_vulns,
                "low": low_vulns
            },
            "by_status": {
                "open": open_vulns,
                "fixing": fixing_vulns,
                "fixed": fixed_vulns
            },
            "open_critical": db.query(Vulnerability).filter(
                Vulnerability.severity == VulnerabilitySeverity.CRITICAL,
                Vulnerability.status == VulnerabilityStatus.OPEN
            ).count()
        },
        "assets": {
            "total": total_assets,
            "active": active_assets,
            "top_vulnerable": [
                {
                    "asset_id": a.id,
                    "target": a.target,
                    "display_name": a.display_name,
                    "open_vulnerabilities": a.vuln_count
                }
                for a in top_vulnerable_assets
            ]
        },
        "recent_activity": [
            {
                "scan_id": s.id,
                "target": s.target,
                "status": s.status.value,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None
            }
            for s in recent_scans
        ]
    }


@router.get("/trends")
async def get_trends(
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """
    Get trends over time (scans, vulnerabilities discovered)
    
    - **days**: Number of days to analyze (1-90)
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Scans per day
    scans_per_day = (
        db.query(
            func.date(Scan.created_at).label('date'),
            func.count(Scan.id).label('count')
        )
        .filter(Scan.created_at >= cutoff_date)
        .group_by(func.date(Scan.created_at))
        .order_by('date')
        .all()
    )
    
    # Vulnerabilities discovered per day
    vulns_per_day = (
        db.query(
            func.date(Vulnerability.discovered_at).label('date'),
            func.count(Vulnerability.id).label('count')
        )
        .filter(Vulnerability.discovered_at >= cutoff_date)
        .group_by(func.date(Vulnerability.discovered_at))
        .order_by('date')
        .all()
    )
    
    return {
        "period_days": days,
        "scans_over_time": [
            {"date": str(row.date), "count": row.count}
            for row in scans_per_day
        ],
        "vulnerabilities_over_time": [
            {"date": str(row.date), "count": row.count}
            for row in vulns_per_day
        ]
    }


@router.get("/activity-feed")
async def get_activity_feed(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get recent activity feed (scans, vulnerabilities, status changes)
    
    Returns chronological feed of important events
    """
    activities = []
    
    # Recent scans
    recent_scans = (
        db.query(Scan)
        .filter(Scan.status.in_([ScanStatus.COMPLETED, ScanStatus.FAILED]))
        .order_by(Scan.created_at.desc())
        .limit(limit // 2)
        .all()
    )
    
    for scan in recent_scans:
        activities.append({
            "type": "scan_completed" if scan.status == ScanStatus.COMPLETED else "scan_failed",
            "timestamp": scan.completed_at or scan.created_at,
            "data": {
                "scan_id": scan.id,
                "target": scan.target,
                "status": scan.status.value,
                "duration_seconds": scan.duration_seconds
            }
        })
    
    # Recent critical vulnerabilities
    recent_critical_vulns = (
        db.query(Vulnerability)
        .filter(Vulnerability.severity == VulnerabilitySeverity.CRITICAL)
        .order_by(Vulnerability.discovered_at.desc())
        .limit(limit // 2)
        .all()
    )
    
    for vuln in recent_critical_vulns:
        activities.append({
            "type": "critical_vulnerability",
            "timestamp": vuln.discovered_at,
            "data": {
                "vulnerability_id": vuln.id,
                "cve_id": vuln.cve_id,
                "title": vuln.title,
                "severity": vuln.severity.value,
                "affected_host": vuln.affected_host
            }
        })
    
    # Sort by timestamp descending
    activities.sort(key=lambda x: x['timestamp'] if x['timestamp'] else datetime.min, reverse=True)
    
    # Format timestamps
    for activity in activities:
        if activity['timestamp']:
            activity['timestamp'] = activity['timestamp'].isoformat()
    
    return {
        "activities": activities[:limit]
    }


@router.get("/tool-performance")
async def get_tool_performance(db: Session = Depends(get_db)):
    """Get performance metrics for each security tool"""
    tool_stats = (
        db.query(
            ScanResult.tool_name,
            func.count(ScanResult.id).label('total_runs'),
            func.avg(ScanResult.execution_time_seconds).label('avg_duration'),
            func.sum(func.case((ScanResult.exit_code == 0, 1), else_=0)).label('success_count')
        )
        .group_by(ScanResult.tool_name)
        .all()
    )
    
    return {
        "tools": [
            {
                "tool_name": row.tool_name,
                "total_runs": row.total_runs,
                "avg_duration_seconds": round(row.avg_duration, 2) if row.avg_duration else 0,
                "success_count": row.success_count,
                "success_rate": round(row.success_count / row.total_runs * 100, 1) if row.total_runs > 0 else 0
            }
            for row in tool_stats
        ]
    }

