"""
Advanced Performance Optimizer for SVG-BIM System

This module provides comprehensive performance optimization including:
- Memory management and garbage collection
- Parallel processing with worker pools
- Adaptive optimization based on system resources
- Caching strategies with intelligent eviction
- Performance profiling and bottleneck detection
- Resource monitoring and alerts
"""

import time
import threading
import multiprocessing
import psutil
import gc
from typing import Dict, List, Any, Callable, Optional, Union
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import wraps, lru_cache
from collections import defaultdict, deque
import logging
from dataclasses import dataclass, field
from enum import Enum
import weakref
import asyncio
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class OptimizationLevel(Enum):
    """Performance optimization levels."""
    MINIMAL = "minimal"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"
    MAXIMUM = "maximum"


class CacheStrategy(Enum):
    """Cache eviction strategies."""
    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    ADAPTIVE = "adaptive"


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations."""
    operation_name: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    cache_hits: int = 0
    cache_misses: int = 0
    errors: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ResourceLimits:
    """Resource limits for optimization."""
    max_memory_mb: float = 1024.0
    max_cpu_percent: float = 80.0
    max_workers: int = multiprocessing.cpu_count()
    cache_size: int = 1000
    gc_threshold: float = 0.8


class AdaptiveCache:
    """Intelligent cache with adaptive eviction."""
    
    def __init__(self, max_size: int = 1000, strategy: CacheStrategy = CacheStrategy.ADAPTIVE):
        self.max_size = max_size
        self.strategy = strategy
        self.cache: Dict[str, Any] = {}
        self.access_count: Dict[str, int] = defaultdict(int)
        self.access_time: Dict[str, float] = {}
        self.size_history: deque = deque(maxlen=100)
        self.hit_rate_history: deque = deque(maxlen=100)
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with access tracking."""
        if key in self.cache:
            self.access_count[key] += 1
            self.access_time[key] = time.time()
            self.hit_rate_history.append(1)
            return self.cache[key]
        else:
            self.hit_rate_history.append(0)
            return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache with eviction if needed."""
        if len(self.cache) >= self.max_size:
            self._evict()
        
        self.cache[key] = value
        self.access_count[key] = 1
        self.access_time[key] = time.time()
        self.size_history.append(len(self.cache))
    
    def _evict(self) -> None:
        """Evict items based on strategy."""
        if self.strategy == CacheStrategy.LRU:
            oldest_key = min(self.access_time.keys(), key=lambda k: self.access_time[k])
            del self.cache[oldest_key]
            del self.access_time[oldest_key]
            del self.access_count[oldest_key]
        elif self.strategy == CacheStrategy.LFU:
            least_frequent_key = min(self.access_count.keys(), key=lambda k: self.access_count[k])
            del self.cache[least_frequent_key]
            del self.access_time[least_frequent_key]
            del self.access_count[least_frequent_key]
        elif self.strategy == CacheStrategy.ADAPTIVE:
            self._adaptive_evict()
    
    def _adaptive_evict(self) -> None:
        """Adaptive eviction based on access patterns."""
        if len(self.hit_rate_history) < 10:
            # Use LRU if not enough history
            oldest_key = min(self.access_time.keys(), key=lambda k: self.access_time[k])
            del self.cache[oldest_key]
            del self.access_time[oldest_key]
            del self.access_count[oldest_key]
        else:
            recent_hit_rate = sum(self.hit_rate_history[-10:]) / 10
            if recent_hit_rate > 0.7:
                # High hit rate - evict least frequently used
                least_frequent_key = min(self.access_count.keys(), key=lambda k: self.access_count[k])
                del self.cache[least_frequent_key]
                del self.access_time[least_frequent_key]
                del self.access_count[least_frequent_key]
            else:
                # Low hit rate - evict oldest
                oldest_key = min(self.access_time.keys(), key=lambda k: self.access_time[k])
                del self.cache[oldest_key]
                del self.access_time[oldest_key]
                del self.access_count[oldest_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.hit_rate_history:
            hit_rate = 0.0
        else:
            hit_rate = sum(self.hit_rate_history) / len(self.hit_rate_history)
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": hit_rate,
            "strategy": self.strategy.value
        }


class MemoryManager:
    """Advanced memory management."""
    
    def __init__(self, limits: ResourceLimits):
        self.limits = limits
        self.process = psutil.Process()
        self.memory_history: deque = deque(maxlen=100)
        self.gc_threshold = limits.gc_threshold
        
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        self.memory_history.append(memory_mb)
        return memory_mb
    
    def should_garbage_collect(self) -> bool:
        """Check if garbage collection is needed."""
        memory_usage = self.get_memory_usage()
        return memory_usage > (self.limits.max_memory_mb * self.gc_threshold)
    
    def force_garbage_collect(self) -> None:
        """Force garbage collection."""
        collected = gc.collect()
        logger.info(f"Garbage collection collected {collected} objects")
    
    def optimize_memory(self) -> Dict[str, Any]:
        """Optimize memory usage."""
        initial_memory = self.get_memory_usage()
        
        # Force garbage collection
        self.force_garbage_collect()
        
        # Clear weak references
        gc.collect()
        
        final_memory = self.get_memory_usage()
        freed_memory = initial_memory - final_memory
        
        return {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "freed_memory_mb": freed_memory,
            "memory_reduction_percent": (freed_memory / initial_memory) * 100 if initial_memory > 0 else 0
        }


class ParallelProcessor:
    """Parallel processing with worker pools."""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=self.max_workers)
        self.active_tasks: Dict[str, Any] = {}
        
    def execute_parallel(self, func: Callable, items: List[Any], 
                        use_processes: bool = False) -> List[Any]:
        """Execute function in parallel on items."""
        executor = self.process_pool if use_processes else self.thread_pool
        
        try:
            results = list(executor.map(func, items))
            return results
        except Exception as e:
            logger.error(f"Parallel execution failed: {e}")
            raise
    
    def execute_batch(self, func: Callable, items: List[Any], 
                     batch_size: int = 100) -> List[Any]:
        """Execute function in batches."""
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = self.execute_parallel(func, batch)
            results.extend(batch_results)
        return results
    
    def shutdown(self) -> None:
        """Shutdown worker pools."""
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)


class PerformanceProfiler:
    """Advanced performance profiling."""
    
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.operation_times: Dict[str, List[float]] = defaultdict(list)
        self.bottlenecks: List[Dict[str, Any]] = []
        
    def profile_operation(self, operation_name: str):
        """Decorator to profile operations."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss / 1024 / 1024
                start_cpu = psutil.cpu_percent()
                
                try:
                    result = func(*args, **kwargs)
                    errors = []
                except Exception as e:
                    errors = [str(e)]
                    raise
                finally:
                    end_time = time.time()
                    end_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    end_cpu = psutil.cpu_percent()
                    
                    execution_time = end_time - start_time
                    memory_usage = end_memory - start_memory
                    cpu_usage = (start_cpu + end_cpu) / 2
                    
                    metrics = PerformanceMetrics(
                        operation_name=operation_name,
                        execution_time=execution_time,
                        memory_usage=memory_usage,
                        cpu_usage=cpu_usage,
                        errors=errors
                    )
                    
                    self.metrics.append(metrics)
                    self.operation_times[operation_name].append(execution_time)
                    
                    # Detect bottlenecks
                    if execution_time > 1.0:  # Operations taking more than 1 second
                        self.bottlenecks.append({
                            "operation": operation_name,
                            "execution_time": execution_time,
                            "memory_usage": memory_usage,
                            "cpu_usage": cpu_usage,
                            "timestamp": time.time()
                        })
                
                return result
            return wrapper
        return decorator
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        if not self.metrics:
            return {"error": "No metrics available"}
        
        # Calculate statistics
        total_operations = len(self.metrics)
        total_time = sum(m.execution_time for m in self.metrics)
        total_memory = sum(m.memory_usage for m in self.metrics)
        total_errors = sum(len(m.errors) for m in self.metrics)
        
        # Operation-specific statistics
        operation_stats = {}
        for operation_name in self.operation_times:
            times = self.operation_times[operation_name]
            operation_stats[operation_name] = {
                "count": len(times),
                "avg_time": sum(times) / len(times),
                "max_time": max(times),
                "min_time": min(times)
            }
        
        return {
            "summary": {
                "total_operations": total_operations,
                "total_execution_time": total_time,
                "total_memory_usage": total_memory,
                "total_errors": total_errors,
                "avg_execution_time": total_time / total_operations if total_operations > 0 else 0
            },
            "operation_statistics": operation_stats,
            "bottlenecks": self.bottlenecks,
            "recent_metrics": self.metrics[-10:] if len(self.metrics) > 10 else self.metrics
        }


class PerformanceOptimizer:
    """Advanced performance optimizer with comprehensive features."""
    
    def __init__(self, optimization_level: OptimizationLevel = OptimizationLevel.STANDARD):
        self.optimization_level = optimization_level
        self.limits = self._get_limits_for_level(optimization_level)
        
        # Initialize components
        self.cache = AdaptiveCache(max_size=self.limits.cache_size)
        self.memory_manager = MemoryManager(self.limits)
        self.parallel_processor = ParallelProcessor(max_workers=self.limits.max_workers)
        self.profiler = PerformanceProfiler()
        
        # Performance monitoring
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Resource monitoring
        self.resource_alerts: List[Dict[str, Any]] = []
        
        logger.info(f"Performance optimizer initialized with level: {optimization_level.value}")
    
    def _get_limits_for_level(self, level: OptimizationLevel) -> ResourceLimits:
        """Get resource limits for optimization level."""
        base_limits = ResourceLimits()
        
        if level == OptimizationLevel.MINIMAL:
            return ResourceLimits(
                max_memory_mb=512.0,
                max_cpu_percent=50.0,
                max_workers=2,
                cache_size=100,
                gc_threshold=0.9
            )
        elif level == OptimizationLevel.STANDARD:
            return base_limits
        elif level == OptimizationLevel.AGGRESSIVE:
            return ResourceLimits(
                max_memory_mb=2048.0,
                max_cpu_percent=90.0,
                max_workers=multiprocessing.cpu_count() * 2,
                cache_size=2000,
                gc_threshold=0.7
            )
        elif level == OptimizationLevel.MAXIMUM:
            return ResourceLimits(
                max_memory_mb=4096.0,
                max_cpu_percent=95.0,
                max_workers=multiprocessing.cpu_count() * 4,
                cache_size=5000,
                gc_threshold=0.6
            )
        
        return base_limits
    
    @contextmanager
    def optimize_operation(self, operation_name: str, func: Callable = None,
                          use_caching: bool = True, use_profiling: bool = True,
                          use_parallel: bool = False, batch_size: int = 100):
        """Context manager for optimized operations."""
        if func is None:
            # Use as decorator
            def decorator(operation_func):
                @wraps(operation_func)
                def wrapper(*args, **kwargs):
                    with self.optimize_operation(operation_name, operation_func,
                                               use_caching, use_profiling, use_parallel):
                        return operation_func(*args, **kwargs)
                return wrapper
            return decorator
        
        # Check resource limits
        self._check_resource_limits()
        
        # Start profiling if enabled
        if use_profiling:
            start_time = time.time()
            start_memory = self.memory_manager.get_memory_usage()
        
        try:
            yield func
        finally:
            # End profiling
            if use_profiling:
                end_time = time.time()
                end_memory = self.memory_manager.get_memory_usage()
                
                metrics = PerformanceMetrics(
                    operation_name=operation_name,
                    execution_time=end_time - start_time,
                    memory_usage=end_memory - start_memory,
                    cpu_usage=psutil.cpu_percent()
                )
                self.profiler.metrics.append(metrics)
            
            # Memory optimization if needed
            if self.memory_manager.should_garbage_collect():
                self.memory_manager.force_garbage_collect()
    
    def optimize_function(self, func: Callable, use_caching: bool = True,
                         use_profiling: bool = True) -> Callable:
        """Optimize a function with caching and profiling."""
        if use_caching:
            # Create cached version
            cached_func = lru_cache(maxsize=self.limits.cache_size)(func)
        else:
            cached_func = func
        
        if use_profiling:
            # Add profiling
            @self.profiler.profile_operation(func.__name__)
            def profiled_func(*args, **kwargs):
                return cached_func(*args, **kwargs)
            return profiled_func
        
        return cached_func
    
    def parallel_process(self, items: List[Any], func: Callable,
                        batch_size: int = 100, use_processes: bool = False) -> List[Any]:
        """Process items in parallel."""
        return self.parallel_processor.execute_batch(func, items, batch_size)
    
    def start_monitoring(self) -> None:
        """Start resource monitoring."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
        self.monitor_thread.start()
        logger.info("Resource monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        logger.info("Resource monitoring stopped")
    
    def _monitor_resources(self) -> None:
        """Monitor system resources."""
        while self.monitoring_active:
            try:
                # Check memory usage
                memory_usage = self.memory_manager.get_memory_usage()
                if memory_usage > self.limits.max_memory_mb:
                    alert = {
                        "type": "memory_high",
                        "current": memory_usage,
                        "limit": self.limits.max_memory_mb,
                        "timestamp": time.time()
                    }
                    self.resource_alerts.append(alert)
                    logger.warning(f"Memory usage high: {memory_usage:.2f}MB")
                
                # Check CPU usage
                cpu_usage = psutil.cpu_percent()
                if cpu_usage > self.limits.max_cpu_percent:
                    alert = {
                        "type": "cpu_high",
                        "current": cpu_usage,
                        "limit": self.limits.max_cpu_percent,
                        "timestamp": time.time()
                    }
                    self.resource_alerts.append(alert)
                    logger.warning(f"CPU usage high: {cpu_usage:.2f}%")
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                time.sleep(10)
    
    def _check_resource_limits(self) -> None:
        """Check if resource limits are exceeded."""
        memory_usage = self.memory_manager.get_memory_usage()
        cpu_usage = psutil.cpu_percent()
        
        if memory_usage > self.limits.max_memory_mb:
            logger.warning(f"Memory limit exceeded: {memory_usage:.2f}MB > {self.limits.max_memory_mb}MB")
            self.memory_manager.force_garbage_collect()
        
        if cpu_usage > self.limits.max_cpu_percent:
            logger.warning(f"CPU limit exceeded: {cpu_usage:.2f}% > {self.limits.max_cpu_percent}%")
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Get comprehensive optimization report."""
        return {
            "optimization_level": self.optimization_level.value,
            "resource_limits": {
                "max_memory_mb": self.limits.max_memory_mb,
                "max_cpu_percent": self.limits.max_cpu_percent,
                "max_workers": self.limits.max_workers,
                "cache_size": self.limits.cache_size
            },
            "current_resources": {
                "memory_usage_mb": self.memory_manager.get_memory_usage(),
                "cpu_usage_percent": psutil.cpu_percent(),
                "available_memory_mb": psutil.virtual_memory().available / 1024 / 1024
            },
            "cache_statistics": self.cache.get_stats(),
            "profiler_summary": self.profiler.get_performance_report(),
            "resource_alerts": self.resource_alerts[-10:] if self.resource_alerts else [],
            "monitoring_active": self.monitoring_active
        }
    
    def optimize_memory(self) -> Dict[str, Any]:
        """Optimize memory usage."""
        return self.memory_manager.optimize_memory()
    
    def clear_cache(self) -> None:
        """Clear all caches."""
        self.cache.cache.clear()
        self.cache.access_count.clear()
        self.cache.access_time.clear()
        logger.info("All caches cleared")
    
    def shutdown(self) -> None:
        """Shutdown optimizer and clean up resources."""
        self.stop_monitoring()
        self.parallel_processor.shutdown()
        self.clear_cache()
        logger.info("Performance optimizer shutdown complete")


# Convenience functions for easy usage
def optimize_operation(operation_name: str, use_caching: bool = True,
                      use_profiling: bool = True):
    """Decorator for optimizing operations."""
    optimizer = PerformanceOptimizer()
    return optimizer.optimize_operation(operation_name, use_caching=use_caching, 
                                      use_profiling=use_profiling)


def parallel_process(items: List[Any], func: Callable, batch_size: int = 100):
    """Process items in parallel."""
    optimizer = PerformanceOptimizer()
    return optimizer.parallel_process(items, func, batch_size)


def get_performance_report() -> Dict[str, Any]:
    """Get current performance report."""
    optimizer = PerformanceOptimizer()
    return optimizer.get_optimization_report() 