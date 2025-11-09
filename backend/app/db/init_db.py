"""
Database initialization - Create default user and seed data
"""
from sqlalchemy.orm import Session
from app.models import User, Asset
from app.utils.logger import logger
import uuid


def create_default_user(db: Session) -> User:
    """Create default system user if not exists"""
    default_user = db.query(User).filter(User.username == "admin").first()
    
    if default_user:
        logger.info("Default user already exists")
        return default_user
    
    logger.info("Creating default admin user...")
    default_user = User(
        id=str(uuid.uuid4()),
        username="admin",
        email="admin@agentpentest.local",
        full_name="System Administrator",
        is_active=True,
        is_superuser=True,
    )
    db.add(default_user)
    db.commit()
    db.refresh(default_user)
    
    logger.info(f"Default user created: {default_user.username} (ID: {default_user.id})")
    return default_user


def init_database(db: Session):
    """Initialize database with seed data"""
    try:
        logger.info("Initializing database...")
        
        # Create default user
        default_user = create_default_user(db)
        
        logger.info("Database initialization complete!")
        return default_user
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        db.rollback()
        raise

