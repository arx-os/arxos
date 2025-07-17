"""
Advanced Performance Optimizer for SVGX Engine

This module provides comprehensive performance optimization including:
- SVGX-aware memory management and garbage collection
- Parallel processing with worker pools optimized for SVGX operations
- Adaptive optimization based on SVGX namespace and component usage
- SVGX-specific caching strategies with intelligent eviction
- Performance profiling and bottleneck detection for SVGX operations
- Resource monitoring and alerts for SVGX workloads
- Windows compatibility and optimization
"""

import time
import threading
import multiprocessing
import psutil
import gc
import os
import platform
from typing import Dict, List, Any, Callable, Optional, Union
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import wraps, lru_cache
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
import weakref
import asyncio
from contextlib import contextmanager

from structlog import get_logger

try:
    from svgx_engine.utils.errors import PerformanceError
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.errors import PerformanceError

logger = get_logger()


class OptimizationLevel(Enum):
    """Performance optimization levels for SVGX operations."""
    MINIMAL = "minimal"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"
    MAXIMUM = "maximum"


class CacheStrategy(Enum):
    """Cache eviction strategies optimized for SVGX."""
    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    ADAPTIVE = "adaptive"
    SVGX_NAMESPACE = "svgx_namespace"  # SVGX-specific strategy


@dataclass
class SVGXPerformanceMetrics:
    """Performance metrics for SVGX operations."""
    operation_name: str
    namespace: str = ""
    component_type: str = ""
    execution_time: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    svgx_elements_processed: int = 0
    errors: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class SVGXResourceLimits:
    """Resource limits for SVGX optimization."""
    max_memory_mb: float = 1024.0
    max_cpu_percent: float = 80.0
    max_workers: int = multiprocessing.cpu_count()
    cache_size: int = 1000
    gc_threshold: float = 0.8
    svgx_cache_size: int = 500  # SVGX-specific cache
    max_svgx_elements: int = 10000  # Max SVGX elements to process


class SVGXAdaptiveCache:
    """Intelligent cache with SVGX-aware eviction."""
    
    def __init__(self, max_size: int = 1000, strategy: CacheStrategy = CacheStrategy.SVGX_NAMESPACE):
        self.max_size = max_size
        self.strategy = strategy
        self.cache: Dict[str, Any] = {}
        self.access_count: Dict[str, int] = defaultdict(int)
        self.access_time: Dict[str, float] = {}
        self.namespace_priority: Dict[str, int] = defaultdict(int)  # SVGX namespace priority
        self.size_history: deque = deque(maxlen=100)
        self.hit_rate_history: deque = deque(maxlen=100)
        
    def get(self, key: str, namespace: str = "") -> Optional[Any]:
        """Get value from cache with SVGX namespace tracking."""
        if key in self.cache:
            self.access_count[key] += 1
            self.access_time[key] = time.time()
            if namespace:
                self.namespace_priority[namespace] += 1
            self.hit_rate_history.append(1)
            return self.cache[key]
        else:
            self.hit_rate_history.append(0)
            return None
    
    def set(self, key: str, value: Any, namespace: str = "") -> None:
        """Set value in cache with SVGX namespace awareness."""
        if len(self.cache) >= self.max_size:
            self._evict()
        
        self.cache[key] = value
        self.access_count[key] = 1
        self.access_time[key] = time.time()
        if namespace:
            self.namespace_priority[namespace] += 1
        self.size_history.append(len(self.cache))
    
    def _evict(self) -> None:
        """Evict items based on SVGX-aware strategy."""
        if self.strategy == CacheStrategy.SVGX_NAMESPACE:
            self._svgx_namespace_evict()
        elif self.strategy == CacheStrategy.LRU:
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
    
    def _svgx_namespace_evict(self) -> None:
        """SVGX namespace-aware eviction strategy."""
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
        """Get SVGX-aware cache statistics."""
        if not self.hit_rate_history:
            hit_rate = 0.0
        else:
            hit_rate = sum(self.hit_rate_history) / len(self.hit_rate_history)
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": hit_rate,
            "strategy": self.strategy.value,
            "namespace_priorities": dict(self.namespace_priority)
        }


class SVGXMemoryManager:
    """Advanced memory management optimized for SVGX."""
    
    def __init__(self, limits: SVGXResourceLimits):
        self.limits = limits
        self.process = psutil.Process()
        self.memory_history: deque = deque(maxlen=100)
        self.gc_threshold = limits.gc_threshold
        self.is_windows = platform.system() == "Windows"
        
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB with Windows optimization."""
        try:
            memory_mb = self.process.memory_info().rss / 1024 / 1024
            self.memory_history.append(memory_mb)
            return memory_mb
        except Exception as e:
            logger.warning(f"Memory usage check failed: {e}")
            return 0.0
    
    def should_garbage_collect(self) -> bool:
        """Check if garbage collection is needed for SVGX operations."""
        memory_usage = self.get_memory_usage()
        return memory_usage > (self.limits.max_memory_mb * self.gc_threshold)
    
    def force_garbage_collect(self) -> None:
        """Force garbage collection with SVGX optimization."""
        try:
            collected = gc.collect()
            logger.info(f"SVGX garbage collection collected {collected} objects")
        except Exception as e:
            logger.error(f"Garbage collection failed: {e}")
    
    def optimize_memory(self) -> Dict[str, Any]:
        """Optimize memory usage for SVGX operations."""
        initial_memory = self.get_memory_usage()
        
        # Force garbage collection
        self.force_garbage_collect()
        
        # Clear weak references
        gc.collect()
        
        # Windows-specific optimization
        if self.is_windows:
            # Clear Windows-specific caches
            import ctypes
            try:
                ctypes.windll.kernel32.SetProcessWorkingSetSize(-1, -1)
            except Exception as e:
                logger.debug(f"Windows memory optimization failed: {e}")
        
        final_memory = self.get_memory_usage()
        freed_memory = initial_memory - final_memory
        
        return {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "freed_memory_mb": freed_memory,
            "memory_reduction_percent": (freed_memory / initial_memory) * 100 if initial_memory > 0 else 0,
            "is_windows": self.is_windows
        }


class SVGXParallelProcessor:
    """Parallel processing optimized for SVGX operations."""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=self.max_workers)
        self.active_tasks: Dict[str, Any] = {}
        self.is_windows = platform.system() == "Windows"
        
    def execute_parallel(self, func: Callable, items: List[Any], 
                        use_processes: bool = False, namespace: str = "") -> List[Any]:
        """Execute SVGX function in parallel on items."""
        # Windows optimization: prefer threads over processes
        if self.is_windows and use_processes:
            logger.info("Using threads instead of processes on Windows for better performance")
            use_processes = False
        
        executor = self.process_pool if use_processes else self.thread_pool
        
        try:
            results = list(executor.map(func, items))
            return results
        except Exception as e:
            logger.error(f"SVGX parallel execution failed: {e}")
            raise PerformanceError(f"Parallel execution failed: {e}")
    
    def execute_batch(self, func: Callable, items: List[Any], 
                     batch_size: int = 100, namespace: str = "") -> List[Any]:
        """Execute SVGX function in batches."""
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = self.execute_parallel(func, batch, namespace=namespace)
            results.extend(batch_results)
        return results
    
    def shutdown(self) -> None:
        """Shutdown worker pools."""
        try:
            self.thread_pool.shutdown(wait=True)
            self.process_pool.shutdown(wait=True)
        except Exception as e:
            logger.error(f"Worker pool shutdown failed: {e}")


class SVGXPerformanceProfiler:
    """Advanced performance profiling for SVGX operations."""
    
    def __init__(self):
        self.metrics: List[SVGXPerformanceMetrics] = []
        self.operation_times: Dict[str, List[float]] = defaultdict(list)
        self.namespace_times: Dict[str, List[float]] = defaultdict(list)
        self.bottlenecks: List[Dict[str, Any]] = []
        
    def profile_operation(self, operation_name: str, namespace: str = "", component_type: str = ""):
        """Decorator to profile SVGX operations."""
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
                    
                    # Count SVGX elements if result is available
                    svgx_elements = 0
                    if hasattr(result, '__len__'):
                        svgx_elements = len(result)
                    
                    metrics = SVGXPerformanceMetrics(
                        operation_name=operation_name,
                        namespace=namespace,
                        component_type=component_type,
                        execution_time=execution_time,
                        memory_usage=memory_usage,
                        cpu_usage=cpu_usage,
                        svgx_elements_processed=svgx_elements,
                        errors=errors
                    )
                    
                    self.metrics.append(metrics)
                    self.operation_times[operation_name].append(execution_time)
                    if namespace:
                        self.namespace_times[namespace].append(execution_time)
                    
                    # Detect bottlenecks for SVGX operations
                    if execution_time > 1.0:  # Operations taking more than 1 second
                        self.bottlenecks.append({
                            "operation": operation_name,
                            "namespace": namespace,
                            "component_type": component_type,
                            "execution_time": execution_time,
                            "memory_usage": memory_usage,
                            "cpu_usage": cpu_usage,
                            "svgx_elements_processed": svgx_elements,
                            "timestamp": time.time()
                        })
                
                return result
            return wrapper
        return decorator
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive SVGX performance report."""
        if not self.metrics:
            return {"error": "No SVGX metrics available"}
        
        # Calculate statistics
        total_operations = len(self.metrics)
        total_time = sum(m.execution_time for m in self.metrics)
        total_memory = sum(m.memory_usage for m in self.metrics)
        total_errors = sum(len(m.errors) for m in self.metrics)
        total_svgx_elements = sum(m.svgx_elements_processed for m in self.metrics)
        
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
        
        # Namespace-specific statistics
        namespace_stats = {}
        for namespace in self.namespace_times:
            times = self.namespace_times[namespace]
            namespace_stats[namespace] = {
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
                "total_svgx_elements_processed": total_svgx_elements,
                "avg_execution_time": total_time / total_operations if total_operations > 0 else 0
            },
            "operation_statistics": operation_stats,
            "namespace_statistics": namespace_stats,
            "bottlenecks": self.bottlenecks,
            "recent_metrics": self.metrics[-10:] if len(self.metrics) > 10 else self.metrics
        }


class SVGXPerformanceOptimizer:
    """Advanced performance optimizer with SVGX-specific features."""
    
    def __init__(self, optimization_level: OptimizationLevel = OptimizationLevel.STANDARD):
        self.optimization_level = optimization_level
        self.limits = self._get_limits_for_level(optimization_level)
        
        # Initialize SVGX components
        self.cache = SVGXAdaptiveCache(max_size=self.limits.cache_size)
        self.memory_manager = SVGXMemoryManager(self.limits)
        self.parallel_processor = SVGXParallelProcessor(max_workers=self.limits.max_workers)
        self.profiler = SVGXPerformanceProfiler()
        
        # Performance monitoring
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Resource monitoring
        self.resource_alerts: List[Dict[str, Any]] = []
        
        logger.info(f"SVGX performance optimizer initialized with level: {optimization_level.value}")
    
    def _get_limits_for_level(self, level: OptimizationLevel) -> SVGXResourceLimits:
        """Get resource limits for SVGX optimization level."""
        base_limits = SVGXResourceLimits()
        
        if level == OptimizationLevel.MINIMAL:
            return SVGXResourceLimits(
                max_memory_mb=512.0,
                max_cpu_percent=50.0,
                max_workers=2,
                cache_size=100,
                gc_threshold=0.9,
                svgx_cache_size=50,
                max_svgx_elements=1000
            )
        elif level == OptimizationLevel.STANDARD:
            return base_limits
        elif level == OptimizationLevel.AGGRESSIVE:
            return SVGXResourceLimits(
                max_memory_mb=2048.0,
                max_cpu_percent=90.0,
                max_workers=multiprocessing.cpu_count() * 2,
                cache_size=2000,
                gc_threshold=0.7,
                svgx_cache_size=1000,
                max_svgx_elements=50000
            )
        elif level == OptimizationLevel.MAXIMUM:
            return SVGXResourceLimits(
                max_memory_mb=4096.0,
                max_cpu_percent=95.0,
                max_workers=multiprocessing.cpu_count() * 4,
                cache_size=5000,
                gc_threshold=0.6,
                svgx_cache_size=2500,
                max_svgx_elements=100000
            )
        
        return base_limits
    
    def optimize_operation(self, operation_name: str, func: Callable = None,
                          use_caching: bool = True, use_profiling: bool = True,
                          use_parallel: bool = False, batch_size: int = 100,
                          namespace: str = "", component_type: str = ""):
        """Context manager and decorator for optimized SVGX operations."""
        # Decorator usage
        if func is None:
            def decorator(operation_func):
                @wraps(operation_func)
                def wrapper(*args, **kwargs):
                    self._check_resource_limits()
                    if use_profiling:
                        start_time = time.time()
                        start_memory = self.memory_manager.get_memory_usage()
                    try:
                        result = operation_func(*args, **kwargs)
                        return result
                    finally:
                        if use_profiling:
                            end_time = time.time()
                            end_memory = self.memory_manager.get_memory_usage()
                            metrics = SVGXPerformanceMetrics(
                                operation_name=operation_name,
                                namespace=namespace,
                                component_type=component_type,
                                execution_time=end_time - start_time,
                                memory_usage=end_memory - start_memory,
                                cpu_usage=psutil.cpu_percent()
                            )
                            self.profiler.metrics.append(metrics)
                        if self.memory_manager.should_garbage_collect():
                            self.memory_manager.force_garbage_collect()
                return wrapper
            return decorator
        # Context manager usage
        @contextmanager
        def _cm():
            self._check_resource_limits()
            if use_profiling:
                start_time = time.time()
                start_memory = self.memory_manager.get_memory_usage()
            try:
                yield
            finally:
                if use_profiling:
                    end_time = time.time()
                    end_memory = self.memory_manager.get_memory_usage()
                    metrics = SVGXPerformanceMetrics(
                        operation_name=operation_name,
                        namespace=namespace,
                        component_type=component_type,
                        execution_time=end_time - start_time,
                        memory_usage=end_memory - start_memory,
                        cpu_usage=psutil.cpu_percent()
                    )
                    self.profiler.metrics.append(metrics)
                if self.memory_manager.should_garbage_collect():
                    self.memory_manager.force_garbage_collect()
        return _cm()
    
    def optimize_function(self, func: Callable, use_caching: bool = True,
                         use_profiling: bool = True, namespace: str = "") -> Callable:
        """Optimize a SVGX function with caching and profiling."""
        if use_caching:
            # Create cached version with SVGX namespace
            cached_func = lru_cache(maxsize=self.limits.svgx_cache_size)(func)
        else:
            cached_func = func
        
        if use_profiling:
            # Add profiling
            @self.profiler.profile_operation(func.__name__, namespace=namespace)
            def profiled_func(*args, **kwargs):
                return cached_func(*args, **kwargs)
            return profiled_func
        
        return cached_func
    
    def parallel_process(self, items: List[Any], func: Callable,
                        batch_size: int = 100, use_processes: bool = False,
                        namespace: str = "") -> List[Any]:
        """Process SVGX items in parallel."""
        return self.parallel_processor.execute_batch(func, items, batch_size, namespace=namespace)
    
    def start_monitoring(self) -> None:
        """Start SVGX resource monitoring."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
        self.monitor_thread.start()
        logger.info("SVGX resource monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop SVGX resource monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        logger.info("SVGX resource monitoring stopped")
    
    def _monitor_resources(self) -> None:
        """Monitor system resources for SVGX operations."""
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
                    logger.warning(f"SVGX memory usage high: {memory_usage:.2f}MB")
                
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
                    logger.warning(f"SVGX CPU usage high: {cpu_usage:.2f}%")
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"SVGX resource monitoring error: {e}")
                time.sleep(10)
    
    def _check_resource_limits(self) -> None:
        """Check if SVGX resource limits are exceeded."""
        memory_usage = self.memory_manager.get_memory_usage()
        cpu_usage = psutil.cpu_percent()
        
        if memory_usage > self.limits.max_memory_mb:
            logger.warning(f"SVGX memory limit exceeded: {memory_usage:.2f}MB > {self.limits.max_memory_mb}MB")
            self.memory_manager.force_garbage_collect()
        
        if cpu_usage > self.limits.max_cpu_percent:
            logger.warning(f"SVGX CPU limit exceeded: {cpu_usage:.2f}% > {self.limits.max_cpu_percent}%")
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Get comprehensive SVGX optimization report."""
        return {
            "optimization_level": self.optimization_level.value,
            "resource_limits": {
                "max_memory_mb": self.limits.max_memory_mb,
                "max_cpu_percent": self.limits.max_cpu_percent,
                "max_workers": self.limits.max_workers,
                "cache_size": self.limits.cache_size,
                "svgx_cache_size": self.limits.svgx_cache_size,
                "max_svgx_elements": self.limits.max_svgx_elements
            },
            "current_resources": {
                "memory_usage_mb": self.memory_manager.get_memory_usage(),
                "cpu_usage_percent": psutil.cpu_percent(),
                "available_memory_mb": psutil.virtual_memory().available / 1024 / 1024
            },
            "cache_statistics": self.cache.get_stats(),
            "profiler_summary": self.profiler.get_performance_report(),
            "resource_alerts": self.resource_alerts[-10:] if self.resource_alerts else [],
            "monitoring_active": self.monitoring_active,
            "is_windows": platform.system() == "Windows"
        }
    
    def optimize_memory(self) -> Dict[str, Any]:
        """Optimize memory usage for SVGX operations."""
        return self.memory_manager.optimize_memory()
    
    def clear_cache(self) -> None:
        """Clear all SVGX caches."""
        self.cache.cache.clear()
        self.cache.access_count.clear()
        self.cache.access_time.clear()
        self.cache.namespace_priority.clear()
        logger.info("All SVGX caches cleared")
    
    def shutdown(self) -> None:
        """Shutdown SVGX optimizer and clean up resources."""
        self.stop_monitoring()
        self.parallel_processor.shutdown()
        self.clear_cache()
        logger.info("SVGX performance optimizer shutdown complete")


# Convenience functions for easy SVGX usage
def optimize_operation(operation_name: str, use_caching: bool = True,
                      use_profiling: bool = True, namespace: str = ""):
    """Decorator for optimizing SVGX operations."""
    optimizer = SVGXPerformanceOptimizer()
    return optimizer.optimize_operation(operation_name, use_caching=use_caching, 
                                      use_profiling=use_profiling, namespace=namespace)


def parallel_process(items: List[Any], func: Callable, batch_size: int = 100,
                    namespace: str = ""):
    """Process SVGX items in parallel."""
    optimizer = SVGXPerformanceOptimizer()
    return optimizer.parallel_process(items, func, batch_size, namespace=namespace)


def get_performance_report() -> Dict[str, Any]:
    """Get current SVGX performance report."""
    optimizer = SVGXPerformanceOptimizer()
    return optimizer.get_optimization_report() 