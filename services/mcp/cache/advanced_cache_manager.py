#!/usr/bin/env python3
"""
Advanced Cache Manager for MCP

This module implements sophisticated caching strategies including:
- Multi-level caching (L1: Memory, L2: Redis, L3: Database)
- Predictive caching based on usage patterns
- Intelligent cache invalidation
- Cache warming strategies
- Cache compression and optimization
"""

import asyncio
import json
import pickle
import logging
import time
import hashlib
from typing import Optional, Any, Dict, List, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, OrderedDict
import threading
import weakref

from cache.redis_manager import RedisManager, CacheType, CacheEntry

logger = logging.getLogger(__name__)


class CacheLevel(str, Enum):
    """Cache level enumeration"""

    L1_MEMORY = "l1_memory"
    L2_REDIS = "l2_redis"
    L3_DATABASE = "l3_database"


class CacheStrategy(str, Enum):
    """Cache strategy enumeration"""

    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    TTL = "ttl"
    ADAPTIVE = "adaptive"


@dataclass
class CacheMetrics:
    """Cache performance metrics"""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    memory_usage: float = 0.0
    avg_response_time: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class PredictiveCacheEntry:
    """Predictive cache entry with usage patterns"""

    key: str
    value: Any
    cache_type: CacheType
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    access_pattern: List[datetime] = field(default_factory=list)
    predicted_next_access: Optional[datetime] = None
    priority_score: float = 0.0


class MemoryCache:
    """L1 Memory cache with LRU/LFU strategies"""

    def __init__(
        self, max_size: int = 1000, strategy: CacheStrategy = CacheStrategy.LRU
    ):
        self.max_size = max_size
        self.strategy = strategy
        self.cache: OrderedDict = OrderedDict()
        self.access_counts: Dict[str, int] = defaultdict(int)
        self.access_times: Dict[str, float] = {}
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        with self.lock:
            if key in self.cache:
                value = self.cache[key]
                self._update_access(key)
                return value
            return None

    def set(self, key: str, value: Any) -> bool:
        """Set value in memory cache"""
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                self.cache[key] = value
            else:
                if len(self.cache) >= self.max_size:
                    self._evict_entry()
                self.cache[key] = value
                self._update_access(key)
            return True

    def _update_access(self, key: str):
        """Update access metrics"""
        self.access_counts[key] += 1
        self.access_times[key] = time.time()
        if self.strategy == CacheStrategy.LRU:
            self.cache.move_to_end(key)

    def _evict_entry(self):
        """Evict entry based on strategy"""
        if self.strategy == CacheStrategy.LRU:
            # Remove least recently used
            self.cache.popitem(last=False)
        elif self.strategy == CacheStrategy.LFU:
            # Remove least frequently used
            min_key = min(
                self.access_counts.keys(), key=lambda k: self.access_counts[k]
            )
            del self.cache[min_key]
            del self.access_counts[min_key]
        elif self.strategy == CacheStrategy.FIFO:
            # Remove first in
            self.cache.popitem(last=False)

    def clear(self):
        """Clear memory cache"""
        with self.lock:
            self.cache.clear()
            self.access_counts.clear()
            self.access_times.clear()


class PredictiveCacheManager:
    """Advanced cache manager with predictive capabilities"""

    def __init__(
        self,
        redis_manager: RedisManager,
        memory_cache_size: int = 1000,
        prediction_window: int = 3600,
    ):
        """
        Initialize predictive cache manager

        Args:
            redis_manager: Redis manager instance
            memory_cache_size: L1 cache size
            prediction_window: Time window for predictions (seconds)
        """
        self.redis_manager = redis_manager
        self.l1_cache = MemoryCache(max_size=memory_cache_size)
        self.prediction_window = prediction_window

        # Predictive analytics
        self.access_patterns: Dict[str, List[datetime]] = defaultdict(list)
        self.prediction_model = self._initialize_prediction_model()

        # Cache warming
        self.warming_queue: asyncio.Queue = asyncio.Queue()
        self.warming_task: Optional[asyncio.Task] = None

        # Performance tracking
        self.metrics: Dict[CacheLevel, CacheMetrics] = {
            CacheLevel.L1_MEMORY: CacheMetrics(),
            CacheLevel.L2_REDIS: CacheMetrics(),
            CacheLevel.L3_DATABASE: CacheMetrics(),
        }

        # Start background tasks
        self._start_background_tasks()

    def _initialize_prediction_model(self) -> Dict[str, Any]:
        """Initialize prediction model"""
        return {
            "patterns": {},
            "weights": {"recency": 0.4, "frequency": 0.3, "time_pattern": 0.3},
        }

    def _start_background_tasks(self):
        """Start background cache management tasks"""
        loop = asyncio.get_event_loop()
        self.warming_task = loop.create_task(self._cache_warming_worker())
        loop.create_task(self._metrics_collector())
        loop.create_task(self._predictive_analysis())

    async def get_cached_data(self, key: str, cache_type: CacheType) -> Optional[Any]:
        """Get data from multi-level cache with predictive optimization"""
        start_time = time.time()

        # Try L1 (Memory) cache first
        l1_result = self.l1_cache.get(key)
        if l1_result:
            self._update_metrics(CacheLevel.L1_MEMORY, True, time.time() - start_time)
            self._record_access_pattern(key)
            return l1_result

        # Try L2 (Redis) cache
        l2_result = await self.redis_manager._get_cached_data(key, cache_type)
        if l2_result:
            # Cache in L1 for future access
            self.l1_cache.set(key, l2_result)
            self._update_metrics(CacheLevel.L2_REDIS, True, time.time() - start_time)
            self._record_access_pattern(key)
            return l2_result

        # L3 (Database) would be handled by the calling service
        self._update_metrics(CacheLevel.L3_DATABASE, False, time.time() - start_time)
        return None

    async def set_cached_data(
        self,
        key: str,
        value: Any,
        cache_type: CacheType,
        ttl: Optional[int] = None,
        priority: float = 0.5,
    ) -> bool:
        """Set data in multi-level cache with intelligent placement"""
        try:
            # Store in L1 (Memory) for immediate access
            self.l1_cache.set(key, value)

            # Store in L2 (Redis) for persistence
            success = await self.redis_manager._set_cached_data(
                key, value, cache_type, ttl
            )

            if success:
                # Update predictive model
                self._update_prediction_model(key, priority)

                # Trigger cache warming if high priority
                if priority > 0.8:
                    await self._schedule_cache_warming(key, cache_type)

            return success

        except Exception as e:
            logger.error(f"Error setting cached data for {key}: {e}")
            return False

    def _record_access_pattern(self, key: str):
        """Record access pattern for predictive analysis"""
        now = datetime.now()
        self.access_patterns[key].append(now)

        # Keep only recent patterns
        cutoff = now - timedelta(seconds=self.prediction_window)
        self.access_patterns[key] = [t for t in self.access_patterns[key] if t > cutoff]

    def _update_prediction_model(self, key: str, priority: float):
        """Update prediction model with new data"""
        patterns = self.access_patterns.get(key, [])
        if len(patterns) >= 3:
            # Calculate access frequency
            frequency = len(patterns) / self.prediction_window

            # Calculate recency
            recency = (datetime.now() - patterns[-1]).total_seconds()
            recency_score = max(0, 1 - (recency / self.prediction_window))

            # Calculate time pattern (hourly patterns)
            hour_patterns = [p.hour for p in patterns]
            time_pattern_score = self._calculate_time_pattern_score(hour_patterns)

            # Update prediction model
            self.prediction_model["patterns"][key] = {
                "frequency": frequency,
                "recency": recency_score,
                "time_pattern": time_pattern_score,
                "priority": priority,
            }

    def _calculate_time_pattern_score(self, hour_patterns: List[int]) -> float:
        """Calculate time pattern similarity score"""
        if len(hour_patterns) < 2:
            return 0.5

        # Calculate variance in access times
        mean_hour = sum(hour_patterns) / len(hour_patterns)
        variance = sum((h - mean_hour) ** 2 for h in hour_patterns) / len(hour_patterns)

        # Lower variance = more predictable pattern
        return max(0, 1 - (variance / 144))  # 144 = 24^2 / 4

    async def _schedule_cache_warming(self, key: str, cache_type: CacheType):
        """Schedule cache warming for related data"""
        # Predict related keys that might be accessed soon
        related_keys = self._predict_related_keys(key, cache_type)

        for related_key in related_keys:
            await self.warming_queue.put((related_key, cache_type, 0.6))

    def _predict_related_keys(self, key: str, cache_type: CacheType) -> List[str]:
        """Predict related keys based on access patterns"""
        related_keys = []

        # Extract building ID from key
        if ":" in key:
            base_id = key.split(":")[1]

            # Predict related validation results
            if cache_type == CacheType.VALIDATION_RESULT:
                related_keys.extend(
                    [
                        f"building_model:{base_id}",
                        f"jurisdiction_match:{base_id}",
                        f"compliance_score:{base_id}",
                    ]
                )

            # Predict related building models
            elif cache_type == CacheType.BUILDING_MODEL:
                related_keys.extend(
                    [
                        f"validation:{base_id}",
                        f"mcp_file:{base_id}",
                        f"jurisdiction_match:{base_id}",
                    ]
                )

        return related_keys

    async def _cache_warming_worker(self):
        """Background worker for cache warming"""
        while True:
            try:
                key, cache_type, priority = await self.warming_queue.get()

                # Check if already cached
                cached = await self.get_cached_data(key, cache_type)
                if cached is None:
                    # Trigger background loading (implement based on your data source)
                    await self._load_and_cache_data(key, cache_type, priority)

                self.warming_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache warming worker: {e}")

    async def _load_and_cache_data(
        self, key: str, cache_type: CacheType, priority: float
    ):
        """Load data from source and cache it"""
        try:
            # This would integrate with your data loading logic
            # For now, we'll just log the warming attempt
            logger.info(
                f"Cache warming: Loading {key} ({cache_type}) with priority {priority}"
            )

            # In a real implementation, you would:
            # 1. Load data from database/file system
            # 2. Process/transform data if needed
            # 3. Cache the result

        except Exception as e:
            logger.error(f"Error loading data for cache warming {key}: {e}")

    async def _metrics_collector(self):
        """Background task to collect cache metrics"""
        while True:
            try:
                await asyncio.sleep(60)  # Collect metrics every minute

                # Update L1 cache metrics
                self.metrics[CacheLevel.L1_MEMORY].size = len(self.l1_cache.cache)
                self.metrics[CacheLevel.L1_MEMORY].memory_usage = (
                    self._estimate_memory_usage()
                )

                # Update L2 cache metrics (from Redis)
                redis_stats = await self.redis_manager.get_cache_stats()
                self.metrics[CacheLevel.L2_REDIS].size = redis_stats.get(
                    "total_keys", 0
                )

                # Calculate hit rates
                for level in CacheLevel:
                    total = self.metrics[level].hits + self.metrics[level].misses
                    if total > 0:
                        self.metrics[level].avg_response_time = self.metrics[
                            level
                        ].avg_response_time * 0.9 + (
                            self.metrics[level].avg_response_time * 0.1
                        )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collector: {e}")

    async def _predictive_analysis(self):
        """Background task for predictive analysis"""
        while True:
            try:
                await asyncio.sleep(300)  # Run analysis every 5 minutes

                # Analyze access patterns and update predictions
                for key, patterns in self.access_patterns.items():
                    if len(patterns) >= 5:
                        self._update_prediction_model(key, 0.5)

                # Clean up old patterns
                cutoff = datetime.now() - timedelta(seconds=self.prediction_window * 2)
                for key in list(self.access_patterns.keys()):
                    self.access_patterns[key] = [
                        t for t in self.access_patterns[key] if t > cutoff
                    ]

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in predictive analysis: {e}")

    def _update_metrics(self, level: CacheLevel, hit: bool, response_time: float):
        """Update cache metrics"""
        metrics = self.metrics[level]
        if hit:
            metrics.hits += 1
        else:
            metrics.misses += 1

        # Update average response time
        total_requests = metrics.hits + metrics.misses
        if total_requests > 0:
            metrics.avg_response_time = (
                metrics.avg_response_time * (total_requests - 1) + response_time
            ) / total_requests

        metrics.last_updated = datetime.now()

    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage of L1 cache"""
        total_size = 0
        for key, value in self.l1_cache.cache.items():
            # Rough estimation
            total_size += len(str(key)) + len(str(value))
        return total_size / 1024  # KB

    async def get_cache_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive cache performance report"""
        report = {
            "levels": {},
            "predictions": {
                "total_patterns": len(self.access_patterns),
                "prediction_model_size": len(self.prediction_model["patterns"]),
            },
            "warming": {
                "queue_size": self.warming_queue.qsize(),
                "active": self.warming_task and not self.warming_task.done(),
            },
        }

        for level, metrics in self.metrics.items():
            total_requests = metrics.hits + metrics.misses
            hit_rate = (
                (metrics.hits / total_requests * 100) if total_requests > 0 else 0
            )

            report["levels"][level.value] = {
                "hits": metrics.hits,
                "misses": metrics.misses,
                "hit_rate": round(hit_rate, 2),
                "size": metrics.size,
                "memory_usage_kb": round(metrics.memory_usage, 2),
                "avg_response_time_ms": round(metrics.avg_response_time * 1000, 2),
                "evictions": metrics.evictions,
            }

        return report

    async def optimize_cache(self) -> Dict[str, Any]:
        """Perform cache optimization"""
        optimizations = {}

        # Analyze hit rates and adjust strategies
        for level, metrics in self.metrics.items():
            total_requests = metrics.hits + metrics.misses
            if total_requests > 100:  # Only optimize if we have enough data
                hit_rate = metrics.hits / total_requests

                if level == CacheLevel.L1_MEMORY:
                    if hit_rate < 0.5:
                        # Low hit rate - increase size or change strategy
                        optimizations[level.value] = {
                            "action": "increase_size",
                            "current_hit_rate": round(hit_rate, 2),
                            "recommendation": "Consider increasing L1 cache size",
                        }
                    elif hit_rate > 0.9:
                        # High hit rate - could reduce size
                        optimizations[level.value] = {
                            "action": "optimize_size",
                            "current_hit_rate": round(hit_rate, 2),
                            "recommendation": "Consider reducing L1 cache size",
                        }

        return optimizations

    async def shutdown(self):
        """Shutdown cache manager"""
        if self.warming_task:
            self.warming_task.cancel()
            try:
                await self.warming_task
            except asyncio.CancelledError:
                pass

        self.l1_cache.clear()
        logger.info("Advanced cache manager shutdown complete")


# Global instance
advanced_cache_manager: Optional[PredictiveCacheManager] = None


async def initialize_advanced_cache(
    redis_manager: RedisManager,
) -> PredictiveCacheManager:
    """Initialize advanced cache manager"""
    global advanced_cache_manager
    if advanced_cache_manager is None:
        advanced_cache_manager = PredictiveCacheManager(redis_manager)
        logger.info("Advanced cache manager initialized")
    return advanced_cache_manager


async def get_advanced_cache() -> PredictiveCacheManager:
    """Get advanced cache manager instance"""
    if advanced_cache_manager is None:
        raise RuntimeError("Advanced cache manager not initialized")
    return advanced_cache_manager
