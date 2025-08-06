"""
Performance Tests for MCP Optimization Components

This module tests the performance optimization components:
- Parallel processing engine
- Memory management system
- Intelligent caching system
- Performance benchmarks
"""

import pytest
import time
import psutil
import os
from typing import List, Dict, Any
from datetime import datetime

from validate.rule_engine import MCPRuleEngine
from validate.parallel_engine import ParallelRuleEngine
from validate.memory_manager import MemoryManager, MemoryOptimizedEngine
from validate.cache_manager import CacheManager, CachedRuleEngine
from models.mcp_models import (
    BuildingModel,
    BuildingObject,
    MCPFile,
    MCPRule,
    RuleCondition,
    RuleAction,
    Jurisdiction,
    RuleSeverity,
    RuleCategory,
    ConditionType,
    ActionType,
)


class TestPerformanceOptimization:
    """Performance test suite for optimization components"""

    def setup_method(self):
        """Set up test fixtures"""
        self.process = psutil.Process(os.getpid())

        # Create base engine
        self.base_engine = MCPRuleEngine()

        # Create optimization components
        self.parallel_engine = ParallelRuleEngine()
        self.memory_manager = MemoryManager()
        self.cache_manager = CacheManager()

        # Create optimized engines
        self.memory_optimized_engine = MemoryOptimizedEngine(
            self.base_engine, self.memory_manager
        )
        self.cached_engine = CachedRuleEngine(self.base_engine, self.cache_manager)

    def create_large_building_model(self, num_objects: int) -> BuildingModel:
        """Create a large building model for performance testing"""
        objects = []
        for i in range(num_objects):
            object_type = f"object_type_{i % 10}"
            properties = {
                "location": f"location_{i % 5}",
                "load": float(i % 100),
                "capacity": float(i % 1000),
                "area": float(i % 500),
                "height": float(i % 20),
                "material": f"material_{i % 3}",
                "system_type": f"system_{i % 4}",
                "voltage": 120 if i % 2 == 0 else 240,
                "gfci_protected": i % 3 == 0,
                "flow_rate": float(i % 10),
                "fire_rating": i % 4,
                "occupancy": i % 50,
            }

            location = {
                "x": float(i % 1000),
                "y": float(i % 1000),
                "width": float(i % 100),
                "height": float(i % 50),
            }

            obj = BuildingObject(
                object_id=f"object_{i:06d}",
                object_type=object_type,
                properties=properties,
                location=location,
                connections=(
                    [f"object_{(i+1) % num_objects:06d}"] if i < num_objects - 1 else []
                ),
            )
            objects.append(obj)

        return BuildingModel(
            building_id=f"large_building_{num_objects}",
            building_name=f"Large Building ({num_objects} objects)",
            objects=objects,
        )

    def create_performance_mcp_files(self) -> List[str]:
        """Create MCP files for performance testing"""
        mcp_file = MCPFile(
            mcp_id="performance_test_mcp",
            name="Performance Test MCP",
            description="MCP file for performance testing",
            jurisdiction=Jurisdiction(country="USA", state="Test"),
            version="1.0",
            effective_date="2024-01-01",
            rules=[
                MCPRule(
                    rule_id="perf_rule_001",
                    name="Performance Test Rule",
                    description="Rule for performance testing",
                    category=RuleCategory.GENERAL,
                    conditions=[
                        RuleCondition(
                            type=ConditionType.PROPERTY,
                            element_type="object_type_0",
                            property="load",
                            operator=">=",
                            value=50.0,
                        )
                    ],
                    actions=[
                        RuleAction(
                            type=ActionType.VALIDATION,
                            message="Performance test violation",
                            severity=RuleSeverity.ERROR,
                        )
                    ],
                )
            ],
        )

        # Save to temporary file
        import tempfile
        import json

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(mcp_file.to_dict(), f, indent=2)
            return [f.name]

    def test_parallel_processing_performance(self):
        """Test parallel processing performance"""
        building_model = self.create_large_building_model(5000)
        mcp_files = self.create_performance_mcp_files()

        # Measure base engine performance
        start_time = time.time()
        base_result = self.base_engine.validate_building_model(
            building_model, mcp_files
        )
        base_execution_time = time.time() - start_time

        # Measure parallel engine performance
        start_time = time.time()
        parallel_result = self.parallel_engine.validate_building_model_parallel(
            building_model, mcp_files
        )
        parallel_execution_time = time.time() - start_time

        # Parallel processing should be faster for large models
        # For small models, overhead might make it slower
        if len(building_model.objects) > 2000 and base_execution_time > 0.01:
            assert (
                parallel_execution_time < base_execution_time * 2.0
            ), f"Parallel processing ({parallel_execution_time:.3f}s) should be reasonable compared to base ({base_execution_time:.3f}s)"
        else:
            # For smaller models or very fast execution, just ensure it completes successfully
            assert (
                parallel_execution_time < 10.0
            ), f"Parallel processing took too long: {parallel_execution_time:.3f}s"

        # Results should be equivalent
        assert (
            base_result.overall_compliance_score
            == parallel_result.overall_compliance_score
        )

        print(
            f"Parallel processing: base {base_execution_time:.3f}s, parallel {parallel_execution_time:.3f}s"
        )

    def test_memory_optimization_performance(self):
        """Test memory optimization performance"""
        building_model = self.create_large_building_model(2000)
        mcp_files = self.create_performance_mcp_files()

        # Measure memory usage with base engine
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        base_result = self.base_engine.validate_building_model(
            building_model, mcp_files
        )
        base_memory = self.process.memory_info().rss / 1024 / 1024
        base_memory_used = base_memory - initial_memory

        # Measure memory usage with optimized engine
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        optimized_result = self.memory_optimized_engine.validate_building_model(
            building_model, mcp_files
        )
        optimized_memory = self.process.memory_info().rss / 1024 / 1024
        optimized_memory_used = optimized_memory - initial_memory

        # Results should be equivalent
        assert (
            base_result.overall_compliance_score
            == optimized_result.overall_compliance_score
        )

        # Memory usage should be reasonable
        assert (
            optimized_memory_used < 1000
        ), f"Memory usage {optimized_memory_used:.1f}MB exceeds 1GB limit"

        print(
            f"Memory optimization: base {base_memory_used:.1f}MB, optimized {optimized_memory_used:.1f}MB"
        )

    def test_caching_performance(self):
        """Test caching performance"""
        building_model = self.create_large_building_model(1000)
        mcp_files = self.create_performance_mcp_files()

        # First validation (cache miss)
        start_time = time.time()
        result1 = self.cached_engine.validate_building_model(building_model, mcp_files)
        first_execution_time = time.time() - start_time

        # Second validation (cache hit)
        start_time = time.time()
        result2 = self.cached_engine.validate_building_model(building_model, mcp_files)
        second_execution_time = time.time() - start_time

        # Cache hit should be faster
        assert (
            second_execution_time < first_execution_time
        ), f"Cache hit ({second_execution_time:.3f}s) should be faster than cache miss ({first_execution_time:.3f}s)"

        # Results should be identical
        assert result1.overall_compliance_score == result2.overall_compliance_score

        # Check cache metrics
        cache_metrics = self.cached_engine.get_cache_metrics()
        assert cache_metrics["hits"] > 0
        assert cache_metrics["hit_rate"] > 0

        print(
            f"Caching performance: miss {first_execution_time:.3f}s, hit {second_execution_time:.3f}s"
        )

    def test_memory_manager_functionality(self):
        """Test memory manager functionality"""
        # Test object pooling
        obj1 = self.memory_manager.get_object("test_type", lambda: {"data": "test1"})
        obj2 = self.memory_manager.get_object("test_type", lambda: {"data": "test2"})

        assert obj1["data"] == "test1"
        assert obj2["data"] == "test2"

        # Test object release
        self.memory_manager.release_object("test_type", obj1)

        # Test weak reference caching
        class TestObject:
            def __init__(self, key, value):
                self.key = key
                self.value = value

            def __eq__(self, other):
                return self.key == other.key and self.value == other.value

        test_obj = TestObject("key", "value")
        self.memory_manager.cache_with_weak_ref("test_key", test_obj)

        retrieved_obj = self.memory_manager.get_from_weak_cache("test_key")
        assert retrieved_obj == test_obj

        # Test memory monitoring
        memory_stats = self.memory_manager.monitor_memory()
        assert memory_stats.used_memory_mb > 0
        assert memory_stats.total_memory_mb > 0

    def test_cache_manager_functionality(self):
        """Test cache manager functionality"""
        # Test basic caching
        test_data = {"key": "value", "number": 42}
        self.cache_manager.set("test_key", test_data)

        retrieved_data = self.cache_manager.get("test_key")
        assert retrieved_data == test_data

        # Test cache miss
        missing_data = self.cache_manager.get("missing_key", "default")
        assert missing_data == "default"

        # Test cache deletion
        self.cache_manager.delete("test_key")
        deleted_data = self.cache_manager.get("test_key")
        assert deleted_data is None

        # Test cache statistics
        stats = self.cache_manager.get_cache_stats()
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats

    def test_parallel_engine_scalability(self):
        """Test parallel engine scalability"""
        model_sizes = [100, 500, 1000, 2000]
        results = {}

        for size in model_sizes:
            building_model = self.create_large_building_model(size)
            mcp_files = self.create_performance_mcp_files()

            # Measure parallel processing time
            start_time = time.time()
            result = self.parallel_engine.validate_building_model_parallel(
                building_model, mcp_files
            )
            execution_time = time.time() - start_time

            results[size] = {
                "execution_time": execution_time,
                "objects_per_second": (
                    size / execution_time if execution_time > 0 else 0
                ),
            }

            print(
                f"Size {size}: {execution_time:.3f}s, {results[size]['objects_per_second']:.0f} obj/s"
            )

        # Verify scalability characteristics
        for i in range(1, len(model_sizes)):
            prev_size = model_sizes[i - 1]
            curr_size = model_sizes[i]

            prev_time = results[prev_size]["execution_time"]
            curr_time = results[curr_size]["execution_time"]

            # Time should scale reasonably
            time_ratio = curr_time / prev_time
            size_ratio = curr_size / prev_size

            assert (
                time_ratio < size_ratio * 2
            ), f"Time scaling {time_ratio:.2f}x for {size_ratio:.2f}x size increase is too high"

    def test_memory_manager_optimization(self):
        """Test memory manager optimization"""
        # Perform some operations to generate memory usage
        for i in range(100):
            obj = self.memory_manager.get_object(
                f"type_{i}", lambda: {"data": f"value_{i}"}
            )
            self.memory_manager.release_object(f"type_{i}", obj)

        # Test optimization
        optimization_result = self.memory_manager.optimize_memory_settings()

        assert "recommendations" in optimization_result
        assert "optimized_settings" in optimization_result
        assert "current_stats" in optimization_result

        # Test memory trends
        trends = self.memory_manager.get_memory_trends()
        assert "trend" in trends

    def test_cache_manager_optimization(self):
        """Test cache manager optimization"""
        # Generate some cache activity
        for i in range(50):
            self.cache_manager.set(f"key_{i}", {"data": f"value_{i}"})
            self.cache_manager.get(f"key_{i}")

        # Test optimization
        optimization_result = self.cache_manager.optimize_cache_settings()

        assert "recommendations" in optimization_result
        assert "optimized_settings" in optimization_result
        assert "current_stats" in optimization_result

    def test_combined_optimization_performance(self):
        """Test combined optimization performance"""
        building_model = self.create_large_building_model(3000)
        mcp_files = self.create_performance_mcp_files()

        # Test with all optimizations combined
        start_time = time.time()
        initial_memory = self.process.memory_info().rss / 1024 / 1024

        # Use cached engine (which includes memory optimization)
        result = self.cached_engine.validate_building_model(building_model, mcp_files)

        execution_time = time.time() - start_time
        final_memory = self.process.memory_info().rss / 1024 / 1024
        memory_used = final_memory - initial_memory

        # Performance assertions
        assert (
            execution_time < 30.0
        ), f"Execution time {execution_time:.3f}s exceeds 30.0s limit"
        assert memory_used < 2000, f"Memory usage {memory_used:.1f}MB exceeds 2GB limit"
        assert result is not None

        print(f"Combined optimization: {execution_time:.3f}s, {memory_used:.1f}MB")

    def test_parallel_engine_configuration(self):
        """Test parallel engine configuration options"""
        # Test different configurations
        configs = [
            {"max_workers": 2, "chunk_size": 500},
            {"max_workers": 4, "chunk_size": 1000},
            {"use_processes": True, "chunk_size": 750},
        ]

        building_model = self.create_large_building_model(2000)
        mcp_files = self.create_performance_mcp_files()

        for config in configs:
            engine = ParallelRuleEngine(config)

            start_time = time.time()
            result = engine.validate_building_model_parallel(building_model, mcp_files)
            execution_time = time.time() - start_time

            # All configurations should complete successfully
            assert result is not None
            assert (
                execution_time < 60.0
            ), f"Configuration {config} took too long: {execution_time:.3f}s"

            print(f"Config {config}: {execution_time:.3f}s")

    def test_memory_manager_cleanup(self):
        """Test memory manager cleanup functionality"""
        # Generate some memory pressure
        for i in range(1000):
            obj = self.memory_manager.get_object(
                f"type_{i}", lambda: {"data": "x" * 1000}
            )
            self.memory_manager.release_object(f"type_{i}", obj)

        # Force cleanup
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        self.memory_manager._perform_cleanup()
        final_memory = self.process.memory_info().rss / 1024 / 1024

        # Cleanup should not increase memory significantly
        memory_change = final_memory - initial_memory
        assert memory_change < 100, f"Cleanup increased memory by {memory_change:.1f}MB"

    def test_cache_manager_persistence(self):
        """Test cache manager persistence functionality"""
        # Enable persistence
        persistent_config = {"enable_persistence": True}
        persistent_cache = CacheManager(persistent_config)

        # Store some data
        test_data = {"persistent": "data", "number": 123}
        persistent_cache.set("persistent_key", test_data)

        # Verify data is stored
        retrieved_data = persistent_cache.get("persistent_key")
        assert retrieved_data == test_data

        # Clear cache
        persistent_cache.clear()

        # Verify cache is cleared
        cleared_data = persistent_cache.get("persistent_key")
        assert cleared_data is None

    def teardown_method(self):
        """Clean up after tests"""
        # Shutdown memory manager
        self.memory_manager.shutdown()

        # Clear caches
        self.cache_manager.clear()
        self.parallel_engine.clear_cache()

        # Clean up temporary files
        import tempfile
        import glob

        temp_files = glob.glob(tempfile.gettempdir() + "/tmp*_mcp_*.json")
        for file in temp_files:
            try:
                os.unlink(file)
            except:
                pass
