"""
Enhanced Performance & Scalability Demo

This script demonstrates the advanced performance optimization features:
- Intelligent batch processing with adaptive sizing
- Multi-level parallelization (thread/process pools)
- Advanced profiling with bottleneck detection
- Resource monitoring and adaptive optimization
- Performance metrics collection and analysis
- Scalability testing and benchmarking
"""

import time
import random
import statistics
from typing import List, Dict, Any

from services.enhanced_performance import (
    AdaptiveBatchProcessor, AdvancedParallelProcessor, AdvancedPerformanceProfiler,
    ScalabilityAnalyzer, EnhancedPerformanceOptimizer,
    BatchStrategy, ParallelizationLevel, OptimizationLevel,
    optimize_operation, batch_process, parallel_process, profile_operation,
    run_scalability_test
)


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"DEMO: {title}")
    print("="*60)


def print_section(title: str):
    """Print a formatted section."""
    print(f"\n--- {title} ---")


def demo_batch_processing():
    """Demonstrate adaptive batch processing."""
    print_header("Adaptive Batch Processing")
    
    # Create different batch processors
    processors = {
        "Fixed Size": AdaptiveBatchProcessor(100, BatchStrategy.FIXED_SIZE),
        "Adaptive Size": AdaptiveBatchProcessor(50, BatchStrategy.ADAPTIVE_SIZE),
        "Memory Based": AdaptiveBatchProcessor(50, BatchStrategy.MEMORY_BASED),
        "Time Based": AdaptiveBatchProcessor(50, BatchStrategy.TIME_BASED)
    }
    
    def process_item(item):
        """Simulate item processing with variable time."""
        time.sleep(random.uniform(0.001, 0.005))
        return item * 2
    
    # Test with different dataset sizes
    dataset_sizes = [100, 500, 1000]
    
    for size in dataset_sizes:
        print_section(f"Dataset Size: {size}")
        items = list(range(size))
        
        for name, processor in processors.items():
            print(f"\n{name} Processor:")
            
            start_time = time.time()
            results = processor.process_batches(items, process_item)
            processing_time = time.time() - start_time
            
            stats = processor.get_batch_statistics()
            
            print(f"  Processing Time: {processing_time:.3f}s")
            print(f"  Total Batches: {stats['total_batches']}")
            print(f"  Optimal Batch Size: {stats['optimal_batch_size']}")
            print(f"  Average Throughput: {stats['avg_throughput']:.1f} items/s")
            print(f"  Success Rate: {stats['success_rate']:.1f}%")
            
            # Verify results
            expected_results = [i * 2 for i in range(size)]
            assert results == expected_results, f"Results mismatch for {name}"


def demo_parallel_processing():
    """Demonstrate multi-level parallel processing."""
    print_header("Multi-Level Parallel Processing")
    
    processor = AdvancedParallelProcessor(max_workers=4)
    
    def process_item(item):
        """Simulate CPU-intensive processing."""
        # Simulate work
        result = 0
        for i in range(1000):
            result += item * i
        time.sleep(0.001)
        return result
    
    # Test different parallelization levels
    levels = [
        ("None", ParallelizationLevel.NONE),
        ("Threads", ParallelizationLevel.THREADS),
        ("Processes", ParallelizationLevel.PROCESSES),
        ("Hybrid", ParallelizationLevel.HYBRID)
    ]
    
    items = list(range(50))
    
    for name, level in levels:
        print_section(f"Parallelization Level: {name}")
        
        start_time = time.time()
        results = processor.execute_parallel(process_item, items, level)
        processing_time = time.time() - start_time
        
        stats = processor.get_parallel_statistics()
        
        print(f"  Processing Time: {processing_time:.3f}s")
        print(f"  Total Operations: {stats['total_operations']}")
        print(f"  Average Efficiency: {stats['avg_efficiency']:.3f}")
        print(f"  Average Load Balance: {stats['avg_load_balance']:.3f}")
        print(f"  Communication Overhead: {stats['avg_communication_overhead']:.3f}")
        
        # Verify results
        assert len(results) == 50, f"Result count mismatch for {name}"


def demo_advanced_profiling():
    """Demonstrate advanced profiling and bottleneck detection."""
    print_header("Advanced Profiling & Bottleneck Detection")
    
    profiler = AdvancedPerformanceProfiler()
    
    # Simulate different types of operations
    @profiler.profile_operation("fast_operation")
    def fast_operation():
        time.sleep(0.01)
        return "fast"
    
    @profiler.profile_operation("slow_operation")
    def slow_operation():
        time.sleep(1.5)  # Exceeds threshold
        return "slow"
    
    @profiler.profile_operation("memory_intensive")
    def memory_intensive_operation():
        # Simulate memory allocation
        large_list = [i for i in range(100000)]
        time.sleep(0.1)
        return len(large_list)
    
    @profiler.profile_operation("error_operation")
    def error_operation():
        raise ValueError("Simulated error")
    
    print_section("Running Operations")
    
    # Run operations
    print("Running fast operation...")
    fast_operation()
    
    print("Running slow operation...")
    slow_operation()
    
    print("Running memory intensive operation...")
    memory_intensive_operation()
    
    print("Running error operation...")
    try:
        error_operation()
    except ValueError:
        pass
    
    # Get performance report
    report = profiler.get_performance_report()
    
    print_section("Performance Report")
    
    summary = report["summary"]
    print(f"Total Operations: {summary['total_operations']}")
    print(f"Total Execution Time: {summary['total_execution_time']:.3f}s")
    print(f"Total Memory Usage: {summary['total_memory_usage']:.1f}MB")
    print(f"Total Errors: {summary['total_errors']}")
    print(f"Average Execution Time: {summary['avg_execution_time']:.3f}s")
    
    print_section("Operation Statistics")
    for op_name, stats in report["operation_statistics"].items():
        print(f"\n{op_name}:")
        print(f"  Count: {stats['count']}")
        print(f"  Avg Time: {stats['avg_time']:.3f}s")
        print(f"  Max Time: {stats['max_time']:.3f}s")
        print(f"  Min Time: {stats['min_time']:.3f}s")
        print(f"  Std Dev: {stats['std_dev']:.3f}s")
    
    print_section("Bottlenecks")
    bottlenecks = report["bottlenecks"]
    print(f"Total Bottlenecks: {bottlenecks['total']}")
    print(f"By Type: {bottlenecks['by_type']}")
    
    print_section("Alerts")
    alerts = report["alerts"]
    print(f"Total Alerts: {alerts['total']}")


def demo_scalability_analysis():
    """Demonstrate scalability analysis."""
    print_header("Scalability Analysis")
    
    analyzer = ScalabilityAnalyzer()
    
    def process_item(item):
        """Simulate scalable processing."""
        # Simulate work that scales with input size
        work_factor = item // 100 + 1
        for i in range(work_factor * 100):
            _ = i * item
        time.sleep(0.001)
        return item * 2
    
    # Test different input sizes
    input_sizes = [10, 50, 100, 200, 500]
    
    print_section("Running Scalability Tests")
    results = analyzer.analyze_scalability(
        input_sizes, process_item, ParallelizationLevel.THREADS
    )
    
    print_section("Scalability Report")
    
    print(f"Test Count: {results['test_count']}")
    print(f"Input Sizes: {results['input_sizes']}")
    
    print("\nThroughputs:")
    for i, throughput in enumerate(results['throughputs']):
        print(f"  Size {results['input_sizes'][i]}: {throughput:.1f} items/s")
    
    print("\nEfficiencies:")
    for i, efficiency in enumerate(results['efficiencies']):
        print(f"  Size {results['input_sizes'][i]}: {efficiency:.3f}")
    
    print("\nMemory Usage:")
    for i, memory in enumerate(results['memory_usages']):
        print(f"  Size {results['input_sizes'][i]}: {memory:.1f}MB")
    
    scaling_analysis = results['scaling_analysis']
    print(f"\nScaling Analysis:")
    print(f"  Average Scaling Factor: {scaling_analysis['avg_scaling_factor']:.3f}")
    print(f"  Scaling Type: {scaling_analysis['scaling_type']}")
    print(f"  Scaling Factors: {[f'{f:.3f}' for f in scaling_analysis['scaling_factors']]}")
    
    print(f"\nRecommendations:")
    for i, rec in enumerate(results['recommendations'], 1):
        print(f"  {i}. {rec}")


def demo_enhanced_optimizer():
    """Demonstrate enhanced performance optimizer."""
    print_header("Enhanced Performance Optimizer")
    
    optimizer = EnhancedPerformanceOptimizer(OptimizationLevel.AGGRESSIVE)
    
    # Define different types of operations
    def svg_parsing_operation(elements):
        """Simulate SVG parsing."""
        results = []
        for element in elements:
            time.sleep(0.001)
            results.append(f"parsed_{element}")
        return results
    
    def bim_assembly_operation(elements):
        """Simulate BIM assembly."""
        results = []
        for element in elements:
            time.sleep(0.002)
            results.append({"type": element, "assembled": True})
        return results
    
    def geometry_processing_operation(elements):
        """Simulate geometry processing."""
        results = []
        for element in elements:
            time.sleep(0.001)
            results.append({"geometry": element, "processed": True})
        return results
    
    # Test different operations
    operations = [
        ("SVG Parsing", svg_parsing_operation),
        ("BIM Assembly", bim_assembly_operation),
        ("Geometry Processing", geometry_processing_operation)
    ]
    
    items = list(range(100))
    
    for name, operation in operations:
        print_section(f"Optimized {name}")
        
        # Test with different optimization strategies
        strategies = [
            ("Batching Only", {"use_batching": True, "use_parallel": False}),
            ("Parallel Only", {"use_batching": False, "use_parallel": True}),
            ("Full Optimization", {"use_batching": True, "use_parallel": True})
        ]
        
        for strategy_name, strategy_config in strategies:
            print(f"\n{strategy_name}:")
            
            start_time = time.time()
            results = optimizer._execute_optimized_operation(
                f"{name.lower().replace(' ', '_')}",
                operation, [items], {},
                **strategy_config,
                use_profiling=True,
                batch_size=20,
                parallel_level=ParallelizationLevel.THREADS
            )
            processing_time = time.time() - start_time
            
            print(f"  Processing Time: {processing_time:.3f}s")
            print(f"  Results Count: {len(results)}")
            print(f"  Throughput: {len(items) / processing_time:.1f} items/s")
    
    # Get performance summary
    summary = optimizer.get_performance_summary()
    
    print_section("Performance Summary")
    
    batch_stats = summary["batch_statistics"]
    print(f"Batch Statistics:")
    print(f"  Total Batches: {batch_stats['total_batches']}")
    print(f"  Average Throughput: {batch_stats['avg_throughput']:.1f} items/s")
    print(f"  Success Rate: {batch_stats['success_rate']:.1f}%")
    
    parallel_stats = summary["parallel_statistics"]
    print(f"\nParallel Statistics:")
    print(f"  Total Operations: {parallel_stats['total_operations']}")
    print(f"  Average Efficiency: {parallel_stats['avg_efficiency']:.3f}")
    print(f"  Average Load Balance: {parallel_stats['avg_load_balance']:.3f}")


def demo_convenience_functions():
    """Demonstrate convenience functions."""
    print_header("Convenience Functions")
    
    def process_item(item):
        """Simple item processing."""
        time.sleep(0.001)
        return item * 2
    
    def process_items(items):
        """Batch item processing."""
        return [item * 2 for item in items]
    
    items = list(range(50))
    
    print_section("Batch Processing")
    start_time = time.time()
    results = batch_process(items, process_item, batch_size=10)
    batch_time = time.time() - start_time
    print(f"Batch Processing Time: {batch_time:.3f}s")
    print(f"Results: {len(results)} items")
    
    print_section("Parallel Processing")
    start_time = time.time()
    results = parallel_process(items, process_item, ParallelizationLevel.THREADS)
    parallel_time = time.time() - start_time
    print(f"Parallel Processing Time: {parallel_time:.3f}s")
    print(f"Results: {len(results)} items")
    
    print_section("Profiled Operation")
    @profile_operation("demo_operation")
    def demo_operation():
        time.sleep(0.1)
        return "completed"
    
    result = demo_operation()
    print(f"Profiled Operation Result: {result}")
    
    print_section("Scalability Test")
    input_sizes = [10, 20, 30]
    scalability_results = run_scalability_test(input_sizes, process_item)
    print(f"Scalability Test Results: {scalability_results['test_count']} tests completed")


def demo_performance_monitoring():
    """Demonstrate performance monitoring."""
    print_header("Performance Monitoring")
    
    optimizer = EnhancedPerformanceOptimizer()
    
    print_section("Starting Performance Monitoring")
    optimizer.start_monitoring()
    
    # Simulate some work
    def monitored_operation():
        time.sleep(0.1)
        return "monitored"
    
    print("Running monitored operations...")
    for i in range(5):
        result = monitored_operation()
        print(f"Operation {i+1}: {result}")
        time.sleep(0.2)
    
    print_section("Stopping Performance Monitoring")
    optimizer.stop_monitoring()
    
    print("Performance monitoring completed.")


def demo_large_scale_benchmark():
    """Demonstrate large-scale performance benchmarking."""
    print_header("Large-Scale Performance Benchmark")
    
    optimizer = EnhancedPerformanceOptimizer(OptimizationLevel.AGGRESSIVE)
    
    def benchmark_operation(item):
        """Benchmark operation with variable complexity."""
        complexity = (item % 10) + 1
        for i in range(complexity * 100):
            _ = i * item
        time.sleep(0.0001)
        return item * 2
    
    # Test with large dataset
    large_dataset = list(range(1000))
    
    print_section("Large Dataset Processing")
    print(f"Dataset Size: {len(large_dataset)} items")
    
    start_time = time.time()
    results = optimizer._execute_optimized_operation(
        "large_scale_benchmark",
        benchmark_operation, [large_dataset], {},
        use_batching=True, use_parallel=True, use_profiling=True,
        batch_size=100, parallel_level=ParallelizationLevel.THREADS
    )
    total_time = time.time() - start_time
    
    print(f"Total Processing Time: {total_time:.3f}s")
    print(f"Throughput: {len(large_dataset) / total_time:.1f} items/s")
    print(f"Results Count: {len(results)}")
    
    # Verify results
    expected_results = [i * 2 for i in range(1000)]
    assert results == expected_results, "Results verification failed"
    print("Results verification: PASSED")
    
    # Get performance summary
    summary = optimizer.get_performance_summary()
    
    print_section("Benchmark Summary")
    
    batch_stats = summary["batch_statistics"]
    print(f"Batch Processing:")
    print(f"  Total Batches: {batch_stats['total_batches']}")
    print(f"  Average Throughput: {batch_stats['avg_throughput']:.1f} items/s")
    print(f"  Success Rate: {batch_stats['success_rate']:.1f}%")
    
    parallel_stats = summary["parallel_statistics"]
    print(f"\nParallel Processing:")
    print(f"  Total Operations: {parallel_stats['total_operations']}")
    print(f"  Average Efficiency: {parallel_stats['avg_efficiency']:.3f}")
    print(f"  Average Load Balance: {parallel_stats['avg_load_balance']:.3f}")


def main():
    """Run all performance demos."""
    print("Enhanced Performance & Scalability System Demo")
    print("=" * 60)
    
    try:
        # Run all demos
        demo_batch_processing()
        demo_parallel_processing()
        demo_advanced_profiling()
        demo_scalability_analysis()
        demo_enhanced_optimizer()
        demo_convenience_functions()
        demo_performance_monitoring()
        demo_large_scale_benchmark()
        
        print("\n" + "="*60)
        print("ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        raise


if __name__ == "__main__":
    main() 