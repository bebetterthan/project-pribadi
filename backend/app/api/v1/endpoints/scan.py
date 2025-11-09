from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.models.scan import Scan
from app.schemas.scan import ScanCreate, ScanResponse
from app.schemas.result import ScanResultResponse
from app.schemas.analysis import AIAnalysisResponse
from app.utils.sanitizers import sanitize_target
from app.services.scanner_service import ScannerService
from app.utils.logger import logger
from app.core.exceptions import NotFoundException, BadRequestException
from datetime import datetime

router = APIRouter()


def get_gemini_key(x_gemini_api_key: Optional[str] = Header(None)) -> Optional[str]:
    """Extract Gemini API key from header"""
    return x_gemini_api_key


@router.post("", response_model=ScanResponse, status_code=201)
async def create_scan(
    scan_data: ScanCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    gemini_key: Optional[str] = Depends(get_gemini_key)
):
    """
    Create and start a new scan with AI strategic planning
    """
    # Validate and sanitize target
    try:
        clean_target = sanitize_target(scan_data.target)
    except ValueError as e:
        raise BadRequestException(str(e))

    # Check if AI is enabled but no key provided
    if scan_data.enable_ai and not gemini_key:
        raise BadRequestException("Gemini API key required when AI analysis is enabled")

    # Decision: Use Agent Orchestrator or Simple Planning?
    use_agent_workflow = scan_data.enable_ai and gemini_key and scan_data.user_prompt

    # For agent workflow, we don't need to pre-select tools
    tools_to_use = scan_data.tools if not use_agent_workflow else ['nmap']  # Agent will decide

    # Create scan record - Mark as RUNNING immediately for real-time experience
    from app.models.scan import ScanStatus
    from datetime import datetime

    scan = Scan(
        target=clean_target,
        user_prompt=scan_data.user_prompt,
        ai_strategy=None,  # Agent will populate this
        agent_thoughts=None,  # Agent will populate this
        tools=tools_to_use,
        profile=scan_data.profile,
        status=ScanStatus.RUNNING,  # Start as RUNNING immediately!
        started_at=datetime.utcnow(),  # Mark start time
    )

    db.add(scan)
    db.commit()
    db.refresh(scan)

    logger.info(f"✅ Created scan {scan.id} for target: {clean_target} - Status: RUNNING")

    if use_agent_workflow and scan_data.user_prompt:
        logger.info(f"🤖 Using AI Agent workflow with objective: {scan_data.user_prompt[:100]}...")

    # Execute scan in background with new DB session
    background_tasks.add_task(
        execute_scan_task,
        scan.id,  # type: ignore
        gemini_key if scan_data.enable_ai else None,
        bool(use_agent_workflow)  # type: ignore
    )

    return scan


def execute_scan_task(scan_id: str, gemini_api_key: Optional[str], use_agent: bool = False):
    """Background task to execute scan - creates its own DB session"""
    from app.db.session import SessionLocal
    import asyncio

    db = SessionLocal()
    try:
        if use_agent and gemini_api_key:
            # Use AI Agent Orchestrator for intelligent workflow
            logger.info(f"🤖 Starting AI Agent workflow for scan {scan_id}")
            from app.services.agent_orchestrator import AgentOrchestrator

            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            orchestrator = AgentOrchestrator(gemini_api_key)

            # Run agent workflow (async)
            result = asyncio.run(orchestrator.run_agent_workflow(scan, db))

            if result['success']:
                logger.info(f"✅ Agent workflow completed for scan {scan_id}")
            else:
                logger.error(f"❌ Agent workflow failed: {result.get('error')}")
        else:
            # Use async scanner service for parallel execution
            logger.info(f"🔧 Using async parallel scanner for scan {scan_id}")
            from app.services.async_scanner_service import AsyncScannerService
            scanner = AsyncScannerService(db)
            scanner.execute_scan(scan_id, gemini_api_key)

    except Exception as e:
        logger.error(f"Background scan task failed for scan {scan_id}: {str(e)}", exc_info=True)
        # Mark scan as failed
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if scan:
            from app.models.scan import ScanStatus
            scan.status = ScanStatus.FAILED  # type: ignore
            scan.error_message = str(e)  # type: ignore
            db.commit()
    finally:
        db.close()


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: str, db: Session = Depends(get_db)):
    """
    Get scan status and details
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()

    if not scan:
        raise NotFoundException("Scan", scan_id)

    return scan


@router.get("/{scan_id}/results")
async def get_scan_results(scan_id: str, db: Session = Depends(get_db)):
    """
    Get scan results with all tool outputs
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()

    if not scan:
        raise NotFoundException("Scan", scan_id)

    # Get all results
    results = [ScanResultResponse.from_orm(r) for r in scan.results]

    # Get AI analysis if exists
    analysis = None
    if scan.analysis:
        analysis = AIAnalysisResponse.from_orm(scan.analysis)

    return {
        "scan": ScanResponse.from_orm(scan),
        "results": results,
        "analysis": analysis
    }


@router.delete("/{scan_id}", status_code=204)
async def delete_scan(scan_id: str, db: Session = Depends(get_db)):
    """
    Delete a scan and all its results
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()

    if not scan:
        raise NotFoundException("Scan", scan_id)

    db.delete(scan)
    db.commit()

    logger.info(f"Deleted scan {scan_id}")

    return None
