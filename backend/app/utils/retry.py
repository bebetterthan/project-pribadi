"""
Retry utility with exponential backoff for resilience
"""
import asyncio
import random
import time
from typing import Callable, TypeVar, Any, Optional, Type, Tuple
from functools import wraps
from app.utils.logger import logger

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior"""
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


class RetryableError(Exception):
    """Base class for errors that should trigger retry"""
    pass


class NonRetryableError(Exception):
    """Base class for errors that should NOT trigger retry"""
    pass


def is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error should trigger a retry
    
    Retryable:
    - Network errors (ConnectionError, TimeoutError)
    - Rate limit errors (contains "429", "rate limit", "quota")
    - Server errors (contains "500", "502", "503")
    - Explicit RetryableError
    
    Non-Retryable:
    - Authentication errors (contains "401", "unauthorized")
    - Authorization errors (contains "403", "forbidden")
    - Validation errors (contains "400", "invalid")
    - Explicit NonRetryableError
    """
    if isinstance(error, NonRetryableError):
        return False
    
    if isinstance(error, (RetryableError, ConnectionError, TimeoutError, asyncio.TimeoutError)):
        return True
    
    error_str = str(error).lower()
    
    # Non-retryable patterns
    non_retryable_patterns = ['401', 'unauthorized', '403', 'forbidden', '400', 'invalid', '404', 'not found']
    if any(pattern in error_str for pattern in non_retryable_patterns):
        return False
    
    # Retryable patterns
    retryable_patterns = ['429', 'rate limit', 'quota', '500', '502', '503', 'timeout', 'connection']
    if any(pattern in error_str for pattern in retryable_patterns):
        return True
    
    # Default: don't retry unknown errors
    return False


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay for next retry with exponential backoff and jitter"""
    delay = min(
        config.base_delay * (config.exponential_base ** attempt),
        config.max_delay
    )
    
    if config.jitter:
        # Add random jitter (0-20% of delay) to avoid thundering herd
        jitter = random.uniform(0, 0.2 * delay)
        delay += jitter
    
    return delay


def retry_sync(
    config: Optional[RetryConfig] = None,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator for synchronous functions with retry logic
    
    Usage:
        @retry_sync(RetryConfig(max_retries=3))
        def my_function():
            # ... code that might fail
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_error = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_error = e
                    
                    # Check if error is retryable
                    if not is_retryable_error(e):
                        logger.warning(f"Non-retryable error in {func.__name__}: {e}")
                        raise
                    
                    # If this was the last attempt, raise
                    if attempt == config.max_retries:
                        logger.error(
                            f"Max retries ({config.max_retries}) reached for {func.__name__}",
                            extra={"error": str(e), "attempts": attempt + 1}
                        )
                        raise
                    
                    # Calculate delay and log retry
                    delay = calculate_delay(attempt, config)
                    logger.warning(
                        f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} after {delay:.2f}s",
                        extra={"error": str(e), "delay": delay}
                    )
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            if last_error:
                raise last_error
            raise RuntimeError(f"Unexpected state in retry logic for {func.__name__}")
        
        return wrapper
    return decorator


def retry_async(
    config: Optional[RetryConfig] = None,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator for async functions with retry logic
    
    Usage:
        @retry_async(RetryConfig(max_retries=3))
        async def my_async_function():
            # ... async code that might fail
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_error = e
                    
                    # Check if error is retryable
                    if not is_retryable_error(e):
                        logger.warning(f"Non-retryable error in {func.__name__}: {e}")
                        raise
                    
                    # If this was the last attempt, raise
                    if attempt == config.max_retries:
                        logger.error(
                            f"Max retries ({config.max_retries}) reached for {func.__name__}",
                            extra={"error": str(e), "attempts": attempt + 1}
                        )
                        raise
                    
                    # Calculate delay and log retry
                    delay = calculate_delay(attempt, config)
                    logger.warning(
                        f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} after {delay:.2f}s",
                        extra={"error": str(e), "delay": delay}
                    )
                    await asyncio.sleep(delay)
            
            # Should never reach here, but just in case
            if last_error:
                raise last_error
            raise RuntimeError(f"Unexpected state in retry logic for {func.__name__}")
        
        return wrapper
    return decorator


# Default retry configs for different scenarios
GEMINI_API_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    base_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True
)

DATABASE_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    base_delay=0.5,
    max_delay=5.0,
    exponential_base=2.0,
    jitter=True
)

TOOL_EXECUTION_RETRY_CONFIG = RetryConfig(
    max_retries=2,
    base_delay=2.0,
    max_delay=10.0,
    exponential_base=2.0,
    jitter=True
)

