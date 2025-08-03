"""
Tests for Performance Optimization Engine

This module contains comprehensive tests for the PerformanceOptimizer class,
ensuring accurate parallel processing, caching, memory optimization, and performance monitoring.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from services.ai.arx_mcp.validate.performance_optimizer import (
    PerformanceOptimizer, OptimizationLevel, CacheStrategy, PerformanceOptimizationError,
    IntelligentCache, ParallelProcessor, MemoryOptimizer, PerformanceMonitor
)
from services.models.mcp_models import BuildingObject, MCPRule, RuleCondition, RuleAction


class TestIntelligentCache:
    """Test suite for IntelligentCache class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.cache = IntelligentCache(max_size=10, strategy=CacheStrategy.ADAPTIVE)
    
    def test_cache_set_and_get(self):
        """Test basic cache set and get operations"""
        # Set value
        self.cache.set("test_key", "test_value")
        
        # Get value
        value = self.cache.get("test_key")
        assert value == "test_value"
    
    def test_cache_ttl_expiration(self):
        """Test TTL-based cache expiration"""
        # Set value with short TTL
        self.cache.set("test_key", "test_value", ttl=0.1)
        
        # Should be available immediately
        value = self.cache.get("test_key")
        assert value == "test_value"
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Should be expired
        value = self.cache.get("test_key")
        assert value is None
    
    def test_cache_lru_eviction(self):
        """Test LRU cache eviction"""
        cache = IntelligentCache(max_size=3, strategy=CacheStrategy.LRU)
        
        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Access key1 to make it most recently used
        cache.get("key1")
        
        # Add new key, should evict key2 (least recently used)
        cache.set("key4", "value4")
        
        # key2 should be evicted
        assert cache.get("key2") is None
        assert cache.get("key1") == "value1"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"
    
    def test_cache_adaptive_eviction(self):
        """Test adaptive cache eviction"""
        cache = IntelligentCache(max_size=3, strategy=CacheStrategy.ADAPTIVE)
        
        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Access key1 multiple times
        cache.get("key1")
        cache.get("key1")
        cache.get("key1")
        
        # Add new key, should evict least valuable (key2 or key3)
        cache.set("key4", "value4")
        
        # Should still have key1 (most accessed)
        assert cache.get("key1") == "value1"
    
    def test_cache_memory_limit(self):
        """Test cache memory limit enforcement"""
        cache = IntelligentCache(max_size=100, strategy=CacheStrategy.ADAPTIVE)
        cache.memory_limit = 1024  # 1KB limit
        
        # Add large value
        large_value = "x" * 2048  # 2KB
        cache.set("large_key", large_value)
        
        # Should be evicted due to memory limit
        assert cache.get("large_key") is None
    
    def test_cache_clear(self):
        """Test cache clearing"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        
        assert len(self.cache.cache) == 2
        
        self.cache.clear()
        
        assert len(self.cache.cache) == 0
        assert self.cache.get("key1") is None
        assert self.cache.get("key2") is None
    
    def test_cache_stats(self):
        """Test cache statistics"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.get("key1")  # Access once
        
        stats = self.cache.get_stats()
        
        assert stats['size'] == 2
        assert stats['max_size'] == 10
        assert stats['strategy'] == 'adaptive'
        assert stats['memory_usage'] > 0


class TestParallelProcessor:
    """Test suite for ParallelProcessor class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = ParallelProcessor(max_workers=2, use_processes=False)
    
    def test_parallel_execution(self):
        """Test parallel execution of functions"""
        def test_func(x):
            time.sleep(0.1)  # Simulate work
            return x * 2
        
        items = [1, 2, 3, 4, 5]
        
        with self.processor as processor:
            results = processor.execute_parallel(test_func, items)
        
        assert results == [2, 4, 6, 8, 10]
    
    def test_parallel_execution_with_errors(self):
        """Test parallel execution with error handling"""
        def test_func(x):
            if x == 3:
                raise ValueError("Test error")
            return x * 2
        
        items = [1, 2, 3, 4, 5]
        
        with self.processor as processor:
            results = processor.execute_parallel(test_func, items)
        
        # Should handle errors gracefully
        assert results[0] == 2
        assert results[1] == 4
        assert results[2] is None  # Error case
        assert results[3] == 8
        assert results[4] == 10
    
    def test_empty_items(self):
        """Test parallel execution with empty items list"""
        def test_func(x):
            return x * 2
        
        with self.processor as processor:
            results = processor.execute_parallel(test_func, [])
        
        assert results == []
    
    def test_processor_stats(self):
        """Test processor statistics"""
        stats = self.processor.get_stats()
        
        assert stats['max_workers'] == 2
        assert stats['use_processes'] == False
        assert 'executor_active' in stats


class TestMemoryOptimizer:
    """Test suite for MemoryOptimizer class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.optimizer = MemoryOptimizer(memory_threshold=0.8)
    
    def test_memory_usage_stats(self):
        """Test memory usage statistics"""
        stats = self.optimizer.get_memory_usage()
        
        assert 'rss_mb' in stats
        assert 'vms_mb' in stats
        assert 'percent' in stats
        assert 'available_mb' in stats
        assert stats['rss_mb'] > 0
        assert stats['percent'] >= 0
    
    def test_memory_optimization(self):
        """Test memory optimization"""
        # Create some objects to collect
        objects = [object() for _ in range(1000)]
        
        # Perform optimization
        optimization_stats = self.optimizer.optimize_memory()
        
        assert 'objects_collected' in optimization_stats
        assert 'memory_freed_mb' in optimization_stats
        assert 'before_memory_mb' in optimization_stats
        assert 'after_memory_mb' in optimization_stats
    
    def test_weak_references(self):
        """Test weak reference management"""
        obj = object()
        self.optimizer.add_weak_ref(obj)
        
        stats = self.optimizer.get_stats()
        assert stats['weak_refs_count'] == 1
        
        # Delete object
        del obj
        
        # Force garbage collection
        self.optimizer.optimize_memory()
        
        stats = self.optimizer.get_stats()
        assert stats['weak_refs_count'] == 0
    
    def test_memory_threshold(self):
        """Test memory threshold checking"""
        # Mock high memory usage
        with patch('psutil.Process') as mock_process:
            mock_process.return_value.memory_percent.return_value = 85.0
            
            assert self.optimizer.should_optimize() == True
        
        # Mock low memory usage
        with patch('psutil.Process') as mock_process:
            mock_process.return_value.memory_percent.return_value = 50.0
            
            assert self.optimizer.should_optimize() == False


class TestPerformanceMonitor:
    """Test suite for PerformanceMonitor class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.monitor = PerformanceMonitor()
    
    def test_timer_operations(self):
        """Test timer start and end operations"""
        self.monitor.start_timer("test_operation")
        time.sleep(0.1)
        duration = self.monitor.end_timer("test_operation")
        
        assert duration > 0.09  # Should be at least 0.1 seconds
        assert duration < 0.2   # Should be less than 0.2 seconds
    
    def test_error_recording(self):
        """Test error recording"""
        error = ValueError("Test error")
        self.monitor.record_error("test_operation", error)
        
        summary = self.monitor.get_performance_summary()
        assert summary['total_errors'] == 1
        assert summary['error_counts']['test_operation'] == 1
    
    def test_performance_summary(self):
        """Test performance summary generation"""
        # Perform some operations
        self.monitor.start_timer("op1")
        time.sleep(0.01)
        self.monitor.end_timer("op1")
        
        self.monitor.start_timer("op2")
        time.sleep(0.02)
        self.monitor.end_timer("op2")
        
        summary = self.monitor.get_performance_summary()
        
        assert summary['total_operations'] == 2
        assert summary['avg_execution_time'] > 0
        assert 'op1' in summary['operation_counts']
        assert 'op2' in summary['operation_counts']


class TestPerformanceOptimizer:
    """Test suite for PerformanceOptimizer class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        config = {
            'cache_size': 100,
            'cache_strategy': 'adaptive',
            'max_workers': 2,
            'use_processes': False,
            'memory_threshold': 0.8,
            'optimization_level': 'advanced',
            'enabled': True
        }
        self.optimizer = PerformanceOptimizer(config)
    
    def test_optimize_rule_execution(self):
        """Test optimized rule execution"""
        # Create mock rules and objects
        rules = [
            MCPRule(rule_id="rule1", name="Test Rule 1", category="test"),
            MCPRule(rule_id="rule2", name="Test Rule 2", category="test")
        ]
        
        objects = [
            BuildingObject(object_id="obj1", object_type="room"),
            BuildingObject(object_id="obj2", object_type="wall")
        ]
        
        def execution_func(rule, building_objects):
            return f"Result for {rule.rule_id}"
        
        results = self.optimizer.optimize_rule_execution(
            rules, objects, execution_func
        )
        
        assert len(results) == 2
        assert results[0] == "Result for rule1"
        assert results[1] == "Result for rule2"
    
    def test_optimize_condition_evaluation(self):
        """Test optimized condition evaluation"""
        conditions = [
            RuleCondition(type="property", element_type="room"),
            RuleCondition(type="spatial", element_type="wall")
        ]
        
        objects = [
            BuildingObject(object_id="obj1", object_type="room"),
            BuildingObject(object_id="obj2", object_type="wall")
        ]
        
        def evaluation_func(condition, building_objects):
            return f"Evaluation for {condition.type}"
        
        results = self.optimizer.optimize_condition_evaluation(
            conditions, objects, evaluation_func
        )
        
        assert len(results) == 2
        assert results[0] == "Evaluation for property"
        assert results[1] == "Evaluation for spatial"
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        key1 = self.optimizer._create_cache_key("test", 123)
        key2 = self.optimizer._create_cache_key("test", 123)
        key3 = self.optimizer._create_cache_key("test", 456)
        
        assert key1 == key2  # Same inputs should produce same key
        assert key1 != key3  # Different inputs should produce different key
    
    def test_optimization_stats(self):
        """Test optimization statistics"""
        stats = self.optimizer.get_optimization_stats()
        
        assert 'cache_stats' in stats
        assert 'parallel_stats' in stats
        assert 'memory_stats' in stats
        assert 'performance_summary' in stats
        assert 'optimization_level' in stats
        assert 'enabled' in stats
    
    def test_cache_clearing(self):
        """Test cache clearing"""
        # Add some data to cache
        self.optimizer.cache.set("test_key", "test_value")
        
        # Clear cache
        self.optimizer.clear_cache()
        
        # Should be empty
        assert self.optimizer.cache.get("test_key") is None
    
    def test_memory_optimization(self):
        """Test memory optimization"""
        optimization_stats = self.optimizer.optimize_memory()
        
        assert 'objects_collected' in optimization_stats
        assert 'memory_freed_mb' in optimization_stats
    
    def test_optimization_level_setting(self):
        """Test optimization level setting"""
        # Test different levels
        for level in OptimizationLevel:
            self.optimizer.set_optimization_level(level)
            assert self.optimizer.optimization_level == level
    
    def test_disabled_optimization(self):
        """Test disabled optimization"""
        config = {'enabled': False}
        optimizer = PerformanceOptimizer(config)
        
        rules = [MCPRule(rule_id="rule1", name="Test", category="test")]
        objects = [BuildingObject(object_id="obj1", object_type="room")]
        
        def execution_func(rule, building_objects):
            return "result"
        
        # Should execute without optimization
        results = optimizer.optimize_rule_execution(rules, objects, execution_func)
        assert results == ["result"]


class TestOptimizationLevel:
    """Test suite for OptimizationLevel enum"""
    
    def test_optimization_levels(self):
        """Test optimization level enum values"""
        assert OptimizationLevel.NONE.value == "none"
        assert OptimizationLevel.BASIC.value == "basic"
        assert OptimizationLevel.ADVANCED.value == "advanced"
        assert OptimizationLevel.AGGRESSIVE.value == "aggressive"


class TestCacheStrategy:
    """Test suite for CacheStrategy enum"""
    
    def test_cache_strategies(self):
        """Test cache strategy enum values"""
        assert CacheStrategy.LRU.value == "lru"
        assert CacheStrategy.TTL.value == "ttl"
        assert CacheStrategy.ADAPTIVE.value == "adaptive"


class TestErrorHandling:
    """Test suite for error handling"""
    
    def test_parallel_execution_error_handling(self):
        """Test error handling in parallel execution"""
        processor = ParallelProcessor(max_workers=2)
        
        def failing_func(x):
            if x == 2:
                raise ValueError("Test error")
            return x * 2
        
        items = [1, 2, 3]
        
        with processor as proc:
            results = proc.execute_parallel(failing_func, items)
        
        assert results[0] == 2
        assert results[1] is None  # Error case
        assert results[2] == 6
    
    def test_cache_error_handling(self):
        """Test error handling in cache operations"""
        cache = IntelligentCache()
        
        # Test with unhashable key
        cache.set("test_key", {"complex": "object"})
        result = cache.get("test_key")
        assert result == {"complex": "object"}
    
    def test_memory_optimization_error_handling(self):
        """Test error handling in memory optimization"""
        optimizer = MemoryOptimizer()
        
        # Should handle errors gracefully
        stats = optimizer.get_memory_usage()
        assert isinstance(stats, dict)


class TestPerformanceBenchmarks:
    """Test suite for performance benchmarks"""
    
    def test_cache_performance(self):
        """Test cache performance with many operations"""
        cache = IntelligentCache(max_size=1000)
        
        start_time = time.time()
        
        # Add many items
        for i in range(1000):
            cache.set(f"key{i}", f"value{i}")
        
        # Access many items
        for i in range(1000):
            cache.get(f"key{i}")
        
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 5.0  # 5 seconds
    
    def test_parallel_processing_performance(self):
        """Test parallel processing performance"""
        processor = ParallelProcessor(max_workers=4)
        
        def work_func(x):
            time.sleep(0.01)  # Simulate work
            return x * 2
        
        items = list(range(100))
        
        start_time = time.time()
        
        with processor as proc:
            results = proc.execute_parallel(work_func, items)
        
        end_time = time.time()
        
        # Should be faster than sequential execution
        assert end_time - start_time < 2.0  # 2 seconds
        assert len(results) == 100
        assert results[0] == 0
        assert results[50] == 100


if __name__ == "__main__":
    pytest.main([__file__]) 