"""
Performance Optimization Demo

This script demonstrates the performance optimization system in action,
showing how it improves SVG-BIM processing performance through:
- Caching
- Batch processing
- Memory management
- Profiling
- Parallel processing
"""

import time
import logging
import sys
import os

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.performance_optimizer import (
    PerformanceOptimizer, OptimizationLevel, CacheStrategy,
    profile_operation, cache_result, batch_process
)
from models.bim import BIMElement, BIMSystem, BIMSpace, BIMRelationship
from services.svg_parser import SVGParser
from services.bim_assembly import BIMAssemblyPipeline

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_sample_svg_data():
    """Create sample SVG data for testing."""
    svg_content = """
    <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
        <!-- Walls -->
        <rect x="100" y="100" width="200" height="20" fill="gray" class="wall" data-bim-type="wall"/>
        <rect x="100" y="300" width="200" height="20" fill="gray" class="wall" data-bim-type="wall"/>
        <rect x="100" y="100" width="20" height="200" fill="gray" class="wall" data-bim-type="wall"/>
        <rect x="280" y="100" width="20" height="200" fill="gray" class="wall" data-bim-type="wall"/>
        
        <!-- Doors -->
        <rect x="180" y="100" width="40" height="20" fill="brown" class="door" data-bim-type="door"/>
        <rect x="180" y="300" width="40" height="20" fill="brown" class="door" data-bim-type="door"/>
        
        <!-- Windows -->
        <rect x="120" y="80" width="60" height="20" fill="blue" class="window" data-bim-type="window"/>
        <rect x="220" y="80" width="60" height="20" fill="blue" class="window" data-bim-type="window"/>
        
        <!-- HVAC Equipment -->
        <circle cx="150" cy="200" r="30" fill="green" class="hvac" data-bim-type="hvac"/>
        <rect x="200" y="180" width="40" height="40" fill="green" class="hvac" data-bim-type="hvac"/>
        
        <!-- Electrical -->
        <circle cx="250" cy="150" r="15" fill="yellow" class="electrical" data-bim-type="electrical"/>
        <circle cx="250" cy="250" r="15" fill="yellow" class="electrical" data-bim-type="electrical"/>
        
        <!-- Plumbing -->
        <rect x="120" y="250" width="20" height="20" fill="blue" class="plumbing" data-bim-type="plumbing"/>
        <rect x="220" y="250" width="20" height="20" fill="blue" class="plumbing" data-bim-type="plumbing"/>
    </svg>
    """
    return svg_content


def demo_basic_optimization():
    """Demonstrate basic performance optimization."""
    print("\n" + "="*60)
    print("DEMO 1: Basic Performance Optimization")
    print("="*60)
    
    optimizer = PerformanceOptimizer(OptimizationLevel.STANDARD)
    
    # Simulate expensive SVG parsing operation
    def expensive_svg_parsing(svg_content):
        time.sleep(0.1)  # Simulate processing time
        return len(svg_content.split('<'))
    
    # Test without optimization
    print("Testing without optimization...")
    start_time = time.time()
    for i in range(3):
        result = expensive_svg_parsing(f"<svg>{i}</svg>")
    no_opt_time = time.time() - start_time
    print(f"Time without optimization: {no_opt_time:.3f}s")
    
    # Test with optimization
    print("\nTesting with optimization...")
    optimized_parser = optimizer.optimize_operation(
        "svg_parsing", expensive_svg_parsing, use_caching=True, use_profiling=True
    )
    
    start_time = time.time()
    for i in range(3):
        result = optimized_parser(f"<svg>{i}</svg>")
    opt_time = time.time() - start_time
    print(f"Time with optimization: {opt_time:.3f}s")
    print(f"Performance improvement: {((no_opt_time - opt_time) / no_opt_time * 100):.1f}%")
    
    # Show optimization report
    report = optimizer.get_optimization_report()
    print(f"\nCache hit rate: {report['cache_stats']['geometry']['hit_rate']:.2%}")


def demo_batch_processing():
    """Demonstrate batch processing optimization."""
    print("\n" + "="*60)
    print("DEMO 2: Batch Processing Optimization")
    print("="*60)
    
    optimizer = PerformanceOptimizer(OptimizationLevel.AGGRESSIVE)
    
    # Simulate BIM element processing
    def process_bim_elements(elements):
        time.sleep(0.05)  # Simulate processing time
        return [f"processed_{elem}" for elem in elements]
    
    # Create large dataset
    elements = [f"element_{i}" for i in range(100)]
    
    # Test sequential processing
    print("Testing sequential processing...")
    start_time = time.time()
    results_seq = []
    for element in elements:
        result = process_bim_elements([element])
        results_seq.extend(result)
    seq_time = time.time() - start_time
    print(f"Sequential time: {seq_time:.3f}s")
    
    # Test batch processing
    print("\nTesting batch processing...")
    start_time = time.time()
    results_batch = optimizer.batch_process(elements, process_bim_elements)
    batch_time = time.time() - start_time
    print(f"Batch time: {batch_time:.3f}s")
    print(f"Performance improvement: {((seq_time - batch_time) / seq_time * 100):.1f}%")
    
    assert len(results_seq) == len(results_batch)
    print(f"Processed {len(results_batch)} elements successfully")


def demo_memory_optimization():
    """Demonstrate memory optimization."""
    print("\n" + "="*60)
    print("DEMO 3: Memory Optimization")
    print("="*60)
    
    optimizer = PerformanceOptimizer(OptimizationLevel.AGGRESSIVE)
    
    # Simulate memory-intensive operation
    def memory_intensive_operation(size):
        # Create large data structures
        large_list = [i for i in range(size)]
        large_dict = {f"key_{i}": f"value_{i}" for i in range(size)}
        time.sleep(0.01)
        return len(large_list) + len(large_dict)
    
    print("Monitoring memory usage during processing...")
    
    # Monitor performance with memory optimization
    report = optimizer.monitor_performance("memory_test", memory_threshold_mb=50)
    
    # Process multiple large datasets
    for i in range(5):
        size = 1000 * (i + 1)
        result = memory_intensive_operation(size)
        print(f"Processed dataset {i+1} with {size} items: {result} total objects")
        
        # Check if memory optimization is needed
        if optimizer.memory_manager.check_memory_threshold():
            print("Memory threshold exceeded, optimizing...")
            opt_result = optimizer.optimize_memory()
            print(f"Freed {opt_result['memory_freed_mb']:.2f}MB, collected {opt_result['objects_collected']} objects")
    
    print(f"\nFinal memory usage: {optimizer.memory_manager.get_memory_usage()['rss_mb']:.2f}MB")


def demo_decorators():
    """Demonstrate performance decorators."""
    print("\n" + "="*60)
    print("DEMO 4: Performance Decorators")
    print("="*60)
    
    # Profiling decorator
    @profile_operation("expensive_calculation")
    def expensive_calculation(x, y):
        time.sleep(0.1)
        return x * y + x + y
    
    # Caching decorator
    @cache_result(ttl=10)
    def expensive_lookup(key):
        time.sleep(0.1)
        return f"result_for_{key}"
    
    # Batch processing decorator
    @batch_process(batch_size=5)
    def process_items(items):
        time.sleep(0.05)
        return [item.upper() for item in items]
    
    print("Testing profiling decorator...")
    result1 = expensive_calculation(5, 10)
    result2 = expensive_calculation(5, 10)
    print(f"Calculation results: {result1}, {result2}")
    
    print("\nTesting caching decorator...")
    start_time = time.time()
    lookup1 = expensive_lookup("test_key")
    first_call_time = time.time() - start_time
    
    start_time = time.time()
    lookup2 = expensive_lookup("test_key")
    second_call_time = time.time() - start_time
    
    print(f"First call time: {first_call_time:.3f}s")
    print(f"Second call time: {second_call_time:.3f}s")
    print(f"Cache speedup: {first_call_time / second_call_time:.1f}x")
    
    print("\nTesting batch processing decorator...")
    items = [f"item_{i}" for i in range(10)]
    results = process_items(items)
    print(f"Processed {len(results)} items: {results[:3]}...")


def demo_svg_bim_integration():
    """Demonstrate SVG-BIM processing with performance optimization."""
    print("\n" + "="*60)
    print("DEMO 5: SVG-BIM Processing with Optimization")
    print("="*60)
    
    optimizer = PerformanceOptimizer(OptimizationLevel.AGGRESSIVE)
    
    # Create sample SVG data
    svg_content = create_sample_svg_data()
    
    # Optimize SVG parsing
    def parse_svg_with_optimization(svg_content):
        # Simulate SVG parsing with optimization
        time.sleep(0.05)
        elements = []
        lines = svg_content.split('\n')
        for line in lines:
            if '<rect' in line or '<circle' in line:
                elements.append(line.strip())
        return elements
    
    optimized_parser = optimizer.optimize_operation(
        "svg_parsing", parse_svg_with_optimization, use_caching=True, use_profiling=True
    )
    
    # Optimize BIM assembly
    def assemble_bim_with_optimization(elements):
        # Simulate BIM assembly with optimization
        time.sleep(0.03)
        bim_elements = []
        for element in elements:
            if 'data-bim-type' in element:
                bim_type = element.split('data-bim-type="')[1].split('"')[0]
                bim_elements.append({
                    'type': bim_type,
                    'element': element,
                    'processed': True
                })
        return bim_elements
    
    optimized_assembler = optimizer.optimize_operation(
        "bim_assembly", assemble_bim_with_optimization, use_caching=True, use_profiling=True
    )
    
    print("Processing SVG with performance optimization...")
    
    # Process multiple times to demonstrate caching
    for i in range(3):
        print(f"\nProcessing iteration {i+1}...")
        
        # Parse SVG
        elements = optimized_parser(svg_content)
        print(f"Parsed {len(elements)} SVG elements")
        
        # Assemble BIM
        bim_elements = optimized_assembler(elements)
        print(f"Assembled {len(bim_elements)} BIM elements")
        
        # Show element types
        types = [elem['type'] for elem in bim_elements]
        type_counts = {}
        for t in types:
            type_counts[t] = type_counts.get(t, 0) + 1
        print(f"Element types: {type_counts}")
    
    # Show final optimization report
    report = optimizer.get_optimization_report()
    print(f"\nFinal Performance Report:")
    print(f"- Total operations: {report['profiler_summary']['total_operations']}")
    print(f"- Total duration: {report['profiler_summary']['total_duration']:.3f}s")
    print(f"- Operations per second: {report['profiler_summary']['operations_per_second']:.1f}")
    print(f"- Memory usage: {report['memory_usage']['rss_mb']:.2f}MB")
    
    # Show cache statistics
    for cache_name, stats in report['cache_stats'].items():
        print(f"- {cache_name} cache hit rate: {stats['hit_rate']:.2%}")


def demo_optimization_levels():
    """Demonstrate different optimization levels."""
    print("\n" + "="*60)
    print("DEMO 6: Optimization Levels Comparison")
    print("="*60)
    
    def test_operation(data):
        time.sleep(0.02)
        return len(data) * 2
    
    test_data = ["item"] * 50
    
    optimization_levels = [
        OptimizationLevel.NONE,
        OptimizationLevel.BASIC,
        OptimizationLevel.STANDARD,
        OptimizationLevel.AGGRESSIVE
    ]
    
    results = {}
    
    for level in optimization_levels:
        print(f"\nTesting {level.value} optimization...")
        optimizer = PerformanceOptimizer(level)
        
        optimized_op = optimizer.optimize_operation("test_op", test_operation)
        
        start_time = time.time()
        for i in range(5):
            result = optimized_op(test_data)
        duration = time.time() - start_time
        
        results[level] = {
            'duration': duration,
            'cache_count': len(optimizer.caches),
            'report': optimizer.get_optimization_report()
        }
        
        print(f"Duration: {duration:.3f}s")
        print(f"Cache count: {len(optimizer.caches)}")
    
    # Compare results
    print("\nOptimization Level Comparison:")
    print("-" * 50)
    baseline = results[OptimizationLevel.NONE]['duration']
    
    for level, result in results.items():
        improvement = ((baseline - result['duration']) / baseline * 100)
        print(f"{level.value:12}: {result['duration']:.3f}s ({improvement:+.1f}%)")


def main():
    """Run all performance optimization demos."""
    print("SVG-BIM Performance Optimization Demo")
    print("=" * 60)
    print("This demo shows how performance optimization improves SVG-BIM processing")
    print("through caching, batch processing, memory management, and profiling.")
    
    try:
        # Run all demos
        demo_basic_optimization()
        demo_batch_processing()
        demo_memory_optimization()
        demo_decorators()
        demo_svg_bim_integration()
        demo_optimization_levels()
        
        print("\n" + "="*60)
        print("PERFORMANCE OPTIMIZATION DEMO COMPLETE")
        print("="*60)
        print("Key benefits demonstrated:")
        print("- Caching reduces redundant computations")
        print("- Batch processing improves throughput")
        print("- Memory management prevents resource exhaustion")
        print("- Profiling provides performance insights")
        print("- Parallel processing leverages multi-core systems")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    main() 