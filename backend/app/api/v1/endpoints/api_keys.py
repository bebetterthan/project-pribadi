"""
API Key Endpoints - Manage API keys for programmatic access
FASE 5: Public API authentication
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.api_key_manager import APIKeyManager
from app.models import User
from pydantic import BaseModel

router = APIRouter()


class CreateAPIKeyRequest(BaseModel):
    name: str
    scopes: Optional[list[str]] = None
    expires_in_days: Optional[int] = None
    rate_limit_per_minute: int = 60


@router.post("/")
async def create_api_key(
    request: CreateAPIKeyRequest,
    db: Session = Depends(get_db)
):
    """
    Create new API key
    
    **WARNING**: The raw API key is only shown once! Save it securely.
    """
    # TODO: Get current user from auth
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    api_key_manager = APIKeyManager(db)
    api_key, raw_key = api_key_manager.create_api_key(
        user_id=user.id,
        name=request.name,
        scopes=request.scopes,
        expires_in_days=request.expires_in_days,
        rate_limit_per_minute=request.rate_limit_per_minute
    )
    
    return {
        "id": api_key.id,
        "name": api_key.name,
        "key": raw_key,  # Only time this is shown!
        "key_prefix": api_key.key_prefix,
        "scopes": api_key.scopes,
        "rate_limit_per_minute": api_key.rate_limit_per_minute,
        "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
        "created_at": api_key.created_at.isoformat() if api_key.created_at else None,
        "warning": "Save this key now! It will not be shown again."
    }


@router.get("/")
async def list_api_keys(db: Session = Depends(get_db)):
    """List all API keys for current user"""
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    api_key_manager = APIKeyManager(db)
    keys = api_key_manager.get_user_keys(user.id)
    
    return {
        "keys": [
            {
                "id": k.id,
                "name": k.name,
                "key_prefix": k.key_prefix,
                "is_active": k.is_active,
                "scopes": k.scopes,
                "rate_limit_per_minute": k.rate_limit_per_minute,
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                "usage_count": k.usage_count,
                "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                "created_at": k.created_at.isoformat() if k.created_at else None
            }
            for k in keys
        ]
    }


@router.post("/{key_id}/revoke")
async def revoke_api_key(key_id: str, db: Session = Depends(get_db)):
    """Revoke (deactivate) API key"""
    api_key_manager = APIKeyManager(db)
    success = api_key_manager.revoke_api_key(key_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return {"success": True, "key_id": key_id, "status": "revoked"}


@router.delete("/{key_id}")
async def delete_api_key(key_id: str, db: Session = Depends(get_db)):
    """Delete API key permanently"""
    api_key_manager = APIKeyManager(db)
    success = api_key_manager.delete_api_key(key_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return {"success": True, "key_id": key_id, "status": "deleted"}

