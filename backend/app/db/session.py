from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.utils.logger import logger

# Create engine with optimized connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite specific
    poolclass=pool.QueuePool,  # Use connection pooling
    pool_size=settings.DATABASE_POOL_SIZE,  # Number of permanent connections
    max_overflow=settings.DATABASE_MAX_OVERFLOW,  # Max extra connections
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,  # Timeout waiting for connection
    pool_pre_ping=True,  # Test connections before using them
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False,  # Set to True for SQL debugging
)

# Enable WAL mode for SQLite (better concurrency)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Configure SQLite for better performance and concurrency"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
    cursor.execute("PRAGMA synchronous=NORMAL")  # Balance between safety and speed
    cursor.execute("PRAGMA cache_size=10000")  # 10MB cache
    cursor.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp tables
    cursor.close()
    logger.debug("SQLite optimizations applied")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
