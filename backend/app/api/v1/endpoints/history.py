"""
History Endpoints - View past scans, chat history, and results
FASE 4: Historical viewing with complete persistence
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.repositories.scan_repository import ScanRepository
from app.repositories.vulnerability_repository import VulnerabilityRepository
from app.services.comparison_engine import ComparisonEngine
from app.models import Scan, ScanStatus, VulnerabilitySeverity, VulnerabilityStatus
from app.utils.logger import logger
from datetime import datetime

router = APIRouter()


# ===========================
# SCAN HISTORY ENDPOINTS
# ===========================

@router.get("/scans")
async def list_scans(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[ScanStatus] = None,
    db: Session = Depends(get_db)
):
    """
    List all scans with pagination and filtering
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Number of records to return (max 100)
    - **status**: Filter by scan status
    """
    scan_repo = ScanRepository(db)
    
    # Get scans with basic info
    filters = {}
    if status:
        filters["status"] = status
    
    scans = scan_repo.get_multi(
        skip=skip,
        limit=limit,
        order_by="created_at",
        order_dir="desc",
        filters=filters
    )
    
    # Convert to response format
    scan_list = []
    for scan in scans:
        scan_data = {
            "id": scan.id,
            "target": scan.target,
            "status": scan.status.value,
            "profile": scan.profile,
            "created_at": scan.created_at.isoformat() if scan.created_at else None,
            "started_at": scan.started_at.isoformat() if scan.started_at else None,
            "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
            "duration_seconds": scan.duration_seconds,
            "summary": scan.summary,
            "tools": scan.tools
        }
        scan_list.append(scan_data)
    
    # Get total count for pagination
    total = scan_repo.count(filters=filters)
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "scans": scan_list
    }


@router.get("/scans/{scan_id}")
async def get_scan_detail(
    scan_id: str,
    db: Session = Depends(get_db)
):
    """
    Get complete details of a specific scan
    
    Includes:
    - Scan metadata
    - Summary statistics
    - Tool list
    - Agent strategy
    """
    scan_repo = ScanRepository(db)
    scan = scan_repo.get_with_relations(scan_id)
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return {
        "id": scan.id,
        "target": scan.target,
        "status": scan.status.value,
        "profile": scan.profile,
        "user_prompt": scan.user_prompt,
        "ai_strategy": scan.ai_strategy,
        "tools": scan.tools,
        "created_at": scan.created_at.isoformat() if scan.created_at else None,
        "started_at": scan.started_at.isoformat() if scan.started_at else None,
        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
        "duration_seconds": scan.duration_seconds,
        "summary": scan.summary,
        "error_message": scan.error_message
    }


@router.get("/scans/{scan_id}/chat")
async def get_scan_chat_history(
    scan_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    message_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get complete chat history for a scan
    
    Returns all agent thoughts, tool executions, and system messages in chronological order
    
    - **skip**: Number of messages to skip
    - **limit**: Number of messages to return (max 500)
    - **message_type**: Filter by message type (thought, tool, output, system, analysis, decision)
    """
    scan_repo = ScanRepository(db)
    scan = scan_repo.get(scan_id)
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Query chat messages
    from app.models.chat_message import ChatMessage
    query = db.query(ChatMessage).filter(ChatMessage.scan_id == scan_id)
    
    if message_type:
        query = query.filter(ChatMessage.message_type == message_type)
    
    query = query.order_by(ChatMessage.sequence)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    messages = query.offset(skip).limit(limit).all()
    
    # Convert to response
    message_list = [msg.to_dict() for msg in messages]
    
    return {
        "scan_id": scan_id,
        "total": total,
        "skip": skip,
        "limit": limit,
        "messages": message_list
    }


@router.get("/scans/{scan_id}/results")
async def get_scan_results(
    scan_id: str,
    tool_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all tool results for a scan
    
    - **tool_name**: Filter results by specific tool (nmap, nuclei, etc.)
    """
    scan_repo = ScanRepository(db)
    scan = scan_repo.get(scan_id)
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    from app.models.result import ScanResult
    query = db.query(ScanResult).filter(ScanResult.scan_id == scan_id)
    
    if tool_name:
        query = query.filter(ScanResult.tool_name == tool_name)
    
    results = query.order_by(ScanResult.created_at).all()
    
    result_list = []
    for result in results:
        result_data = {
            "id": result.id,
            "tool_name": result.tool_name,
            "exit_code": result.exit_code,
            "execution_time": result.execution_time,
            "parsed_output": result.parsed_output,
            "error_message": result.error_message,
            "created_at": result.created_at.isoformat() if result.created_at else None
        }
        # Only include raw output if explicitly requested (can be large)
        result_list.append(result_data)
    
    return {
        "scan_id": scan_id,
        "total": len(result_list),
        "results": result_list
    }


@router.get("/scans/{scan_id}/vulnerabilities")
async def get_scan_vulnerabilities(
    scan_id: str,
    severity: Optional[VulnerabilitySeverity] = None,
    status: Optional[VulnerabilityStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get all vulnerabilities discovered in a scan
    
    - **severity**: Filter by severity (critical, high, medium, low, info)
    - **status**: Filter by status (open, acknowledged, fixing, fixed, false_positive)
    - **skip**: Pagination offset
    - **limit**: Max results to return
    """
    scan_repo = ScanRepository(db)
    scan = scan_repo.get(scan_id)
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    vuln_repo = VulnerabilityRepository(db)
    vulns = vuln_repo.get_scan_vulnerabilities(
        scan_id=scan_id,
        severity=severity,
        status=status,
        skip=skip,
        limit=limit
    )
    
    # Get vulnerability statistics
    vuln_stats = vuln_repo.get_statistics(scan_id=scan_id)
    
    vuln_list = []
    for vuln in vulns:
        vuln_data = {
            "id": vuln.id,
            "cve_id": vuln.cve_id,
            "title": vuln.title,
            "description": vuln.description,
            "severity": vuln.severity.value,
            "cvss_score": vuln.cvss_score,
            "priority_score": vuln.priority_score,
            "affected_host": vuln.affected_host,
            "affected_url": vuln.affected_url,
            "affected_port": vuln.affected_port,
            "tool_name": vuln.tool_name,
            "template_id": vuln.template_id,
            "exploit_available": vuln.exploit_available,
            "patch_available": vuln.patch_available,
            "status": vuln.status.value,
            "remediation": vuln.remediation,
            "discovered_at": vuln.discovered_at.isoformat() if vuln.discovered_at else None,
            "references": vuln.references
        }
        vuln_list.append(vuln_data)
    
    return {
        "scan_id": scan_id,
        "total": vuln_stats["total"],
        "statistics": vuln_stats,
        "skip": skip,
        "limit": limit,
        "vulnerabilities": vuln_list
    }


# ===========================
# STATISTICS ENDPOINTS
# ===========================

@router.get("/stats/overview")
async def get_overview_statistics(db: Session = Depends(get_db)):
    """
    Get overall platform statistics
    
    Returns counts, averages, and trends across all scans
    """
    scan_repo = ScanRepository(db)
    vuln_repo = VulnerabilityRepository(db)
    
    scan_stats = scan_repo.get_statistics()
    vuln_stats = vuln_repo.get_statistics()
    
    return {
        "scans": scan_stats,
        "vulnerabilities": vuln_stats,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/stats/scans")
async def get_scan_statistics(db: Session = Depends(get_db)):
    """
    Get detailed scan statistics
    
    Breakdown by status, profile, and time periods
    """
    scan_repo = ScanRepository(db)
    stats = scan_repo.get_statistics()
    
    return stats


# ===========================
# COMPARISON ENDPOINTS
# ===========================

@router.get("/scans/{scan_id}/compare")
async def compare_scan_with_previous(
    scan_id: str,
    baseline_scan_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Compare a scan with its baseline (previous scan)
    
    Shows what changed:
    - New vulnerabilities
    - Fixed vulnerabilities
    - Risk score trend
    
    If baseline_scan_id not provided, automatically uses most recent previous scan
    """
    comparison_engine = ComparisonEngine(db)
    
    try:
        comparison = await comparison_engine.compare_scans(
            current_scan_id=scan_id,
            baseline_scan_id=baseline_scan_id
        )
        
        if not comparison:
            return {
                "scan_id": scan_id,
                "has_baseline": False,
                "message": "No previous scan found for comparison"
            }
        
        return {
            "id": comparison.id,
            "scan_id": scan_id,
            "baseline_scan_id": comparison.baseline_scan_id,
            "current_scan_id": comparison.current_scan_id,
            "changes_detected": comparison.changes_detected,
            "summary": comparison.summary,
            "created_at": comparison.created_at.isoformat() if comparison.created_at else None
        }
        
    except Exception as e:
        logger.error(f"Comparison failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")
