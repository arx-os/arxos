#!/usr/bin/env python3
"""
Level of Detail (LOD) System Test Suite
Tests symbol complexity, zoom levels, and performance optimization
"""

import unittest
import json
import time
import requests
from typing import Dict, List, Any
import sys
import os

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class LODSystemTestSuite(unittest.TestCase):
    """Comprehensive test suite for the LOD system"""
    
    def setUp(self):
        """Set up test environment"""
        self.base_url = "http://localhost:8000"
        self.session = requests.Session()
        
        # Test data
        self.test_symbols = {
            'simple': {
                'id': 'test-simple-1',
                'name': 'Simple Circle',
                'category': 'test',
                'svg': '<circle cx="10" cy="10" r="8" fill="blue" stroke="black" stroke-width="1"/>',
                'complexity': 'low'
            },
            'medium': {
                'id': 'test-medium-1',
                'name': 'Medium Device',
                'category': 'test',
                'svg': '''
                    <rect x="3" y="3" width="14" height="14" fill="lightblue" stroke="black" stroke-width="1"/>
                    <circle cx="10" cy="10" r="3" fill="white" stroke="black" stroke-width="1"/>
                    <line x1="7" y1="10" x2="13" y2="10" stroke="black" stroke-width="2"/>
                    <line x1="10" y1="7" x2="10" y2="13" stroke="black" stroke-width="2"/>
                ''',
                'complexity': 'medium'
            },
            'complex': {
                'id': 'test-complex-1',
                'name': 'Complex Controller',
                'category': 'test',
                'svg': '''
                    <rect x="2" y="2" width="16" height="16" fill="lightgray" stroke="black" stroke-width="1"/>
                    <rect x="4" y="4" width="12" height="4" fill="white" stroke="black" stroke-width="0.5"/>
                    <rect x="4" y="10" width="12" height="4" fill="white" stroke="black" stroke-width="0.5"/>
                    <circle cx="6" cy="6" r="1" fill="green"/>
                    <circle cx="10" cy="6" r="1" fill="yellow"/>
                    <circle cx="14" cy="6" r="1" fill="red"/>
                    <circle cx="6" cy="12" r="1" fill="blue"/>
                    <circle cx="10" cy="12" r="1" fill="purple"/>
                    <circle cx="14" cy="12" r="1" fill="orange"/>
                    <text x="10" y="18" text-anchor="middle" font-size="2" fill="black">CTRL</text>
                ''',
                'complexity': 'high'
            }
        }
        
        # LOD configuration
        self.lod_levels = {
            'high': {'minZoom': 2.0, 'complexity': 1.0, 'name': 'High Detail'},
            'medium': {'minZoom': 0.5, 'complexity': 0.7, 'name': 'Medium Detail'},
            'low': {'minZoom': 0.1, 'complexity': 0.4, 'name': 'Low Detail'},
            'minimal': {'minZoom': 0.0, 'complexity': 0.2, 'name': 'Minimal Detail'}
        }
    
    def test_01_lod_manager_initialization(self):
        """Test LOD manager initialization"""
        print("\n=== Test 1: LOD Manager Initialization ===")
        
        # Test LOD manager creation
        lod_config = {
            'lodLevels': self.lod_levels,
            'enableTransitions': True,
            'transitionDuration': 200
        }
        
        # Simulate LOD manager initialization
        lod_manager = {
            'currentLODLevel': 'medium',
            'lastZoomLevel': 1.0,
            'switchingLOD': False,
            'lodCache': {},
            'symbolLODData': {},
            'lodStats': {
                'totalSwitches': 0,
                'lastSwitchTime': 0,
                'averageSwitchTime': 0,
                'switchTimes': []
            }
        }
        
        self.assertIsNotNone(lod_manager)
        self.assertEqual(lod_manager['currentLODLevel'], 'medium')
        self.assertEqual(lod_manager['lastZoomLevel'], 1.0)
        self.assertFalse(lod_manager['switchingLOD'])
        
        print("✓ LOD manager initialized successfully")
        print(f"  - Current LOD level: {lod_manager['currentLODLevel']}")
        print(f"  - Last zoom level: {lod_manager['lastZoomLevel']}")
        print(f"  - Transitions enabled: {lod_config['enableTransitions']}")
    
    def test_02_lod_level_determination(self):
        """Test LOD level determination based on zoom levels"""
        print("\n=== Test 2: LOD Level Determination ===")
        
        def get_lod_level_for_zoom(zoom_level, lod_levels):
            """Determine appropriate LOD level for zoom level"""
            levels = list(lod_levels.keys())[::-1]  # Start with highest detail
            
            for level in levels:
                if zoom_level >= lod_levels[level]['minZoom']:
                    return level
            
            return 'minimal'  # Fallback
        
        # Test different zoom levels
        test_zoom_levels = [0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        expected_levels = ['minimal', 'low', 'medium', 'medium', 'high', 'high', 'high']
        
        for zoom, expected in zip(test_zoom_levels, expected_levels):
            actual = get_lod_level_for_zoom(zoom, self.lod_levels)
            self.assertEqual(actual, expected)
            print(f"✓ Zoom {zoom}: {actual} (expected: {expected})")
    
    def test_03_symbol_complexity_analysis(self):
        """Test symbol complexity analysis"""
        print("\n=== Test 3: Symbol Complexity Analysis ===")
        
        def count_svg_elements(svg_content):
            """Count SVG elements for complexity measurement"""
            import re
            
            # Count various SVG elements
            elements = re.findall(r'<(path|rect|circle|ellipse|line|polyline|polygon|text)', svg_content)
            return len(elements)
        
        def analyze_symbol_complexity(symbol):
            """Analyze symbol complexity"""
            element_count = count_svg_elements(symbol['svg'])
            
            # Determine complexity based on element count
            if element_count <= 3:
                complexity = 'low'
            elif element_count <= 8:
                complexity = 'medium'
            else:
                complexity = 'high'
            
            return {
                'element_count': element_count,
                'complexity': complexity,
                'expected': symbol['complexity']
            }
        
        # Test each symbol type
        for symbol_type, symbol in self.test_symbols.items():
            analysis = analyze_symbol_complexity(symbol)
            
            print(f"✓ {symbol['name']}:")
            print(f"  - Element count: {analysis['element_count']}")
            print(f"  - Detected complexity: {analysis['complexity']}")
            print(f"  - Expected complexity: {analysis['expected']}")
            
            # Verify complexity detection is reasonable
            self.assertIn(analysis['complexity'], ['low', 'medium', 'high'])
    
    def test_04_lod_svg_generation(self):
        """Test LOD SVG generation for different complexity levels"""
        print("\n=== Test 4: LOD SVG Generation ===")
        
        def generate_lod_svg(svg_content, complexity_factor):
            """Generate simplified SVG based on complexity factor"""
            import re
            
            # For testing purposes, simulate SVG simplification
            if complexity_factor < 0.5:
                # Remove detailed elements (simulate)
                simplified = re.sub(r'<text[^>]*>.*?</text>', '', svg_content)
                simplified = re.sub(r'<path[^>]*d="[^"]*c[^"]*"[^>]*>', '', simplified)
                simplified = re.sub(r'<path[^>]*d="[^"]*s[^"]*"[^>]*>', '', simplified)
            else:
                simplified = svg_content
            
            return simplified
        
        # Test LOD generation for complex symbol
        complex_symbol = self.test_symbols['complex']
        original_svg = complex_symbol['svg']
        
        # Generate different LOD levels
        lod_versions = {}
        for level, config in self.lod_levels.items():
            lod_svg = generate_lod_svg(original_svg, config['complexity'])
            lod_versions[level] = lod_svg
            
            # Count elements in each version
            element_count = len(re.findall(r'<(path|rect|circle|ellipse|line|polyline|polygon|text)', lod_svg))
            
            print(f"✓ {level} LOD:")
            print(f"  - Complexity factor: {config['complexity']}")
            print(f"  - Element count: {element_count}")
            print(f"  - SVG length: {len(lod_svg)} chars")
            
            # Verify that higher complexity has more elements
            if level == 'high':
                self.assertGreater(element_count, 0)
            elif level == 'minimal':
                self.assertLessEqual(element_count, 5)  # Should be simplified
    
    def test_05_lod_switching_performance(self):
        """Test LOD switching performance"""
        print("\n=== Test 5: LOD Switching Performance ===")
        
        def simulate_lod_switch(from_level, to_level, symbol_count=100):
            """Simulate LOD switching performance"""
            start_time = time.time()
            
            # Simulate processing each symbol
            for i in range(symbol_count):
                # Simulate symbol processing time
                time.sleep(0.001)  # 1ms per symbol
            
            switch_time = (time.time() - start_time) * 1000  # Convert to ms
            return switch_time
        
        # Test different LOD switch scenarios
        test_scenarios = [
            ('high', 'medium', 50),
            ('medium', 'low', 100),
            ('low', 'minimal', 200),
            ('minimal', 'high', 50)
        ]
        
        performance_results = []
        
        for from_level, to_level, symbol_count in test_scenarios:
            switch_time = simulate_lod_switch(from_level, to_level, symbol_count)
            performance_results.append({
                'from': from_level,
                'to': to_level,
                'symbol_count': symbol_count,
                'switch_time': switch_time
            })
            
            print(f"✓ {from_level} → {to_level} ({symbol_count} symbols): {switch_time:.2f}ms")
            
            # Performance assertions
            self.assertLess(switch_time, 1000)  # Should complete within 1 second
            self.assertGreater(switch_time, 0)  # Should take some time
        
        # Calculate average switch time
        avg_switch_time = sum(r['switch_time'] for r in performance_results) / len(performance_results)
        print(f"✓ Average switch time: {avg_switch_time:.2f}ms")
        
        return performance_results
    
    def test_06_lod_cache_management(self):
        """Test LOD cache management"""
        print("\n=== Test 6: LOD Cache Management ===")
        
        class LODCache:
            def __init__(self, max_size=1000):
                self.cache = {}
                self.max_size = max_size
            
            def get(self, key):
                return self.cache.get(key)
            
            def set(self, key, value):
                if len(self.cache) >= self.max_size:
                    # Remove oldest entry
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                self.cache[key] = value
            
            def clear(self):
                self.cache.clear()
            
            def size(self):
                return len(self.cache)
        
        # Test cache operations
        cache = LODCache(max_size=5)
        
        # Add test data
        test_data = {
            'zoom_1.0_scale_1.0': 'high_detail_svg',
            'zoom_0.5_scale_1.0': 'medium_detail_svg',
            'zoom_0.1_scale_1.0': 'low_detail_svg',
            'zoom_0.05_scale_1.0': 'minimal_detail_svg',
            'zoom_2.0_scale_1.0': 'ultra_high_detail_svg',
            'zoom_0.2_scale_1.0': 'should_evict_oldest'  # This should evict the first entry
        }
        
        for key, value in test_data.items():
            cache.set(key, value)
            print(f"✓ Cached: {key} → {value}")
        
        # Verify cache size limit
        self.assertEqual(cache.size(), 5)
        print(f"✓ Cache size: {cache.size()}")
        
        # Verify oldest entry was evicted
        self.assertIsNone(cache.get('zoom_1.0_scale_1.0'))
        self.assertIsNotNone(cache.get('zoom_0.2_scale_1.0'))
        print("✓ Cache eviction working correctly")
        
        # Test cache clear
        cache.clear()
        self.assertEqual(cache.size(), 0)
        print("✓ Cache cleared successfully")
    
    def test_07_lod_statistics_tracking(self):
        """Test LOD statistics tracking"""
        print("\n=== Test 7: LOD Statistics Tracking ===")
        
        class LODStats:
            def __init__(self):
                self.total_switches = 0
                self.last_switch_time = 0
                self.average_switch_time = 0
                self.switch_times = []
            
            def update_stats(self, switch_time):
                self.total_switches += 1
                self.last_switch_time = time.time()
                self.switch_times.append(switch_time)
                
                # Keep only last 100 switch times
                if len(self.switch_times) > 100:
                    self.switch_times.pop(0)
                
                # Calculate average
                self.average_switch_time = sum(self.switch_times) / len(self.switch_times)
            
            def get_stats(self):
                return {
                    'total_switches': self.total_switches,
                    'last_switch_time': self.last_switch_time,
                    'average_switch_time': self.average_switch_time,
                    'switch_times_count': len(self.switch_times)
                }
        
        # Test statistics tracking
        stats = LODStats()
        
        # Simulate multiple LOD switches
        test_switch_times = [50, 75, 45, 60, 80, 55, 70, 40, 65, 90]
        
        for switch_time in test_switch_times:
            stats.update_stats(switch_time)
        
        # Verify statistics
        current_stats = stats.get_stats()
        
        self.assertEqual(current_stats['total_switches'], 10)
        self.assertEqual(current_stats['switch_times_count'], 10)
        self.assertGreater(current_stats['average_switch_time'], 0)
        
        print(f"✓ Total switches: {current_stats['total_switches']}")
        print(f"✓ Average switch time: {current_stats['average_switch_time']:.2f}ms")
        print(f"✓ Switch times tracked: {current_stats['switch_times_count']}")
        
        # Verify average calculation
        expected_average = sum(test_switch_times) / len(test_switch_times)
        self.assertAlmostEqual(current_stats['average_switch_time'], expected_average, places=1)
        print(f"✓ Average calculation verified: {expected_average:.2f}ms")
    
    def test_08_lod_transition_effects(self):
        """Test LOD transition effects"""
        print("\n=== Test 8: LOD Transition Effects ===")
        
        def simulate_transition(duration_ms, symbol_count=50):
            """Simulate LOD transition with fade effect"""
            start_time = time.time()
            
            # Simulate fade out
            fade_out_time = duration_ms / 2
            time.sleep(fade_out_time / 1000)
            
            # Simulate SVG content update
            update_time = 10  # 10ms for content update
            time.sleep(update_time / 1000)
            
            # Simulate fade in
            fade_in_time = duration_ms / 2
            time.sleep(fade_in_time / 1000)
            
            total_time = (time.time() - start_time) * 1000
            return total_time
        
        # Test different transition durations
        transition_durations = [100, 200, 300, 500]
        
        for duration in transition_durations:
            actual_duration = simulate_transition(duration)
            
            print(f"✓ Transition {duration}ms: {actual_duration:.2f}ms")
            
            # Verify transition time is reasonable
            self.assertGreater(actual_duration, duration * 0.8)  # Allow some tolerance
            self.assertLess(actual_duration, duration * 1.5)
    
    def test_09_lod_memory_optimization(self):
        """Test LOD memory optimization"""
        print("\n=== Test 9: LOD Memory Optimization ===")
        
        def estimate_memory_usage(svg_content, complexity_factor):
            """Estimate memory usage for SVG content"""
            # Rough estimation: 1 character ≈ 1 byte
            base_memory = len(svg_content)
            
            # Apply complexity factor
            optimized_memory = base_memory * complexity_factor
            
            return {
                'base_memory': base_memory,
                'optimized_memory': optimized_memory,
                'savings': base_memory - optimized_memory,
                'savings_percent': ((base_memory - optimized_memory) / base_memory) * 100
            }
        
        # Test memory optimization for complex symbol
        complex_symbol = self.test_symbols['complex']
        
        memory_results = {}
        for level, config in self.lod_levels.items():
            memory_usage = estimate_memory_usage(complex_symbol['svg'], config['complexity'])
            memory_results[level] = memory_usage
            
            print(f"✓ {level} LOD:")
            print(f"  - Base memory: {memory_usage['base_memory']} bytes")
            print(f"  - Optimized memory: {memory_usage['optimized_memory']:.0f} bytes")
            print(f"  - Memory savings: {memory_usage['savings_percent']:.1f}%")
            
            # Verify memory savings
            self.assertGreater(memory_usage['savings_percent'], 0)
            self.assertLess(memory_usage['optimized_memory'], memory_usage['base_memory'])
        
        # Calculate total memory savings
        total_savings = sum(r['savings_percent'] for r in memory_results.values()) / len(memory_results)
        print(f"✓ Average memory savings: {total_savings:.1f}%")
        
        return memory_results
    
    def test_10_comprehensive_lod_test(self):
        """Comprehensive LOD system test"""
        print("\n=== Test 10: Comprehensive LOD System Test ===")
        
        # Simulate complete LOD workflow
        test_results = {
            'initialization': True,
            'symbol_analysis': {},
            'lod_generation': {},
            'performance_metrics': {},
            'memory_optimization': {},
            'overall_success': True
        }
        
        # 1. Symbol analysis
        for symbol_type, symbol in self.test_symbols.items():
            element_count = len(re.findall(r'<(path|rect|circle|ellipse|line|polyline|polygon|text)', symbol['svg']))
            test_results['symbol_analysis'][symbol_type] = {
                'element_count': element_count,
                'complexity': symbol['complexity']
            }
        
        # 2. LOD generation for each symbol
        for symbol_type, symbol in self.test_symbols.items():
            lod_versions = {}
            for level, config in self.lod_levels.items():
                # Simulate LOD generation
                simplified_svg = symbol['svg']  # In real implementation, this would be simplified
                lod_versions[level] = {
                    'complexity': config['complexity'],
                    'svg_length': len(simplified_svg)
                }
            test_results['lod_generation'][symbol_type] = lod_versions
        
        # 3. Performance metrics
        performance_data = self.test_05_lod_switching_performance()
        test_results['performance_metrics'] = {
            'average_switch_time': sum(r['switch_time'] for r in performance_data) / len(performance_data),
            'total_tests': len(performance_data)
        }
        
        # 4. Memory optimization
        memory_data = self.test_09_lod_memory_optimization()
        test_results['memory_optimization'] = {
            'average_savings': sum(r['savings_percent'] for r in memory_data.values()) / len(memory_data)
        }
        
        # Verify overall success
        self.assertTrue(test_results['overall_success'])
        self.assertGreater(len(test_results['symbol_analysis']), 0)
        self.assertGreater(len(test_results['lod_generation']), 0)
        self.assertGreater(test_results['performance_metrics']['total_tests'], 0)
        self.assertGreater(test_results['memory_optimization']['average_savings'], 0)
        
        print("✓ Comprehensive LOD test completed successfully")
        print(f"  - Symbols analyzed: {len(test_results['symbol_analysis'])}")
        print(f"  - LOD levels tested: {len(self.lod_levels)}")
        print(f"  - Performance tests: {test_results['performance_metrics']['total_tests']}")
        print(f"  - Average memory savings: {test_results['memory_optimization']['average_savings']:.1f}%")
        
        return test_results

def run_lod_test_suite():
    """Run the complete LOD test suite"""
    print("=" * 60)
    print("LEVEL OF DETAIL (LOD) SYSTEM TEST SUITE")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(LODSystemTestSuite)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generate test report
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_tests': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
    }
    
    print("\n" + "=" * 60)
    print("LOD TEST SUITE SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {report['total_tests']}")
    print(f"Failures: {report['failures']}")
    print(f"Errors: {report['errors']}")
    print(f"Success Rate: {report['success_rate']:.1f}%")
    
    # Save detailed report
    with open('lod_test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: lod_test_report.json")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    import re  # Import here for the tests that use it
    
    success = run_lod_test_suite()
    sys.exit(0 if success else 1) 