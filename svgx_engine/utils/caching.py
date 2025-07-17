"""
SVGX Engine - Caching System

Comprehensive caching system with multiple backends,
TTL support, and performance monitoring.
"""

import time
import threading
import hashlib
import json
import pickle
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CacheBackend(Enum):
    """Cache backend types."""
    MEMORY = "memory"
    REDIS = "redis"
    DISK = "disk"


class CachePolicy(Enum):
    """Cache eviction policies."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In, First Out
    TTL = "ttl"  # Time To Live


@dataclass
class CacheEntry:
    """Cache entry structure."""
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    ttl: Optional[timedelta] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl is None:
            return False
        return datetime.now() - self.created_at > self.ttl
    
    def touch(self):
        """Update access time and count."""
        self.accessed_at = datetime.now()
        self.access_count += 1


class MemoryCache:
    """In-memory cache implementation."""
    
    def __init__(self, max_size: int = 1000, policy: CachePolicy = CachePolicy.LRU):
        self.max_size = max_size
        self.policy = policy
        self.cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._access_order: List[str] = []
        self._access_counts: Dict[str, int] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            
            # Check if expired
            if entry.is_expired():
                del self.cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                if key in self._access_counts:
                    del self._access_counts[key]
                return None
            
            # Update access info
            entry.touch()
            self._access_counts[key] = entry.access_count
            
            # Update access order for LRU
            if self.policy == CachePolicy.LRU:
                if key in self._access_order:
                    self._access_order.remove(key)
                self._access_order.append(key)
            
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None,
             metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Set value in cache."""
        with self._lock:
            # Check if we need to evict
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_entry()
            
            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                ttl=ttl,
                metadata=metadata or {}
            )
            
            self.cache[key] = entry
            self._access_counts[key] = 0
            
            # Update access order for LRU
            if self.policy == CachePolicy.LRU:
                if key in self._access_order:
                    self._access_order.remove(key)
                self._access_order.append(key)
            
            return True
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                if key in self._access_counts:
                    del self._access_counts[key]
                return True
            return False
    
    def clear(self):
        """Clear all entries."""
        with self._lock:
            self.cache.clear()
            self._access_order.clear()
            self._access_counts.clear()
    
    def size(self) -> int:
        """Get cache size."""
        return len(self.cache)
    
    def keys(self) -> List[str]:
        """Get all cache keys."""
        return list(self.cache.keys())
    
    def _evict_entry(self):
        """Evict an entry based on policy."""
        if not self.cache:
            return
        
        if self.policy == CachePolicy.LRU:
            # Remove least recently used
            if self._access_order:
                key_to_evict = self._access_order[0]
                del self.cache[key_to_evict]
                self._access_order.pop(0)
                if key_to_evict in self._access_counts:
                    del self._access_counts[key_to_evict]
        
        elif self.policy == CachePolicy.LFU:
            # Remove least frequently used
            if self._access_counts:
                min_key = min(self._access_counts.keys(), 
                             key=lambda k: self._access_counts[k])
                del self.cache[min_key]
                if min_key in self._access_order:
                    self._access_order.remove(min_key)
                del self._access_counts[min_key]
        
        elif self.policy == CachePolicy.FIFO:
            # Remove first in
            key_to_evict = next(iter(self.cache.keys()))
            del self.cache[key_to_evict]
            if key_to_evict in self._access_order:
                self._access_order.remove(key_to_evict)
            if key_to_evict in self._access_counts:
                del self._access_counts[key_to_evict]
        
        elif self.policy == CachePolicy.TTL:
            # Remove expired entries
            expired_keys = [key for key, entry in self.cache.items() 
                          if entry.is_expired()]
            for key in expired_keys:
                del self.cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                if key in self._access_counts:
                    del self._access_counts[key]
    
    def cleanup_expired(self):
        """Remove expired entries."""
        with self._lock:
            expired_keys = [key for key, entry in self.cache.items() 
                          if entry.is_expired()]
            for key in expired_keys:
                del self.cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                if key in self._access_counts:
                    del self._access_counts[key]


class CacheManager:
    """Centralized cache manager for SVGX Engine."""
    
    def __init__(self, backend: CacheBackend = CacheBackend.MEMORY,
                 max_size: int = 1000, policy: CachePolicy = CachePolicy.LRU):
        self.backend = backend
        self.max_size = max_size
        self.policy = policy
        self.cache = self._create_cache()
        self.stats = CacheStats()
        self._lock = threading.RLock()
    
    def _create_cache(self) -> MemoryCache:
        """Create cache instance based on backend."""
        if self.backend == CacheBackend.MEMORY:
            return MemoryCache(max_size=self.max_size, policy=self.policy)
        else:
            # For now, fallback to memory cache
            logger.warning(f"Backend {self.backend} not implemented, using memory cache")
            return MemoryCache(max_size=self.max_size, policy=self.policy)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        start_time = time.time()
        
        try:
            value = self.cache.get(key)
            
            # Update stats
            with self._lock:
                if value is not None:
                    self.stats.hits += 1
                else:
                    self.stats.misses += 1
                self.stats.total_requests += 1
            
            duration = (time.time() - start_time) * 1000
            self.stats.record_request(duration)
            
            return value
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.stats.errors += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None,
             metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Set value in cache."""
        start_time = time.time()
        
        try:
            success = self.cache.set(key, value, ttl, metadata)
            
            # Update stats
            with self._lock:
                if success:
                    self.stats.sets += 1
                self.stats.total_requests += 1
            
            duration = (time.time() - start_time) * 1000
            self.stats.record_request(duration)
            
            return success
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self.stats.errors += 1
            return False
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        start_time = time.time()
        
        try:
            success = self.cache.delete(key)
            
            # Update stats
            with self._lock:
                if success:
                    self.stats.deletes += 1
                self.stats.total_requests += 1
            
            duration = (time.time() - start_time) * 1000
            self.stats.record_request(duration)
            
            return success
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            self.stats.errors += 1
            return False
    
    def clear(self):
        """Clear all entries."""
        try:
            self.cache.clear()
            with self._lock:
                self.stats.clears += 1
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            self.stats.errors += 1
    
    def size(self) -> int:
        """Get cache size."""
        return self.cache.size()
    
    def keys(self) -> List[str]:
        """Get all cache keys."""
        return self.cache.keys()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            return {
                'backend': self.backend.value,
                'policy': self.policy.value,
                'max_size': self.max_size,
                'current_size': self.size(),
                'hits': self.stats.hits,
                'misses': self.stats.misses,
                'sets': self.stats.sets,
                'deletes': self.stats.deletes,
                'clears': self.stats.clears,
                'errors': self.stats.errors,
                'total_requests': self.stats.total_requests,
                'hit_rate': self.stats.hit_rate,
                'avg_response_time_ms': self.stats.avg_response_time,
                'request_times': self.stats.request_times[-10:]  # Last 10 requests
            }
    
    def cleanup(self):
        """Cleanup expired entries."""
        try:
            self.cache.cleanup_expired()
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")


class CacheStats:
    """Cache statistics."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.clears = 0
        self.errors = 0
        self.total_requests = 0
        self.request_times: List[float] = []
        self._lock = threading.Lock()
    
    @property
    def hit_rate(self) -> float:
        """Calculate hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests
    
    @property
    def avg_response_time(self) -> float:
        """Calculate average response time."""
        if not self.request_times:
            return 0.0
        return sum(self.request_times) / len(self.request_times)
    
    def record_request(self, duration_ms: float):
        """Record request duration."""
        with self._lock:
            self.request_times.append(duration_ms)
            # Keep only last 100 request times
            if len(self.request_times) > 100:
                self.request_times.pop(0)


class CacheDecorator:
    """Decorator for caching function results."""
    
    def __init__(self, cache_manager: CacheManager, ttl: Optional[timedelta] = None,
                 key_prefix: str = ""):
        self.cache_manager = cache_manager
        self.ttl = ttl
        self.key_prefix = key_prefix
    
    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = self._generate_key(func, args, kwargs)
            
            # Try to get from cache
            cached_value = self.cache_manager.get(key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            self.cache_manager.set(key, result, self.ttl)
            
            return result
        
        return wrapper
    
    def _generate_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function and arguments."""
        # Create a string representation of the function call
        func_name = func.__name__
        args_str = str(args)
        kwargs_str = str(sorted(kwargs.items()))
        
        # Create hash
        key_string = f"{self.key_prefix}:{func_name}:{args_str}:{kwargs_str}"
        return hashlib.md5(key_string.encode()).hexdigest()


# Global cache manager instance
_cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """Get the global cache manager."""
    return _cache_manager


def cache_result(ttl: Optional[timedelta] = None, key_prefix: str = ""):
    """Decorator to cache function results."""
    return CacheDecorator(_cache_manager, ttl, key_prefix)


def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    return _cache_manager.get(key)


def cache_set(key: str, value: Any, ttl: Optional[timedelta] = None,
              metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Set value in cache."""
    return _cache_manager.set(key, value, ttl, metadata)


def cache_delete(key: str) -> bool:
    """Delete value from cache."""
    return _cache_manager.delete(key)


def cache_clear():
    """Clear all cache entries."""
    _cache_manager.clear()


def cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    return _cache_manager.get_stats()


def cache_cleanup():
    """Cleanup expired cache entries."""
    _cache_manager.cleanup()


def setup_cache(backend: CacheBackend = CacheBackend.MEMORY,
                max_size: int = 1000, policy: CachePolicy = CachePolicy.LRU):
    """Setup cache with custom configuration."""
    global _cache_manager
    _cache_manager = CacheManager(backend, max_size, policy) 