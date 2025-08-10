"""
Advanced Caching Strategies and Optimization.

Provides intelligent caching strategies, cache warming, invalidation patterns,
and performance optimization for various cache scenarios.
"""

import time
import json
import hashlib
import threading
from typing import Dict, Any, Optional, List, Union, Callable, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from abc import ABC, abstractmethod
from collections import defaultdict, OrderedDict
import asyncio
from contextlib import contextmanager

from infrastructure.logging.structured_logging import get_logger, performance_logger
from infrastructure.performance.monitoring import performance_monitor


logger = get_logger(__name__)


class CacheStrategy(Enum):
    """Cache strategy types."""
    LRU = "lru"                    # Least Recently Used
    LFU = "lfu"                    # Least Frequently Used  
    FIFO = "fifo"                  # First In First Out
    ADAPTIVE = "adaptive"          # Adaptive replacement
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"
    REFRESH_AHEAD = "refresh_ahead"


class CacheLevel(Enum):
    """Cache hierarchy levels."""
    L1_MEMORY = "l1_memory"        # In-process memory cache
    L2_REDIS = "l2_redis"          # Redis cache
    L3_DATABASE = "l3_database"    # Database query cache
    CDN = "cdn"                    # Content Delivery Network


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    total_size_bytes: int = 0
    avg_response_time_ms: float = 0.0
    hit_rate_percent: float = 0.0
    
    def update_hit(self, response_time_ms: float) -> None:
        """Update metrics for cache hit."""
        self.hits += 1
        self.total_requests += 1
        self._update_avg_response_time(response_time_ms)
        self._calculate_hit_rate()
    
    def update_miss(self, response_time_ms: float) -> None:
        """Update metrics for cache miss."""
        self.misses += 1
        self.total_requests += 1
        self._update_avg_response_time(response_time_ms)
        self._calculate_hit_rate()
    
    def update_eviction(self) -> None:
        """Update metrics for cache eviction."""
        self.evictions += 1
    
    def _update_avg_response_time(self, response_time_ms: float) -> None:
        """Update average response time."""
        if self.total_requests == 1:
            self.avg_response_time_ms = response_time_ms
        else:
            # Rolling average
            self.avg_response_time_ms = (
                (self.avg_response_time_ms * (self.total_requests - 1) + response_time_ms) 
                / self.total_requests
            )
    
    def _calculate_hit_rate(self) -> None:
        """Calculate hit rate percentage."""
        if self.total_requests > 0:
            self.hit_rate_percent = (self.hits / self.total_requests) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "total_requests": self.total_requests,
            "total_size_bytes": self.total_size_bytes,
            "avg_response_time_ms": round(self.avg_response_time_ms, 2),
            "hit_rate_percent": round(self.hit_rate_percent, 2)
        }


@dataclass 
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    size_bytes: int = 0
    tags: Set[str] = field(default_factory=set)
    
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl_seconds is None:
            return False
        
        age_seconds = (datetime.now(timezone.utc) - self.created_at).total_seconds()
        return age_seconds > self.ttl_seconds
    
    def touch(self) -> None:
        """Update access information."""
        self.last_accessed = datetime.now(timezone.utc)
        self.access_count += 1
    
    def calculate_size(self) -> int:
        """Calculate approximate size in bytes."""
        try:
            if isinstance(self.value, (str, bytes)):
                self.size_bytes = len(self.value)
            else:
                # Approximate size using JSON serialization
                json_str = json.dumps(self.value, default=str)
                self.size_bytes = len(json_str.encode('utf-8'))
        except:
            self.size_bytes = 1024  # Default estimate
        
        return self.size_bytes


class IntelligentCache:
    """Intelligent multi-level cache with adaptive strategies."""
    
    def __init__(self, max_size: int = 10000, max_memory_mb: int = 100,
                 default_ttl: int = 3600, strategy: CacheStrategy = CacheStrategy.ADAPTIVE):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl = default_ttl
        self.strategy = strategy
        
        # Cache storage
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order = OrderedDict()  # For LRU
        self.frequency_counter = defaultdict(int)  # For LFU
        
        # Metrics and monitoring
        self.metrics = CacheMetrics()
        self.lock = threading.RLock()
        
        # Adaptive strategy parameters
        self.hit_rate_window = deque(maxlen=1000)
        self.strategy_performance = {
            CacheStrategy.LRU: deque(maxlen=100),
            CacheStrategy.LFU: deque(maxlen=100)
        }
        
        # Background maintenance
        self.maintenance_thread = None
        self.maintenance_active = False
        
        logger.info(f"Initialized intelligent cache with strategy: {strategy.value}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        start_time = time.time()
        
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # Check expiration
                if entry.is_expired():
                    self._remove_entry(key)
                    self.metrics.update_miss((time.time() - start_time) * 1000)
                    
                    performance_monitor.collector.increment_counter(
                        "cache.expired_entries_total", 1.0, {"strategy": self.strategy.value}
                    )
                    return default
                
                # Update access information
                entry.touch()
                self._update_access_order(key)
                
                self.metrics.update_hit((time.time() - start_time) * 1000)
                
                performance_monitor.collector.record_cache_performance(
                    operation="get",
                    hit=True,
                    duration=(time.time() - start_time),
                    key_pattern=self._get_key_pattern(key)
                )
                
                return entry.value
            
            self.metrics.update_miss((time.time() - start_time) * 1000)
            
            performance_monitor.collector.record_cache_performance(
                operation="get",
                hit=False,
                duration=(time.time() - start_time),
                key_pattern=self._get_key_pattern(key)
            )
            
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, 
            tags: Optional[Set[str]] = None) -> bool:
        """Set value in cache."""
        start_time = time.time()
        
        with self.lock:
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(timezone.utc),
                last_accessed=datetime.now(timezone.utc),
                ttl_seconds=ttl or self.default_ttl,
                tags=tags or set()
            )
            entry.calculate_size()
            
            # Check if we need to make space
            if not self._ensure_capacity(entry.size_bytes):
                logger.warning(f"Failed to make space for cache key: {key}")
                return False
            
            # Store entry
            self.cache[key] = entry
            self._update_access_order(key)
            
            # Update metrics
            self.metrics.total_size_bytes += entry.size_bytes
            
            performance_monitor.collector.record_cache_performance(
                operation="set",
                hit=True,
                duration=(time.time() - start_time),
                key_pattern=self._get_key_pattern(key)
            )
            
            return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self.lock:
            if key in self.cache:
                self._remove_entry(key)
                return True
            return False
    
    def invalidate_by_tags(self, tags: Set[str]) -> int:
        """Invalidate cache entries by tags."""
        count = 0
        with self.lock:
            keys_to_remove = []
            for key, entry in self.cache.items():
                if entry.tags.intersection(tags):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                self._remove_entry(key)
                count += 1
        
        logger.info(f"Invalidated {count} cache entries by tags: {tags}")
        return count
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()
            self.frequency_counter.clear()
            self.metrics.total_size_bytes = 0
        
        logger.info("Cache cleared")
    
    def _ensure_capacity(self, required_bytes: int) -> bool:
        """Ensure cache has capacity for new entry."""
        # Check size limit
        if len(self.cache) >= self.max_size:
            if not self._evict_entries(1):
                return False
        
        # Check memory limit
        if self.metrics.total_size_bytes + required_bytes > self.max_memory_bytes:
            bytes_to_free = (self.metrics.total_size_bytes + required_bytes) - self.max_memory_bytes
            if not self._evict_entries_by_size(bytes_to_free):
                return False
        
        return True
    
    def _evict_entries(self, count: int) -> bool:
        """Evict entries based on strategy."""
        evicted = 0
        
        if self.strategy == CacheStrategy.LRU:
            evicted = self._evict_lru(count)
        elif self.strategy == CacheStrategy.LFU:
            evicted = self._evict_lfu(count)
        elif self.strategy == CacheStrategy.FIFO:
            evicted = self._evict_fifo(count)
        elif self.strategy == CacheStrategy.ADAPTIVE:
            evicted = self._evict_adaptive(count)
        
        return evicted >= count
    
    def _evict_entries_by_size(self, bytes_to_free: int) -> bool:
        """Evict entries to free specified bytes."""
        freed_bytes = 0
        
        # Use current strategy to select victims
        if self.strategy == CacheStrategy.LRU:
            # Evict least recently used
            for key in list(self.access_order.keys()):
                if freed_bytes >= bytes_to_free:
                    break
                entry = self.cache[key]
                freed_bytes += entry.size_bytes
                self._remove_entry(key)
        
        elif self.strategy == CacheStrategy.LFU:
            # Evict least frequently used
            sorted_keys = sorted(
                self.cache.keys(),
                key=lambda k: (self.frequency_counter[k], self.cache[k].last_accessed)
            )
            
            for key in sorted_keys:
                if freed_bytes >= bytes_to_free:
                    break
                entry = self.cache[key]
                freed_bytes += entry.size_bytes
                self._remove_entry(key)
        
        return freed_bytes >= bytes_to_free
    
    def _evict_lru(self, count: int) -> int:
        """Evict least recently used entries."""
        evicted = 0
        keys_to_remove = list(self.access_order.keys())[:count]
        
        for key in keys_to_remove:
            self._remove_entry(key)
            evicted += 1
        
        return evicted
    
    def _evict_lfu(self, count: int) -> int:
        """Evict least frequently used entries."""
        evicted = 0
        
        # Sort by frequency and last access time
        sorted_keys = sorted(
            self.cache.keys(),
            key=lambda k: (self.frequency_counter[k], self.cache[k].last_accessed)
        )
        
        for key in sorted_keys[:count]:
            self._remove_entry(key)
            evicted += 1
        
        return evicted
    
    def _evict_fifo(self, count: int) -> int:
        """Evict first in, first out entries."""
        evicted = 0
        
        # Sort by creation time
        sorted_keys = sorted(
            self.cache.keys(),
            key=lambda k: self.cache[k].created_at
        )
        
        for key in sorted_keys[:count]:
            self._remove_entry(key)
            evicted += 1
        
        return evicted
    
    def _evict_adaptive(self, count: int) -> int:
        """Adaptive eviction based on recent performance."""
        # Use the strategy that has been performing better recently
        lru_performance = statistics.mean(self.strategy_performance[CacheStrategy.LRU]) if self.strategy_performance[CacheStrategy.LRU] else 0
        lfu_performance = statistics.mean(self.strategy_performance[CacheStrategy.LFU]) if self.strategy_performance[CacheStrategy.LFU] else 0
        
        if lru_performance >= lfu_performance:
            return self._evict_lru(count)
        else:
            return self._evict_lfu(count)
    
    def _remove_entry(self, key: str) -> None:
        """Remove entry from cache and update structures."""
        if key in self.cache:
            entry = self.cache[key]
            self.metrics.total_size_bytes -= entry.size_bytes
            self.metrics.update_eviction()
            
            del self.cache[key]
            
            if key in self.access_order:
                del self.access_order[key]
            
            if key in self.frequency_counter:
                del self.frequency_counter[key]
    
    def _update_access_order(self, key: str) -> None:
        """Update access order for LRU strategy."""
        if key in self.access_order:
            self.access_order.move_to_end(key)
        else:
            self.access_order[key] = True
        
        # Update frequency counter
        self.frequency_counter[key] += 1
    
    def _get_key_pattern(self, key: str) -> str:
        """Extract pattern from cache key for metrics."""
        # Simple pattern extraction - customize based on key naming convention
        parts = key.split(':')
        return parts[0] if parts else "unknown"
    
    def start_maintenance(self) -> None:
        """Start background maintenance thread."""
        if not self.maintenance_active:
            self.maintenance_active = True
            self.maintenance_thread = threading.Thread(
                target=self._maintenance_loop,
                daemon=True
            )
            self.maintenance_thread.start()
            logger.info("Cache maintenance started")
    
    def stop_maintenance(self) -> None:
        """Stop background maintenance."""
        self.maintenance_active = False
        if self.maintenance_thread:
            self.maintenance_thread.join(timeout=5)
        logger.info("Cache maintenance stopped")
    
    def _maintenance_loop(self) -> None:
        """Background maintenance loop."""
        while self.maintenance_active:
            try:
                self._cleanup_expired_entries()
                self._collect_performance_metrics()
                time.sleep(300)  # Run every 5 minutes
            except Exception as e:
                logger.error(f"Error in cache maintenance: {e}")
                time.sleep(300)
    
    def _cleanup_expired_entries(self) -> None:
        """Clean up expired cache entries."""
        expired_keys = []
        
        with self.lock:
            for key, entry in self.cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
        
        for key in expired_keys:
            with self.lock:
                if key in self.cache:  # Double-check in case it was removed
                    self._remove_entry(key)
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def _collect_performance_metrics(self) -> None:
        """Collect and report performance metrics."""
        metrics_dict = self.metrics.to_dict()
        
        # Report to performance monitor
        performance_monitor.collector.set_gauge("cache.size_entries", len(self.cache))
        performance_monitor.collector.set_gauge("cache.size_bytes", self.metrics.total_size_bytes)
        performance_monitor.collector.set_gauge("cache.hit_rate_percent", self.metrics.hit_rate_percent)
        performance_monitor.collector.set_gauge("cache.avg_response_time_ms", self.metrics.avg_response_time_ms)
        
        logger.debug("Cache performance metrics", extra={"metrics": metrics_dict})
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current cache metrics."""
        with self.lock:
            return {
                **self.metrics.to_dict(),
                "strategy": self.strategy.value,
                "entry_count": len(self.cache),
                "max_size": self.max_size,
                "max_memory_mb": self.max_memory_bytes // (1024 * 1024)
            }


class MultiLevelCache:
    """Multi-level cache hierarchy with intelligent promotion/demotion."""
    
    def __init__(self):
        self.levels = {
            CacheLevel.L1_MEMORY: IntelligentCache(max_size=1000, max_memory_mb=50),
            CacheLevel.L2_REDIS: None,  # Would be Redis client in production
        }
        
        self.promotion_threshold = 3  # Promote after 3 hits in L2
        self.access_counters = defaultdict(int)
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from multi-level cache."""
        # Try L1 first
        l1_cache = self.levels[CacheLevel.L1_MEMORY]
        value = l1_cache.get(key)
        
        if value is not None:
            return value
        
        # Try L2 (Redis) - mock implementation
        if self.levels[CacheLevel.L2_REDIS]:
            # In production, this would query Redis
            value = None  # Mock Redis get
            
            if value is not None:
                # Track access for potential promotion
                self.access_counters[key] += 1
                
                # Promote to L1 if accessed frequently
                if self.access_counters[key] >= self.promotion_threshold:
                    l1_cache.set(key, value, ttl=1800)  # Shorter TTL in L1
                    logger.debug(f"Promoted key {key} from L2 to L1")
                
                return value
        
        return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in multi-level cache."""
        # Always set in L1
        l1_cache = self.levels[CacheLevel.L1_MEMORY]
        l1_cache.set(key, value, ttl)
        
        # Also set in L2 with longer TTL
        if self.levels[CacheLevel.L2_REDIS]:
            # In production, set in Redis with longer TTL
            redis_ttl = (ttl or 3600) * 2
            # redis_client.setex(key, redis_ttl, value)
    
    def invalidate(self, key: str) -> None:
        """Invalidate key across all cache levels."""
        for cache in self.levels.values():
            if cache:
                cache.delete(key)
        
        if key in self.access_counters:
            del self.access_counters[key]


class CacheWarmupManager:
    """Manages cache warming strategies."""
    
    def __init__(self, cache: Union[IntelligentCache, MultiLevelCache]):
        self.cache = cache
        self.warmup_strategies = {}
        
    def register_warmup_strategy(self, name: str, strategy_func: Callable[[], Dict[str, Any]]) -> None:
        """Register a cache warmup strategy."""
        self.warmup_strategies[name] = strategy_func
        logger.info(f"Registered cache warmup strategy: {name}")
    
    async def warmup_cache(self, strategies: Optional[List[str]] = None) -> Dict[str, int]:
        """Warm up cache using specified strategies."""
        strategies = strategies or list(self.warmup_strategies.keys())
        results = {}
        
        for strategy_name in strategies:
            if strategy_name in self.warmup_strategies:
                try:
                    start_time = time.time()
                    strategy_func = self.warmup_strategies[strategy_name]
                    
                    # Execute strategy
                    data = strategy_func()
                    
                    # Load data into cache
                    loaded_count = 0
                    for key, value in data.items():
                        self.cache.set(key, value)
                        loaded_count += 1
                    
                    duration = time.time() - start_time
                    results[strategy_name] = loaded_count
                    
                    logger.info(f"Cache warmup '{strategy_name}' completed", extra={
                        "loaded_entries": loaded_count,
                        "duration_seconds": duration
                    })
                    
                except Exception as e:
                    logger.error(f"Cache warmup '{strategy_name}' failed: {e}")
                    results[strategy_name] = 0
        
        return results
    
    def schedule_periodic_warmup(self, strategies: List[str], interval_minutes: int = 60) -> None:
        """Schedule periodic cache warmup."""
        def warmup_task():
            while True:
                try:
                    asyncio.run(self.warmup_cache(strategies))
                except Exception as e:
                    logger.error(f"Scheduled cache warmup failed: {e}")
                
                time.sleep(interval_minutes * 60)
        
        warmup_thread = threading.Thread(target=warmup_task, daemon=True)
        warmup_thread.start()
        
        logger.info(f"Scheduled periodic cache warmup every {interval_minutes} minutes")


# Global cache instances
intelligent_cache = IntelligentCache(
    max_size=10000,
    max_memory_mb=100,
    default_ttl=3600,
    strategy=CacheStrategy.ADAPTIVE
)

multi_level_cache = MultiLevelCache()
cache_warmup_manager = CacheWarmupManager(intelligent_cache)


def cached(ttl: int = 3600, key_prefix: str = "", 
          tags: Optional[Set[str]] = None, cache_instance: Optional[IntelligentCache] = None):
    """Decorator for caching function results."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache = cache_instance or intelligent_cache
            
            # Generate cache key
            key_parts = [key_prefix or func.__name__]
            
            # Add args to key
            for arg in args:
                if isinstance(arg, (str, int, float, bool)):
                    key_parts.append(str(arg))
                else:
                    key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])
            
            # Add kwargs to key
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (str, int, float, bool)):
                    key_parts.append(f"{k}:{v}")
                else:
                    key_parts.append(f"{k}:{hashlib.md5(str(v).encode()).hexdigest()[:8]}")
            
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Cache the result
            cache.set(cache_key, result, ttl=ttl, tags=tags)
            
            # Log cache miss
            performance_logger.log_cache_operation(
                operation="miss",
                key=cache_key,
                hit=False,
                duration=execution_time
            )
            
            return result
        
        return wrapper
    return decorator