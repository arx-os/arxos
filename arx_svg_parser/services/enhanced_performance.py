"""
Enhanced Performance & Scalability System for SVG-BIM

This module provides advanced performance optimization including:
- Intelligent batch processing with adaptive sizing
- Multi-level parallelization (thread/process pools)
- Advanced profiling with bottleneck detection
- Resource monitoring and adaptive optimization
- Performance metrics collection and analysis
- Scalability testing and benchmarking
"""

import time
import threading
import multiprocessing
import psutil
import gc
import asyncio
import statistics
from typing import Dict, List, Any, Callable, Optional, Union, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from functools import wraps, lru_cache
from collections import defaultdict, deque
import logging
from dataclasses import dataclass, field
from enum import Enum
import weakref
from contextlib import contextmanager
import json
import os
from pathlib import Path

# Import OptimizationLevel from existing performance optimizer
from services.performance_optimizer import OptimizationLevel

logger = logging.getLogger(__name__)


class BatchStrategy(Enum):
    """Batch processing strategies."""
    FIXED_SIZE = "fixed_size"
    ADAPTIVE_SIZE = "adaptive_size"
    MEMORY_BASED = "memory_based"
    TIME_BASED = "time_based"


class ParallelizationLevel(Enum):
    """Parallelization levels."""
    NONE = "none"
    THREADS = "threads"
    PROCESSES = "processes"
    HYBRID = "hybrid"


@dataclass
class BatchMetrics:
    """Metrics for batch processing."""
    batch_size: int
    processing_time: float
    memory_usage: float
    cpu_usage: float
    success_count: int
    error_count: int
    throughput: float  # items per second


@dataclass
class ParallelMetrics:
    """Metrics for parallel processing."""
    worker_count: int
    total_time: float
    parallel_efficiency: float
    load_balance: float
    communication_overhead: float


@dataclass
class ScalabilityMetrics:
    """Comprehensive scalability metrics."""
    input_size: int
    processing_time: float
    memory_usage: float
    cpu_usage: float
    throughput: float
    efficiency: float
    bottlenecks: List[str]
    recommendations: List[str]


class AdaptiveBatchProcessor:
    """Intelligent batch processor with adaptive sizing."""
    
    def __init__(self, initial_batch_size: int = 100, strategy: BatchStrategy = BatchStrategy.ADAPTIVE_SIZE):
        self.initial_batch_size = initial_batch_size
        self.strategy = strategy
        self.batch_metrics: List[BatchMetrics] = []
        self.optimal_batch_size = initial_batch_size
        self.performance_history: deque = deque(maxlen=50)
        
    def process_batches(self, items: List[Any], process_func: Callable, 
                       max_workers: int = None) -> List[Any]:
        """Process items in adaptive batches."""
        if not items:
            return []
        
        max_workers = max_workers or multiprocessing.cpu_count()
        results = []
        
        # Determine optimal batch size
        batch_size = self._calculate_optimal_batch_size(len(items), max_workers)
        
        # Process in batches
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = self._process_single_batch(batch, process_func, max_workers)
            results.extend(batch_results)
            
            # Update batch size based on performance
            self._update_batch_size()
        
        return results
    
    def _calculate_optimal_batch_size(self, total_items: int, max_workers: int) -> int:
        """Calculate optimal batch size based on strategy."""
        if self.strategy == BatchStrategy.FIXED_SIZE:
            return self.initial_batch_size
        elif self.strategy == BatchStrategy.ADAPTIVE_SIZE:
            return self._adaptive_batch_size(total_items, max_workers)
        elif self.strategy == BatchStrategy.MEMORY_BASED:
            return self._memory_based_batch_size()
        elif self.strategy == BatchStrategy.TIME_BASED:
            return self._time_based_batch_size()
        else:
            return self.initial_batch_size
    
    def _adaptive_batch_size(self, total_items: int, max_workers: int) -> int:
        """Calculate adaptive batch size based on performance history."""
        if not self.performance_history:
            return self.initial_batch_size
        
        # Analyze recent performance
        recent_metrics = list(self.performance_history)[-10:]
        avg_throughput = statistics.mean([m.throughput for m in recent_metrics])
        
        # Adjust batch size based on throughput
        if avg_throughput > 1000:  # High throughput
            return min(self.optimal_batch_size * 2, total_items // max_workers)
        elif avg_throughput < 100:  # Low throughput
            return max(self.optimal_batch_size // 2, 10)
        else:
            return self.optimal_batch_size
    
    def _memory_based_batch_size(self) -> int:
        """Calculate batch size based on available memory."""
        available_memory = psutil.virtual_memory().available / (1024 * 1024)  # MB
        memory_per_item = 0.1  # Estimated MB per item
        
        max_items = int(available_memory / memory_per_item / 2)  # Use 50% of available memory
        return min(max_items, self.optimal_batch_size)
    
    def _time_based_batch_size(self) -> int:
        """Calculate batch size based on processing time."""
        if not self.performance_history:
            return self.initial_batch_size
        
        recent_times = [m.processing_time for m in list(self.performance_history)[-5:]]
        avg_time = statistics.mean(recent_times)
        
        target_time = 0.1  # Target 100ms per batch
        if avg_time > target_time * 2:
            return max(self.optimal_batch_size // 2, 10)
        elif avg_time < target_time / 2:
            return self.optimal_batch_size * 2
        else:
            return self.optimal_batch_size
    
    def _process_single_batch(self, batch: List[Any], process_func: Callable, 
                             max_workers: int) -> List[Any]:
        """Process a single batch and collect metrics."""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        start_cpu = psutil.cpu_percent()
        
        try:
            # Use parallel processing for large batches
            if len(batch) > 50 and max_workers > 1:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = [executor.submit(process_func, item) for item in batch]
                    results = [future.result() for future in as_completed(futures)]
            else:
                results = [process_func(item) for item in batch]
            
            success_count = len(results)
            error_count = 0
            
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            results = []
            success_count = 0
            error_count = len(batch)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        end_cpu = psutil.cpu_percent()
        
        # Calculate metrics
        processing_time = end_time - start_time
        memory_usage = end_memory - start_memory
        cpu_usage = (start_cpu + end_cpu) / 2
        throughput = len(batch) / processing_time if processing_time > 0 else 0
        
        # Store metrics
        metrics = BatchMetrics(
            batch_size=len(batch),
            processing_time=processing_time,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            success_count=success_count,
            error_count=error_count,
            throughput=throughput
        )
        
        self.batch_metrics.append(metrics)
        self.performance_history.append(metrics)
        
        return results
    
    def _update_batch_size(self) -> None:
        """Update optimal batch size based on recent performance."""
        if len(self.performance_history) < 5:
            return
        
        recent_metrics = list(self.performance_history)[-5:]
        avg_throughput = statistics.mean([m.throughput for m in recent_metrics])
        
        # Adjust optimal batch size
        if avg_throughput > 1000:
            self.optimal_batch_size = min(self.optimal_batch_size * 1.2, 1000)
        elif avg_throughput < 100:
            self.optimal_batch_size = max(self.optimal_batch_size * 0.8, 10)
    
    def get_batch_statistics(self) -> Dict[str, Any]:
        """Get batch processing statistics."""
        if not self.batch_metrics:
            return {"error": "No batch metrics available"}
        
        throughputs = [m.throughput for m in self.batch_metrics]
        processing_times = [m.processing_time for m in self.batch_metrics]
        memory_usages = [m.memory_usage for m in self.batch_metrics]
        
        return {
            "total_batches": len(self.batch_metrics),
            "optimal_batch_size": self.optimal_batch_size,
            "avg_throughput": statistics.mean(throughputs),
            "avg_processing_time": statistics.mean(processing_times),
            "avg_memory_usage": statistics.mean(memory_usages),
            "total_items_processed": sum(m.success_count for m in self.batch_metrics),
            "total_errors": sum(m.error_count for m in self.batch_metrics),
            "success_rate": sum(m.success_count for m in self.batch_metrics) / 
                          sum(m.success_count + m.error_count for m in self.batch_metrics) * 100
        }


class AdvancedParallelProcessor:
    """Advanced parallel processor with multiple strategies."""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=self.max_workers)
        self.parallel_metrics: List[ParallelMetrics] = []
        self.active_tasks: Dict[str, Any] = {}
        
    def execute_parallel(self, func: Callable, items: List[Any], 
                        level: ParallelizationLevel = ParallelizationLevel.THREADS,
                        batch_size: int = 100) -> List[Any]:
        """Execute function in parallel with different strategies."""
        if not items:
            return []
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        try:
            if level == ParallelizationLevel.NONE:
                results = [func(item) for item in items]
            elif level == ParallelizationLevel.THREADS:
                results = self._execute_threads(func, items, batch_size)
            elif level == ParallelizationLevel.PROCESSES:
                results = self._execute_processes(func, items, batch_size)
            elif level == ParallelizationLevel.HYBRID:
                results = self._execute_hybrid(func, items, batch_size)
            else:
                results = [func(item) for item in items]
            
            success_count = len(results)
            error_count = 0
            
        except Exception as e:
            logger.error(f"Parallel execution error: {e}")
            results = []
            success_count = 0
            error_count = len(items)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Calculate metrics
        total_time = end_time - start_time
        memory_usage = end_memory - start_memory
        parallel_efficiency = self._calculate_efficiency(total_time, len(items), level)
        load_balance = self._calculate_load_balance(items, level)
        communication_overhead = self._calculate_communication_overhead(level)
        
        # Store metrics
        metrics = ParallelMetrics(
            worker_count=self.max_workers,
            total_time=total_time,
            parallel_efficiency=parallel_efficiency,
            load_balance=load_balance,
            communication_overhead=communication_overhead
        )
        
        self.parallel_metrics.append(metrics)
        
        return results
    
    def _execute_threads(self, func: Callable, items: List[Any], batch_size: int) -> List[Any]:
        """Execute using thread pool."""
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                batch_results = list(executor.map(func, batch))
                results.extend(batch_results)
        
        return results
    
    def _execute_processes(self, func: Callable, items: List[Any], batch_size: int) -> List[Any]:
        """Execute using process pool."""
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                batch_results = list(executor.map(func, batch))
                results.extend(batch_results)
        
        return results
    
    def _execute_hybrid(self, func: Callable, items: List[Any], batch_size: int) -> List[Any]:
        """Execute using hybrid thread/process approach."""
        # Split items for different processing strategies
        cpu_intensive_items = items[:len(items)//2]
        io_intensive_items = items[len(items)//2:]
        
        results = []
        
        # Process CPU-intensive items with processes
        if cpu_intensive_items:
            with ProcessPoolExecutor(max_workers=self.max_workers//2) as executor:
                cpu_results = list(executor.map(func, cpu_intensive_items))
                results.extend(cpu_results)
        
        # Process IO-intensive items with threads
        if io_intensive_items:
            with ThreadPoolExecutor(max_workers=self.max_workers//2) as executor:
                io_results = list(executor.map(func, io_intensive_items))
                results.extend(io_results)
        
        return results
    
    def _calculate_efficiency(self, total_time: float, item_count: int, 
                            level: ParallelizationLevel) -> float:
        """Calculate parallel efficiency."""
        if level == ParallelizationLevel.NONE:
            return 1.0
        
        # Estimate sequential time
        estimated_sequential_time = total_time * self.max_workers
        
        if estimated_sequential_time > 0:
            return (item_count / estimated_sequential_time) / (item_count / total_time)
        else:
            return 0.0
    
    def _calculate_load_balance(self, items: List[Any], level: ParallelizationLevel) -> float:
        """Calculate load balance across workers."""
        if level == ParallelizationLevel.NONE:
            return 1.0
        
        # Simple estimation based on worker count
        items_per_worker = len(items) / self.max_workers
        ideal_distribution = [items_per_worker] * self.max_workers
        
        # Calculate variance from ideal
        actual_distribution = [len(items) // self.max_workers] * self.max_workers
        remainder = len(items) % self.max_workers
        for i in range(remainder):
            actual_distribution[i] += 1
        
        variance = sum((actual - ideal) ** 2 for actual, ideal in zip(actual_distribution, ideal_distribution))
        return 1.0 / (1.0 + variance)
    
    def _calculate_communication_overhead(self, level: ParallelizationLevel) -> float:
        """Calculate communication overhead."""
        if level == ParallelizationLevel.NONE:
            return 0.0
        elif level == ParallelizationLevel.THREADS:
            return 0.05  # Low overhead for threads
        elif level == ParallelizationLevel.PROCESSES:
            return 0.15  # Higher overhead for processes
        elif level == ParallelizationLevel.HYBRID:
            return 0.10  # Medium overhead for hybrid
        else:
            return 0.0
    
    def get_parallel_statistics(self) -> Dict[str, Any]:
        """Get parallel processing statistics."""
        if not self.parallel_metrics:
            return {"error": "No parallel metrics available"}
        
        efficiencies = [m.parallel_efficiency for m in self.parallel_metrics]
        load_balances = [m.load_balance for m in self.parallel_metrics]
        communication_overheads = [m.communication_overhead for m in self.parallel_metrics]
        
        return {
            "total_operations": len(self.parallel_metrics),
            "avg_efficiency": statistics.mean(efficiencies),
            "avg_load_balance": statistics.mean(load_balances),
            "avg_communication_overhead": statistics.mean(communication_overheads),
            "max_workers": self.max_workers
        }


class AdvancedPerformanceProfiler:
    """Advanced performance profiler with bottleneck detection."""
    
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.operation_times: Dict[str, List[float]] = defaultdict(list)
        self.bottlenecks: List[Dict[str, Any]] = []
        self.performance_alerts: List[Dict[str, Any]] = []
        self.thresholds = {
            "slow_operation": 1.0,  # seconds
            "high_memory": 500.0,   # MB
            "high_cpu": 80.0,       # percent
            "error_rate": 0.1       # 10%
        }
        
    def profile_operation(self, operation_name: str, collect_detailed: bool = True):
        """Decorator to profile operations with detailed metrics."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss / 1024 / 1024
                start_cpu = psutil.cpu_percent()
                
                # Collect detailed metrics if requested
                detailed_metrics = {}
                if collect_detailed:
                    detailed_metrics = self._collect_detailed_metrics()
                
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
                    
                    # Create metrics
                    metrics = PerformanceMetrics(
                        operation_name=operation_name,
                        execution_time=execution_time,
                        memory_usage=memory_usage,
                        cpu_usage=cpu_usage,
                        errors=errors
                    )
                    
                    self.metrics.append(metrics)
                    self.operation_times[operation_name].append(execution_time)
                    
                    # Check for bottlenecks and alerts
                    self._check_bottlenecks(operation_name, execution_time, memory_usage, cpu_usage)
                    self._check_alerts(operation_name, execution_time, memory_usage, cpu_usage, errors)
                
                return result
            return wrapper
        return decorator
    
    def _collect_detailed_metrics(self) -> Dict[str, Any]:
        """Collect detailed system metrics."""
        return {
            "cpu_count": multiprocessing.cpu_count(),
            "memory_total": psutil.virtual_memory().total / (1024 * 1024 * 1024),  # GB
            "memory_available": psutil.virtual_memory().available / (1024 * 1024 * 1024),  # GB
            "disk_usage": psutil.disk_usage('/').percent,
            "network_io": psutil.net_io_counters()._asdict()
        }
    
    def _check_bottlenecks(self, operation_name: str, execution_time: float, 
                          memory_usage: float, cpu_usage: float) -> None:
        """Check for performance bottlenecks."""
        if execution_time > self.thresholds["slow_operation"]:
            self.bottlenecks.append({
                "type": "slow_operation",
                "operation": operation_name,
                "execution_time": execution_time,
                "threshold": self.thresholds["slow_operation"],
                "timestamp": time.time()
            })
        
        if memory_usage > self.thresholds["high_memory"]:
            self.bottlenecks.append({
                "type": "high_memory",
                "operation": operation_name,
                "memory_usage": memory_usage,
                "threshold": self.thresholds["high_memory"],
                "timestamp": time.time()
            })
        
        if cpu_usage > self.thresholds["high_cpu"]:
            self.bottlenecks.append({
                "type": "high_cpu",
                "operation": operation_name,
                "cpu_usage": cpu_usage,
                "threshold": self.thresholds["high_cpu"],
                "timestamp": time.time()
            })
    
    def _check_alerts(self, operation_name: str, execution_time: float, 
                     memory_usage: float, cpu_usage: float, errors: List[str]) -> None:
        """Check for performance alerts."""
        error_rate = len(errors) / 1 if errors else 0  # Simplified error rate
        
        if error_rate > self.thresholds["error_rate"]:
            self.performance_alerts.append({
                "type": "high_error_rate",
                "operation": operation_name,
                "error_rate": error_rate,
                "errors": errors,
                "timestamp": time.time()
            })
    
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
                "avg_time": statistics.mean(times),
                "max_time": max(times),
                "min_time": min(times),
                "std_dev": statistics.stdev(times) if len(times) > 1 else 0
            }
        
        # Bottleneck analysis
        bottleneck_summary = defaultdict(int)
        for bottleneck in self.bottlenecks:
            bottleneck_summary[bottleneck["type"]] += 1
        
        return {
            "summary": {
                "total_operations": total_operations,
                "total_execution_time": total_time,
                "total_memory_usage": total_memory,
                "total_errors": total_errors,
                "avg_execution_time": total_time / total_operations if total_operations > 0 else 0
            },
            "operation_statistics": operation_stats,
            "bottlenecks": {
                "total": len(self.bottlenecks),
                "by_type": dict(bottleneck_summary),
                "recent": self.bottlenecks[-10:] if len(self.bottlenecks) > 10 else self.bottlenecks
            },
            "alerts": {
                "total": len(self.performance_alerts),
                "recent": self.performance_alerts[-10:] if len(self.performance_alerts) > 10 else self.performance_alerts
            },
            "recent_metrics": self.metrics[-10:] if len(self.metrics) > 10 else self.metrics
        }


class ScalabilityAnalyzer:
    """Analyze system scalability and provide recommendations."""
    
    def __init__(self):
        self.scalability_tests: List[ScalabilityMetrics] = []
        self.benchmark_results: Dict[str, List[float]] = defaultdict(list)
        
    def analyze_scalability(self, input_sizes: List[int], process_func: Callable,
                          parallel_level: ParallelizationLevel = ParallelizationLevel.THREADS) -> Dict[str, Any]:
        """Analyze scalability across different input sizes."""
        results = []
        
        for size in input_sizes:
            # Create test data
            test_data = list(range(size))
            
            # Measure performance
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024
            start_cpu = psutil.cpu_percent()
            
            try:
                # Process with parallel processor
                processor = AdvancedParallelProcessor()
                processed_data = processor.execute_parallel(process_func, test_data, parallel_level)
                
                success_count = len(processed_data)
                error_count = size - success_count
                
            except Exception as e:
                logger.error(f"Scalability test failed for size {size}: {e}")
                processed_data = []
                success_count = 0
                error_count = size
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            end_cpu = psutil.cpu_percent()
            
            # Calculate metrics
            processing_time = end_time - start_time
            memory_usage = end_memory - start_memory
            cpu_usage = (start_cpu + end_cpu) / 2
            throughput = size / processing_time if processing_time > 0 else 0
            efficiency = self._calculate_efficiency(size, processing_time, parallel_level)
            
            # Detect bottlenecks
            bottlenecks = self._detect_bottlenecks(size, processing_time, memory_usage, cpu_usage)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(size, processing_time, memory_usage, cpu_usage, bottlenecks)
            
            # Create metrics
            metrics = ScalabilityMetrics(
                input_size=size,
                processing_time=processing_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                throughput=throughput,
                efficiency=efficiency,
                bottlenecks=bottlenecks,
                recommendations=recommendations
            )
            
            self.scalability_tests.append(metrics)
            results.append(metrics)
        
        return self._generate_scalability_report(results)
    
    def _calculate_efficiency(self, input_size: int, processing_time: float, 
                            parallel_level: ParallelizationLevel) -> float:
        """Calculate processing efficiency."""
        if parallel_level == ParallelizationLevel.NONE:
            return 1.0
        
        # Estimate ideal time based on linear scaling
        base_time = processing_time / input_size if input_size > 0 else 0
        ideal_time = base_time * input_size
        
        if ideal_time > 0:
            return ideal_time / processing_time
        else:
            return 0.0
    
    def _detect_bottlenecks(self, input_size: int, processing_time: float, 
                           memory_usage: float, cpu_usage: float) -> List[str]:
        """Detect performance bottlenecks."""
        bottlenecks = []
        
        # Time-based bottlenecks
        if processing_time > input_size * 0.001:  # More than 1ms per item
            bottlenecks.append("processing_time")
        
        # Memory-based bottlenecks
        if memory_usage > input_size * 0.1:  # More than 0.1MB per item
            bottlenecks.append("memory_usage")
        
        # CPU-based bottlenecks
        if cpu_usage > 90:
            bottlenecks.append("cpu_usage")
        
        return bottlenecks
    
    def _generate_recommendations(self, input_size: int, processing_time: float,
                                memory_usage: float, cpu_usage: float, 
                                bottlenecks: List[str]) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        if "processing_time" in bottlenecks:
            recommendations.append("Consider parallel processing")
            recommendations.append("Optimize algorithm complexity")
        
        if "memory_usage" in bottlenecks:
            recommendations.append("Implement memory pooling")
            recommendations.append("Use streaming processing")
        
        if "cpu_usage" in bottlenecks:
            recommendations.append("Increase worker count")
            recommendations.append("Use process-based parallelization")
        
        if not bottlenecks:
            recommendations.append("Performance is optimal")
        
        return recommendations
    
    def _generate_scalability_report(self, results: List[ScalabilityMetrics]) -> Dict[str, Any]:
        """Generate comprehensive scalability report."""
        if not results:
            return {"error": "No scalability test results"}
        
        # Calculate scaling factors
        throughputs = [r.throughput for r in results]
        efficiencies = [r.efficiency for r in results]
        memory_usages = [r.memory_usage for r in results]
        
        # Analyze scaling patterns
        scaling_analysis = self._analyze_scaling_patterns(results)
        
        return {
            "test_count": len(results),
            "input_sizes": [r.input_size for r in results],
            "throughputs": throughputs,
            "efficiencies": efficiencies,
            "memory_usages": memory_usages,
            "scaling_analysis": scaling_analysis,
            "recommendations": self._generate_overall_recommendations(results)
        }
    
    def _analyze_scaling_patterns(self, results: List[ScalabilityMetrics]) -> Dict[str, Any]:
        """Analyze how the system scales with input size."""
        if len(results) < 2:
            return {"error": "Insufficient data for scaling analysis"}
        
        # Calculate scaling factors
        input_sizes = [r.input_size for r in results]
        processing_times = [r.processing_time for r in results]
        
        # Linear scaling analysis
        scaling_factors = []
        for i in range(1, len(results)):
            size_ratio = input_sizes[i] / input_sizes[i-1]
            time_ratio = processing_times[i] / processing_times[i-1]
            scaling_factor = time_ratio / size_ratio
            scaling_factors.append(scaling_factor)
        
        avg_scaling_factor = statistics.mean(scaling_factors)
        
        # Determine scaling type
        if avg_scaling_factor < 0.8:
            scaling_type = "sub-linear (excellent)"
        elif avg_scaling_factor < 1.2:
            scaling_type = "linear (good)"
        elif avg_scaling_factor < 2.0:
            scaling_type = "super-linear (acceptable)"
        else:
            scaling_type = "exponential (poor)"
        
        return {
            "avg_scaling_factor": avg_scaling_factor,
            "scaling_type": scaling_type,
            "scaling_factors": scaling_factors
        }
    
    def _generate_overall_recommendations(self, results: List[ScalabilityMetrics]) -> List[str]:
        """Generate overall recommendations based on all test results."""
        recommendations = []
        
        # Analyze bottlenecks across all tests
        all_bottlenecks = []
        for result in results:
            all_bottlenecks.extend(result.bottlenecks)
        
        bottleneck_counts = defaultdict(int)
        for bottleneck in all_bottlenecks:
            bottleneck_counts[bottleneck] += 1
        
        # Generate recommendations based on most common bottlenecks
        if bottleneck_counts["processing_time"] > len(results) * 0.5:
            recommendations.append("Implement caching for repeated operations")
            recommendations.append("Consider using more efficient algorithms")
        
        if bottleneck_counts["memory_usage"] > len(results) * 0.5:
            recommendations.append("Implement memory management strategies")
            recommendations.append("Consider streaming processing for large datasets")
        
        if bottleneck_counts["cpu_usage"] > len(results) * 0.5:
            recommendations.append("Increase parallelization level")
            recommendations.append("Consider distributed processing")
        
        if not recommendations:
            recommendations.append("System scales well across tested input sizes")
        
        return recommendations


class EnhancedPerformanceOptimizer:
    """Enhanced performance optimizer combining all optimization strategies."""
    
    def __init__(self, optimization_level: OptimizationLevel = OptimizationLevel.STANDARD):
        self.optimization_level = optimization_level
        self.batch_processor = AdaptiveBatchProcessor()
        self.parallel_processor = AdvancedParallelProcessor()
        self.profiler = AdvancedPerformanceProfiler()
        self.scalability_analyzer = ScalabilityAnalyzer()
        self.monitoring_active = False
        self.monitor_thread = None
        
    def optimize_operation(self, operation_name: str, func: Callable = None,
                          use_batching: bool = True, use_parallel: bool = True,
                          use_profiling: bool = True, batch_size: int = 100,
                          parallel_level: ParallelizationLevel = ParallelizationLevel.THREADS):
        """Optimize an operation with multiple strategies."""
        if func is None:
            # Use as decorator
            def decorator(operation_func):
                @wraps(operation_func)
                def wrapper(*args, **kwargs):
                    return self._execute_optimized_operation(
                        operation_name, operation_func, args, kwargs,
                        use_batching, use_parallel, use_profiling, batch_size, parallel_level
                    )
                return wrapper
            return decorator
        
        # Use as context manager
        return self._execute_optimized_operation(
            operation_name, func, [], {},
            use_batching, use_parallel, use_profiling, batch_size, parallel_level
        )
    
    def _execute_optimized_operation(self, operation_name: str, func: Callable,
                                   args: List[Any], kwargs: Dict[str, Any],
                                   use_batching: bool, use_parallel: bool,
                                   use_profiling: bool, batch_size: int,
                                   parallel_level: ParallelizationLevel):
        """Execute operation with optimizations."""
        if use_profiling:
            profiled_func = self.profiler.profile_operation(operation_name)(func)
        else:
            profiled_func = func
        
        if use_batching and len(args) > 0 and isinstance(args[0], (list, tuple)):
            # Batch processing
            items = args[0]
            if use_parallel:
                return self.parallel_processor.execute_parallel(
                    profiled_func, items, parallel_level, batch_size
                )
            else:
                return self.batch_processor.process_batches(
                    items, profiled_func
                )
        else:
            # Single operation
            return profiled_func(*args, **kwargs)
    
    def run_scalability_test(self, input_sizes: List[int], process_func: Callable,
                           parallel_level: ParallelizationLevel = ParallelizationLevel.THREADS) -> Dict[str, Any]:
        """Run comprehensive scalability test."""
        return self.scalability_analyzer.analyze_scalability(input_sizes, process_func, parallel_level)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        return {
            "batch_statistics": self.batch_processor.get_batch_statistics(),
            "parallel_statistics": self.parallel_processor.get_parallel_statistics(),
            "performance_report": self.profiler.get_performance_report()
        }
    
    def start_monitoring(self) -> None:
        """Start continuous performance monitoring."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_performance, daemon=True)
        self.monitor_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        logger.info("Performance monitoring stopped")
    
    def _monitor_performance(self) -> None:
        """Monitor performance continuously."""
        while self.monitoring_active:
            try:
                # Collect current metrics
                memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
                cpu_usage = psutil.cpu_percent()
                
                # Check for performance issues
                if memory_usage > 1000:  # 1GB
                    logger.warning(f"High memory usage: {memory_usage:.1f}MB")
                
                if cpu_usage > 80:
                    logger.warning(f"High CPU usage: {cpu_usage:.1f}%")
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                time.sleep(10)


# Convenience functions
def optimize_operation(operation_name: str, use_batching: bool = True,
                      use_parallel: bool = True, use_profiling: bool = True):
    """Decorator for optimized operations."""
    optimizer = EnhancedPerformanceOptimizer()
    return optimizer.optimize_operation(operation_name, use_batching=use_batching,
                                      use_parallel=use_parallel, use_profiling=use_profiling)


def batch_process(items: List[Any], process_func: Callable, batch_size: int = 100) -> List[Any]:
    """Process items in batches."""
    processor = AdaptiveBatchProcessor()
    return processor.process_batches(items, process_func)


def parallel_process(items: List[Any], process_func: Callable,
                   level: ParallelizationLevel = ParallelizationLevel.THREADS) -> List[Any]:
    """Process items in parallel."""
    processor = AdvancedParallelProcessor()
    return processor.execute_parallel(process_func, items, level)


def profile_operation(operation_name: str):
    """Profile an operation."""
    profiler = AdvancedPerformanceProfiler()
    return profiler.profile_operation(operation_name)


def run_scalability_test(input_sizes: List[int], process_func: Callable) -> Dict[str, Any]:
    """Run scalability test."""
    analyzer = ScalabilityAnalyzer()
    return analyzer.analyze_scalability(input_sizes, process_func) 