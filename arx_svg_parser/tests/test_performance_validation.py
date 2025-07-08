#!/usr/bin/env python3
"""
Performance Validation Tests for Arxos Platform
Tests viewport manager performance under various load conditions
"""

import unittest
import time
import psutil
import os
import gc
import threading
import concurrent.futures
from unittest.mock import Mock, patch, MagicMock
import statistics
import json
from pathlib import Path

# Import the actual viewport manager for performance testing
try:
    from services.viewport_manager import ViewportManager
    HAS_VIEWPORT_MANAGER = True
except ImportError:
    HAS_VIEWPORT_MANAGER = False
    print("Warning: ViewportManager not found, using mock for performance tests")

# Mock viewport manager for testing if real one not available
class MockViewportManager:
    def __init__(self):
        self.currentZoom = 1.0
        self.panX = 0
        self.panY = 0
        self.minZoom = 0.1
        self.maxZoom = 5.0
        self.zoomHistory = []
        self.eventHandlers = {}
        self.scaleFactors = {'x': 1.0, 'y': 1.0}
        
    def screenToSVG(self, screenX, screenY):
        return (screenX - self.panX) / self.currentZoom, (screenY - self.panY) / self.currentZoom
    
    def svgToScreen(self, svgX, svgY):
        return svgX * self.currentZoom + self.panX, svgY * self.currentZoom + self.panY
    
    def setZoom(self, zoom):
        self.currentZoom = max(self.minZoom, min(zoom, self.maxZoom))
        self.saveZoomState()
        self.triggerEvent('zoomChanged', {'zoom': self.currentZoom})
    
    def setPan(self, x, y):
        self.panX = x
        self.panY = y
        self.saveZoomState()
        self.triggerEvent('panChanged', {'panX': x, 'panY': y})
    
    def saveZoomState(self):
        state = {'zoom': self.currentZoom, 'panX': self.panX, 'panY': self.panY}
        self.zoomHistory.append(state)
        if len(self.zoomHistory) > 50:
            self.zoomHistory.pop(0)
    
    def addEventListener(self, event, handler):
        if event not in self.eventHandlers:
            self.eventHandlers[event] = []
        self.eventHandlers[event].append(handler)
    
    def triggerEvent(self, event, data=None):
        if event in self.eventHandlers:
            for handler in self.eventHandlers[event]:
                handler(data or {})

class PerformanceMetrics:
    """Helper class for collecting and analyzing performance metrics"""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = None
        self.start_memory = None
    
    def start_measurement(self, test_name):
        """Start measuring performance for a test"""
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.metrics[test_name] = {
            'start_time': self.start_time,
            'start_memory': self.start_memory,
            'operations': [],
            'memory_samples': []
        }
    
    def record_operation(self, test_name, operation_name, duration):
        """Record an operation duration"""
        if test_name in self.metrics:
            self.metrics[test_name]['operations'].append({
                'name': operation_name,
                'duration': duration
            })
    
    def record_memory_sample(self, test_name):
        """Record current memory usage"""
        if test_name in self.metrics:
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            self.metrics[test_name]['memory_samples'].append(current_memory)
    
    def end_measurement(self, test_name):
        """End measurement and calculate statistics"""
        if test_name in self.metrics:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            total_time = end_time - self.start_time
            memory_delta = end_memory - self.start_memory
            
            # Calculate operation statistics
            operation_durations = [op['duration'] for op in self.metrics[test_name]['operations']]
            
            stats = {
                'total_time': total_time,
                'total_operations': len(operation_durations),
                'avg_operation_time': statistics.mean(operation_durations) if operation_durations else 0,
                'min_operation_time': min(operation_durations) if operation_durations else 0,
                'max_operation_time': max(operation_durations) if operation_durations else 0,
                'memory_start': self.start_memory,
                'memory_end': end_memory,
                'memory_delta': memory_delta,
                'memory_peak': max(self.metrics[test_name]['memory_samples']) if self.metrics[test_name]['memory_samples'] else 0,
                'operations_per_second': len(operation_durations) / total_time if total_time > 0 else 0
            }
            
            self.metrics[test_name]['stats'] = stats
            return stats
    
    def save_metrics(self, filename='performance_metrics.json'):
        """Save metrics to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.metrics, f, indent=2, default=str)
    
    def print_summary(self, test_name):
        """Print performance summary for a test"""
        if test_name in self.metrics and 'stats' in self.metrics[test_name]:
            stats = self.metrics[test_name]['stats']
            print(f"\n=== Performance Summary for {test_name} ===")
            print(f"Total Time: {stats['total_time']:.3f}s")
            print(f"Total Operations: {stats['total_operations']}")
            print(f"Operations/Second: {stats['operations_per_second']:.2f}")
            print(f"Avg Operation Time: {stats['avg_operation_time']*1000:.3f}ms")
            print(f"Min Operation Time: {stats['min_operation_time']*1000:.3f}ms")
            print(f"Max Operation Time: {stats['max_operation_time']*1000:.3f}ms")
            print(f"Memory Start: {stats['memory_start']:.2f}MB")
            print(f"Memory End: {stats['memory_end']:.2f}MB")
            print(f"Memory Delta: {stats['memory_delta']:.2f}MB")
            print(f"Memory Peak: {stats['memory_peak']:.2f}MB")

class TestViewportPerformance(unittest.TestCase):
    """Performance tests for viewport manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.metrics = PerformanceMetrics()
        
        # Use real viewport manager if available, otherwise use mock
        if HAS_VIEWPORT_MANAGER:
            self.viewport = ViewportManager()
        else:
            self.viewport = MockViewportManager()
        
        # Performance thresholds (adjust based on your requirements)
        self.thresholds = {
            'max_operation_time_ms': 16.67,  # 60 FPS = 16.67ms per frame
            'max_memory_delta_mb': 50,       # 50MB memory increase
            'min_operations_per_second': 100, # 100 operations per second
            'max_coordinate_conversion_time_ms': 1.0  # 1ms for coordinate conversion
        }
    
    def tearDown(self):
        """Clean up after tests"""
        # Force garbage collection
        gc.collect()
    
    def test_high_frequency_zoom_operations(self):
        """Test viewport manager performance under high-frequency zoom operations"""
        test_name = 'high_frequency_zoom'
        self.metrics.start_measurement(test_name)
        
        # Perform rapid zoom operations
        zoom_levels = [0.1, 0.5, 1.0, 2.0, 5.0] * 100  # 500 operations
        
        for i, zoom in enumerate(zoom_levels):
            start_time = time.time()
            self.viewport.setZoom(zoom)
            duration = time.time() - start_time
            
            self.metrics.record_operation(test_name, f'zoom_{i}', duration)
            
            # Record memory every 50 operations
            if i % 50 == 0:
                self.metrics.record_memory_sample(test_name)
        
        stats = self.metrics.end_measurement(test_name)
        self.metrics.print_summary(test_name)
        
        # Assert performance requirements
        self.assertLess(stats['max_operation_time'] * 1000, self.thresholds['max_operation_time_ms'],
                       f"Zoom operation took {stats['max_operation_time']*1000:.3f}ms, expected < {self.thresholds['max_operation_time_ms']}ms")
        
        self.assertGreater(stats['operations_per_second'], self.thresholds['min_operations_per_second'],
                          f"Only {stats['operations_per_second']:.2f} operations/second, expected > {self.thresholds['min_operations_per_second']}")
        
        self.assertLess(stats['memory_delta'], self.thresholds['max_memory_delta_mb'],
                       f"Memory increased by {stats['memory_delta']:.2f}MB, expected < {self.thresholds['max_memory_delta_mb']}MB")
    
    def test_high_frequency_pan_operations(self):
        """Test viewport manager performance under high-frequency pan operations"""
        test_name = 'high_frequency_pan'
        self.metrics.start_measurement(test_name)
        
        # Perform rapid pan operations
        pan_positions = [(i, i*2) for i in range(1000)]  # 1000 operations
        
        for i, (x, y) in enumerate(pan_positions):
            start_time = time.time()
            self.viewport.setPan(x, y)
            duration = time.time() - start_time
            
            self.metrics.record_operation(test_name, f'pan_{i}', duration)
            
            # Record memory every 100 operations
            if i % 100 == 0:
                self.metrics.record_memory_sample(test_name)
        
        stats = self.metrics.end_measurement(test_name)
        self.metrics.print_summary(test_name)
        
        # Assert performance requirements
        self.assertLess(stats['max_operation_time'] * 1000, self.thresholds['max_operation_time_ms'])
        self.assertGreater(stats['operations_per_second'], self.thresholds['min_operations_per_second'])
        self.assertLess(stats['memory_delta'], self.thresholds['max_memory_delta_mb'])
    
    def test_coordinate_conversion_performance(self):
        """Test coordinate conversion performance with large coordinate sets"""
        test_name = 'coordinate_conversion'
        self.metrics.start_measurement(test_name)
        
        # Generate large set of test coordinates
        test_coordinates = [(x, y) for x in range(1000) for y in range(1000)]  # 1M coordinates
        
        # Test screen to SVG conversion
        for i, (screen_x, screen_y) in enumerate(test_coordinates[:10000]):  # Test first 10K
            start_time = time.time()
            svg_x, svg_y = self.viewport.screenToSVG(screen_x, screen_y)
            duration = time.time() - start_time
            
            self.metrics.record_operation(test_name, f'screen_to_svg_{i}', duration)
            
            # Record memory every 1000 operations
            if i % 1000 == 0:
                self.metrics.record_memory_sample(test_name)
        
        # Test SVG to screen conversion
        for i, (svg_x, svg_y) in enumerate(test_coordinates[:10000]):  # Test first 10K
            start_time = time.time()
            screen_x, screen_y = self.viewport.svgToScreen(svg_x, svg_y)
            duration = time.time() - start_time
            
            self.metrics.record_operation(test_name, f'svg_to_screen_{i}', duration)
        
        stats = self.metrics.end_measurement(test_name)
        self.metrics.print_summary(test_name)
        
        # Assert coordinate conversion performance
        self.assertLess(stats['max_operation_time'] * 1000, self.thresholds['max_coordinate_conversion_time_ms'],
                       f"Coordinate conversion took {stats['max_operation_time']*1000:.3f}ms, expected < {self.thresholds['max_coordinate_conversion_time_ms']}ms")
    
    def test_large_symbol_count_rendering(self):
        """Test performance with large number of symbols"""
        test_name = 'large_symbol_count'
        self.metrics.start_measurement(test_name)
        
        # Simulate large number of symbols
        symbol_count = 10000
        symbols = []
        
        # Create symbols
        for i in range(symbol_count):
            symbol = {
                'id': f'symbol_{i}',
                'x': i % 1000,
                'y': i // 1000,
                'type': 'device'
            }
            symbols.append(symbol)
        
        # Simulate rendering operations
        for i in range(100):  # 100 render cycles
            start_time = time.time()
            
            # Simulate coordinate conversion for all symbols
            for symbol in symbols:
                screen_x, screen_y = self.viewport.svgToScreen(symbol['x'], symbol['y'])
                # Simulate some rendering work
                _ = screen_x + screen_y
            
            duration = time.time() - start_time
            self.metrics.record_operation(test_name, f'render_cycle_{i}', duration)
            
            # Record memory every 10 cycles
            if i % 10 == 0:
                self.metrics.record_memory_sample(test_name)
        
        stats = self.metrics.end_measurement(test_name)
        self.metrics.print_summary(test_name)
        
        # Assert rendering performance
        self.assertLess(stats['avg_operation_time'] * 1000, self.thresholds['max_operation_time_ms'] * 10,  # Allow 10x for rendering
                       f"Average render cycle took {stats['avg_operation_time']*1000:.3f}ms")
    
    def test_concurrent_viewport_operations(self):
        """Test viewport manager performance under concurrent operations"""
        test_name = 'concurrent_operations'
        self.metrics.start_measurement(test_name)
        
        def zoom_worker(worker_id):
            """Worker function for zoom operations"""
            for i in range(100):
                zoom = 0.1 + (i % 50) * 0.1
                start_time = time.time()
                self.viewport.setZoom(zoom)
                duration = time.time() - start_time
                return f'zoom_worker_{worker_id}_{i}', duration
        
        def pan_worker(worker_id):
            """Worker function for pan operations"""
            for i in range(100):
                x, y = i * 10, i * 20
                start_time = time.time()
                self.viewport.setPan(x, y)
                duration = time.time() - start_time
                return f'pan_worker_{worker_id}_{i}', duration
        
        # Run concurrent operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # Submit zoom and pan workers
            zoom_futures = [executor.submit(zoom_worker, i) for i in range(2)]
            pan_futures = [executor.submit(pan_worker, i) for i in range(2)]
            
            # Collect results
            for future in concurrent.futures.as_completed(zoom_futures + pan_futures):
                try:
                    operation_name, duration = future.result()
                    self.metrics.record_operation(test_name, operation_name, duration)
                except Exception as e:
                    print(f"Worker failed: {e}")
        
        # Record memory after concurrent operations
        self.metrics.record_memory_sample(test_name)
        
        stats = self.metrics.end_measurement(test_name)
        self.metrics.print_summary(test_name)
        
        # Assert concurrent performance
        self.assertLess(stats['max_operation_time'] * 1000, self.thresholds['max_operation_time_ms'] * 2,  # Allow 2x for concurrency
                       f"Concurrent operation took {stats['max_operation_time']*1000:.3f}ms")
    
    def test_memory_leak_detection(self):
        """Test for memory leaks during extended viewport operations"""
        test_name = 'memory_leak_detection'
        self.metrics.start_measurement(test_name)
        
        # Perform extended operations
        for cycle in range(10):  # 10 cycles
            # Perform zoom operations
            for i in range(100):
                zoom = 0.1 + (i % 50) * 0.1
                self.viewport.setZoom(zoom)
            
            # Perform pan operations
            for i in range(100):
                x, y = i * 10, i * 20
                self.viewport.setPan(x, y)
            
            # Force garbage collection
            gc.collect()
            
            # Record memory after each cycle
            self.metrics.record_memory_sample(test_name)
        
        stats = self.metrics.end_measurement(test_name)
        self.metrics.print_summary(test_name)
        
        # Check for memory leaks (memory should not continuously increase)
        memory_samples = self.metrics.metrics[test_name]['memory_samples']
        if len(memory_samples) > 3:
            # Calculate memory growth rate
            memory_growth = (memory_samples[-1] - memory_samples[0]) / len(memory_samples)
            
            # Memory growth should be minimal (less than 1MB per cycle)
            self.assertLess(memory_growth, 1.0,
                           f"Memory growth rate: {memory_growth:.2f}MB per cycle, expected < 1.0MB")
    
    def test_event_handling_performance(self):
        """Test event handling performance under load"""
        test_name = 'event_handling'
        self.metrics.start_measurement(test_name)
        
        # Create event handlers
        event_count = 0
        def event_handler(data):
            nonlocal event_count
            event_count += 1
            # Simulate some event processing work
            _ = sum(range(100))
        
        # Register event handlers
        self.viewport.addEventListener('zoomChanged', event_handler)
        self.viewport.addEventListener('panChanged', event_handler)
        
        # Trigger many events
        for i in range(1000):
            start_time = time.time()
            
            # Trigger zoom event
            self.viewport.setZoom(0.1 + (i % 50) * 0.1)
            
            # Trigger pan event
            self.viewport.setPan(i * 10, i * 20)
            
            duration = time.time() - start_time
            self.metrics.record_operation(test_name, f'event_trigger_{i}', duration)
            
            # Record memory every 100 events
            if i % 100 == 0:
                self.metrics.record_memory_sample(test_name)
        
        stats = self.metrics.end_measurement(test_name)
        self.metrics.print_summary(test_name)
        
        # Assert event handling performance
        self.assertLess(stats['max_operation_time'] * 1000, self.thresholds['max_operation_time_ms'] * 5,  # Allow 5x for event handling
                       f"Event handling took {stats['max_operation_time']*1000:.3f}ms")
        
        # Verify events were processed
        self.assertGreater(event_count, 0, "No events were processed")
    
    def test_zoom_history_performance(self):
        """Test zoom history management performance"""
        test_name = 'zoom_history'
        self.metrics.start_measurement(test_name)
        
        # Perform many zoom operations to test history management
        for i in range(1000):
            start_time = time.time()
            self.viewport.setZoom(0.1 + (i % 50) * 0.1)
            duration = time.time() - start_time
            
            self.metrics.record_operation(test_name, f'zoom_history_{i}', duration)
            
            # Record memory every 100 operations
            if i % 100 == 0:
                self.metrics.record_memory_sample(test_name)
        
        stats = self.metrics.end_measurement(test_name)
        self.metrics.print_summary(test_name)
        
        # Assert zoom history performance
        self.assertLess(stats['max_operation_time'] * 1000, self.thresholds['max_operation_time_ms'],
                       f"Zoom history operation took {stats['max_operation_time']*1000:.3f}ms")
        
        # Verify history size is managed properly
        if hasattr(self.viewport, 'zoomHistory'):
            self.assertLessEqual(len(self.viewport.zoomHistory), 50,
                               f"Zoom history size: {len(self.viewport.zoomHistory)}, expected <= 50")

if __name__ == '__main__':
    # Run performance tests
    unittest.main(verbosity=2)
    
    # Save metrics to file
    if hasattr(TestViewportPerformance, 'metrics'):
        TestViewportPerformance.metrics.save_metrics() 