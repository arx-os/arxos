"""
Tests for Enhanced Performance & Scalability System

This module tests the advanced performance optimization features including:
- Adaptive batch processing
- Multi-level parallelization
- Advanced profiling and bottleneck detection
- Scalability analysis and recommendations
"""

import unittest
import time
import threading
import multiprocessing
import psutil
import statistics
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from core.services.enhanced_performance
    AdaptiveBatchProcessor, AdvancedParallelProcessor, AdvancedPerformanceProfiler,
    ScalabilityAnalyzer, EnhancedPerformanceOptimizer,
    BatchStrategy, ParallelizationLevel, OptimizationLevel,
    BatchMetrics, ParallelMetrics, ScalabilityMetrics,
    optimize_operation, batch_process, parallel_process, profile_operation,
    run_scalability_test
)


class TestAdaptiveBatchProcessor(unittest.TestCase):
    """Test adaptive batch processing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = AdaptiveBatchProcessor(initial_batch_size=50)
        
    def test_initialization(self):
        """Test processor initialization."""
        self.assertEqual(self.processor.initial_batch_size, 50)
        self.assertEqual(self.processor.optimal_batch_size, 50)
        self.assertEqual(self.processor.strategy, BatchStrategy.ADAPTIVE_SIZE)
        self.assertEqual(len(self.processor.batch_metrics), 0)
    
    def test_fixed_size_strategy(self):
        """Test fixed size batch strategy."""
        processor = AdaptiveBatchProcessor(
            initial_batch_size=100, 
            strategy=BatchStrategy.FIXED_SIZE
        )
        
        def process_item(item):
            time.sleep(0.001)  # Simulate work
            return item * 2
        
        items = list(range(250))
        results = processor.process_batches(items, process_item)
        
        self.assertEqual(len(results), 250)
        self.assertEqual(results[:5], [0, 2, 4, 6, 8])
        self.assertEqual(processor.optimal_batch_size, 100)  # Should not change
    
    def test_adaptive_size_strategy(self):
        """Test adaptive size batch strategy."""
        def process_item(item):
            time.sleep(0.001)  # Simulate work
            return item * 2
        
        items = list(range(200))
        results = self.processor.process_batches(items, process_item)
        
        self.assertEqual(len(results), 200)
        self.assertEqual(results[:5], [0, 2, 4, 6, 8])
        self.assertGreater(len(self.processor.batch_metrics), 0)
    
    def test_memory_based_strategy(self):
        """Test memory-based batch strategy."""
        processor = AdaptiveBatchProcessor(strategy=BatchStrategy.MEMORY_BASED)
        
        def process_item(item):
            return item * 2
        
        items = list(range(100))
        results = processor.process_batches(items, process_item)
        
        self.assertEqual(len(results), 100)
        self.assertGreater(len(processor.batch_metrics), 0)
    
    def test_time_based_strategy(self):
        """Test time-based batch strategy."""
        processor = AdaptiveBatchProcessor(strategy=BatchStrategy.TIME_BASED)
        
        def process_item(item):
            time.sleep(0.001)  # Simulate work
            return item * 2
        
        items = list(range(100))
        results = processor.process_batches(items, process_item)
        
        self.assertEqual(len(results), 100)
        self.assertGreater(len(processor.batch_metrics), 0)
    
    def test_empty_items(self):
        """Test processing empty item list."""
        def process_item(item):
            return item * 2
        
        results = self.processor.process_batches([], process_item)
        self.assertEqual(results, [])
        self.assertEqual(len(self.processor.batch_metrics), 0)
    
    def test_error_handling(self):
        """Test error handling in batch processing."""
        def process_item(item):
            if item == 50:  # Simulate error
                raise ValueError("Test error")
            return item * 2
        
        items = list(range(100))
        results = self.processor.process_batches(items, process_item)
        
        # Should handle errors gracefully
        self.assertLess(len(results), 100)  # Some items failed
        self.assertGreater(len(self.processor.batch_metrics), 0)
    
    def test_batch_statistics(self):
        """Test batch statistics generation."""
        def process_item(item):
            time.sleep(0.001)
            return item * 2
        
        items = list(range(100))
        self.processor.process_batches(items, process_item)
        
        stats = self.processor.get_batch_statistics()
        
        self.assertIn("total_batches", stats)
        self.assertIn("optimal_batch_size", stats)
        self.assertIn("avg_throughput", stats)
        self.assertIn("success_rate", stats)
        self.assertGreater(stats["total_batches"], 0)
    
    def test_adaptive_batch_size_update(self):
        """Test adaptive batch size updates."""
        # Process with high throughput
        def fast_process(item):
            return item * 2
        
        items = list(range(200))
        self.processor.process_batches(items, fast_process)
        
        initial_size = self.processor.initial_batch_size
        self.assertGreaterEqual(self.processor.optimal_batch_size, initial_size)
        
        # Process with low throughput
        def slow_process(item):
            time.sleep(0.01)
            return item * 2
        
        self.processor.process_batches(items, slow_process)
        
        # Should adjust batch size based on performance
        self.assertNotEqual(self.processor.optimal_batch_size, initial_size)


class TestAdvancedParallelProcessor(unittest.TestCase):
    """Test advanced parallel processing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = AdvancedParallelProcessor(max_workers=2)
        
    def test_initialization(self):
        """Test processor initialization."""
        self.assertEqual(self.processor.max_workers, 2)
        self.assertEqual(len(self.processor.parallel_metrics), 0)
    
    def test_none_parallelization(self):
        """Test no parallelization level."""
        def process_item(item):
            time.sleep(0.001)
            return item * 2
        
        items = list(range(10))
        results = self.processor.execute_parallel(
            process_item, items, ParallelizationLevel.NONE
        )
        
        self.assertEqual(len(results), 10)
        self.assertEqual(results[:5], [0, 2, 4, 6, 8])
    
    def test_thread_parallelization(self):
        """Test thread-based parallelization."""
        def process_item(item):
            time.sleep(0.001)
            return item * 2
        
        items = list(range(20))
        results = self.processor.execute_parallel(
            process_item, items, ParallelizationLevel.THREADS
        )
        
        self.assertEqual(len(results), 20)
        self.assertEqual(results[:5], [0, 2, 4, 6, 8])
        self.assertGreater(len(self.processor.parallel_metrics), 0)
    
    def test_process_parallelization(self):
        """Test process-based parallelization."""
        def process_item(item):
            time.sleep(0.001)
            return item * 2
        
        items = list(range(20))
        results = self.processor.execute_parallel(
            process_item, items, ParallelizationLevel.PROCESSES
        )
        
        self.assertEqual(len(results), 20)
        self.assertEqual(results[:5], [0, 2, 4, 6, 8])
        self.assertGreater(len(self.processor.parallel_metrics), 0)
    
    def test_hybrid_parallelization(self):
        """Test hybrid parallelization."""
        def process_item(item):
            time.sleep(0.001)
            return item * 2
        
        items = list(range(20))
        results = self.processor.execute_parallel(
            process_item, items, ParallelizationLevel.HYBRID
        )
        
        self.assertEqual(len(results), 20)
        self.assertEqual(results[:5], [0, 2, 4, 6, 8])
        self.assertGreater(len(self.processor.parallel_metrics), 0)
    
    def test_error_handling(self):
        """Test error handling in parallel processing."""
        def process_item(item):
            if item == 5:  # Simulate error
                raise ValueError("Test error")
            return item * 2
        
        items = list(range(10))
        
        with self.assertRaises(ValueError):
            self.processor.execute_parallel(
                process_item, items, ParallelizationLevel.THREADS
            )
    
    def test_parallel_statistics(self):
        """Test parallel statistics generation."""
        def process_item(item):
            time.sleep(0.001)
            return item * 2
        
        items = list(range(20))
        self.processor.execute_parallel(
            process_item, items, ParallelizationLevel.THREADS
        )
        
        stats = self.processor.get_parallel_statistics()
        
        self.assertIn("total_operations", stats)
        self.assertIn("avg_efficiency", stats)
        self.assertIn("avg_load_balance", stats)
        self.assertIn("max_workers", stats)
        self.assertGreater(stats["total_operations"], 0)
    
    def test_efficiency_calculation(self):
        """Test parallel efficiency calculation."""
        def process_item(item):
            time.sleep(0.001)
            return item * 2
        
        items = list(range(10))
        self.processor.execute_parallel(
            process_item, items, ParallelizationLevel.THREADS
        )
        
        metrics = self.processor.parallel_metrics[0]
        self.assertGreaterEqual(metrics.parallel_efficiency, 0.0)
        self.assertLessEqual(metrics.parallel_efficiency, 1.0)
    
    def test_load_balance_calculation(self):
        """Test load balance calculation."""
        def process_item(item):
            time.sleep(0.001)
            return item * 2
        
        items = list(range(10))
        self.processor.execute_parallel(
            process_item, items, ParallelizationLevel.THREADS
        )
        
        metrics = self.processor.parallel_metrics[0]
        self.assertGreaterEqual(metrics.load_balance, 0.0)
        self.assertLessEqual(metrics.load_balance, 1.0)


class TestAdvancedPerformanceProfiler(unittest.TestCase):
    """Test advanced performance profiling functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.profiler = AdvancedPerformanceProfiler()
        
    def test_initialization(self):
        """Test profiler initialization."""
        self.assertEqual(len(self.profiler.metrics), 0)
        self.assertEqual(len(self.profiler.bottlenecks), 0)
        self.assertEqual(len(self.profiler.performance_alerts), 0)
    
    def test_profile_operation_decorator(self):
        """Test profiling decorator."""
        @self.profiler.profile_operation("test_operation")
        def test_function():
            time.sleep(0.01)
            return "result"
        
        result = test_function()
        
        self.assertEqual(result, "result")
        self.assertEqual(len(self.profiler.metrics), 1)
        self.assertEqual(self.profiler.metrics[0].operation_name, "test_operation")
    
    def test_profile_operation_with_errors(self):
        """Test profiling with errors."""
        @self.profiler.profile_operation("error_operation")
        def error_function():
            raise ValueError("Test error")
        
        with self.assertRaises(ValueError):
            error_function()
        
        self.assertEqual(len(self.profiler.metrics), 1)
        self.assertEqual(len(self.profiler.metrics[0].errors), 1)
    
    def test_bottleneck_detection(self):
        """Test bottleneck detection."""
        @self.profiler.profile_operation("slow_operation")
        def slow_function():
            time.sleep(1.1)  # Exceeds slow operation threshold
            return "result"
        
        slow_function()
        
        self.assertGreater(len(self.profiler.bottlenecks), 0)
        self.assertEqual(self.profiler.bottlenecks[0]["type"], "slow_operation")
    
    def test_alert_generation(self):
        """Test performance alert generation."""
        @self.profiler.profile_operation("error_operation")
        def error_function():
            raise ValueError("Test error")
        
        with self.assertRaises(ValueError):
            error_function()
        
        # Should generate alert for high error rate
        self.assertGreater(len(self.profiler.performance_alerts), 0)
    
    def test_performance_report(self):
        """Test performance report generation."""
        @self.profiler.profile_operation("test_operation")
        def test_function():
            time.sleep(0.01)
            return "result"
        
        test_function()
        test_function()  # Call twice
        
        report = self.profiler.get_performance_report()
        
        self.assertIn("summary", report)
        self.assertIn("operation_statistics", report)
        self.assertIn("bottlenecks", report)
        self.assertIn("alerts", report)
        self.assertEqual(report["summary"]["total_operations"], 2)
    
    def test_detailed_metrics_collection(self):
        """Test detailed metrics collection."""
        detailed_metrics = self.profiler._collect_detailed_metrics()
        
        self.assertIn("cpu_count", detailed_metrics)
        self.assertIn("memory_total", detailed_metrics)
        self.assertIn("memory_available", detailed_metrics)
        self.assertIn("disk_usage", detailed_metrics)
        self.assertIn("network_io", detailed_metrics)


class TestScalabilityAnalyzer(unittest.TestCase):
    """Test scalability analysis functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = ScalabilityAnalyzer()
        
    def test_initialization(self):
        """Test analyzer initialization."""
        self.assertEqual(len(self.analyzer.scalability_tests), 0)
        self.assertEqual(len(self.analyzer.benchmark_results), 0)
    
    def test_scalability_analysis(self):
        """Test scalability analysis."""
        def process_item(item):
            time.sleep(0.001)
            return item * 2
        
        input_sizes = [10, 50, 100]
        results = self.analyzer.analyze_scalability(
            input_sizes, process_item, ParallelizationLevel.THREADS
        )
        
        self.assertIn("test_count", results)
        self.assertIn("input_sizes", results)
        self.assertIn("throughputs", results)
        self.assertIn("scaling_analysis", results)
        self.assertEqual(results["test_count"], 3)
    
    def test_efficiency_calculation(self):
        """Test efficiency calculation."""
        efficiency = self.analyzer._calculate_efficiency(
            100, 1.0, ParallelizationLevel.THREADS
        )
        
        self.assertGreaterEqual(efficiency, 0.0)
        self.assertLessEqual(efficiency, 1.0)
    
    def test_bottleneck_detection(self):
        """Test bottleneck detection."""
        bottlenecks = self.analyzer._detect_bottlenecks(
            1000, 2.0, 500.0, 95.0
        )
        
        self.assertIsInstance(bottlenecks, list)
        self.assertIn("processing_time", bottlenecks)
        self.assertIn("cpu_usage", bottlenecks)
    
    def test_recommendation_generation(self):
        """Test recommendation generation."""
        bottlenecks = ["processing_time", "memory_usage"]
        recommendations = self.analyzer._generate_recommendations(
            1000, 2.0, 500.0, 95.0, bottlenecks
        )
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
    
    def test_scaling_pattern_analysis(self):
        """Test scaling pattern analysis."""
        # Create test metrics
        metrics = [
            ScalabilityMetrics(
                input_size=10, processing_time=0.1, memory_usage=10.0,
                cpu_usage=50.0, throughput=100.0, efficiency=0.8,
                bottlenecks=[], recommendations=[]
            ),
            ScalabilityMetrics(
                input_size=20, processing_time=0.2, memory_usage=20.0,
                cpu_usage=60.0, throughput=100.0, efficiency=0.7,
                bottlenecks=[], recommendations=[]
            )
        ]
        
        analysis = self.analyzer._analyze_scaling_patterns(metrics)
        
        self.assertIn("avg_scaling_factor", analysis)
        self.assertIn("scaling_type", analysis)
        self.assertIn("scaling_factors", analysis)
    
    def test_overall_recommendations(self):
        """Test overall recommendation generation."""
        # Create test metrics with bottlenecks
        metrics = [
            ScalabilityMetrics(
                input_size=10, processing_time=0.1, memory_usage=10.0,
                cpu_usage=50.0, throughput=100.0, efficiency=0.8,
                bottlenecks=["processing_time"], recommendations=[]
            ),
            ScalabilityMetrics(
                input_size=20, processing_time=0.2, memory_usage=20.0,
                cpu_usage=60.0, throughput=100.0, efficiency=0.7,
                bottlenecks=["processing_time"], recommendations=[]
            )
        ]
        
        recommendations = self.analyzer._generate_overall_recommendations(metrics)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)


class TestEnhancedPerformanceOptimizer(unittest.TestCase):
    """Test enhanced performance optimizer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.optimizer = EnhancedPerformanceOptimizer(OptimizationLevel.STANDARD)
        
    def test_initialization(self):
        """Test optimizer initialization."""
        self.assertEqual(self.optimizer.optimization_level, OptimizationLevel.STANDARD)
        self.assertIsNotNone(self.optimizer.batch_processor)
        self.assertIsNotNone(self.optimizer.parallel_processor)
        self.assertIsNotNone(self.optimizer.profiler)
        self.assertIsNotNone(self.optimizer.scalability_analyzer)
    
    def test_optimize_operation_decorator(self):
        """Test operation optimization decorator."""
        @self.optimizer.optimize_operation("test_operation")
        def test_function(items):
            return [item * 2 for item in items]
        
        items = list(range(10))
        results = test_function(items)
        
        self.assertEqual(len(results), 10)
        self.assertEqual(results[:5], [0, 2, 4, 6, 8])
    
    def test_optimize_operation_with_batching(self):
        """Test operation optimization with batching."""
        def process_items(items):
            return [item * 2 for item in items]
        
        items = list(range(100))
        results = self.optimizer._execute_optimized_operation(
            "test_operation", process_items, [items], {},
            use_batching=True, use_parallel=False, use_profiling=True,
            batch_size=20, parallel_level=ParallelizationLevel.THREADS
        )
        
        self.assertEqual(len(results), 100)
        self.assertEqual(results[:5], [0, 2, 4, 6, 8])
    
    def test_optimize_operation_with_parallel(self):
        """Test operation optimization with parallelization."""
        def process_item(item):
            time.sleep(0.001)
            return item * 2
        
        items = list(range(20))
        results = self.optimizer._execute_optimized_operation(
            "test_operation", process_item, [items], {},
            use_batching=True, use_parallel=True, use_profiling=True,
            batch_size=10, parallel_level=ParallelizationLevel.THREADS
        )
        
        self.assertEqual(len(results), 20)
        self.assertEqual(results[:5], [0, 2, 4, 6, 8])
    
    def test_scalability_test(self):
        """Test scalability testing."""
        def process_item(item):
            time.sleep(0.001)
            return item * 2
        
        input_sizes = [10, 20, 30]
        results = self.optimizer.run_scalability_test(
            input_sizes, process_item, ParallelizationLevel.THREADS
        )
        
        self.assertIn("test_count", results)
        self.assertIn("input_sizes", results)
        self.assertIn("throughputs", results)
        self.assertEqual(results["test_count"], 3)
    
    def test_performance_summary(self):
        """Test performance summary generation."""
        # Run some operations to generate metrics
        def process_item(item):
            time.sleep(0.001)
            return item * 2
        
        items = list(range(20))
        self.optimizer._execute_optimized_operation(
            "test_operation", process_item, [items], {},
            use_batching=True, use_parallel=True, use_profiling=True,
            batch_size=10, parallel_level=ParallelizationLevel.THREADS
        )
        
        summary = self.optimizer.get_performance_summary()
        
        self.assertIn("batch_statistics", summary)
        self.assertIn("parallel_statistics", summary)
        self.assertIn("performance_report", summary)
    
    def test_monitoring(self):
        """Test performance monitoring."""
        self.optimizer.start_monitoring()
        time.sleep(0.1)  # Let monitoring run briefly
        self.optimizer.stop_monitoring()
        
        # Should not raise exceptions
        self.assertFalse(self.optimizer.monitoring_active)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    def test_optimize_operation_decorator(self):
        """Test optimize_operation decorator."""
        @optimize_operation("test_operation")
        def test_function(items):
            return [item * 2 for item in items]
        
        items = list(range(10))
        results = test_function(items)
        
        self.assertEqual(len(results), 10)
        self.assertEqual(results[:5], [0, 2, 4, 6, 8])
    
    def test_batch_process(self):
        """Test batch_process function."""
        def process_item(item):
            return item * 2
        
        items = list(range(100))
        results = batch_process(items, process_item, batch_size=20)
        
        self.assertEqual(len(results), 100)
        self.assertEqual(results[:5], [0, 2, 4, 6, 8])
    
    def test_parallel_process(self):
        """Test parallel_process function."""
        def process_item(item):
            time.sleep(0.001)
            return item * 2
        
        items = list(range(20))
        results = parallel_process(items, process_item, ParallelizationLevel.THREADS)
        
        self.assertEqual(len(results), 20)
        self.assertEqual(results[:5], [0, 2, 4, 6, 8])
    
    def test_profile_operation(self):
        """Test profile_operation decorator."""
        @profile_operation("test_operation")
        def test_function():
            time.sleep(0.01)
            return "result"
        
        result = test_function()
        
        self.assertEqual(result, "result")
    
    def test_run_scalability_test(self):
        """Test run_scalability_test function."""
        def process_item(item):
            time.sleep(0.001)
            return item * 2
        
        input_sizes = [10, 20]
        results = run_scalability_test(input_sizes, process_item)
        
        self.assertIn("test_count", results)
        self.assertEqual(results["test_count"], 2)


class TestPerformanceIntegration(unittest.TestCase):
    """Integration tests for performance optimization."""
    
    def test_svg_parsing_optimization(self):
        """Test SVG parsing with performance optimization."""
        optimizer = EnhancedPerformanceOptimizer(OptimizationLevel.STANDARD)
        
        def parse_svg_element(element):
            time.sleep(0.001)  # Simulate parsing
            return f"parsed_{element}"
        
        elements = ["rect", "circle", "line", "text"] * 25  # 100 elements
        results = optimizer._execute_optimized_operation(
            "svg_parsing", parse_svg_element, [elements], {},
            use_batching=True, use_parallel=True, use_profiling=True,
            batch_size=20, parallel_level=ParallelizationLevel.THREADS
        )
        
        self.assertEqual(len(results), 100)
        self.assertTrue(all(result.startswith("parsed_") for result in results))
    
    def test_bim_assembly_optimization(self):
        """Test BIM assembly with performance optimization."""
        optimizer = EnhancedPerformanceOptimizer(OptimizationLevel.AGGRESSIVE)
        
        def assemble_bim_element(element):
            time.sleep(0.001)  # Simulate assembly
            return {"type": element, "assembled": True}
        
        elements = ["wall", "door", "window", "floor"] * 25  # 100 elements
        results = optimizer._execute_optimized_operation(
            "bim_assembly", assemble_bim_element, [elements], {},
            use_batching=True, use_parallel=True, use_profiling=True,
            batch_size=25, parallel_level=ParallelizationLevel.THREADS
        )
        
        self.assertEqual(len(results), 100)
        self.assertTrue(all(result["assembled"] for result in results))
    
    def test_geometry_processing_optimization(self):
        """Test geometry processing with performance optimization."""
        optimizer = EnhancedPerformanceOptimizer(OptimizationLevel.STANDARD)
        
        def process_geometry(geometry):
            time.sleep(0.001)  # Simulate processing
            return {"processed": True, "geometry": geometry}
        
        geometries = [{"type": "rect", "x": i, "y": i} for i in range(50)]
        results = optimizer._execute_optimized_operation(
            "geometry_processing", process_geometry, [geometries], {},
            use_batching=True, use_parallel=True, use_profiling=True,
            batch_size=10, parallel_level=ParallelizationLevel.THREADS
        )
        
        self.assertEqual(len(results), 50)
        self.assertTrue(all(result["processed"] for result in results))
    
    def test_large_scale_processing(self):
        """Test large-scale processing with optimization."""
        optimizer = EnhancedPerformanceOptimizer(OptimizationLevel.AGGRESSIVE)
        
        def process_large_item(item):
            time.sleep(0.0001)  # Fast processing
            return item * 2
        
        large_dataset = list(range(1000))
        start_time = time.time()
        
        results = optimizer._execute_optimized_operation(
            "large_scale_processing", process_large_item, [large_dataset], {},
            use_batching=True, use_parallel=True, use_profiling=True,
            batch_size=100, parallel_level=ParallelizationLevel.THREADS
        )
        
        processing_time = time.time() - start_time
        
        self.assertEqual(len(results), 1000)
        self.assertEqual(results[:5], [0, 2, 4, 6, 8])
        self.assertLess(processing_time, 5.0)  # Should complete within 5 seconds
    
    def test_memory_efficient_processing(self):
        """Test memory-efficient processing."""
        optimizer = EnhancedPerformanceOptimizer(OptimizationLevel.STANDARD)
        
        def memory_intensive_process(item):
            # Simulate memory-intensive operation
            large_data = [item] * 1000
            return sum(large_data)
        
        items = list(range(100))
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        results = optimizer._execute_optimized_operation(
            "memory_intensive", memory_intensive_process, [items], {},
            use_batching=True, use_parallel=False, use_profiling=True,
            batch_size=10, parallel_level=ParallelizationLevel.NONE
        )
        
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_increase = end_memory - start_memory
        
        self.assertEqual(len(results), 100)
        self.assertLess(memory_increase, 100)  # Should not increase memory by more than 100MB


if __name__ == "__main__":
    unittest.main() 