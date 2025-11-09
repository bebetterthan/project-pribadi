"""
Bulk Operations Endpoints - Batch processing for efficiency
FASE 5: Production optimizations
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Asset, Scan, Vulnerability, VulnerabilityStatus
from pydantic import BaseModel
from typing import List, Optional
import asyncio

router = APIRouter()


class BulkScanRequest(BaseModel):
    asset_ids: List[str]
    scan_profile: str = "standard"


class BulkUpdateVulnRequest(BaseModel):
    vulnerability_ids: List[str]
    status: str
    notes: Optional[str] = None


class BulkDeleteRequest(BaseModel):
    ids: List[str]


@router.post("/scans")
async def bulk_create_scans(
    request: BulkScanRequest,
    db: Session = Depends(get_db)
):
    """Create multiple scans at once"""
    # Verify all assets exist
    assets = db.query(Asset).filter(Asset.id.in_(request.asset_ids)).all()
    
    if len(assets) != len(request.asset_ids):
        raise HTTPException(status_code=404, detail="One or more assets not found")
    
    created_scans = []
    for asset in assets:
        scan = Scan(
            asset_id=asset.id,
            target=asset.target,
            profile=request.scan_profile,
            tools=["nmap", "nuclei"],  # Default tools
            status="pending"
        )
        db.add(scan)
        created_scans.append(scan)
    
    db.commit()
    
    return {
        "success": True,
        "created_count": len(created_scans),
        "scans": [
            {
                "id": s.id,
                "asset_id": s.asset_id,
                "target": s.target,
                "status": s.status.value if hasattr(s.status, 'value') else s.status
            }
            for s in created_scans
        ]
    }


@router.patch("/vulnerabilities")
async def bulk_update_vulnerabilities(
    request: BulkUpdateVulnRequest,
    db: Session = Depends(get_db)
):
    """Update multiple vulnerabilities at once"""
    try:
        status_enum = VulnerabilityStatus(request.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}")
    
    # Update all vulnerabilities
    updated_count = (
        db.query(Vulnerability)
        .filter(Vulnerability.id.in_(request.vulnerability_ids))
        .update({
            "status": status_enum,
            "notes": request.notes
        }, synchronize_session=False)
    )
    
    db.commit()
    
    return {
        "success": True,
        "updated_count": updated_count,
        "status": request.status
    }


@router.delete("/assets")
async def bulk_delete_assets(
    request: BulkDeleteRequest,
    db: Session = Depends(get_db)
):
    """Delete multiple assets at once"""
    deleted_count = (
        db.query(Asset)
        .filter(Asset.id.in_(request.ids))
        .delete(synchronize_session=False)
    )
    
    db.commit()
    
    return {
        "success": True,
        "deleted_count": deleted_count
    }

