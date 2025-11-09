from fastapi import APIRouter
from app.api.v1.endpoints import (
    scan, scan_stream, analysis, history, tools, chat, 
    health, metrics, notifications, api_keys, dashboard, export,
    vulnerabilities, teams, bulk_operations, performance
)

api_router = APIRouter()

# Core scan functionality
api_router.include_router(scan.router, prefix="/scan", tags=["scan"])
api_router.include_router(scan_stream.router, prefix="/scan", tags=["scan-stream"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])

# Data & history
api_router.include_router(history.router, prefix="/history", tags=["history"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(export.router, prefix="/export", tags=["export"])

# Vulnerability management & collaboration
api_router.include_router(vulnerabilities.router, prefix="/vulnerabilities", tags=["vulnerabilities"])

# Team collaboration
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])

# Communication & collaboration
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

# Bulk operations
api_router.include_router(bulk_operations.router, prefix="/bulk", tags=["bulk-operations"])

# Configuration & tools
api_router.include_router(tools.router, tags=["tools"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])

# Monitoring endpoints (no prefix - available at root API level)
api_router.include_router(health.router, tags=["monitoring"])
api_router.include_router(metrics.router, tags=["monitoring"])
api_router.include_router(performance.router, prefix="/performance", tags=["performance"])
