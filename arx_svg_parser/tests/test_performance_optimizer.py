"""
Tests for Performance Optimization System

This module tests the performance optimization components including:
- PerformanceCache
- PerformanceProfiler
- BatchProcessor
- MemoryManager
- PerformanceOptimizer
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from ..services.performance_optimizer import (
    PerformanceCache, CacheStrategy, PerformanceProfiler, PerformanceMetrics,
    BatchProcessor, MemoryManager, PerformanceOptimizer, OptimizationLevel,
    profile_operation, cache_result, batch_process
)


class TestPerformanceCache:
    """Test PerformanceCache functionality."""
    
    def test_lru_cache_basic_operations(self):
        """Test basic LRU cache operations."""
        cache = PerformanceCache(CacheStrategy.LRU, max_size=3)
        
        # Test set and get
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        assert cache.hits == 1
        assert cache.misses == 0
        
        # Test cache miss
        assert cache.get("nonexistent") is None
        assert cache.misses == 1
    
    def test_lru_cache_eviction(self):
        """Test LRU cache eviction."""
        cache = PerformanceCache(CacheStrategy.LRU, max_size=2)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # Should evict key1
        
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
    
    def test_ttl_cache_expiration(self):
        """Test TTL cache expiration."""
        cache = PerformanceCache(CacheStrategy.TTL, max_size=10, ttl=0.1)
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(0.2)
        assert cache.get("key1") is None
    
    def test_cache_clear(self):
        """Test cache clearing."""
        cache = PerformanceCache(CacheStrategy.LRU, max_size=10)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        assert len(cache.cache) == 2
        cache.clear()
        assert len(cache.cache) == 0
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = PerformanceCache(CacheStrategy.LRU, max_size=10)
        
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        
        stats = cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 0.5
        assert stats['size'] == 1


class TestPerformanceProfiler:
    """Test PerformanceProfiler functionality."""
    
    def test_profile_basic(self):
        """Test basic profiling."""
        profiler = PerformanceProfiler()
        
        profiler.start_profile("test_operation")
        time.sleep(0.1)
        metrics = profiler.end_profile("test_operation", element_count=10)
        
        assert metrics.operation_name == "test_operation"
        assert metrics.duration > 0.09  # Should be at least 0.1 seconds
        assert metrics.element_count == 10
    
    def test_profile_decorator(self):
        """Test profiling decorator."""
        profiler = PerformanceProfiler()
        
        @profiler.profile_function("decorated_function")
        def test_function():
            time.sleep(0.05)
            return "result"
        
        result = test_function()
        assert result == "result"
        assert len(profiler.metrics) == 1
        assert profiler.metrics[0].operation_name == "decorated_function"
    
    def test_profile_summary(self):
        """Test profile summary generation."""
        profiler = PerformanceProfiler()
        
        # Add some test metrics
        profiler.metrics = [
            PerformanceMetrics(
                operation_name="op1",
                start_time=0,
                end_time=1,
                memory_start=100,
                memory_end=110,
                cpu_percent=50,
                element_count=10
            ),
            PerformanceMetrics(
                operation_name="op2",
                start_time=1,
                end_time=2,
                memory_start=110,
                memory_end=120,
                cpu_percent=60,
                element_count=20
            )
        ]
        
        summary = profiler.get_summary()
        assert summary['total_operations'] == 2
        assert summary['total_duration'] == 2
        assert summary['total_elements_processed'] == 30


class TestBatchProcessor:
    """Test BatchProcessor functionality."""
    
    def test_sequential_batch_processing(self):
        """Test sequential batch processing."""
        processor = BatchProcessor(batch_size=3)
        
        def process_batch(batch):
            return [item * 2 for item in batch]
        
        items = [1, 2, 3, 4, 5, 6]
        results = processor.process_batches(items, process_batch, use_parallel=False)
        
        assert results == [2, 4, 6, 8, 10, 12]
    
    def test_parallel_batch_processing(self):
        """Test parallel batch processing."""
        processor = BatchProcessor(batch_size=2, max_workers=2)
        
        def process_batch(batch):
            time.sleep(0.01)  # Simulate work
            return [item * 2 for item in batch]
        
        items = [1, 2, 3, 4, 5, 6]
        results = processor.process_batches(items, process_batch, use_parallel=True)
        
        assert results == [2, 4, 6, 8, 10, 12]
    
    def test_empty_items(self):
        """Test processing empty item list."""
        processor = BatchProcessor(batch_size=10)
        
        def process_batch(batch):
            return batch
        
        results = processor.process_batches([], process_batch)
        assert results == []


class TestMemoryManager:
    """Test MemoryManager functionality."""
    
    @patch('psutil.Process')
    def test_memory_usage(self, mock_process):
        """Test memory usage monitoring."""
        mock_process.return_value.memory_info.return_value.rss = 1024 * 1024 * 100  # 100MB
        mock_process.return_value.memory_percent.return_value = 25.0
        
        manager = MemoryManager()
        usage = manager.get_memory_usage()
        
        assert usage['rss_mb'] == 100
        assert usage['percent'] == 25.0
    
    @patch('psutil.Process')
    def test_memory_threshold_check(self, mock_process):
        """Test memory threshold checking."""
        mock_process.return_value.memory_info.return_value.rss = 1024 * 1024 * 1500  # 1500MB
        
        manager = MemoryManager(memory_threshold_mb=1000)
        assert manager.check_memory_threshold() is True
        
        manager = MemoryManager(memory_threshold_mb=2000)
        assert manager.check_memory_threshold() is False
    
    @patch('gc.collect')
    def test_memory_optimization(self, mock_gc_collect):
        """Test memory optimization."""
        mock_gc_collect.return_value = 10
        
        manager = MemoryManager()
        result = manager.optimize_memory()
        
        assert result['objects_collected'] == 10
        mock_gc_collect.assert_called()


class TestPerformanceOptimizer:
    """Test PerformanceOptimizer functionality."""
    
    def test_initialization(self):
        """Test optimizer initialization."""
        optimizer = PerformanceOptimizer(OptimizationLevel.STANDARD)
        
        assert optimizer.optimization_level == OptimizationLevel.STANDARD
        assert optimizer.profiler is not None
        assert optimizer.memory_manager is not None
        assert optimizer.batch_processor is not None
    
    def test_cache_initialization(self):
        """Test cache initialization based on optimization level."""
        # Standard level should have caches
        optimizer = PerformanceOptimizer(OptimizationLevel.STANDARD)
        assert 'geometry' in optimizer.caches
        assert 'properties' in optimizer.caches
        assert 'relationships' in optimizer.caches
        
        # None level should have no caches
        optimizer = PerformanceOptimizer(OptimizationLevel.NONE)
        assert len(optimizer.caches) == 0
    
    def test_operation_optimization(self):
        """Test operation optimization."""
        optimizer = PerformanceOptimizer(OptimizationLevel.STANDARD)
        
        def test_operation(x, y):
            time.sleep(0.01)
            return x + y
        
        optimized_op = optimizer.optimize_operation("test_op", test_operation)
        result = optimized_op(1, 2)
        
        assert result == 3
        assert len(optimizer.profiler.metrics) == 1
    
    def test_batch_processing(self):
        """Test batch processing."""
        optimizer = PerformanceOptimizer(OptimizationLevel.STANDARD)
        
        def process_batch(batch):
            return [item * 2 for item in batch]
        
        items = [1, 2, 3, 4, 5]
        results = optimizer.batch_process(items, process_batch)
        
        assert results == [2, 4, 6, 8, 10]
    
    def test_performance_monitoring(self):
        """Test performance monitoring."""
        optimizer = PerformanceOptimizer(OptimizationLevel.STANDARD)
        
        report = optimizer.monitor_performance("test_operation")
        
        assert 'operation_name' in report
        assert 'memory_before_mb' in report
        assert 'memory_after_mb' in report
        assert 'cache_stats' in report
    
    def test_optimization_report(self):
        """Test optimization report generation."""
        optimizer = PerformanceOptimizer(OptimizationLevel.STANDARD)
        
        report = optimizer.get_optimization_report()
        
        assert 'optimization_level' in report
        assert 'profiler_summary' in report
        assert 'memory_usage' in report
        assert 'cache_stats' in report
        assert 'system_info' in report
    
    def test_cache_clearing(self):
        """Test cache clearing."""
        optimizer = PerformanceOptimizer(OptimizationLevel.STANDARD)
        
        # Add some data to caches
        optimizer.caches['geometry'].set("test_key", "test_value")
        
        assert len(optimizer.caches['geometry'].cache) == 1
        optimizer.clear_caches()
        assert len(optimizer.caches['geometry'].cache) == 0


class TestPerformanceDecorators:
    """Test performance decorators."""
    
    def test_profile_operation_decorator(self):
        """Test profile_operation decorator."""
        @profile_operation("test_function")
        def test_function():
            time.sleep(0.01)
            return "result"
        
        result = test_function()
        assert result == "result"
    
    def test_cache_result_decorator(self):
        """Test cache_result decorator."""
        @cache_result(ttl=1)
        def expensive_function(x):
            time.sleep(0.01)
            return x * 2
        
        # First call should be slow
        start_time = time.time()
        result1 = expensive_function(5)
        first_call_time = time.time() - start_time
        
        # Second call should be fast (cached)
        start_time = time.time()
        result2 = expensive_function(5)
        second_call_time = time.time() - start_time
        
        assert result1 == result2 == 10
        assert second_call_time < first_call_time
    
    def test_batch_process_decorator(self):
        """Test batch_process decorator."""
        @batch_process(batch_size=2)
        def process_items(items):
            return [item * 2 for item in items]
        
        items = [1, 2, 3, 4, 5]
        results = process_items(items)
        
        # With parallel processing, order may not be preserved
        # So we check that all expected results are present
        assert len(results) == 5
        assert all(r in results for r in [2, 4, 6, 8, 10])
        assert all(isinstance(r, int) for r in results)


class TestPerformanceIntegration:
    """Integration tests for performance optimization."""
    
    def test_svg_parsing_optimization(self):
        """Test SVG parsing with performance optimization."""
        optimizer = PerformanceOptimizer(OptimizationLevel.STANDARD)
        
        # Simulate SVG parsing operation
        def parse_svg_elements(elements):
            time.sleep(0.01)  # Simulate parsing time
            return [f"parsed_{elem}" for elem in elements]
        
        optimized_parser = optimizer.optimize_operation(
            "svg_parsing", parse_svg_elements, use_caching=True, use_profiling=True
        )
        
        elements = ["rect", "circle", "line", "text"]
        results = optimized_parser(elements)
        
        assert results == ["parsed_rect", "parsed_circle", "parsed_line", "parsed_text"]
        assert len(optimizer.profiler.metrics) == 1
    
    def test_bim_assembly_optimization(self):
        """Test BIM assembly with performance optimization."""
        optimizer = PerformanceOptimizer(OptimizationLevel.AGGRESSIVE)
        
        # Simulate BIM assembly operation
        def assemble_bim_elements(elements):
            time.sleep(0.01)  # Simulate assembly time
            return {"assembled_elements": len(elements), "elements": elements}
        
        optimized_assembler = optimizer.optimize_operation(
            "bim_assembly", assemble_bim_elements, use_caching=True, use_profiling=True
        )
        
        elements = ["wall", "door", "window", "floor"]
        result = optimized_assembler(elements)
        
        assert result["assembled_elements"] == 4
        assert result["elements"] == elements
        assert len(optimizer.profiler.metrics) == 1
    
    def test_memory_optimization_during_processing(self):
        """Test memory optimization during heavy processing."""
        optimizer = PerformanceOptimizer(OptimizationLevel.AGGRESSIVE)
        
        # Simulate memory-intensive operation
        def memory_intensive_operation(data_size):
            # Simulate memory allocation
            large_list = [i for i in range(data_size)]
            time.sleep(0.01)
            return len(large_list)
        
        # Monitor performance
        report = optimizer.monitor_performance("memory_test", memory_threshold_mb=50)
        
        result = memory_intensive_operation(1000)
        assert result == 1000
        assert 'memory_before_mb' in report
        assert 'memory_after_mb' in report


if __name__ == "__main__":
    pytest.main([__file__]) 