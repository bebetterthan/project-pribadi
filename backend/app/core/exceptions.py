from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Optional, Dict, Any
from app.utils.logger import logger


# ============================================================================
# Base Exceptions
# ============================================================================

class APIException(Exception):
    """
    Base API exception with user-friendly messages
    
    Attributes:
        message: User-facing error message (safe to expose)
        status_code: HTTP status code
        technical_detail: Technical detail (logged but not exposed)
        error_code: Machine-readable error code
    """
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        technical_detail: Optional[str] = None,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.technical_detail = technical_detail or message
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)


# ============================================================================
# HTTP Exceptions (User-facing)
# ============================================================================

class NotFoundException(APIException):
    """Resource not found"""
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"The requested {resource} was not found",
            status_code=status.HTTP_404_NOT_FOUND,
            technical_detail=f"{resource} with id '{resource_id}' not found",
            error_code="RESOURCE_NOT_FOUND"
        )


class BadRequestException(APIException):
    """Bad request"""
    def __init__(self, message: str, technical_detail: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            technical_detail=technical_detail,
            error_code="BAD_REQUEST"
        )


class UnauthorizedException(APIException):
    """Unauthorized access"""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED"
        )


class ForbiddenException(APIException):
    """Forbidden access"""
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN"
        )


class RateLimitException(APIException):
    """Rate limit exceeded"""
    def __init__(self, retry_after: Optional[int] = None):
        message = "Too many requests. Please try again later."
        if retry_after:
            message += f" Retry after {retry_after} seconds."
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED"
        )


class ServiceUnavailableException(APIException):
    """Service temporarily unavailable"""
    def __init__(self, service_name: str = "Service"):
        super().__init__(
            message=f"{service_name} is temporarily unavailable. Please try again later.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="SERVICE_UNAVAILABLE"
        )


# ============================================================================
# Business Logic Exceptions (Internal + User-facing)
# ============================================================================

class ToolNotInstalledError(APIException):
    """Required pentesting tool is not installed"""
    def __init__(self, tool_name: str):
        super().__init__(
            message=f"The required tool '{tool_name}' is not available. Please contact support.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            technical_detail=f"Tool '{tool_name}' not installed or not in PATH",
            error_code="TOOL_NOT_INSTALLED"
        )


class InvalidTargetError(APIException):
    """Target validation failed"""
    def __init__(self, target: str, reason: str = "Invalid format"):
        super().__init__(
            message=f"The target '{target}' is not valid: {reason}",
            status_code=status.HTTP_400_BAD_REQUEST,
            technical_detail=f"Target validation failed for '{target}': {reason}",
            error_code="INVALID_TARGET"
        )


class BlacklistedTargetError(APIException):
    """Target is blacklisted (internal IPs, etc.)"""
    def __init__(self, target: str):
        super().__init__(
            message="This target cannot be scanned due to security policies.",
            status_code=status.HTTP_403_FORBIDDEN,
            technical_detail=f"Target '{target}' is blacklisted (internal IP or restricted)",
            error_code="BLACKLISTED_TARGET"
        )


class ScanExecutionError(APIException):
    """Scan execution failed"""
    def __init__(self, tool_name: str, reason: str):
        super().__init__(
            message=f"Scan failed: {reason}. Please try again or contact support.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            technical_detail=f"{tool_name} execution failed: {reason}",
            error_code="SCAN_EXECUTION_FAILED"
        )


class ScanTimeoutError(APIException):
    """Scan timed out"""
    def __init__(self, tool_name: str, timeout: int):
        super().__init__(
            message=f"Scan took too long and was cancelled. Please try again with a smaller scope.",
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            technical_detail=f"{tool_name} timed out after {timeout} seconds",
            error_code="SCAN_TIMEOUT"
        )


class ConcurrentScanError(APIException):
    """Concurrent scan limit reached"""
    def __init__(self):
        super().__init__(
            message="Maximum concurrent scans reached. Please wait for active scans to complete.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="CONCURRENT_SCAN_LIMIT"
        )


# ============================================================================
# AI Service Exceptions
# ============================================================================

class AIServiceError(APIException):
    """AI service encountered an error"""
    def __init__(self, reason: str, technical_detail: Optional[str] = None):
        super().__init__(
            message=f"AI analysis unavailable: {reason}. Raw results will be provided.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            technical_detail=technical_detail or reason,
            error_code="AI_SERVICE_ERROR"
        )


class AIQuotaExceededError(APIException):
    """AI API quota exceeded"""
    def __init__(self):
        super().__init__(
            message="AI analysis temporarily unavailable due to high demand. Please try again in a few minutes.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            technical_detail="Gemini API quota exceeded",
            error_code="AI_QUOTA_EXCEEDED"
        )


class AIContentFilterError(APIException):
    """AI content blocked by safety filter"""
    def __init__(self):
        super().__init__(
            message="AI analysis blocked due to content policy. Raw results will be provided.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            technical_detail="Gemini safety filter blocked the content",
            error_code="AI_CONTENT_FILTERED"
        )


# ============================================================================
# Database Exceptions
# ============================================================================

class DatabaseError(APIException):
    """Database operation failed"""
    def __init__(self, operation: str, technical_detail: Optional[str] = None):
        super().__init__(
            message="A database error occurred. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            technical_detail=technical_detail or f"Database {operation} failed",
            error_code="DATABASE_ERROR"
        )


# ============================================================================
# Exception Handlers
# ============================================================================

async def api_exception_handler(request: Request, exc: APIException):
    """Handle custom API exceptions"""
    from app.utils.context import get_context
    
    # Log technical detail with context
    context = get_context()
    logger.error(
        f"API Exception: {exc.technical_detail}",
        extra={
            **context,
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        },
        exc_info=True
    )
    
    # Return user-friendly message
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "code": exc.error_code,
                "path": str(request.url.path),
            }
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle pydantic validation errors"""
    from app.utils.context import get_context
    
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    
    context = get_context()
    logger.warning(
        f"Validation error: {errors}",
        extra={**context, "path": str(request.url.path)}
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "message": "Request validation failed. Please check your input.",
                "code": "VALIDATION_ERROR",
                "path": str(request.url.path),
                "details": errors,
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions"""
    from app.utils.context import get_context
    
    context = get_context()
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={**context, "path": str(request.url.path)},
        exc_info=True
    )
    
    # Don't expose internal errors in production
    from app.config import settings
    if settings.is_production:
        message = "An internal error occurred. Please contact support if this persists."
    else:
        message = f"Internal server error: {str(exc)}"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": message,
                "code": "INTERNAL_ERROR",
                "path": str(request.url.path),
            }
        },
    )
