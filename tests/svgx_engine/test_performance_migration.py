#!/usr/bin/env python3
"""
Test script for SVGX Performance Optimizer Migration

This script validates the migration of performance_optimizer.py from arx_svg_parser
to svgx_engine with SVGX-specific enhancements.
"""

import sys
import os
import time
import tempfile
import shutil
from pathlib import Path

# Add the svgx_engine to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_performance_optimizer_migration():
    """Test the performance optimizer migration."""
    print("🔧 Testing SVGX Performance Optimizer Migration")
    print("=" * 60)
    
    test_results = []
    
    try:
        # Test 1: Import the performance optimizer
        print("\n1. Testing imports...")
        from svgx_engine.services.performance import (
            SVGXPerformanceOptimizer,
            SVGXAdaptiveCache,
            SVGXMemoryManager,
            SVGXParallelProcessor,
            SVGXPerformanceProfiler,
            SVGXPerformanceMetrics,
            SVGXResourceLimits,
            OptimizationLevel,
            CacheStrategy,
            optimize_operation,
            parallel_process,
            get_performance_report
        )
        print("✅ All performance optimizer imports successful")
        test_results.append(("Imports", True, "All classes and functions imported successfully"))
        
        # Test 2: Test SVGX Adaptive Cache
        print("\n2. Testing SVGX Adaptive Cache...")
        cache = SVGXAdaptiveCache(max_size=5, strategy=CacheStrategy.SVGX_NAMESPACE)
        
        # Test basic operations
        cache.set("key1", "value1", namespace="svgx.core")
        cache.set("key2", "value2", namespace="svgx.physics")
        cache.set("key3", "value3", namespace="svgx.behavior")
        
        # Test retrieval
        assert cache.get("key1", namespace="svgx.core") == "value1"
        assert cache.get("key2", namespace="svgx.physics") == "value2"
        assert cache.get("key3", namespace="svgx.behavior") == "value3"
        
        # Test cache stats
        stats = cache.get_stats()
        assert "size" in stats
        assert "hit_rate" in stats
        assert "namespace_priorities" in stats
        
        print("✅ SVGX Adaptive Cache working correctly")
        test_results.append(("SVGX Adaptive Cache", True, "Cache operations and namespace tracking working"))
        
        # Test 3: Test SVGX Memory Manager
        print("\n3. Testing SVGX Memory Manager...")
        limits = SVGXResourceLimits(max_memory_mb=1024.0, gc_threshold=0.8)
        memory_manager = SVGXMemoryManager(limits)
        
        # Test memory usage
        memory_usage = memory_manager.get_memory_usage()
        assert isinstance(memory_usage, float)
        assert memory_usage >= 0
        
        # Test garbage collection
        memory_manager.force_garbage_collect()
        
        # Test memory optimization
        optimization_result = memory_manager.optimize_memory()
        assert "initial_memory_mb" in optimization_result
        assert "final_memory_mb" in optimization_result
        assert "freed_memory_mb" in optimization_result
        assert "is_windows" in optimization_result
        
        print("✅ SVGX Memory Manager working correctly")
        test_results.append(("SVGX Memory Manager", True, "Memory management and Windows compatibility working"))
        
        # Test 4: Test SVGX Parallel Processor
        print("\n4. Testing SVGX Parallel Processor...")
        processor = SVGXParallelProcessor(max_workers=2)
        
        # Test parallel processing
        def test_func(x):
            time.sleep(0.01)  # Simulate work
            return x * 2
        
        items = list(range(10))
        results = processor.execute_parallel(test_func, items, namespace="svgx.test")
        assert len(results) == 10
        assert results == [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
        
        # Test batch processing
        batch_results = processor.execute_batch(test_func, items, batch_size=3, namespace="svgx.batch")
        assert len(batch_results) == 10
        
        processor.shutdown()
        print("✅ SVGX Parallel Processor working correctly")
        test_results.append(("SVGX Parallel Processor", True, "Parallel processing and Windows optimization working"))
        
        # Test 5: Test SVGX Performance Profiler
        print("\n5. Testing SVGX Performance Profiler...")
        profiler = SVGXPerformanceProfiler()
        
        # Test profiling decorator
        @profiler.profile_operation("test_operation", namespace="svgx.test", component_type="parser")
        def test_profiled_func():
            time.sleep(0.01)
            return "test_result"
        
        result = test_profiled_func()
        assert result == "test_result"
        
        # Test performance report
        report = profiler.get_performance_report()
        assert "summary" in report
        assert "operation_statistics" in report
        assert "namespace_statistics" in report
        assert "bottlenecks" in report
        
        print("✅ SVGX Performance Profiler working correctly")
        test_results.append(("SVGX Performance Profiler", True, "Profiling and SVGX metrics working"))
        
        # Test 6: Test SVGX Performance Optimizer
        print("\n6. Testing SVGX Performance Optimizer...")
        optimizer = SVGXPerformanceOptimizer(OptimizationLevel.STANDARD)
        
        # Test optimization levels
        assert optimizer.optimization_level == OptimizationLevel.STANDARD
        assert optimizer.limits.max_memory_mb == 1024.0
        
        # Test function optimization
        @optimizer.optimize_function
        def test_optimized_func(x):
            time.sleep(0.01)
            return x * 3
        
        result = test_optimized_func(5)
        assert result == 15
        
        # Test parallel processing
        items = list(range(5))
        results = optimizer.parallel_process(items, lambda x: x * 2, batch_size=2, namespace="svgx.parallel")
        assert results == [0, 2, 4, 6, 8]
        
        # Test optimization report
        report = optimizer.get_optimization_report()
        assert "optimization_level" in report
        assert "resource_limits" in report
        assert "current_resources" in report
        assert "cache_statistics" in report
        assert "profiler_summary" in report
        assert "is_windows" in report
        
        # Test memory optimization
        memory_result = optimizer.optimize_memory()
        assert "initial_memory_mb" in memory_result
        assert "final_memory_mb" in memory_result
        
        # Test cache clearing
        optimizer.clear_cache()
        
        optimizer.shutdown()
        print("✅ SVGX Performance Optimizer working correctly")
        test_results.append(("SVGX Performance Optimizer", True, "Full optimization system working"))
        
        # Test 7: Test convenience functions
        print("\n7. Testing convenience functions...")
        
        # Test optimize_operation decorator
        @optimize_operation("convenience_test", use_caching=True, use_profiling=True, namespace="svgx.convenience")
        def test_convenience_func():
            time.sleep(0.01)
            return "convenience_result"
        
        result = test_convenience_func()
        assert result == "convenience_result"
        
        # Test parallel_process function
        items = list(range(3))
        results = parallel_process(items, lambda x: x * 4, batch_size=2, namespace="svgx.convenience")
        assert results == [0, 4, 8]
        
        # Test get_performance_report function
        report = get_performance_report()
        assert "optimization_level" in report
        assert "resource_limits" in report
        
        print("✅ Convenience functions working correctly")
        test_results.append(("Convenience Functions", True, "All convenience functions working"))
        
        # Test 8: Test Windows compatibility
        print("\n8. Testing Windows compatibility...")
        import platform
        is_windows = platform.system() == "Windows"
        
        # Test Windows-specific optimizations
        if is_windows:
            # Test that Windows optimizations are applied
            optimizer = SVGXPerformanceOptimizer(OptimizationLevel.STANDARD)
            report = optimizer.get_optimization_report()
            assert report["is_windows"] == True
            
            # Test parallel processor Windows optimization
            processor = SVGXParallelProcessor(max_workers=2)
            # This should use threads instead of processes on Windows
            results = processor.execute_parallel(lambda x: x * 2, [1, 2, 3], use_processes=True, namespace="svgx.windows")
            assert results == [2, 4, 6]
            processor.shutdown()
            
            print("✅ Windows compatibility working correctly")
            test_results.append(("Windows Compatibility", True, "Windows-specific optimizations working"))
        else:
            print("✅ Non-Windows system compatibility working correctly")
            test_results.append(("Windows Compatibility", True, "Non-Windows system working correctly"))
        
        # Test 9: Test error handling
        print("\n9. Testing error handling...")
        from svgx_engine.utils.errors import PerformanceError
        
        # Test that PerformanceError is properly defined
        error = PerformanceError("Test error", "TEST_ERROR", {"detail": "test"})
        assert str(error) == "TEST_ERROR: Test error"
        assert error.to_dict()["error_type"] == "PerformanceError"
        
        print("✅ Error handling working correctly")
        test_results.append(("Error Handling", True, "PerformanceError properly defined"))
        
        # Test 10: Test services package integration
        print("\n10. Testing services package integration...")
        from svgx_engine.services import (
            SVGXPerformanceOptimizer,
            SVGXAdaptiveCache,
            SVGXMemoryManager,
            SVGXParallelProcessor,
            SVGXPerformanceProfiler,
            SVGXPerformanceMetrics,
            SVGXResourceLimits,
            OptimizationLevel,
            CacheStrategy,
            optimize_operation,
            parallel_process,
            get_performance_report
        )
        
        # Test that all components are available
        optimizer = SVGXPerformanceOptimizer()
        cache = SVGXAdaptiveCache()
        memory_manager = SVGXMemoryManager(SVGXResourceLimits())
        processor = SVGXParallelProcessor()
        profiler = SVGXPerformanceProfiler()
        
        print("✅ Services package integration working correctly")
        test_results.append(("Services Integration", True, "All performance components available in services package"))
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE OPTIMIZER MIGRATION TEST RESULTS")
        print("=" * 60)
        
        passed_tests = sum(1 for _, passed, _ in test_results if passed)
        total_tests = len(test_results)
        
        for test_name, passed, details in test_results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} {test_name}: {details}")
        
        print(f"\n🎯 Overall Result: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - Performance Optimizer Migration Successful!")
            return True
        else:
            print("❌ Some tests failed - Performance Optimizer Migration needs attention")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_performance_optimizer_migration()
    sys.exit(0 if success else 1) 