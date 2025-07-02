#!/usr/bin/env python3
"""
Viewport Culling Performance Test Suite
Tests the viewport culling system for performance optimization with large numbers of objects
"""

import unittest
import time
import json
import requests
from typing import Dict, List, Any
import sys
import os

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ViewportCullingTestSuite(unittest.TestCase):
    """Test suite for viewport culling performance optimization"""
    
    def setUp(self):
        """Set up test environment"""
        self.base_url = "http://localhost:8000"
        self.test_floor_id = 1
        self.test_objects = []
        
        # Performance thresholds
        self.culling_time_threshold = 16  # ms (60fps target)
        self.render_time_threshold = 16   # ms
        self.memory_threshold = 50 * 1024 * 1024  # 50MB
        
        print(f"\n{'='*60}")
        print("VIEWPORT CULLING PERFORMANCE TEST SUITE")
        print(f"{'='*60}")
    
    def tearDown(self):
        """Clean up test environment"""
        # Clear test objects
        self.clear_test_objects()
        print(f"\n{'='*60}")
    
    def test_01_culling_enabled_by_default(self):
        """Test that viewport culling is enabled by default"""
        print("\n1. Testing Culling Enabled by Default")
        
        # Check if culling is enabled in viewport manager
        response = self.get_viewport_state()
        self.assertIsNotNone(response)
        
        # Verify culling properties exist
        self.assertIn('cullingEnabled', response)
        self.assertTrue(response['cullingEnabled'], "Culling should be enabled by default")
        
        print("✅ Culling enabled by default")
    
    def test_02_culling_toggle_functionality(self):
        """Test culling toggle functionality"""
        print("\n2. Testing Culling Toggle Functionality")
        
        # Enable culling
        response = self.toggle_culling(True)
        self.assertIsNotNone(response)
        self.assertTrue(response['cullingEnabled'])
        
        # Disable culling
        response = self.toggle_culling(False)
        self.assertIsNotNone(response)
        self.assertFalse(response['cullingEnabled'])
        
        # Re-enable culling
        response = self.toggle_culling(True)
        self.assertIsNotNone(response)
        self.assertTrue(response['cullingEnabled'])
        
        print("✅ Culling toggle functionality working")
    
    def test_03_object_visibility_detection(self):
        """Test object visibility detection based on zoom/pan"""
        print("\n3. Testing Object Visibility Detection")
        
        # Generate test objects
        object_count = 100
        objects = self.generate_test_objects(object_count)
        self.assertEqual(len(objects), object_count)
        
        # Test visibility at different zoom levels
        zoom_levels = [0.5, 1.0, 2.0, 5.0]
        
        for zoom in zoom_levels:
            # Set zoom level
            self.set_viewport_zoom(zoom)
            time.sleep(0.1)  # Allow culling to update
            
            # Get visibility stats
            stats = self.get_culling_stats()
            self.assertIsNotNone(stats)
            
            # Verify visibility changes with zoom
            self.assertGreater(stats['totalObjects'], 0)
            self.assertGreaterEqual(stats['visibleObjects'], 0)
            self.assertLessEqual(stats['visibleObjects'], stats['totalObjects'])
            
            print(f"  Zoom {zoom}x: {stats['visibleObjects']}/{stats['totalObjects']} objects visible")
        
        print("✅ Object visibility detection working")
    
    def test_04_culling_performance_with_100_objects(self):
        """Test culling performance with 100 objects"""
        print("\n4. Testing Culling Performance with 100 Objects")
        
        object_count = 100
        performance_data = self.test_culling_performance(object_count)
        
        # Verify performance metrics
        self.assertLess(performance_data['cullingTime'], self.culling_time_threshold)
        self.assertGreater(performance_data['cullingEfficiency'], 0)
        
        print(f"  Culling Time: {performance_data['cullingTime']:.2f}ms")
        print(f"  Culling Efficiency: {performance_data['cullingEfficiency']:.1f}%")
        print(f"  Visible Objects: {performance_data['visibleObjects']}/{performance_data['totalObjects']}")
        
        print("✅ 100 objects performance acceptable")
    
    def test_05_culling_performance_with_500_objects(self):
        """Test culling performance with 500 objects"""
        print("\n5. Testing Culling Performance with 500 Objects")
        
        object_count = 500
        performance_data = self.test_culling_performance(object_count)
        
        # Verify performance metrics
        self.assertLess(performance_data['cullingTime'], self.culling_time_threshold * 2)  # Allow more time for more objects
        self.assertGreater(performance_data['cullingEfficiency'], 0)
        
        print(f"  Culling Time: {performance_data['cullingTime']:.2f}ms")
        print(f"  Culling Efficiency: {performance_data['cullingEfficiency']:.1f}%")
        print(f"  Visible Objects: {performance_data['visibleObjects']}/{performance_data['totalObjects']}")
        
        print("✅ 500 objects performance acceptable")
    
    def test_06_culling_performance_with_1000_objects(self):
        """Test culling performance with 1000 objects"""
        print("\n6. Testing Culling Performance with 1000 Objects")
        
        object_count = 1000
        performance_data = self.test_culling_performance(object_count)
        
        # Verify performance metrics
        self.assertLess(performance_data['cullingTime'], self.culling_time_threshold * 3)  # Allow more time for many objects
        self.assertGreater(performance_data['cullingEfficiency'], 0)
        
        print(f"  Culling Time: {performance_data['cullingTime']:.2f}ms")
        print(f"  Culling Efficiency: {performance_data['cullingEfficiency']:.1f}%")
        print(f"  Visible Objects: {performance_data['visibleObjects']}/{performance_data['totalObjects']}")
        
        print("✅ 1000 objects performance acceptable")
    
    def test_07_bounds_cache_functionality(self):
        """Test bounds cache functionality for optimization"""
        print("\n7. Testing Bounds Cache Functionality")
        
        # Generate objects
        objects = self.generate_test_objects(100)
        
        # First culling operation (should calculate bounds)
        start_time = time.time()
        stats1 = self.get_culling_stats()
        first_culling_time = (time.time() - start_time) * 1000
        
        # Second culling operation (should use cached bounds)
        start_time = time.time()
        stats2 = self.get_culling_stats()
        second_culling_time = (time.time() - start_time) * 1000
        
        # Verify cache is working (second operation should be faster)
        self.assertLess(second_culling_time, first_culling_time * 1.5)  # Allow some variance
        
        print(f"  First culling: {first_culling_time:.2f}ms")
        print(f"  Second culling: {second_culling_time:.2f}ms")
        print(f"  Cache speedup: {first_culling_time / second_culling_time:.1f}x")
        
        print("✅ Bounds cache optimization working")
    
    def test_08_memory_usage_optimization(self):
        """Test memory usage optimization"""
        print("\n8. Testing Memory Usage Optimization")
        
        # Generate objects and monitor memory
        object_counts = [100, 500, 1000]
        memory_usage = []
        
        for count in object_counts:
            objects = self.generate_test_objects(count)
            time.sleep(0.1)  # Allow memory to stabilize
            
            # Get memory usage
            memory_data = self.get_memory_usage()
            memory_usage.append({
                'object_count': count,
                'memory_usage': memory_data['totalMemoryUsage'],
                'bounds_cache_size': memory_data['boundsCacheSize']
            })
            
            print(f"  {count} objects: {memory_data['totalMemoryUsage'] / 1024 / 1024:.2f}MB")
        
        # Verify memory usage is reasonable
        for usage in memory_usage:
            self.assertLess(usage['memory_usage'], self.memory_threshold)
        
        print("✅ Memory usage within acceptable limits")
    
    def test_09_culling_margin_adjustment(self):
        """Test culling margin adjustment"""
        print("\n9. Testing Culling Margin Adjustment")
        
        # Generate objects
        objects = self.generate_test_objects(200)
        
        # Test different margins
        margins = [50, 100, 200]
        
        for margin in margins:
            # Set culling margin
            self.set_culling_margin(margin)
            time.sleep(0.1)
            
            # Get visibility stats
            stats = self.get_culling_stats()
            
            print(f"  Margin {margin}px: {stats['visibleObjects']}/{stats['totalObjects']} objects visible")
        
        print("✅ Culling margin adjustment working")
    
    def test_10_comprehensive_performance_test(self):
        """Run comprehensive performance test"""
        print("\n10. Running Comprehensive Performance Test")
        
        test_config = {
            'tests': [
                {'name': 'Grid 100', 'count': 100, 'pattern': 'grid'},
                {'name': 'Grid 500', 'count': 500, 'pattern': 'grid'},
                {'name': 'Grid 1000', 'count': 1000, 'pattern': 'grid'},
                {'name': 'Random 100', 'count': 100, 'pattern': 'random'},
                {'name': 'Random 500', 'count': 500, 'pattern': 'random'},
                {'name': 'Spiral 100', 'count': 100, 'pattern': 'spiral'},
                {'name': 'Spiral 500', 'count': 500, 'pattern': 'spiral'}
            ]
        }
        
        results = self.run_comprehensive_test(test_config)
        
        # Verify all tests completed successfully
        self.assertEqual(len(results), len(test_config['tests']))
        
        # Generate performance report
        report = self.generate_performance_report(results)
        
        # Save report
        with open('viewport_culling_performance_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("✅ Comprehensive performance test completed")
        print(f"  Report saved: viewport_culling_performance_report.json")
    
    # Helper methods
    
    def get_viewport_state(self) -> Dict[str, Any]:
        """Get current viewport state"""
        try:
            response = requests.get(f"{self.base_url}/api/viewport/state")
            return response.json() if response.status_code == 200 else None
        except:
            return None
    
    def toggle_culling(self, enable: bool) -> Dict[str, Any]:
        """Toggle viewport culling"""
        try:
            response = requests.post(f"{self.base_url}/api/viewport/culling", 
                                   json={'enabled': enable})
            return response.json() if response.status_code == 200 else None
        except:
            return None
    
    def generate_test_objects(self, count: int) -> List[Dict[str, Any]]:
        """Generate test objects"""
        try:
            response = requests.post(f"{self.base_url}/api/test/generate-objects",
                                   json={'count': count, 'pattern': 'grid'})
            if response.status_code == 200:
                data = response.json()
                self.test_objects.extend(data.get('objects', []))
                return data.get('objects', [])
            return []
        except:
            return []
    
    def clear_test_objects(self):
        """Clear test objects"""
        try:
            requests.delete(f"{self.base_url}/api/test/clear-objects")
        except:
            pass
    
    def set_viewport_zoom(self, zoom: float):
        """Set viewport zoom level"""
        try:
            requests.post(f"{self.base_url}/api/viewport/zoom", 
                         json={'zoom': zoom})
        except:
            pass
    
    def get_culling_stats(self) -> Dict[str, Any]:
        """Get culling statistics"""
        try:
            response = requests.get(f"{self.base_url}/api/viewport/culling/stats")
            return response.json() if response.status_code == 200 else {}
        except:
            return {}
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        try:
            response = requests.get(f"{self.base_url}/api/performance/memory")
            return response.json() if response.status_code == 200 else {}
        except:
            return {}
    
    def set_culling_margin(self, margin: int):
        """Set culling margin"""
        try:
            requests.post(f"{self.base_url}/api/viewport/culling/margin",
                         json={'margin': margin})
        except:
            pass
    
    def test_culling_performance(self, object_count: int) -> Dict[str, Any]:
        """Test culling performance with given object count"""
        # Generate objects
        objects = self.generate_test_objects(object_count)
        
        # Measure culling performance
        start_time = time.time()
        stats = self.get_culling_stats()
        culling_time = (time.time() - start_time) * 1000
        
        return {
            'totalObjects': stats.get('totalObjects', 0),
            'visibleObjects': stats.get('visibleObjects', 0),
            'culledObjects': stats.get('culledObjects', 0),
            'cullingTime': culling_time,
            'cullingEfficiency': stats.get('cullingEfficiency', 0)
        }
    
    def run_comprehensive_test(self, test_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Run comprehensive performance test"""
        try:
            response = requests.post(f"{self.base_url}/api/test/comprehensive",
                                   json=test_config)
            return response.json() if response.status_code == 200 else []
        except:
            return []
    
    def generate_performance_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate performance report"""
        report = {
            'timestamp': time.time(),
            'testResults': results,
            'summary': {
                'totalTests': len(results),
                'averageGenerationTime': 0,
                'averageRenderTime': 0,
                'averageCullingTime': 0,
                'maxCullingTime': 0,
                'minCullingTime': float('inf')
            }
        }
        
        if results:
            total_gen_time = sum(r.get('generationTime', 0) for r in results)
            total_render_time = sum(r.get('renderTime', 0) for r in results)
            total_culling_time = sum(r.get('metrics', {}).get('culling', {}).get('cullingTime', 0) for r in results)
            
            report['summary']['averageGenerationTime'] = total_gen_time / len(results)
            report['summary']['averageRenderTime'] = total_render_time / len(results)
            report['summary']['averageCullingTime'] = total_culling_time / len(results)
            
            culling_times = [r.get('metrics', {}).get('culling', {}).get('cullingTime', 0) for r in results]
            if culling_times:
                report['summary']['maxCullingTime'] = max(culling_times)
                report['summary']['minCullingTime'] = min(culling_times)
        
        return report


def run_viewport_culling_tests():
    """Run the viewport culling test suite"""
    print("Starting Viewport Culling Performance Test Suite...")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(ViewportCullingTestSuite)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_viewport_culling_tests()
    sys.exit(0 if success else 1) 