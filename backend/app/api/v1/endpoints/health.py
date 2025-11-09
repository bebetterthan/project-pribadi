"""
Health check and monitoring endpoints
"""
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Any
import time
import asyncio
from datetime import datetime
import psutil
import os

from app.db.session import get_db
from app.config import settings
from app.utils.logger import logger
from app.utils.circuit_breaker import get_all_circuit_breakers

router = APIRouter()

# Track application start time
APP_START_TIME = time.time()


async def check_database(db: Session) -> Dict[str, Any]:
    """Check database connectivity and latency"""
    start = time.time()
    try:
        # Simple query to check connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        latency_ms = int((time.time() - start) * 1000)
        return {
            "status": "healthy",
            "latency_ms": latency_ms
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_gemini_api() -> Dict[str, Any]:
    """
    Check if Gemini API is accessible
    Note: This is a lightweight check, not a full API call
    """
    try:
        # Check if API key is configured
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            return {
                "status": "degraded",
                "message": "API key not configured"
            }
        
        # Check circuit breaker status
        breakers = get_all_circuit_breakers()
        if "gemini_api" in breakers:
            breaker_state = breakers["gemini_api"]["state"]
            if breaker_state == "open":
                return {
                    "status": "degraded",
                    "message": "Circuit breaker is open (service recovering)",
                    "circuit_breaker": breaker_state
                }
            elif breaker_state == "half_open":
                return {
                    "status": "degraded",
                    "message": "Circuit breaker is half-open (testing recovery)",
                    "circuit_breaker": breaker_state
                }
        
        return {
            "status": "healthy",
            "message": "API key configured, circuit breaker closed"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_nmap_binary() -> Dict[str, Any]:
    """Check if Nmap is installed"""
    try:
        import shutil
        nmap_path = shutil.which("nmap")
        
        if not nmap_path:
            return {
                "status": "degraded",
                "message": "Nmap not found in PATH (using mock mode)",
                "mock_mode": settings.USE_MOCK_TOOLS
            }
        
        # Try to get version
        import subprocess
        result = subprocess.run(
            ["nmap", "--version"],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0] if result.stdout else "unknown"
            return {
                "status": "healthy",
                "path": nmap_path,
                "version": version_line.strip()
            }
        else:
            return {
                "status": "degraded",
                "message": "Nmap found but version check failed"
            }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "mock_mode": settings.USE_MOCK_TOOLS
        }


async def check_disk_space() -> Dict[str, Any]:
    """Check available disk space"""
    try:
        disk = psutil.disk_usage('.')
        free_percent = 100 - disk.percent
        
        status_val = "healthy"
        if free_percent < 10:
            status_val = "unhealthy"
        elif free_percent < 20:
            status_val = "degraded"
        
        return {
            "status": status_val,
            "free_percent": round(free_percent, 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "total_gb": round(disk.total / (1024**3), 2)
        }
    except Exception as e:
        return {
            "status": "unknown",
            "error": str(e)
        }


async def check_memory() -> Dict[str, Any]:
    """Check memory usage"""
    try:
        mem = psutil.virtual_memory()
        used_percent = mem.percent
        
        status_val = "healthy"
        if used_percent > 90:
            status_val = "unhealthy"
        elif used_percent > 80:
            status_val = "degraded"
        
        return {
            "status": status_val,
            "used_percent": round(used_percent, 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "total_gb": round(mem.total / (1024**3), 2)
        }
    except Exception as e:
        return {
            "status": "unknown",
            "error": str(e)
        }


@router.get("/health", tags=["monitoring"])
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check endpoint
    
    Returns overall system health and individual component status.
    Used by load balancers and monitoring tools.
    """
    start_time = time.time()
    
    # Run all health checks in parallel
    checks_results = await asyncio.gather(
        check_database(db),
        check_gemini_api(),
        check_nmap_binary(),
        check_disk_space(),
        check_memory(),
        return_exceptions=True
    )
    
    checks = {
        "database": checks_results[0] if not isinstance(checks_results[0], Exception) else {"status": "error", "error": str(checks_results[0])},
        "gemini_api": checks_results[1] if not isinstance(checks_results[1], Exception) else {"status": "error", "error": str(checks_results[1])},
        "nmap_binary": checks_results[2] if not isinstance(checks_results[2], Exception) else {"status": "error", "error": str(checks_results[2])},
        "disk_space": checks_results[3] if not isinstance(checks_results[3], Exception) else {"status": "error", "error": str(checks_results[3])},
        "memory": checks_results[4] if not isinstance(checks_results[4], Exception) else {"status": "error", "error": str(checks_results[4])},
    }
    
    # Determine overall status
    statuses = [check.get("status", "unknown") for check in checks.values()]
    
    if "unhealthy" in statuses or "error" in statuses:
        overall_status = "unhealthy"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    elif "degraded" in statuses:
        overall_status = "degraded"
        http_status = status.HTTP_200_OK
    else:
        overall_status = "healthy"
        http_status = status.HTTP_200_OK
    
    uptime_seconds = int(time.time() - APP_START_TIME)
    
    response = {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": uptime_seconds,
        "checks": checks,
        "check_duration_ms": int((time.time() - start_time) * 1000)
    }
    
    # Log unhealthy status
    if overall_status != "healthy":
        logger.warning(
            f"Health check returned {overall_status} status",
            extra={"health_status": overall_status, "checks": checks}
        )
    
    return JSONResponse(
        status_code=http_status,
        content=response
    )


@router.get("/health/ready", tags=["monitoring"])
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness probe - checks if service is ready to accept requests
    
    Returns 200 if ready, 503 if not ready.
    Used by Kubernetes readiness probes.
    """
    try:
        # Check database
        db.execute("SELECT 1")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ready"}
        )
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "reason": str(e)}
        )


@router.get("/health/live", tags=["monitoring"])
async def liveness_check():
    """
    Liveness probe - checks if service is alive
    
    Always returns 200 OK if process is running.
    Used by Kubernetes liveness probes.
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "alive"}
    )


@router.get("/health/circuit-breakers", tags=["monitoring"])
async def circuit_breaker_status():
    """Get status of all circuit breakers"""
    breakers = get_all_circuit_breakers()
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "circuit_breakers": breakers,
            "count": len(breakers)
        }
    )

