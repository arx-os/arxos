"""
Performance Optimization Engine for MCP Rule Validation

This module provides advanced performance optimization capabilities for the MCP rule engine,
including parallel processing, intelligent caching, memory optimization, and performance monitoring.

Key Features:
- Parallel rule execution with thread pools
- Intelligent caching with LRU and TTL strategies
- Memory optimization and garbage collection
- Performance monitoring and metrics
- Adaptive optimization based on workload
- Resource management and cleanup
"""

import time
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import weakref
import gc
import psutil
import hashlib
import json
from functools import lru_cache
from collections import OrderedDict, defaultdict

from services.models.mcp_models import BuildingObject, MCPRule, RuleCondition, RuleAction

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache strategy types"""
    LRU = "lru"
    TTL = "ttl"
    ADAPTIVE = "adaptive"


class OptimizationLevel(Enum):
    """Performance optimization levels"""
    NONE = "none"
    BASIC = "basic"
    ADVANCED = "advanced"
    AGGRESSIVE = "aggressive"


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    value: Any
    timestamp: float
    access_count: int = 0
    size_bytes: int = 0
    ttl: Optional[float] = None


@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring"""
    execution_time: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    cache_hit_rate: float = 0.0
    parallel_efficiency: float = 0.0
    throughput: float = 0.0


class IntelligentCache:
    """
    Intelligent caching system with multiple strategies.
    
    Supports LRU, TTL, and adaptive caching with automatic
    memory management and performance optimization.
    """
    
    def __init__(self, max_size: int = 1000, strategy: CacheStrategy = CacheStrategy.ADAPTIVE):
        """Initialize intelligent cache"""
        self.max_size = max_size
        self.strategy = strategy
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.access_stats = defaultdict(int)
        self.memory_limit = 100 * 1024 * 1024  # 100MB default
        self.current_memory = 0
        self.lock = threading.RLock()
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # Check TTL
                if entry.ttl and time.time() - entry.timestamp > entry.ttl:
                    self._remove_entry(key)
                    return None
                
                # Update access stats
                entry.access_count += 1
                entry.timestamp = time.time()
                self.access_stats[key] += 1
                
                # Move to end (LRU)
                self.cache.move_to_end(key)
                return entry.value
            
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache"""
        with self.lock:
            # Calculate entry size
            size_bytes = self._estimate_size(value)
            
            # Remove if key exists
            if key in self.cache:
                self._remove_entry(key)
            
            # Create new entry
            entry = CacheEntry(
                value=value,
                timestamp=time.time(),
                size_bytes=size_bytes,
                ttl=ttl
            )
            
            # Check memory limits
            while (self.current_memory + size_bytes > self.memory_limit or 
                   len(self.cache) >= self.max_size):
                self._evict_least_valuable()
            
            # Add entry
            self.cache[key] = entry
            self.current_memory += size_bytes
    
    def _remove_entry(self, key: str) -> None:
        """Remove entry from cache"""
        if key in self.cache:
            entry = self.cache[key]
            self.current_memory -= entry.size_bytes
            del self.cache[key]
            if key in self.access_stats:
                del self.access_stats[key]
    
    def _evict_least_valuable(self) -> None:
        """Evict least valuable entry based on strategy"""
        if not self.cache:
            return
        
        if self.strategy == CacheStrategy.LRU:
            # Remove least recently used
            key = next(iter(self.cache))
            self._remove_entry(key)
        
        elif self.strategy == CacheStrategy.TTL:
            # Remove expired entries first, then oldest
            current_time = time.time()
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.ttl and current_time - entry.timestamp > entry.ttl
            ]
            
            if expired_keys:
                self._remove_entry(expired_keys[0])
            else:
                # Remove oldest
                key = next(iter(self.cache))
                self._remove_entry(key)
        
        elif self.strategy == CacheStrategy.ADAPTIVE:
            # Remove based on access frequency and size
            worst_key = min(
                self.cache.keys(),
                key=lambda k: (self.access_stats.get(k, 0), -self.cache[k].size_bytes)
            )
            self._remove_entry(worst_key)
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate memory size of value"""
        try:
            return len(json.dumps(value, default=str).encode('utf-8'))
        except:
            return 1024  # Default estimate
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.access_stats.clear()
            self.current_memory = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'memory_usage': self.current_memory,
                'memory_limit': self.memory_limit,
                'strategy': self.strategy.value,
                'hit_rate': self._calculate_hit_rate()
            }
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total_accesses = sum(self.access_stats.values())
        if total_accesses == 0:
            return 0.0
        return len(self.access_stats) / total_accesses if total_accesses > 0 else 0.0


class ParallelProcessor:
    """
    Parallel processing engine for rule execution.
    
    Provides thread and process pools for parallel rule evaluation,
    with intelligent workload distribution and resource management.
    """
    
    def __init__(self, max_workers: Optional[int] = None, use_processes: bool = False):
        """Initialize parallel processor"""
        self.max_workers = max_workers or min(32, (multiprocessing.cpu_count() or 1) + 4)
        self.use_processes = use_processes
        self.executor = None
        self.lock = threading.Lock()
        
    def __enter__(self):
        """Context manager entry"""
        self._create_executor()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self._shutdown_executor()
    
    def _create_executor(self):
        """Create thread or process pool executor"""
        if self.use_processes:
            self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
        else:
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
    
    def _shutdown_executor(self):
        """Shutdown executor"""
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None
    
    def execute_parallel(self, func: Callable, items: List[Any], 
                        chunk_size: Optional[int] = None) -> List[Any]:
        """
        Execute function in parallel on items.
        
        Args:
            func: Function to execute
            items: List of items to process
            chunk_size: Size of chunks for processing
            
        Returns:
            List of results in same order as items
        """
        if not items:
            return []
        
        if not self.executor:
            self._create_executor()
        
        # Determine chunk size
        if chunk_size is None:
            chunk_size = max(1, len(items) // (self.max_workers * 2))
        
        # Submit tasks
        futures = []
        for i in range(0, len(items), chunk_size):
            chunk = items[i:i + chunk_size]
            future = self.executor.submit(self._process_chunk, func, chunk)
            futures.append((i, future))
        
        # Collect results
        results = [None] * len(items)
        for start_idx, future in futures:
            try:
                chunk_results = future.result(timeout=300)  # 5 minute timeout
                for j, result in enumerate(chunk_results):
                    results[start_idx + j] = result
            except Exception as e:
                logger.error(f"Error in parallel execution: {e}")
                # Fill with None for failed chunks
                for j in range(len(chunk_results) if 'chunk_results' in locals() else chunk_size):
                    if start_idx + j < len(results):
                        results[start_idx + j] = None
        
        return results
    
    def _process_chunk(self, func: Callable, chunk: List[Any]) -> List[Any]:
        """Process a chunk of items"""
        return [func(item) for item in chunk]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get parallel processor statistics"""
        return {
            'max_workers': self.max_workers,
            'use_processes': self.use_processes,
            'executor_active': self.executor is not None
        }


class MemoryOptimizer:
    """
    Memory optimization and management system.
    
    Provides memory monitoring, garbage collection optimization,
    and adaptive memory management for large rule sets.
    """
    
    def __init__(self, memory_threshold: float = 0.8):
        """Initialize memory optimizer"""
        self.memory_threshold = memory_threshold
        self.memory_history = []
        self.gc_stats = defaultdict(int)
        self.weak_refs = weakref.WeakSet()
        
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / 1024 / 1024
        }
    
    def should_optimize(self) -> bool:
        """Check if memory optimization is needed"""
        memory_usage = self.get_memory_usage()
        return memory_usage['percent'] > (self.memory_threshold * 100)
    
    def optimize_memory(self) -> Dict[str, Any]:
        """Perform memory optimization"""
        before_stats = self.get_memory_usage()
        
        # Force garbage collection
        collected = gc.collect()
        
        # Clear weak references
        self.weak_refs.clear()
        
        # Clear memory history if too large
        if len(self.memory_history) > 1000:
            self.memory_history = self.memory_history[-500:]
        
        after_stats = self.get_memory_usage()
        
        optimization_stats = {
            'objects_collected': collected,
            'memory_freed_mb': before_stats['rss_mb'] - after_stats['rss_mb'],
            'before_memory_mb': before_stats['rss_mb'],
            'after_memory_mb': after_stats['rss_mb']
        }
        
        self.gc_stats['total_collections'] += 1
        self.gc_stats['total_objects_collected'] += collected
        
        return optimization_stats
    
    def add_weak_ref(self, obj: Any) -> None:
        """Add weak reference for automatic cleanup"""
        self.weak_refs.add(obj)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory optimization statistics"""
        current_memory = self.get_memory_usage()
        
        return {
            'current_memory_mb': current_memory['rss_mb'],
            'memory_percent': current_memory['percent'],
            'available_memory_mb': current_memory['available_mb'],
            'total_collections': self.gc_stats['total_collections'],
            'total_objects_collected': self.gc_stats['total_objects_collected'],
            'weak_refs_count': len(self.weak_refs)
        }


class PerformanceMonitor:
    """
    Performance monitoring and metrics collection.
    
    Tracks execution times, resource usage, and performance
    trends for optimization and debugging.
    """
    
    def __init__(self):
        """Initialize performance monitor"""
        self.metrics_history = []
        self.start_times = {}
        self.operation_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        
    def start_timer(self, operation: str) -> None:
        """Start timing an operation"""
        self.start_times[operation] = time.time()
        self.operation_counts[operation] += 1
    
    def end_timer(self, operation: str) -> float:
        """End timing an operation and return duration"""
        if operation not in self.start_times:
            return 0.0
        
        duration = time.time() - self.start_times[operation]
        del self.start_times[operation]
        
        # Store metric
        metric = PerformanceMetrics(
            execution_time=duration,
            memory_usage=self._get_memory_usage(),
            cpu_usage=self._get_cpu_usage()
        )
        
        self.metrics_history.append({
            'operation': operation,
            'timestamp': time.time(),
            'metrics': metric
        })
        
        # Keep only last 1000 metrics
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-500:]
        
        return duration
    
    def record_error(self, operation: str, error: Exception) -> None:
        """Record an error for an operation"""
        self.error_counts[operation] += 1
        logger.error(f"Error in {operation}: {error}")
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage percentage"""
        try:
            return psutil.virtual_memory().percent
        except:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        try:
            return psutil.cpu_percent()
        except:
            return 0.0
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics"""
        if not self.metrics_history:
            return {}
        
        # Calculate averages
        execution_times = [m['metrics'].execution_time for m in self.metrics_history]
        memory_usages = [m['metrics'].memory_usage for m in self.metrics_history]
        cpu_usages = [m['metrics'].cpu_usage for m in self.metrics_history]
        
        return {
            'total_operations': sum(self.operation_counts.values()),
            'total_errors': sum(self.error_counts.values()),
            'avg_execution_time': sum(execution_times) / len(execution_times),
            'avg_memory_usage': sum(memory_usages) / len(memory_usages),
            'avg_cpu_usage': sum(cpu_usages) / len(cpu_usages),
            'operation_counts': dict(self.operation_counts),
            'error_counts': dict(self.error_counts)
        }


class PerformanceOptimizer:
    """
    Main performance optimization engine.
    
    Orchestrates parallel processing, caching, memory optimization,
    and performance monitoring for the MCP rule engine.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize performance optimizer"""
        self.config = config or {}
        
        # Initialize components
        self.cache = IntelligentCache(
            max_size=self.config.get('cache_size', 1000),
            strategy=CacheStrategy(self.config.get('cache_strategy', 'adaptive'))
        )
        
        self.parallel_processor = ParallelProcessor(
            max_workers=self.config.get('max_workers'),
            use_processes=self.config.get('use_processes', False)
        )
        
        self.memory_optimizer = MemoryOptimizer(
            memory_threshold=self.config.get('memory_threshold', 0.8)
        )
        
        self.performance_monitor = PerformanceMonitor()
        
        # Optimization settings
        self.optimization_level = OptimizationLevel(
            self.config.get('optimization_level', 'advanced')
        )
        
        self.enabled = self.config.get('enabled', True)
        
    def optimize_rule_execution(self, rules: List[MCPRule], 
                               building_objects: List[BuildingObject],
                               execution_func: Callable) -> List[Any]:
        """
        Optimize rule execution with parallel processing and caching.
        
        Args:
            rules: List of rules to execute
            building_objects: Building objects for validation
            execution_func: Function to execute for each rule
            
        Returns:
            List of execution results
        """
        if not self.enabled:
            return [execution_func(rule, building_objects) for rule in rules]
        
        self.performance_monitor.start_timer('rule_execution')
        
        try:
            # Check memory and optimize if needed
            if self.memory_optimizer.should_optimize():
                self.memory_optimizer.optimize_memory()
            
            # Create cache key for building objects
            cache_key = self._create_cache_key(building_objects)
            
            # Check cache for existing results
            cached_results = self.cache.get(cache_key)
            if cached_results:
                self.performance_monitor.end_timer('rule_execution')
                return cached_results
            
            # Execute rules in parallel
            with self.parallel_processor as processor:
                results = processor.execute_parallel(
                    lambda rule: execution_func(rule, building_objects),
                    rules
                )
            
            # Cache results
            self.cache.set(cache_key, results, ttl=3600)  # 1 hour TTL
            
            self.performance_monitor.end_timer('rule_execution')
            return results
            
        except Exception as e:
            self.performance_monitor.record_error('rule_execution', e)
            self.performance_monitor.end_timer('rule_execution')
            raise
    
    def optimize_condition_evaluation(self, conditions: List[RuleCondition],
                                   objects: List[BuildingObject],
                                   evaluation_func: Callable) -> List[Any]:
        """
        Optimize condition evaluation with caching and parallel processing.
        
        Args:
            conditions: List of conditions to evaluate
            objects: Building objects to evaluate against
            evaluation_func: Function to evaluate each condition
            
        Returns:
            List of evaluation results
        """
        if not self.enabled:
            return [evaluation_func(condition, objects) for condition in conditions]
        
        self.performance_monitor.start_timer('condition_evaluation')
        
        try:
            # Create cache key
            cache_key = self._create_cache_key(conditions, objects)
            
            # Check cache
            cached_results = self.cache.get(cache_key)
            if cached_results:
                self.performance_monitor.end_timer('condition_evaluation')
                return cached_results
            
            # Evaluate conditions in parallel
            with self.parallel_processor as processor:
                results = processor.execute_parallel(
                    lambda condition: evaluation_func(condition, objects),
                    conditions
                )
            
            # Cache results
            self.cache.set(cache_key, results, ttl=1800)  # 30 minutes TTL
            
            self.performance_monitor.end_timer('condition_evaluation')
            return results
            
        except Exception as e:
            self.performance_monitor.record_error('condition_evaluation', e)
            self.performance_monitor.end_timer('condition_evaluation')
            raise
    
    def _create_cache_key(self, *args) -> str:
        """Create cache key from arguments"""
        # Create hash of arguments
        key_data = json.dumps(args, default=str, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get comprehensive optimization statistics"""
        return {
            'cache_stats': self.cache.get_stats(),
            'parallel_stats': self.parallel_processor.get_stats(),
            'memory_stats': self.memory_optimizer.get_stats(),
            'performance_summary': self.performance_monitor.get_performance_summary(),
            'optimization_level': self.optimization_level.value,
            'enabled': self.enabled
        }
    
    def clear_cache(self) -> None:
        """Clear all caches"""
        self.cache.clear()
    
    def optimize_memory(self) -> Dict[str, Any]:
        """Perform memory optimization"""
        return self.memory_optimizer.optimize_memory()
    
    def set_optimization_level(self, level: OptimizationLevel) -> None:
        """Set optimization level"""
        self.optimization_level = level
        
        # Adjust settings based on level
        if level == OptimizationLevel.NONE:
            self.enabled = False
        elif level == OptimizationLevel.BASIC:
            self.enabled = True
            self.cache.max_size = 100
        elif level == OptimizationLevel.ADVANCED:
            self.enabled = True
            self.cache.max_size = 1000
        elif level == OptimizationLevel.AGGRESSIVE:
            self.enabled = True
            self.cache.max_size = 5000
            self.parallel_processor.max_workers = min(64, multiprocessing.cpu_count() * 2)


class PerformanceOptimizationError(Exception):
    """Exception raised when performance optimization fails"""
    pass 