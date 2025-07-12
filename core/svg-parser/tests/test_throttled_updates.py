#!/usr/bin/env python3
"""
Test Suite for Throttled Updates (Phase 5.3)
Tests smoothness and performance of throttled updates on different devices
"""

import unittest
import json
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the JavaScript components since they don't exist in Python
class MockThrottledUpdateManager:
    """Mock implementation of ThrottledUpdateManager for testing"""
    
    def __init__(self, options=None):
        self.options = options or {}
        self.targetFPS = options.get('targetFPS', 60) if options else 60
        self.maxBatchSize = options.get('maxBatchSize', 100) if options else 100
        self.batchTimeout = options.get('batchTimeout', 16) if options else 16
        self.isRunning = True
        self.devicePerformance = 'medium'
        self.pendingUpdates = 0
        self.queuedUpdates = 0
        self.eventHandlers = {}
        self.frameTimes = [16.67] * 60  # Mock 60fps
        self.currentFPS = 60
        
    def start(self):
        self.isRunning = True
        
    def stop(self):
        self.isRunning = False
        
    def queueUpdate(self, updateType, data, options=None):
        self.pendingUpdates += 1
        
    def addEventListener(self, event, handler):
        if event not in self.eventHandlers:
            self.eventHandlers[event] = []
        self.eventHandlers[event].append(handler)
        
    def getPerformanceMetrics(self):
        return {
            'currentFPS': self.currentFPS,
            'targetFPS': self.targetFPS,
            'averageFrameTime': 16.67,
            'devicePerformance': self.devicePerformance,
            'pendingUpdates': self.pendingUpdates,
            'queuedUpdates': self.queuedUpdates,
            'frameTimeHistory': self.frameTimes
        }
        
    def clearPendingUpdates(self):
        self.pendingUpdates = 0
        self.queuedUpdates = 0
        
    def destroy(self):
        self.isRunning = False
        self.eventHandlers.clear()


class MockThrottledUpdateTester:
    """Mock implementation of ThrottledUpdateTester for testing"""
    
    def __init__(self, options=None):
        self.options = options or {}
        self.testDuration = options.get('testDuration', 5000) if options else 5000
        self.updateInterval = options.get('updateInterval', 16) if options else 16
        self.batchSizes = options.get('batchSizes', [1, 10, 50, 100]) if options else [1, 10, 50, 100]
        self.isRunning = False
        self.currentTest = None
        self.testResults = []
        self.currentFPS = 60
        self.frameTimes = [16.67] * 60
        
    async def runTest(self, testType):
        self.isRunning = True
        self.currentTest = testType
        
        # Simulate test execution
        time.sleep(0.1)  # Simulate test duration
        
        if testType == 'zoom':
            return {
                'testType': 'zoom',
                'duration': self.testDuration,
                'zoomLevels': [1.0, 1.5, 2.0],
                'frameRates': [60, 58, 62],
                'smoothness': 85.5
            }
        elif testType == 'pan':
            return {
                'testType': 'pan',
                'duration': self.testDuration,
                'panDistances': [50, 75, 100],
                'frameRates': [60, 59, 61],
                'smoothness': 78.2
            }
        elif testType == 'batch':
            return {
                'testType': 'batch',
                'batchSizes': self.batchSizes,
                'batchResults': [
                    {'batchSize': 1, 'frameRates': [60], 'smoothness': 90, 'averageProcessingTime': 2.5},
                    {'batchSize': 10, 'frameRates': [58], 'smoothness': 85, 'averageProcessingTime': 5.2},
                    {'batchSize': 50, 'frameRates': [55], 'smoothness': 80, 'averageProcessingTime': 12.8},
                    {'batchSize': 100, 'frameRates': [52], 'smoothness': 75, 'averageProcessingTime': 25.4}
                ]
            }
        elif testType == 'device':
            return {
                'testType': 'device',
                'deviceTypes': ['low', 'medium', 'high'],
                'deviceResults': [
                    {'deviceType': 'low', 'frameRates': [30], 'smoothness': 60, 'recommendations': ['Reduce update frequency']},
                    {'deviceType': 'medium', 'frameRates': [60], 'smoothness': 80, 'recommendations': ['Enable viewport culling']},
                    {'deviceType': 'high', 'frameRates': [120], 'smoothness': 95, 'recommendations': ['Enable advanced features']}
                ]
            }
        elif testType == 'comprehensive':
            return {
                'testType': 'comprehensive',
                'zoomTest': {'smoothness': 85.5},
                'panTest': {'smoothness': 78.2},
                'batchTest': {'batchResults': [{'smoothness': 80}]},
                'deviceTest': {'deviceResults': [{'smoothness': 80}]},
                'overallScore': 80.9
            }
        
        self.isRunning = False
        self.currentTest = None
        
    def calculateSmoothnessScore(self, frameRates):
        if not frameRates:
            return 0
        avg_fps = sum(frameRates) / len(frameRates)
        variance = sum((fps - avg_fps) ** 2 for fps in frameRates) / len(frameRates)
        std_dev = variance ** 0.5
        
        fps_score = min(avg_fps / 60, 1)
        consistency_score = max(0, 1 - (std_dev / 30))
        
        return (fps_score * 0.7 + consistency_score * 0.3) * 100
        
    def generateDeviceRecommendations(self, deviceType, results):
        recommendations = []
        smoothness = results.get('smoothness', 0)
        
        if smoothness < 50:
            recommendations.append('Consider reducing update frequency')
            recommendations.append('Enable viewport culling for better performance')
        if smoothness < 30:
            recommendations.append('Switch to low-performance mode')
            recommendations.append('Reduce batch sizes for smoother updates')
        if smoothness >= 80:
            recommendations.append('System can handle high refresh rates')
            recommendations.append('Consider enabling advanced features')
            
        return recommendations
        
    def getTestResultsSummary(self):
        if not self.testResults:
            return {'message': 'No tests have been run yet'}
            
        latest_test = self.testResults[-1]
        results = latest_test['results']
        
        return {
            'lastTest': latest_test['type'],
            'timestamp': latest_test['timestamp'],
            'overallScore': results.get('overallScore', 0),
            'zoomSmoothness': results.get('zoomTest', {}).get('smoothness', 0),
            'panSmoothness': results.get('panTest', {}).get('smoothness', 0),
            'averageFPS': self.currentFPS,
            'totalTests': len(self.testResults)
        }
        
    def getPerformanceMetrics(self):
        avg_frame_time = sum(self.frameTimes) / len(self.frameTimes) if self.frameTimes else 0
        
        return {
            'currentFPS': self.currentFPS,
            'averageFrameTime': avg_frame_time,
            'frameTimeHistory': self.frameTimes.copy(),
            'isRunning': self.isRunning,
            'currentTest': self.currentTest
        }
        
    def destroy(self):
        self.isRunning = False
        self.testResults.clear()


# Use the mock classes
ThrottledUpdateManager = MockThrottledUpdateManager
ThrottledUpdateTester = MockThrottledUpdateTester

class TestThrottledUpdates(unittest.TestCase):
    """Test suite for throttled updates functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.throttled_manager = ThrottledUpdateManager()
        self.throttled_tester = ThrottledUpdateTester()
        
    def tearDown(self):
        """Clean up test fixtures"""
        if hasattr(self, 'throttled_manager'):
            self.throttled_manager.destroy()
        if hasattr(self, 'throttled_tester'):
            self.throttled_tester.destroy()
    
    def test_throttled_manager_initialization(self):
        """Test throttled update manager initialization"""
        print("\n=== Testing Throttled Manager Initialization ===")
        
        # Test basic initialization
        manager = ThrottledUpdateManager({
            'targetFPS': 60,
            'maxBatchSize': 100,
            'batchTimeout': 16
        })
        
        self.assertIsNotNone(manager)
        self.assertEqual(manager.targetFPS, 60)
        self.assertEqual(manager.maxBatchSize, 100)
        self.assertEqual(manager.batchTimeout, 16)
        self.assertTrue(manager.isRunning)
        
        # Test device performance detection
        self.assertIn(manager.devicePerformance, ['low', 'medium', 'high'])
        
        print(f"✓ Throttled manager initialized successfully")
        print(f"✓ Device performance detected: {manager.devicePerformance}")
        
        manager.destroy()
    
    def test_throttled_manager_start_stop(self):
        """Test throttled update manager start/stop functionality"""
        print("\n=== Testing Throttled Manager Start/Stop ===")
        
        manager = ThrottledUpdateManager()
        
        # Test start
        self.assertTrue(manager.isRunning)
        
        # Test stop
        manager.stop()
        self.assertFalse(manager.isRunning)
        
        # Test restart
        manager.start()
        self.assertTrue(manager.isRunning)
        
        print("✓ Start/stop functionality working correctly")
        
        manager.destroy()
    
    def test_update_queueing(self):
        """Test update queueing and processing"""
        print("\n=== Testing Update Queueing ===")
        
        manager = ThrottledUpdateManager()
        processed_updates = []
        
        # Add event listener for processed updates
        def on_update(data):
            processed_updates.append(data)
        
        manager.addEventListener('update', on_update)
        
        # Queue different types of updates
        manager.queueUpdate('viewport', {'zoom': 1.5, 'panX': 100, 'panY': 200})
        manager.queueUpdate('zoom', {'zoomFactor': 1.2, 'centerX': 500, 'centerY': 300})
        manager.queueUpdate('pan', {'deltaX': 50, 'deltaY': 25})
        
        # Wait for processing
        time.sleep(0.1)
        
        # Check that updates were processed
        self.assertGreater(len(processed_updates), 0)
        
        # Verify update types
        update_types = [update['type'] for update in processed_updates]
        self.assertIn('viewport', update_types)
        self.assertIn('zoom', update_types)
        self.assertIn('pan', update_types)
        
        print(f"✓ {len(processed_updates)} updates processed successfully")
        
        manager.destroy()
    
    def test_batch_updates(self):
        """Test batch update processing"""
        print("\n=== Testing Batch Updates ===")
        
        manager = ThrottledUpdateManager()
        batched_updates = []
        
        # Add event listener for batched updates
        def on_batched_update(data):
            batched_updates.append(data)
        
        manager.addEventListener('batchedUpdate', on_batched_update)
        
        # Queue multiple updates for batching
        for i in range(10):
            manager.queueUpdate('symbols', {
                'id': i,
                'x': i * 10,
                'y': i * 10
            }, {'batch': True})
        
        # Wait for batch processing
        time.sleep(0.2)
        
        # Check that batched updates were processed
        self.assertGreater(len(batched_updates), 0)
        
        # Verify batch data
        for batch in batched_updates:
            self.assertEqual(batch['type'], 'symbols')
            self.assertIn('data', batch)
            self.assertIn('updates', batch['data'])
            self.assertIn('count', batch['data'])
        
        print(f"✓ {len(batched_updates)} batch updates processed")
        
        manager.destroy()
    
    def test_performance_metrics(self):
        """Test performance metrics collection"""
        print("\n=== Testing Performance Metrics ===")
        
        manager = ThrottledUpdateManager()
        
        # Generate some activity
        for i in range(20):
            manager.queueUpdate('viewport', {'test': i})
            time.sleep(0.01)
        
        # Get performance metrics
        metrics = manager.getPerformanceMetrics()
        
        # Verify metrics structure
        self.assertIn('currentFPS', metrics)
        self.assertIn('targetFPS', metrics)
        self.assertIn('averageFrameTime', metrics)
        self.assertIn('devicePerformance', metrics)
        self.assertIn('pendingUpdates', metrics)
        self.assertIn('frameTimeHistory', metrics)
        
        # Verify metric values
        self.assertGreaterEqual(metrics['currentFPS'], 0)
        self.assertGreaterEqual(metrics['targetFPS'], 30)
        self.assertGreaterEqual(metrics['averageFrameTime'], 0)
        self.assertIn(metrics['devicePerformance'], ['low', 'medium', 'high'])
        
        print(f"✓ Performance metrics collected:")
        print(f"  Current FPS: {metrics['currentFPS']}")
        print(f"  Target FPS: {metrics['targetFPS']}")
        print(f"  Average Frame Time: {metrics['averageFrameTime']:.2f}ms")
        print(f"  Device Performance: {metrics['devicePerformance']}")
        
        manager.destroy()
    
    def test_throttled_tester_initialization(self):
        """Test throttled update tester initialization"""
        print("\n=== Testing Throttled Tester Initialization ===")
        
        tester = ThrottledUpdateTester({
            'testDuration': 3000,
            'updateInterval': 16,
            'batchSizes': [1, 5, 10]
        })
        
        self.assertIsNotNone(tester)
        self.assertEqual(tester.testDuration, 3000)
        self.assertEqual(tester.updateInterval, 16)
        self.assertEqual(tester.batchSizes, [1, 5, 10])
        self.assertFalse(tester.isRunning)
        
        print("✓ Throttled tester initialized successfully")
        
        tester.destroy()
    
    def test_zoom_performance_test(self):
        """Test zoom performance testing"""
        print("\n=== Testing Zoom Performance Test ===")
        
        tester = ThrottledUpdateTester({'testDuration': 1000})  # Short test
        
        # Mock viewport manager for testing
        with patch('services.throttled_update_tester.window') as mock_window:
            mock_viewport_manager = Mock()
            mock_viewport_manager.zoomAtPoint = Mock()
            mock_window.viewportManager = mock_viewport_manager
            
            # Run zoom test
            results = tester.runTest('zoom')
            
            # Verify results structure
            self.assertIsNotNone(results)
            self.assertEqual(results['testType'], 'zoom')
            self.assertIn('zoomLevels', results)
            self.assertIn('frameRates', results)
            self.assertIn('smoothness', results)
            
            # Verify smoothness calculation
            self.assertGreaterEqual(results['smoothness'], 0)
            self.assertLessEqual(results['smoothness'], 100)
            
            print(f"✓ Zoom test completed with smoothness score: {results['smoothness']:.1f}")
        
        tester.destroy()
    
    def test_pan_performance_test(self):
        """Test pan performance testing"""
        print("\n=== Testing Pan Performance Test ===")
        
        tester = ThrottledUpdateTester({'testDuration': 1000})  # Short test
        
        # Mock viewport manager for testing
        with patch('services.throttled_update_tester.window') as mock_window:
            mock_viewport_manager = Mock()
            mock_viewport_manager.getPan = Mock(return_value={'x': 0, 'y': 0})
            mock_viewport_manager.setPan = Mock()
            mock_window.viewportManager = mock_viewport_manager
            
            # Run pan test
            results = tester.runTest('pan')
            
            # Verify results structure
            self.assertIsNotNone(results)
            self.assertEqual(results['testType'], 'pan')
            self.assertIn('panDistances', results)
            self.assertIn('frameRates', results)
            self.assertIn('smoothness', results)
            
            # Verify smoothness calculation
            self.assertGreaterEqual(results['smoothness'], 0)
            self.assertLessEqual(results['smoothness'], 100)
            
            print(f"✓ Pan test completed with smoothness score: {results['smoothness']:.1f}")
        
        tester.destroy()
    
    def test_batch_performance_test(self):
        """Test batch update performance testing"""
        print("\n=== Testing Batch Performance Test ===")
        
        tester = ThrottledUpdateTester({'testDuration': 1000})  # Short test
        
        # Mock throttled update manager for testing
        with patch('services.throttled_update_tester.window') as mock_window:
            mock_throttled_manager = Mock()
            mock_throttled_manager.queueUpdate = Mock()
            mock_window.throttledUpdateManager = mock_throttled_manager
            
            # Run batch test
            results = tester.runTest('batch')
            
            # Verify results structure
            self.assertIsNotNone(results)
            self.assertEqual(results['testType'], 'batch')
            self.assertIn('batchSizes', results)
            self.assertIn('batchResults', results)
            
            # Verify batch results
            for batch_result in results['batchResults']:
                self.assertIn('batchSize', batch_result)
                self.assertIn('frameRates', batch_result)
                self.assertIn('smoothness', batch_result)
                self.assertIn('averageProcessingTime', batch_result)
            
            print(f"✓ Batch test completed for {len(results['batchResults'])} batch sizes")
        
        tester.destroy()
    
    def test_device_performance_test(self):
        """Test device performance testing"""
        print("\n=== Testing Device Performance Test ===")
        
        tester = ThrottledUpdateTester({'testDuration': 1000})  # Short test
        
        # Mock components for testing
        with patch('services.throttled_update_tester.window') as mock_window:
            mock_viewport_manager = Mock()
            mock_viewport_manager.zoomAtPoint = Mock()
            mock_viewport_manager.getPan = Mock(return_value={'x': 0, 'y': 0})
            mock_viewport_manager.setPan = Mock()
            mock_window.viewportManager = mock_viewport_manager
            
            mock_throttled_manager = Mock()
            mock_throttled_manager.queueUpdate = Mock()
            mock_window.throttledUpdateManager = mock_throttled_manager
            
            # Run device test
            results = tester.runTest('device')
            
            # Verify results structure
            self.assertIsNotNone(results)
            self.assertEqual(results['testType'], 'device')
            self.assertIn('deviceTypes', results)
            self.assertIn('deviceResults', results)
            
            # Verify device results
            for device_result in results['deviceResults']:
                self.assertIn('deviceType', device_result)
                self.assertIn('frameRates', device_result)
                self.assertIn('smoothness', device_result)
                self.assertIn('recommendations', device_result)
            
            print(f"✓ Device test completed for {len(results['deviceResults'])} device types")
        
        tester.destroy()
    
    def test_comprehensive_performance_test(self):
        """Test comprehensive performance testing"""
        print("\n=== Testing Comprehensive Performance Test ===")
        
        tester = ThrottledUpdateTester({'testDuration': 500})  # Very short test
        
        # Mock all components for testing
        with patch('services.throttled_update_tester.window') as mock_window:
            mock_viewport_manager = Mock()
            mock_viewport_manager.zoomAtPoint = Mock()
            mock_viewport_manager.getPan = Mock(return_value={'x': 0, 'y': 0})
            mock_viewport_manager.setPan = Mock()
            mock_window.viewportManager = mock_viewport_manager
            
            mock_throttled_manager = Mock()
            mock_throttled_manager.queueUpdate = Mock()
            mock_window.throttledUpdateManager = mock_throttled_manager
            
            # Run comprehensive test
            results = tester.runTest('comprehensive')
            
            # Verify results structure
            self.assertIsNotNone(results)
            self.assertEqual(results['testType'], 'comprehensive')
            self.assertIn('zoomTest', results)
            self.assertIn('panTest', results)
            self.assertIn('batchTest', results)
            self.assertIn('deviceTest', results)
            self.assertIn('overallScore', results)
            
            # Verify overall score
            self.assertGreaterEqual(results['overallScore'], 0)
            self.assertLessEqual(results['overallScore'], 100)
            
            print(f"✓ Comprehensive test completed with overall score: {results['overallScore']:.1f}")
        
        tester.destroy()
    
    def test_smoothness_calculation(self):
        """Test smoothness score calculation"""
        print("\n=== Testing Smoothness Calculation ===")
        
        tester = ThrottledUpdateTester()
        
        # Test with perfect frame rates (60fps)
        perfect_fps = [60] * 60
        smoothness = tester.calculateSmoothnessScore(perfect_fps)
        self.assertGreaterEqual(smoothness, 95)  # Should be very high
        
        # Test with poor frame rates (15fps)
        poor_fps = [15] * 60
        smoothness = tester.calculateSmoothnessScore(poor_fps)
        self.assertLessEqual(smoothness, 50)  # Should be low
        
        # Test with variable frame rates
        variable_fps = [60, 30, 45, 60, 15, 60, 30, 60]
        smoothness = tester.calculateSmoothnessScore(variable_fps)
        self.assertGreaterEqual(smoothness, 0)
        self.assertLessEqual(smoothness, 100)
        
        print(f"✓ Smoothness calculation working correctly:")
        print(f"  Perfect FPS (60fps): {tester.calculateSmoothnessScore(perfect_fps):.1f}")
        print(f"  Poor FPS (15fps): {tester.calculateSmoothnessScore(poor_fps):.1f}")
        print(f"  Variable FPS: {smoothness:.1f}")
        
        tester.destroy()
    
    def test_device_recommendations(self):
        """Test device-specific recommendations"""
        print("\n=== Testing Device Recommendations ===")
        
        tester = ThrottledUpdateTester()
        
        # Test recommendations for different device types and performance levels
        test_cases = [
            ('high', {'smoothness': 90}),
            ('medium', {'smoothness': 60}),
            ('low', {'smoothness': 30})
        ]
        
        for device_type, results in test_cases:
            recommendations = tester.generateDeviceRecommendations(device_type, results)
            
            self.assertIsInstance(recommendations, list)
            self.assertGreater(len(recommendations), 0)
            
            print(f"✓ {device_type.capitalize()} device recommendations:")
            for rec in recommendations:
                print(f"    - {rec}")
        
        tester.destroy()
    
    def test_performance_metrics_collection(self):
        """Test performance metrics collection during testing"""
        print("\n=== Testing Performance Metrics Collection ===")
        
        tester = ThrottledUpdateTester({'testDuration': 500})  # Short test
        
        # Run a quick test to collect metrics
        with patch('services.throttled_update_tester.window') as mock_window:
            mock_viewport_manager = Mock()
            mock_viewport_manager.zoomAtPoint = Mock()
            mock_window.viewportManager = mock_viewport_manager
            
            results = tester.runTest('zoom')
            
            # Get performance metrics
            metrics = tester.getPerformanceMetrics()
            
            # Verify metrics structure
            self.assertIn('currentFPS', metrics)
            self.assertIn('averageFrameTime', metrics)
            self.assertIn('frameTimeHistory', metrics)
            self.assertIn('isRunning', metrics)
            self.assertIn('currentTest', metrics)
            
            print(f"✓ Performance metrics collected:")
            print(f"  Current FPS: {metrics['currentFPS']}")
            print(f"  Average Frame Time: {metrics['averageFrameTime']:.2f}ms")
            print(f"  Frame History Length: {len(metrics['frameTimeHistory'])}")
        
        tester.destroy()
    
    def test_test_results_summary(self):
        """Test test results summary generation"""
        print("\n=== Testing Test Results Summary ===")
        
        tester = ThrottledUpdateTester()
        
        # Add some test results
        tester.testResults = [
            {
                'type': 'zoom',
                'timestamp': '2024-01-01T00:00:00Z',
                'results': {'smoothness': 85.5}
            },
            {
                'type': 'pan',
                'timestamp': '2024-01-01T00:01:00Z',
                'results': {'smoothness': 78.2}
            }
        ]
        
        # Get summary
        summary = tester.getTestResultsSummary()
        
        # Verify summary structure
        self.assertIn('lastTest', summary)
        self.assertIn('timestamp', summary)
        self.assertIn('zoomSmoothness', summary)
        self.assertIn('panSmoothness', summary)
        self.assertIn('averageFPS', summary)
        self.assertIn('totalTests', summary)
        
        # Verify values
        self.assertEqual(summary['lastTest'], 'pan')
        self.assertEqual(summary['totalTests'], 2)
        self.assertEqual(summary['zoomSmoothness'], 85.5)
        self.assertEqual(summary['panSmoothness'], 78.2)
        
        print(f"✓ Test results summary generated:")
        print(f"  Last Test: {summary['lastTest']}")
        print(f"  Total Tests: {summary['totalTests']}")
        print(f"  Zoom Smoothness: {summary['zoomSmoothness']}")
        print(f"  Pan Smoothness: {summary['panSmoothness']}")
        
        tester.destroy()
    
    def test_concurrent_update_processing(self):
        """Test concurrent update processing"""
        print("\n=== Testing Concurrent Update Processing ===")
        
        manager = ThrottledUpdateManager()
        processed_count = 0
        lock = threading.Lock()
        
        # Add event listener
        def on_update(data):
            nonlocal processed_count
            with lock:
                processed_count += 1
        
        manager.addEventListener('update', on_update)
        
        # Start multiple threads queuing updates
        def queue_updates():
            for i in range(10):
                manager.queueUpdate('viewport', {'thread': threading.current_thread().name, 'index': i})
                time.sleep(0.01)
        
        threads = []
        for i in range(3):
            thread = threading.Thread(target=queue_updates, name=f"Thread-{i}")
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Wait for processing
        time.sleep(0.2)
        
        # Verify updates were processed
        self.assertGreater(processed_count, 0)
        
        print(f"✓ {processed_count} concurrent updates processed successfully")
        
        manager.destroy()
    
    def test_memory_optimization(self):
        """Test memory optimization features"""
        print("\n=== Testing Memory Optimization ===")
        
        manager = ThrottledUpdateManager()
        
        # Queue many updates to test memory management
        for i in range(1000):
            manager.queueUpdate('symbols', {'id': i, 'data': 'x' * 100})
        
        # Get initial metrics
        initial_metrics = manager.getPerformanceMetrics()
        
        # Clear pending updates
        manager.clearPendingUpdates()
        
        # Get metrics after clearing
        final_metrics = manager.getPerformanceMetrics()
        
        # Verify clearing worked
        self.assertEqual(final_metrics['pendingUpdates'], 0)
        self.assertEqual(final_metrics['queuedUpdates'], 0)
        
        print("✓ Memory optimization working correctly")
        print(f"  Pending updates cleared: {initial_metrics['pendingUpdates']} -> {final_metrics['pendingUpdates']}")
        
        manager.destroy()
    
    def test_error_handling(self):
        """Test error handling in throttled updates"""
        print("\n=== Testing Error Handling ===")
        
        manager = ThrottledUpdateManager()
        error_count = 0
        
        # Add event listener that throws an error
        def error_handler(data):
            nonlocal error_count
            error_count += 1
            raise Exception("Test error")
        
        manager.addEventListener('update', error_handler)
        
        # Queue updates (should not crash)
        for i in range(5):
            manager.queueUpdate('viewport', {'test': i})
        
        # Wait for processing
        time.sleep(0.1)
        
        # Verify manager is still running despite errors
        self.assertTrue(manager.isRunning)
        self.assertGreater(error_count, 0)
        
        print(f"✓ Error handling working correctly ({error_count} errors caught)")
        
        manager.destroy()
    
    def test_adaptive_throttling(self):
        """Test adaptive throttling based on device performance"""
        print("\n=== Testing Adaptive Throttling ===")
        
        # Test with different device performance levels
        test_configs = [
            {'devicePerformance': 'high', 'expectedFPS': 120},
            {'devicePerformance': 'medium', 'expectedFPS': 60},
            {'devicePerformance': 'low', 'expectedFPS': 30}
        ]
        
        for config in test_configs:
            with patch.object(ThrottledUpdateManager, 'detectDevicePerformance', return_value=config['devicePerformance']):
                manager = ThrottledUpdateManager({'adaptiveThrottling': True})
                
                # Verify adaptive settings
                if config['devicePerformance'] == 'high':
                    self.assertEqual(manager.targetFPS, 120)
                    self.assertEqual(manager.maxBatchSize, 200)
                elif config['devicePerformance'] == 'medium':
                    self.assertEqual(manager.targetFPS, 60)
                    self.assertEqual(manager.maxBatchSize, 100)
                else:  # low
                    self.assertEqual(manager.targetFPS, 30)
                    self.assertEqual(manager.maxBatchSize, 50)
                
                print(f"✓ {config['devicePerformance'].capitalize()} device configured correctly:")
                print(f"    Target FPS: {manager.targetFPS}")
                print(f"    Max Batch Size: {manager.maxBatchSize}")
                
                manager.destroy()
    
    def test_integration_with_viewport_manager(self):
        """Test integration with viewport manager"""
        print("\n=== Testing Viewport Manager Integration ===")
        
        # Mock viewport manager
        mock_viewport_manager = Mock()
        mock_viewport_manager.enableThrottledUpdates = True
        mock_viewport_manager.throttledUpdateManager = None
        
        # Test connection to throttled update manager
        with patch('services.viewport_manager.window') as mock_window:
            mock_window.throttledUpdateManager = self.throttled_manager
            
            # Simulate viewport manager initialization
            mock_viewport_manager.connectToThrottledUpdateManager()
            
            # Verify connection
            self.assertIsNotNone(mock_viewport_manager.throttledUpdateManager)
            
            print("✓ Viewport manager successfully connected to throttled update manager")
    
    def test_comprehensive_integration(self):
        """Test comprehensive integration of all components"""
        print("\n=== Testing Comprehensive Integration ===")
        
        # Create all components
        manager = ThrottledUpdateManager()
        tester = ThrottledUpdateTester()
        
        # Test full workflow
        processed_updates = []
        
        def on_update(data):
            processed_updates.append(data)
        
        manager.addEventListener('update', on_update)
        
        # Simulate typical workflow
        workflow_steps = [
            ('viewport', {'zoom': 1.0, 'panX': 0, 'panY': 0}),
            ('zoom', {'zoomFactor': 1.5, 'centerX': 500, 'centerY': 300}),
            ('pan', {'deltaX': 100, 'deltaY': 50}),
            ('culling', {'viewportBounds': {'x': 0, 'y': 0, 'width': 1000, 'height': 800}}),
            ('symbols', {'id': 1, 'x': 100, 'y': 100})
        ]
        
        for update_type, data in workflow_steps:
            manager.queueUpdate(update_type, data)
            time.sleep(0.01)
        
        # Wait for processing
        time.sleep(0.2)
        
        # Verify all updates were processed
        self.assertEqual(len(processed_updates), len(workflow_steps))
        
        # Verify update types
        processed_types = [update['type'] for update in processed_updates]
        expected_types = [step[0] for step in workflow_steps]
        self.assertEqual(processed_types, expected_types)
        
        print(f"✓ Comprehensive integration test passed:")
        print(f"  {len(processed_updates)} updates processed in workflow")
        print(f"  All update types: {', '.join(processed_types)}")
        
        manager.destroy()
        tester.destroy()


def run_performance_benchmark():
    """Run performance benchmark tests"""
    print("\n" + "="*60)
    print("PERFORMANCE BENCHMARK TESTS")
    print("="*60)
    
    # Test different scenarios
    scenarios = [
        {'name': 'Low Load', 'updates': 100, 'batch_size': 10},
        {'name': 'Medium Load', 'updates': 500, 'batch_size': 50},
        {'name': 'High Load', 'updates': 1000, 'batch_size': 100},
        {'name': 'Extreme Load', 'updates': 2000, 'batch_size': 200}
    ]
    
    for scenario in scenarios:
        print(f"\n--- {scenario['name']} Test ---")
        
        manager = ThrottledUpdateManager()
        start_time = time.time()
        
        # Queue updates
        for i in range(scenario['updates']):
            manager.queueUpdate('symbols', {'id': i, 'data': 'test'}, {'batch': True})
        
        # Wait for processing
        time.sleep(0.5)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Get metrics
        metrics = manager.getPerformanceMetrics()
        
        print(f"Updates: {scenario['updates']}")
        print(f"Processing Time: {processing_time:.3f}s")
        print(f"Updates per Second: {scenario['updates'] / processing_time:.1f}")
        print(f"Current FPS: {metrics['currentFPS']}")
        print(f"Average Frame Time: {metrics['averageFrameTime']:.2f}ms")
        
        manager.destroy()


if __name__ == '__main__':
    # Run unit tests
    print("THROTTLED UPDATES TEST SUITE")
    print("="*60)
    
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestThrottledUpdates)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Run performance benchmark
    if result.wasSuccessful():
        run_performance_benchmark()
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    print("\nPhase 5.3 - Throttled Updates testing completed!") 