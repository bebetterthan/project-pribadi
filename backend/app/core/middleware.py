"""
Custom middleware for request processing
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
from typing import Callable

from app.utils.context import set_trace_id, set_request_start_time, clear_context, get_context
from app.utils.logger import logger
from app.config import settings


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to inject request context for distributed tracing
    
    - Generates/extracts trace_id
    - Tracks request duration
    - Adds context to all logs
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract trace ID
        trace_id = request.headers.get("X-Trace-ID")
        if not trace_id:
            from app.utils.context import generate_trace_id
            trace_id = generate_trace_id()
        
        # Set context
        set_trace_id(trace_id)
        start_time = time.time()
        set_request_start_time(start_time)
        
        # Log request start
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                **get_context(),
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Add trace ID to response headers
            response.headers["X-Trace-ID"] = trace_id
            
            # Log request completion
            duration = time.time() - start_time
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    **get_context(),
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": int(duration * 1000)
                }
            )
            
            return response
            
        except Exception as e:
            # Log request error
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra={
                    **get_context(),
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "duration_ms": int(duration * 1000)
                },
                exc_info=True
            )
            raise
        
        finally:
            # Clear context after request
            clear_context()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware
    
    Note: For production, consider using Redis-based rate limiting
    with libraries like slowapi or fastapi-limiter
    """
    
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self._request_counts = {}  # {ip: [(timestamp, count), ...]}
        self._cleanup_interval = 60  # seconds
        self._last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Skip rate limiting for health/metrics endpoints
        if request.url.path in ["/health", "/health/ready", "/health/live", "/metrics"]:
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Cleanup old entries periodically
        if current_time - self._last_cleanup > self._cleanup_interval:
            self._cleanup_old_entries(current_time)
            self._last_cleanup = current_time
        
        # Check rate limit
        if not self._check_rate_limit(client_ip, current_time):
            from fastapi.responses import JSONResponse
            logger.warning(
                f"Rate limit exceeded for {client_ip}",
                extra={"client_ip": client_ip, "path": request.url.path}
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "message": "Too many requests. Please try again later.",
                        "code": "RATE_LIMIT_EXCEEDED"
                    }
                },
                headers={"Retry-After": "60"}
            )
        
        return await call_next(request)
    
    def _check_rate_limit(self, client_ip: str, current_time: float) -> bool:
        """Check if client is within rate limit"""
        minute_ago = current_time - 60
        
        # Get or initialize request history
        if client_ip not in self._request_counts:
            self._request_counts[client_ip] = []
        
        # Remove requests older than 1 minute
        self._request_counts[client_ip] = [
            (ts, count) for ts, count in self._request_counts[client_ip]
            if ts > minute_ago
        ]
        
        # Count requests in last minute
        total_requests = sum(count for _, count in self._request_counts[client_ip])
        
        if total_requests >= self.calls_per_minute:
            return False
        
        # Add current request
        self._request_counts[client_ip].append((current_time, 1))
        return True
    
    def _cleanup_old_entries(self, current_time: float):
        """Remove old entries to prevent memory leak"""
        minute_ago = current_time - 60
        for ip in list(self._request_counts.keys()):
            self._request_counts[ip] = [
                (ts, count) for ts, count in self._request_counts[ip]
                if ts > minute_ago
            ]
            # Remove IP if no recent requests
            if not self._request_counts[ip]:
                del self._request_counts[ip]
