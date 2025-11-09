"""
Vulnerability Management Endpoints - CRUD and collaboration
FASE 5: Team collaboration on vulnerabilities
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Vulnerability, VulnerabilityStatus, User, VulnerabilityComment
from app.services.notification_manager import NotificationManager
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()


class UpdateVulnerabilityRequest(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class AddCommentRequest(BaseModel):
    content: str


@router.patch("/{vulnerability_id}")
async def update_vulnerability(
    vulnerability_id: str,
    request: UpdateVulnerabilityRequest,
    db: Session = Depends(get_db)
):
    """Update vulnerability (status, assignment, notes)"""
    vuln = db.query(Vulnerability).filter(Vulnerability.id == vulnerability_id).first()
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    # Get current user (TODO: from auth)
    user = db.query(User).filter(User.username == "admin").first()
    
    old_status = vuln.status.value if vuln.status else None
    
    # Update fields
    if request.status:
        try:
            vuln.status = VulnerabilityStatus(request.status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}")
    
    if request.assigned_to:
        assignee = db.query(User).filter(User.id == request.assigned_to).first()
        if not assignee:
            raise HTTPException(status_code=404, detail="Assignee user not found")
        vuln.assigned_to = request.assigned_to
        
        # Send notification
        notification_manager = NotificationManager(db)
        await notification_manager.notify_assigned(
            user_id=request.assigned_to,
            vuln_id=vuln.id,
            title=vuln.title,
            assigned_by_username=user.username if user else "System"
        )
    
    if request.notes:
        vuln.notes = request.notes
    
    vuln.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(vuln)
    
    # Send status change notification if status changed
    if request.status and old_status != vuln.status.value and vuln.assigned_to:
        notification_manager = NotificationManager(db)
        await notification_manager.notify_status_changed(
            user_id=vuln.assigned_to,
            vuln_id=vuln.id,
            title=vuln.title,
            old_status=old_status,
            new_status=vuln.status.value,
            changed_by_username=user.username if user else "System"
        )
    
    return {
        "success": True,
        "vulnerability": {
            "id": vuln.id,
            "status": vuln.status.value,
            "assigned_to": vuln.assigned_to,
            "notes": vuln.notes,
            "updated_at": vuln.updated_at.isoformat() if vuln.updated_at else None
        }
    }


@router.post("/{vulnerability_id}/comments")
async def add_comment(
    vulnerability_id: str,
    request: AddCommentRequest,
    db: Session = Depends(get_db)
):
    """Add comment to vulnerability"""
    vuln = db.query(Vulnerability).filter(Vulnerability.id == vulnerability_id).first()
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    # Get current user (TODO: from auth)
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Create comment
    comment = VulnerabilityComment(
        vulnerability_id=vulnerability_id,
        user_id=user.id,
        content=request.content
    )
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    return {
        "success": True,
        "comment": {
            "id": comment.id,
            "content": comment.content,
            "user_id": comment.user_id,
            "created_at": comment.created_at.isoformat() if comment.created_at else None
        }
    }


@router.get("/{vulnerability_id}/comments")
async def get_comments(vulnerability_id: str, db: Session = Depends(get_db)):
    """Get all comments for vulnerability"""
    vuln = db.query(Vulnerability).filter(Vulnerability.id == vulnerability_id).first()
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    comments = vuln.comments
    
    return {
        "comments": [
            {
                "id": c.id,
                "content": c.content,
                "user_id": c.user_id,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "edited_at": c.edited_at.isoformat() if c.edited_at else None
            }
            for c in comments
        ]
    }

