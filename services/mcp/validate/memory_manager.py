"""
Memory Management System for MCP Rule Validation

This module provides memory optimization capabilities:
- Object pooling for frequently used objects
- Weak references for large data structures
- Memory monitoring and cleanup
- Garbage collection optimization
"""

import gc
import weakref
import threading
import time
import psutil
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import logging


@dataclass
class MemoryStats:
    """Memory usage statistics"""

    total_memory_mb: float
    available_memory_mb: float
    used_memory_mb: float
    memory_percentage: float
    object_count: int
    cache_size: int
    timestamp: float = field(default_factory=time.time)


class ObjectPool:
    """Object pool for memory optimization"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.pool: Dict[str, List[Any]] = defaultdict(list)
        self.lock = threading.Lock()
        self.stats = {"hits": 0, "misses": 0, "creates": 0, "releases": 0}

    def get(self, obj_type: str, factory: Callable[[], Any]) -> Any:
        """Get object from pool or create new one"""
        with self.lock:
            if self.pool[obj_type]:
                obj = self.pool[obj_type].pop()
                self.stats["hits"] += 1
                return obj
            else:
                obj = factory()
                self.stats["misses"] += 1
                self.stats["creates"] += 1
                return obj

    def release(self, obj_type: str, obj: Any):
        """Release object back to pool"""
        with self.lock:
            if len(self.pool[obj_type]) < self.max_size:
                self.pool[obj_type].append(obj)
                self.stats["releases"] += 1

    def clear(self):
        """Clear all pools"""
        with self.lock:
            self.pool.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self.lock:
            return {
                "stats": self.stats.copy(),
                "pool_sizes": {k: len(v) for k, v in self.pool.items()},
                "total_objects": sum(len(v) for v in self.pool.values()),
            }


class MemoryManager:
    """
    Memory management system for MCP validation

    Features:
    - Object pooling
    - Weak references
    - Memory monitoring
    - Automatic cleanup
    - Performance optimization
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize memory manager

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Memory settings
        self.memory_threshold_mb = self.config.get("memory_threshold_mb", 1024)
        self.cleanup_interval = self.config.get("cleanup_interval", 300)  # 5 minutes
        self.max_cache_size = self.config.get("max_cache_size", 10000)

        # Object pools
        self.object_pool = ObjectPool(max_size=self.max_cache_size)

        # Weak reference cache
        self.weak_cache: Dict[str, weakref.ref] = {}

        # Memory monitoring
        self.memory_stats: List[MemoryStats] = []
        self.max_stats_history = self.config.get("max_stats_history", 100)

        # Thread safety
        self._lock = threading.Lock()

        # Start cleanup thread
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
        self._start_cleanup_thread()

        self.logger.info("Memory Manager initialized")

    def _start_cleanup_thread(self):
        """Start background cleanup thread"""

        def cleanup_worker():
            while not self._stop_cleanup.wait(self.cleanup_interval):
                try:
                    self._perform_cleanup()
                except Exception as e:
                    self.logger.error(f"Error in cleanup thread: {e}")

        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()

    def _perform_cleanup(self):
        """Perform memory cleanup"""
        current_memory = self._get_memory_usage()

        if current_memory.used_memory_mb > self.memory_threshold_mb:
            self.logger.info(
                f"Memory threshold exceeded ({current_memory.used_memory_mb:.1f}MB), "
                f"performing cleanup"
            )

            # Clear weak references
            self._cleanup_weak_references()

            # Clear object pools
            self.object_pool.clear()

            # Force garbage collection
            gc.collect()

            # Update stats
            self._update_memory_stats()

            self.logger.info(
                f"Cleanup completed, memory usage: {self._get_memory_usage().used_memory_mb:.1f}MB"
            )

    def _cleanup_weak_references(self):
        """Clean up expired weak references"""
        expired_keys = []

        for key, weak_ref in self.weak_cache.items():
            if weak_ref() is None:
                expired_keys.append(key)

        for key in expired_keys:
            del self.weak_cache[key]

        if expired_keys:
            self.logger.debug(f"Cleaned up {len(expired_keys)} expired weak references")

    def _get_memory_usage(self) -> MemoryStats:
        """Get current memory usage statistics"""
        process = psutil.Process()
        memory_info = process.memory_info()
        virtual_memory = psutil.virtual_memory()

        return MemoryStats(
            total_memory_mb=virtual_memory.total / 1024 / 1024,
            available_memory_mb=virtual_memory.available / 1024 / 1024,
            used_memory_mb=memory_info.rss / 1024 / 1024,
            memory_percentage=virtual_memory.percent,
            object_count=len(gc.get_objects()),
            cache_size=sum(len(pool) for pool in self.object_pool.pool.values()),
        )

    def _update_memory_stats(self):
        """Update memory statistics"""
        stats = self._get_memory_usage()

        with self._lock:
            self.memory_stats.append(stats)

            # Keep only recent stats
            if len(self.memory_stats) > self.max_stats_history:
                self.memory_stats = self.memory_stats[-self.max_stats_history :]

    def get_object(self, obj_type: str, factory: Callable[[], Any]) -> Any:
        """Get object from pool"""
        return self.object_pool.get(obj_type, factory)

    def release_object(self, obj_type: str, obj: Any):
        """Release object to pool"""
        self.object_pool.release(obj_type, obj)

    def cache_with_weak_ref(self, key: str, obj: Any):
        """Cache object with weak reference"""
        self.weak_cache[key] = weakref.ref(obj)

    def get_from_weak_cache(self, key: str) -> Optional[Any]:
        """Get object from weak reference cache"""
        weak_ref = self.weak_cache.get(key)
        if weak_ref:
            obj = weak_ref()
            if obj is not None:
                return obj
            else:
                # Clean up expired reference
                del self.weak_cache[key]
        return None

    def monitor_memory(self) -> MemoryStats:
        """Monitor current memory usage"""
        stats = self._get_memory_usage()
        self._update_memory_stats()
        return stats

    def get_memory_trends(self) -> Dict[str, Any]:
        """Get memory usage trends"""
        with self._lock:
            if len(self.memory_stats) < 2:
                return {"trend": "insufficient_data"}

            recent_stats = self.memory_stats[-10:]  # Last 10 measurements
            first_usage = recent_stats[0].used_memory_mb
            last_usage = recent_stats[-1].used_memory_mb

            trend = "stable"
            if last_usage > first_usage * 1.1:
                trend = "increasing"
            elif last_usage < first_usage * 0.9:
                trend = "decreasing"

            return {
                "trend": trend,
                "change_mb": last_usage - first_usage,
                "change_percentage": ((last_usage - first_usage) / first_usage) * 100,
                "average_usage_mb": sum(s.used_memory_mb for s in recent_stats)
                / len(recent_stats),
                "peak_usage_mb": max(s.used_memory_mb for s in recent_stats),
            }

    def optimize_memory_settings(self) -> Dict[str, Any]:
        """Dynamically optimize memory settings based on usage patterns"""
        trends = self.get_memory_trends()
        current_stats = self._get_memory_usage()

        recommendations = []

        # Check memory pressure
        if current_stats.memory_percentage > 80:
            recommendations.append(
                "High memory pressure - consider reducing cache sizes"
            )
            self.max_cache_size = max(1000, self.max_cache_size // 2)

        # Check object count
        if current_stats.object_count > 100000:
            recommendations.append(
                "High object count - consider more aggressive cleanup"
            )
            self.cleanup_interval = max(60, self.cleanup_interval // 2)

        # Check cache efficiency
        pool_stats = self.object_pool.get_stats()
        hit_rate = pool_stats["stats"]["hits"] / max(
            1, pool_stats["stats"]["hits"] + pool_stats["stats"]["misses"]
        )

        if hit_rate < 0.3:
            recommendations.append("Low cache hit rate - consider reducing pool sizes")
            self.max_cache_size = max(100, self.max_cache_size // 2)

        return {
            "recommendations": recommendations,
            "optimized_settings": {
                "max_cache_size": self.max_cache_size,
                "cleanup_interval": self.cleanup_interval,
                "memory_threshold_mb": self.memory_threshold_mb,
            },
            "current_stats": {
                "memory_percentage": current_stats.memory_percentage,
                "object_count": current_stats.object_count,
                "cache_hit_rate": hit_rate,
            },
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get memory performance metrics"""
        current_stats = self._get_memory_usage()
        trends = self.get_memory_trends()
        pool_stats = self.object_pool.get_stats()

        return {
            "current_memory_mb": current_stats.used_memory_mb,
            "available_memory_mb": current_stats.available_memory_mb,
            "memory_percentage": current_stats.memory_percentage,
            "object_count": current_stats.object_count,
            "cache_size": current_stats.cache_size,
            "memory_trend": trends,
            "pool_stats": pool_stats,
            "weak_cache_size": len(self.weak_cache),
        }

    def shutdown(self):
        """Shutdown memory manager"""
        self._stop_cleanup.set()
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)

        # Clear all caches
        self.object_pool.clear()
        self.weak_cache.clear()

        self.logger.info("Memory Manager shutdown complete")


class MemoryOptimizedEngine:
    """Memory-optimized wrapper for MCP rule engine"""

    def __init__(self, base_engine, memory_manager: MemoryManager):
        self.base_engine = base_engine
        self.memory_manager = memory_manager
        self.logger = logging.getLogger(__name__)

    def validate_building_model(self, building_model, mcp_files):
        """Validate building model with memory optimization"""
        # Monitor memory before validation
        initial_stats = self.memory_manager.monitor_memory()

        try:
            # Perform validation
            result = self.base_engine.validate_building_model(building_model, mcp_files)

            # Monitor memory after validation
            final_stats = self.memory_manager.monitor_memory()

            # Log memory usage
            memory_used = final_stats.used_memory_mb - initial_stats.used_memory_mb
            self.logger.info(f"Validation completed, memory usage: {memory_used:.1f}MB")

            return result

        except Exception as e:
            self.logger.error(f"Error in memory-optimized validation: {e}")
            raise

    def get_memory_metrics(self):
        """Get memory performance metrics"""
        return self.memory_manager.get_performance_metrics()
