from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.scan import Scan
from app.schemas.analysis import AIAnalysisResponse

router = APIRouter()


@router.get("/{scan_id}", response_model=AIAnalysisResponse)
async def get_analysis(scan_id: str, db: Session = Depends(get_db)):
    """
    Get AI analysis for a scan
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if not scan.analysis:
        raise HTTPException(status_code=404, detail="Analysis not available for this scan")

    return scan.analysis
