"""
Simple in-memory cache implementation
Lightweight alternative to Redis for development/personal projects
"""
import time
from typing import Any, Optional, Dict
from threading import Lock
from collections import OrderedDict
from app.utils.logger import logger


class SimpleCache:
    """
    Thread-safe in-memory cache with TTL and LRU eviction
    
    Features:
    - Time-to-live (TTL) expiration
    - LRU eviction when max size reached
    - Thread-safe operations
    - Simple key-value storage
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize cache
        
        Args:
            max_size: Maximum number of items in cache
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if exists and not expired"""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            item = self._cache[key]
            
            # Check if expired
            if time.time() > item['expires_at']:
                del self._cache[key]
                self._misses += 1
                logger.debug(f"Cache EXPIRED: {key}")
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            logger.debug(f"Cache HIT: {key}")
            return item['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL"""
        with self._lock:
            # Use default TTL if not specified
            ttl = ttl or self.default_ttl
            expires_at = time.time() + ttl
            
            # If key exists, update and move to end
            if key in self._cache:
                self._cache[key] = {'value': value, 'expires_at': expires_at}
                self._cache.move_to_end(key)
                logger.debug(f"Cache UPDATE: {key} (TTL: {ttl}s)")
                return
            
            # If cache is full, remove oldest item (LRU)
            if len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                logger.debug(f"Cache EVICTED (LRU): {oldest_key}")
            
            # Add new item
            self._cache[key] = {'value': value, 'expires_at': expires_at}
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache DELETE: {key}")
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache CLEARED: {count} items removed")
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries"""
        with self._lock:
            now = time.time()
            expired_keys = [
                key for key, item in self._cache.items()
                if now > item['expires_at']
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info(f"Cache CLEANUP: {len(expired_keys)} expired items removed")
            
            return len(expired_keys)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': f"{hit_rate:.2f}%",
                'total_requests': total_requests
            }
    
    def reset_stats(self) -> None:
        """Reset statistics counters"""
        with self._lock:
            self._hits = 0
            self._misses = 0
            logger.info("Cache stats RESET")


# Global cache instance
_cache_instance: Optional[SimpleCache] = None


def get_cache() -> SimpleCache:
    """Get or create global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        from app.config import settings
        _cache_instance = SimpleCache(
            max_size=1000,
            default_ttl=settings.CACHE_TTL if hasattr(settings, 'CACHE_TTL') else 3600
        )
        logger.info("Cache initialized")
    return _cache_instance


def cache_key(*args) -> str:
    """Generate cache key from arguments"""
    return ":".join(str(arg) for arg in args)
