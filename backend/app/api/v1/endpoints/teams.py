"""
Team Management Endpoints - Multi-user collaboration
FASE 5: Team collaboration infrastructure
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Team, TeamMember, User
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()


class CreateTeamRequest(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None


class InviteMemberRequest(BaseModel):
    user_id: str
    role: str = "member"


@router.post("/")
async def create_team(request: CreateTeamRequest, db: Session = Depends(get_db)):
    """Create new team"""
    # Check if slug already exists
    existing = db.query(Team).filter(Team.slug == request.slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Team slug already exists")
    
    team = Team(
        name=request.name,
        slug=request.slug,
        description=request.description
    )
    
    db.add(team)
    db.commit()
    db.refresh(team)
    
    return {
        "id": team.id,
        "name": team.name,
        "slug": team.slug,
        "description": team.description,
        "created_at": team.created_at.isoformat() if team.created_at else None
    }


@router.get("/")
async def list_teams(db: Session = Depends(get_db)):
    """List all teams"""
    teams = db.query(Team).filter(Team.is_active == True).all()
    
    return {
        "teams": [
            {
                "id": t.id,
                "name": t.name,
                "slug": t.slug,
                "description": t.description,
                "member_count": len(t.members),
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in teams
        ]
    }


@router.get("/{team_id}")
async def get_team(team_id: str, db: Session = Depends(get_db)):
    """Get team details"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return {
        "id": team.id,
        "name": team.name,
        "slug": team.slug,
        "description": team.description,
        "is_active": team.is_active,
        "members": [
            {
                "user_id": m.user_id,
                "role": m.role,
                "joined_at": m.joined_at.isoformat() if m.joined_at else None
            }
            for m in team.members
        ],
        "created_at": team.created_at.isoformat() if team.created_at else None
    }


@router.post("/{team_id}/members")
async def invite_member(
    team_id: str,
    request: InviteMemberRequest,
    db: Session = Depends(get_db)
):
    """Invite user to team"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already member
    existing = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == request.user_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail="User already in team")
    
    member = TeamMember(
        team_id=team_id,
        user_id=request.user_id,
        role=request.role
    )
    
    db.add(member)
    db.commit()
    db.refresh(member)
    
    return {
        "success": True,
        "team_id": team_id,
        "user_id": request.user_id,
        "role": request.role
    }


@router.delete("/{team_id}/members/{user_id}")
async def remove_member(team_id: str, user_id: str, db: Session = Depends(get_db)):
    """Remove user from team"""
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    db.delete(member)
    db.commit()
    
    return {"success": True, "team_id": team_id, "user_id": user_id}

