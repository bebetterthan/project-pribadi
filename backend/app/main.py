from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.api.v1.router import api_router
from app.utils.logger import logger
from app.db.session import engine
from app.models import Base  # Import all models
from app.core.exceptions import (
    APIException,
    api_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from app.core.middleware import RequestContextMiddleware, RateLimitMiddleware


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    debug=settings.DEBUG,
    description="AI-powered security assessment platform"
)

# Exception handlers
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Middlewares (order matters - first added is executed last)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Rate limiting (after CORS)
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(
        RateLimitMiddleware,
        calls_per_minute=settings.RATE_LIMIT_PER_MINUTE
    )
# Request context (executed first)
app.add_middleware(RequestContextMiddleware)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("=" * 70)
    logger.info(f"[START] Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info("=" * 70)
    
    # Environment info
    logger.info(f"[ENV] Environment: {settings.ENVIRONMENT}")
    logger.info(f"[DEBUG] Debug Mode: {settings.DEBUG}")
    logger.info(f"[CORS] CORS Origins: {settings.cors_origins_list}")
    logger.info(f"[RATE] Rate Limiting: {'Enabled' if settings.RATE_LIMIT_ENABLED else 'Disabled'}")
    logger.info(f"[METRICS] Metrics: {'Enabled' if settings.METRICS_ENABLED else 'Disabled'}")
    logger.info(f"[MOCK] Mock Tools: {settings.USE_MOCK_TOOLS}")
    
    # Initialize database
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("[OK] Database tables created/verified")
        
        # Initialize default data
        from app.db.session import SessionLocal
        from app.db.init_db import init_database
        
        db = SessionLocal()
        try:
            default_user = init_database(db)
            logger.info(f"[OK] Database initialized - Default user: {default_user.username}")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[ERROR] Database initialization failed: {e}")
        raise
    
    # Log available routes (only in development)
    if settings.is_development:
        logger.info("\n[ROUTES] Available API Routes:")
        for route in app.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                methods = ', '.join(sorted(route.methods))
                logger.info(f"   {methods:20} {route.path}")
    
    # Startup summary
    logger.info("=" * 70)
    logger.info("[OK] Application Ready!")
    logger.info(f"[DOCS] API Docs:        http://localhost:8000{settings.API_V1_PREFIX}/docs")
    logger.info(f"[HEALTH] Health Check:    http://localhost:8000{settings.API_V1_PREFIX}/health")
    logger.info(f"[METRICS] Metrics:         http://localhost:8000{settings.API_V1_PREFIX}/metrics")
    logger.info("=" * 70)


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "operational",
        "documentation": f"{settings.API_V1_PREFIX}/docs",
        "health_check": f"{settings.API_V1_PREFIX}/health",
        "metrics": f"{settings.API_V1_PREFIX}/metrics"
    }
