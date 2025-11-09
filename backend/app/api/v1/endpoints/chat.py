"""
Chat History Endpoints
Retrieve SSE message history for replay
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.scan import Scan
from app.models.chat_message import ChatMessage
from app.utils.logger import logger

router = APIRouter()


@router.get("/scan/{scan_id}/chat")
async def get_scan_chat_history(
    scan_id: str,
    limit: int = 1000,  # Max messages to return
    db: Session = Depends(get_db)
):
    """
    Get complete chat history for a scan
    Returns all SSE messages in chronological order
    
    This allows users to replay the entire conversation even after page refresh
    """
    logger.info(f"📜 Fetching chat history for scan {scan_id}")
    
    # Check if scan exists
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        logger.warning(f"⚠️ Scan {scan_id} not found")
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Get messages
    messages = db.query(ChatMessage).filter(
        ChatMessage.scan_id == scan_id
    ).order_by(
        ChatMessage.sequence.asc()
    ).limit(limit).all()
    
    logger.info(f"✅ Retrieved {len(messages)} chat messages for scan {scan_id}")
    
    return {
        "scan_id": scan_id,
        "total_messages": len(messages),
        "messages": [msg.to_dict() for msg in messages]
    }


@router.get("/scan/{scan_id}/chat/latest")
async def get_latest_chat_messages(
    scan_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get latest N chat messages for a scan
    Useful for polling/realtime updates
    """
    # Check if scan exists
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Get latest messages
    messages = db.query(ChatMessage).filter(
        ChatMessage.scan_id == scan_id
    ).order_by(
        ChatMessage.sequence.desc()
    ).limit(limit).all()
    
    # Reverse to chronological order
    messages.reverse()
    
    return {
        "scan_id": scan_id,
        "count": len(messages),
        "messages": [msg.to_dict() for msg in messages]
    }


@router.get("/scan/{scan_id}/chat/summary")
async def get_chat_summary(
    scan_id: str,
    db: Session = Depends(get_db)
):
    """
    Get summary statistics of chat history
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Count messages by type
    message_counts = {}
    messages = db.query(ChatMessage).filter(
        ChatMessage.scan_id == scan_id
    ).all()
    
    for msg in messages:
        message_counts[msg.message_type] = message_counts.get(msg.message_type, 0) + 1
    
    return {
        "scan_id": scan_id,
        "total_messages": len(messages),
        "message_types": message_counts,
        "first_message": messages[0].created_at.isoformat() if messages else None,
        "last_message": messages[-1].created_at.isoformat() if messages else None
    }

