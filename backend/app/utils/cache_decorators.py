"""
Caching decorators for easy function result caching
"""
import functools
import hashlib
import json
from typing import Callable, Any, Optional
from app.utils.cache import get_cache, cache_key
from app.utils.logger import logger


def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    Decorator to cache function results
    
    Usage:
        @cached(ttl=300, key_prefix="scan_results")
        def get_scan_results(scan_id: str):
            # expensive operation
            return results
    
    Args:
        ttl: Time-to-live in seconds (None = use default)
        key_prefix: Prefix for cache key
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            cache = get_cache()
            
            # Generate cache key from function name and arguments
            # Convert args/kwargs to hashable string
            try:
                args_str = json.dumps(args, sort_keys=True, default=str)
                kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)
                key_parts = [key_prefix or func.__name__, args_str, kwargs_str]
                key_hash = hashlib.md5(
                    ":".join(key_parts).encode()
                ).hexdigest()
                full_key = cache_key(key_prefix or func.__name__, key_hash)
            except Exception as e:
                logger.warning(f"Failed to generate cache key: {e}")
                # If can't generate key, just execute function
                return func(*args, **kwargs)
            
            # Try to get from cache
            cached_value = cache.get(full_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(full_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


def cache_invalidate(key_prefix: str):
    """
    Decorator to invalidate cache entries with given prefix after function execution
    
    Usage:
        @cache_invalidate(key_prefix="scan_results")
        def delete_scan(scan_id: str):
            # delete operation
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            result = func(*args, **kwargs)
            
            # Note: This is a simple implementation
            # For prefix-based invalidation, we'd need to track keys
            # For now, we just clear the whole cache
            cache = get_cache()
            cache.clear()
            logger.info(f"Cache invalidated by {func.__name__}")
            
            return result
        
        return wrapper
    return decorator


# Specific cache decorators for common use cases
def cache_scan_results(ttl: int = 300):
    """Cache scan results for 5 minutes"""
    return cached(ttl=ttl, key_prefix="scan_results")


def cache_ai_analysis(ttl: int = 3600):
    """Cache AI analysis for 1 hour"""
    return cached(ttl=ttl, key_prefix="ai_analysis")


def cache_tool_output(ttl: int = 600):
    """Cache tool output for 10 minutes"""
    return cached(ttl=ttl, key_prefix="tool_output")
