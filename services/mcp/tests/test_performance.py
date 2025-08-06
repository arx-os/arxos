"""
Performance tests for MCP Rule Validation Engine

This module tests performance characteristics including:
- Large building model validation
- Memory usage optimization
- Execution time benchmarks
- Scalability testing
"""

import pytest
import time
import psutil
import os
from typing import List, Dict, Any
from datetime import datetime

from validate.rule_engine import MCPRuleEngine
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


class TestPerformance:
    """Performance test suite for MCP validation engine"""

    def setup_method(self):
        """Set up test fixtures"""
        self.engine = MCPRuleEngine()
        self.process = psutil.Process(os.getpid())

    def create_large_building_model(self, num_objects: int) -> BuildingModel:
        """Create a large building model for performance testing"""

        objects = []
        for i in range(num_objects):
            object_type = f"object_type_{i % 10}"  # 10 different types
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

        # Create a simple MCP file
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

    def test_small_model_performance(self):
        """Test performance with small building model (100 objects)"""

        building_model = self.create_large_building_model(100)
        mcp_files = self.create_performance_mcp_files()

        # Measure memory before
        memory_before = self.process.memory_info().rss / 1024 / 1024  # MB

        # Measure execution time
        start_time = time.time()
        report = self.engine.validate_building_model(building_model, mcp_files)
        execution_time = time.time() - start_time

        # Measure memory after
        memory_after = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before

        # Performance assertions
        assert (
            execution_time < 1.0
        ), f"Execution time {execution_time:.3f}s exceeds 1.0s limit"
        assert (
            memory_used < 100
        ), f"Memory usage {memory_used:.1f}MB exceeds 100MB limit"
        assert report is not None

        print(f"Small model (100 objects): {execution_time:.3f}s, {memory_used:.1f}MB")

    def test_medium_model_performance(self):
        """Test performance with medium building model (1,000 objects)"""

        building_model = self.create_large_building_model(1000)
        mcp_files = self.create_performance_mcp_files()

        # Measure memory before
        memory_before = self.process.memory_info().rss / 1024 / 1024  # MB

        # Measure execution time
        start_time = time.time()
        report = self.engine.validate_building_model(building_model, mcp_files)
        execution_time = time.time() - start_time

        # Measure memory after
        memory_after = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before

        # Performance assertions
        assert (
            execution_time < 5.0
        ), f"Execution time {execution_time:.3f}s exceeds 5.0s limit"
        assert (
            memory_used < 500
        ), f"Memory usage {memory_used:.1f}MB exceeds 500MB limit"
        assert report is not None

        print(
            f"Medium model (1,000 objects): {execution_time:.3f}s, {memory_used:.1f}MB"
        )

    def test_large_model_performance(self):
        """Test performance with large building model (10,000 objects)"""

        building_model = self.create_large_building_model(10000)
        mcp_files = self.create_performance_mcp_files()

        # Measure memory before
        memory_before = self.process.memory_info().rss / 1024 / 1024  # MB

        # Measure execution time
        start_time = time.time()
        report = self.engine.validate_building_model(building_model, mcp_files)
        execution_time = time.time() - start_time

        # Measure memory after
        memory_after = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before

        # Performance assertions
        assert (
            execution_time < 30.0
        ), f"Execution time {execution_time:.3f}s exceeds 30.0s limit"
        assert memory_used < 2000, f"Memory usage {memory_used:.1f}MB exceeds 2GB limit"
        assert report is not None

        print(
            f"Large model (10,000 objects): {execution_time:.3f}s, {memory_used:.1f}MB"
        )

    def test_cache_performance(self):
        """Test cache performance with repeated validations"""

        building_model = self.create_large_building_model(1000)
        mcp_files = self.create_performance_mcp_files()

        # First validation (cache miss)
        start_time = time.time()
        report1 = self.engine.validate_building_model(building_model, mcp_files)
        first_execution_time = time.time() - start_time

        # Second validation (cache hit)
        start_time = time.time()
        report2 = self.engine.validate_building_model(building_model, mcp_files)
        second_execution_time = time.time() - start_time

        # Cache should improve performance
        assert (
            second_execution_time < first_execution_time
        ), f"Cache hit ({second_execution_time:.3f}s) should be faster than cache miss ({first_execution_time:.3f}s)"

        # Results should be identical
        assert report1.overall_compliance_score == report2.overall_compliance_score

        print(
            f"Cache performance: {first_execution_time:.3f}s -> {second_execution_time:.3f}s"
        )

    def test_memory_cleanup(self):
        """Test memory cleanup after validation"""

        building_model = self.create_large_building_model(5000)
        mcp_files = self.create_performance_mcp_files()

        # Measure memory before
        memory_before = self.process.memory_info().rss / 1024 / 1024  # MB

        # Run validation
        report = self.engine.validate_building_model(building_model, mcp_files)

        # Force garbage collection
        import gc

        gc.collect()

        # Measure memory after cleanup
        memory_after = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before

        # Memory should be reasonable after cleanup
        assert (
            memory_increase < 1000
        ), f"Memory increase {memory_increase:.1f}MB exceeds 1GB limit"

        print(f"Memory cleanup: {memory_increase:.1f}MB increase after cleanup")

    def test_concurrent_validations(self):
        """Test concurrent validation performance"""

        import threading
        import queue

        results_queue = queue.Queue()

        def validate_building(building_id: int):
            """Validate a building model"""
            building_model = self.create_large_building_model(100)
            mcp_files = self.create_performance_mcp_files()

            start_time = time.time()
            report = self.engine.validate_building_model(building_model, mcp_files)
            execution_time = time.time() - start_time

            results_queue.put((building_id, execution_time, report))

        # Run concurrent validations
        threads = []
        num_concurrent = 5

        start_time = time.time()

        for i in range(num_concurrent):
            thread = threading.Thread(target=validate_building, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        # Verify all validations completed
        assert len(results) == num_concurrent

        # Calculate performance metrics
        individual_times = [r[1] for r in results]
        avg_individual_time = sum(individual_times) / len(individual_times)

        # Concurrent execution should be reasonably efficient
        efficiency_ratio = total_time / avg_individual_time
        assert (
            efficiency_ratio < num_concurrent * 2
        ), f"Concurrent efficiency ratio {efficiency_ratio:.2f} is too high"

        print(
            f"Concurrent validations: {total_time:.3f}s total, {avg_individual_time:.3f}s avg per validation"
        )

    def test_rule_complexity_performance(self):
        """Test performance with complex rules"""

        building_model = self.create_large_building_model(1000)

        # Create complex MCP file with many rules
        complex_rules = []
        for i in range(50):  # 50 complex rules
            rule = MCPRule(
                rule_id=f"complex_rule_{i}",
                name=f"Complex Rule {i}",
                description=f"Complex rule for performance testing {i}",
                category=RuleCategory.GENERAL,
                conditions=[
                    RuleCondition(
                        type=ConditionType.PROPERTY,
                        element_type=f"object_type_{i % 10}",
                        property="load",
                        operator=">=",
                        value=float(i % 100),
                    ),
                    RuleCondition(
                        type=ConditionType.PROPERTY,
                        element_type=f"object_type_{i % 10}",
                        property="capacity",
                        operator="<=",
                        value=float((i + 50) % 1000),
                    ),
                ],
                actions=[
                    RuleAction(
                        type=ActionType.VALIDATION,
                        message=f"Complex rule violation {i}",
                        severity=RuleSeverity.ERROR,
                    ),
                    RuleAction(
                        type=ActionType.CALCULATION,
                        formula="area * count",
                        unit="sqft",
                        description=f"Complex calculation {i}",
                    ),
                ],
            )
            complex_rules.append(rule)

        mcp_file = MCPFile(
            mcp_id="complex_performance_test",
            name="Complex Performance Test MCP",
            description="MCP file with complex rules for performance testing",
            jurisdiction=Jurisdiction(country="USA", state="Test"),
            version="1.0",
            effective_date="2024-01-01",
            rules=complex_rules,
        )

        # Save to temporary file
        import tempfile
        import json

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(mcp_file.to_dict(), f, indent=2)
            mcp_files = [f.name]

        # Measure performance
        start_time = time.time()
        report = self.engine.validate_building_model(building_model, mcp_files)
        execution_time = time.time() - start_time

        # Performance assertions
        assert (
            execution_time < 60.0
        ), f"Complex rules execution time {execution_time:.3f}s exceeds 60.0s limit"
        assert report is not None

        print(f"Complex rules (50 rules, 1000 objects): {execution_time:.3f}s")

    def test_memory_profiling(self):
        """Test memory profiling during validation"""

        building_model = self.create_large_building_model(2000)
        mcp_files = self.create_performance_mcp_files()

        # Profile memory usage during validation
        memory_samples = []

        def memory_monitor():
            """Monitor memory usage"""
            while True:
                memory_mb = self.process.memory_info().rss / 1024 / 1024
                memory_samples.append(memory_mb)
                time.sleep(0.1)

        import threading

        monitor_thread = threading.Thread(target=memory_monitor, daemon=True)
        monitor_thread.start()

        # Run validation
        start_time = time.time()
        report = self.engine.validate_building_model(building_model, mcp_files)
        execution_time = time.time() - start_time

        # Analyze memory usage
        if memory_samples:
            max_memory = max(memory_samples)
            avg_memory = sum(memory_samples) / len(memory_samples)

            # Memory should be reasonable
            assert (
                max_memory < 2000
            ), f"Peak memory usage {max_memory:.1f}MB exceeds 2GB limit"
            assert (
                avg_memory < 1500
            ), f"Average memory usage {avg_memory:.1f}MB exceeds 1.5GB limit"

            print(f"Memory profiling: peak {max_memory:.1f}MB, avg {avg_memory:.1f}MB")

    def test_scalability_benchmark(self):
        """Benchmark scalability across different model sizes"""

        model_sizes = [100, 500, 1000, 2000, 5000]
        results = {}

        for size in model_sizes:
            building_model = self.create_large_building_model(size)
            mcp_files = self.create_performance_mcp_files()

            # Measure performance
            start_time = time.time()
            report = self.engine.validate_building_model(building_model, mcp_files)
            execution_time = time.time() - start_time

            # Measure memory
            memory_mb = self.process.memory_info().rss / 1024 / 1024

            results[size] = {
                "execution_time": execution_time,
                "memory_mb": memory_mb,
                "objects_per_second": (
                    size / execution_time if execution_time > 0 else 0
                ),
            }

            print(
                f"Size {size}: {execution_time:.3f}s, {memory_mb:.1f}MB, {results[size]['objects_per_second']:.0f} obj/s"
            )

        # Verify scalability characteristics
        for i in range(1, len(model_sizes)):
            prev_size = model_sizes[i - 1]
            curr_size = model_sizes[i]

            prev_time = results[prev_size]["execution_time"]
            curr_time = results[curr_size]["execution_time"]

            # Time should scale reasonably (not exponentially)
            time_ratio = curr_time / prev_time
            size_ratio = curr_size / prev_size

            # Time should scale better than linearly (due to optimizations)
            assert (
                time_ratio < size_ratio * 1.5
            ), f"Time scaling {time_ratio:.2f}x for {size_ratio:.2f}x size increase is too high"

        print("Scalability benchmark completed successfully")

    def teardown_method(self):
        """Clean up after tests"""
        # Clear cache to prevent memory leaks
        self.engine.clear_cache()

        # Clean up temporary files
        import tempfile
        import glob

        temp_files = glob.glob(tempfile.gettempdir() + "/tmp*_mcp_*.json")
        for file in temp_files:
            try:
                os.unlink(file)
            except:
                pass
