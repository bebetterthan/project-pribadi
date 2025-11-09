"""
Context management for distributed tracing and structured logging
"""
import contextvars
import uuid
from typing import Optional, Dict, Any
from datetime import datetime

# Context variables for tracing
trace_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('trace_id', default=None)
scan_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('scan_id', default=None)
user_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('user_id', default=None)
request_start_time_var: contextvars.ContextVar[Optional[float]] = contextvars.ContextVar('request_start_time', default=None)


def generate_trace_id() -> str:
    """Generate a unique trace ID for request tracking"""
    return f"trace-{uuid.uuid4().hex[:16]}"


def set_trace_id(trace_id: Optional[str] = None) -> str:
    """Set trace ID in context (or generate if not provided)"""
    if trace_id is None:
        trace_id = generate_trace_id()
    trace_id_var.set(trace_id)
    return trace_id


def get_trace_id() -> Optional[str]:
    """Get current trace ID from context"""
    return trace_id_var.get()


def set_scan_id(scan_id: str):
    """Set scan ID in context"""
    scan_id_var.set(scan_id)


def get_scan_id() -> Optional[str]:
    """Get current scan ID from context"""
    return scan_id_var.get()


def set_user_id(user_id: str):
    """Set user ID in context"""
    user_id_var.set(user_id)


def get_user_id() -> Optional[str]:
    """Get current user ID from context"""
    return user_id_var.get()


def set_request_start_time(start_time: float):
    """Set request start time in context"""
    request_start_time_var.set(start_time)


def get_request_start_time() -> Optional[float]:
    """Get request start time from context"""
    return request_start_time_var.get()


def get_context() -> Dict[str, Any]:
    """Get all context variables as dict (for logging)"""
    context = {}
    
    trace_id = get_trace_id()
    if trace_id:
        context['trace_id'] = trace_id
    
    scan_id = get_scan_id()
    if scan_id:
        context['scan_id'] = scan_id
    
    user_id = get_user_id()
    if user_id:
        context['user_id'] = user_id
    
    start_time = get_request_start_time()
    if start_time:
        import time
        context['request_duration_ms'] = int((time.time() - start_time) * 1000)
    
    return context


def clear_context():
    """Clear all context variables"""
    trace_id_var.set(None)
    scan_id_var.set(None)
    user_id_var.set(None)
    request_start_time_var.set(None)


class RequestContext:
    """Context manager for request-scoped context"""
    
    def __init__(self, trace_id: Optional[str] = None, scan_id: Optional[str] = None, user_id: Optional[str] = None):
        self.trace_id = trace_id
        self.scan_id = scan_id
        self.user_id = user_id
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        set_request_start_time(self.start_time)
        
        if self.trace_id:
            set_trace_id(self.trace_id)
        else:
            set_trace_id()
        
        if self.scan_id:
            set_scan_id(self.scan_id)
        
        if self.user_id:
            set_user_id(self.user_id)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        clear_context()
    
    async def __aenter__(self):
        return self.__enter__()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__exit__(exc_type, exc_val, exc_tb)

