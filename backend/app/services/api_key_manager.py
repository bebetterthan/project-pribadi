"""
API Key Manager - Manage API keys for programmatic access
FASE 5: Public API with authentication
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models import APIKey, User
from app.utils.logger import logger
from datetime import datetime, timedelta
import hashlib


class APIKeyManager:
    """Manage API keys for users"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_api_key(
        self,
        user_id: str,
        name: str,
        scopes: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None,
        rate_limit_per_minute: int = 60
    ) -> tuple[APIKey, str]:
        """
        Create new API key for user
        
        Returns: (APIKey object, raw_key string)
        WARNING: raw_key is only shown once!
        """
        # Generate key
        raw_key, key_hash = APIKey.generate_key()
        key_prefix = raw_key[:12]  # agp_xxxxxxx
        
        # Calculate expiry
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Create API key
        api_key = APIKey(
            user_id=user_id,
            name=name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            scopes=scopes,
            rate_limit_per_minute=rate_limit_per_minute,
            expires_at=expires_at,
            is_active=True
        )
        
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)
        
        logger.info(f"[APIKey] Created key '{name}' for user {user_id}")
        
        return api_key, raw_key
    
    def verify_api_key(self, raw_key: str) -> Optional[User]:
        """
        Verify API key and return associated user
        
        Returns: User object if valid, None if invalid
        """
        # Hash the provided key
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Find API key
        api_key = self.db.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        ).first()
        
        if not api_key:
            return None
        
        # Check if expired
        if api_key.is_expired():
            logger.warning(f"[APIKey] Expired key attempt: {api_key.key_prefix}")
            return None
        
        # Update usage
        api_key.last_used_at = datetime.utcnow()
        api_key.usage_count += 1
        self.db.commit()
        
        # Get user
        user = self.db.query(User).filter(User.id == api_key.user_id).first()
        
        if not user or not user.is_active:
            return None
        
        logger.debug(f"[APIKey] Verified key: {api_key.key_prefix}")
        return user
    
    def get_user_keys(self, user_id: str) -> List[APIKey]:
        """Get all API keys for user"""
        return self.db.query(APIKey).filter(APIKey.user_id == user_id).order_by(APIKey.created_at.desc()).all()
    
    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke (deactivate) API key"""
        api_key = self.db.query(APIKey).filter(APIKey.id == key_id).first()
        if not api_key:
            return False
        
        api_key.is_active = False
        self.db.commit()
        
        logger.info(f"[APIKey] Revoked key: {api_key.key_prefix}")
        return True
    
    def delete_api_key(self, key_id: str) -> bool:
        """Delete API key permanently"""
        api_key = self.db.query(APIKey).filter(APIKey.id == key_id).first()
        if not api_key:
            return False
        
        self.db.delete(api_key)
        self.db.commit()
        
        logger.info(f"[APIKey] Deleted key: {api_key.key_prefix}")
        return True

