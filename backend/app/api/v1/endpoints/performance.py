"""
Performance monitoring endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db, engine
from app.utils.cache import get_cache
from app.utils.logger import logger
from app.config import settings

router = APIRouter()


@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    if not settings.CACHE_ENABLED:
        return {"enabled": False, "message": "Cache is disabled"}
    
    cache = get_cache()
    stats = cache.stats()
    
    return {
        "enabled": True,
        "stats": stats,
        "config": {
            "max_size": cache.max_size,
            "default_ttl": cache.default_ttl,
        }
    }


@router.post("/cache/clear")
async def clear_cache():
    """Clear all cache entries"""
    if not settings.CACHE_ENABLED:
        return {"enabled": False, "message": "Cache is disabled"}
    
    cache = get_cache()
    cache.clear()
    
    logger.info("Cache cleared via API")
    
    return {"success": True, "message": "Cache cleared"}


@router.post("/cache/cleanup")
async def cleanup_expired_cache():
    """Remove expired cache entries"""
    if not settings.CACHE_ENABLED:
        return {"enabled": False, "message": "Cache is disabled"}
    
    cache = get_cache()
    removed = cache.cleanup_expired()
    
    return {
        "success": True, 
        "removed": removed,
        "message": f"Removed {removed} expired entries"
    }


@router.get("/database/stats")
async def get_database_stats(db: Session = Depends(get_db)):
    """Get database connection pool statistics"""
    pool = engine.pool
    
    return {
        "pool_size": pool.size(),  # type: ignore
        "checked_in": pool.checkedin(),  # type: ignore
        "checked_out": pool.checkedout(),  # type: ignore
        "overflow": pool.overflow(),  # type: ignore
        "config": {
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_timeout": settings.DATABASE_POOL_TIMEOUT,
        }
    }


@router.get("/performance")
async def get_performance_metrics(db: Session = Depends(get_db)):
    """Get comprehensive performance metrics"""
    
    metrics = {
        "cache": {},
        "database": {},
        "config": {}
    }
    
    # Cache metrics
    if settings.CACHE_ENABLED:
        cache = get_cache()
        metrics["cache"] = cache.stats()
    else:
        metrics["cache"] = {"enabled": False}
    
    # Database metrics
    pool = engine.pool
    metrics["database"] = {
        "pool_size": pool.size(),  # type: ignore
        "checked_in": pool.checkedin(),  # type: ignore
        "checked_out": pool.checkedout(),  # type: ignore
        "overflow": pool.overflow(),  # type: ignore
    }
    
    # Configuration
    metrics["config"] = {
        "cache_enabled": settings.CACHE_ENABLED,
        "max_concurrent_scans": settings.MAX_CONCURRENT_SCANS,
        "max_concurrent_tool_executions": settings.MAX_CONCURRENT_TOOL_EXECUTIONS,
        "database_pool_size": settings.DATABASE_POOL_SIZE,
    }
    
    return metrics
