"""
Export Endpoints - Export data in various formats
FASE 5: Reporting and compliance exports
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Scan, Vulnerability, ScanStatus
from app.utils.logger import logger
import json
import csv
import io
from datetime import datetime

router = APIRouter()


@router.get("/scan/{scan_id}/json")
async def export_scan_json(scan_id: str, db: Session = Depends(get_db)):
    """Export complete scan data as JSON"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Get all related data
    vulnerabilities = scan.vulnerabilities
    tool_results = scan.results
    chat_messages = scan.chat_messages
    
    export_data = {
        "scan": {
            "id": scan.id,
            "target": scan.target,
            "status": scan.status.value,
            "profile": scan.profile,
            "started_at": scan.started_at.isoformat() if scan.started_at else None,
            "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
            "duration_seconds": scan.duration_seconds,
            "tools": scan.tools
        },
        "vulnerabilities": [
            {
                "id": v.id,
                "cve_id": v.cve_id,
                "title": v.title,
                "description": v.description,
                "severity": v.severity.value,
                "cvss_score": v.cvss_score,
                "affected_host": v.affected_host,
                "affected_url": v.affected_url,
                "status": v.status.value,
                "recommendation": v.recommendation,
                "discovered_at": v.discovered_at.isoformat() if v.discovered_at else None
            }
            for v in vulnerabilities
        ],
        "tool_results": [
            {
                "tool_name": r.tool_name,
                "target": r.target,
                "exit_code": r.exit_code,
                "execution_time_seconds": r.execution_time_seconds,
                "started_at": r.started_at.isoformat() if r.started_at else None
            }
            for r in tool_results
        ],
        "exported_at": datetime.utcnow().isoformat(),
        "export_version": "1.0"
    }
    
    # Return as downloadable JSON file
    json_str = json.dumps(export_data, indent=2)
    
    return Response(
        content=json_str,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=scan_{scan_id}_{datetime.utcnow().strftime('%Y%m%d')}.json"
        }
    )


@router.get("/scan/{scan_id}/csv")
async def export_scan_csv(scan_id: str, db: Session = Depends(get_db)):
    """Export scan vulnerabilities as CSV"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "CVE ID",
        "Title",
        "Severity",
        "CVSS Score",
        "Affected Host",
        "Affected URL",
        "Status",
        "Recommendation",
        "Discovered At"
    ])
    
    # Write vulnerabilities
    for vuln in scan.vulnerabilities:
        writer.writerow([
            vuln.cve_id or "N/A",
            vuln.title,
            vuln.severity.value,
            vuln.cvss_score or "N/A",
            vuln.affected_host or "N/A",
            vuln.affected_url or "N/A",
            vuln.status.value,
            vuln.recommendation or "N/A",
            vuln.discovered_at.isoformat() if vuln.discovered_at else "N/A"
        ])
    
    # Get CSV content
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=scan_{scan_id}_vulnerabilities.csv"
        }
    )


@router.get("/vulnerabilities/csv")
async def export_all_vulnerabilities_csv(
    status: str = None,
    db: Session = Depends(get_db)
):
    """Export all vulnerabilities as CSV (with optional status filter)"""
    query = db.query(Vulnerability)
    
    if status:
        from app.models import VulnerabilityStatus
        try:
            status_enum = VulnerabilityStatus(status)
            query = query.filter(Vulnerability.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    vulnerabilities = query.order_by(Vulnerability.discovered_at.desc()).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "ID",
        "CVE ID",
        "Title",
        "Severity",
        "CVSS Score",
        "Affected Host",
        "Status",
        "Assigned To",
        "Discovered At",
        "Updated At"
    ])
    
    for vuln in vulnerabilities:
        writer.writerow([
            vuln.id,
            vuln.cve_id or "N/A",
            vuln.title,
            vuln.severity.value,
            vuln.cvss_score or "N/A",
            vuln.affected_host or "N/A",
            vuln.status.value,
            vuln.assigned_to or "Unassigned",
            vuln.discovered_at.isoformat() if vuln.discovered_at else "N/A",
            vuln.updated_at.isoformat() if vuln.updated_at else "N/A"
        ])
    
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=vulnerabilities_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        }
    )

