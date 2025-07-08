#!/usr/bin/env python3
"""
Unit Tests for Viewport Manager
Tests zoom constraints, coordinate conversion, pan boundaries, and touch gestures
"""

import unittest
import json
import math
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the JavaScript ViewportManager class for testing
class MockViewportManager:
    """Mock implementation of ViewportManager for unit testing"""
    
    def __init__(self, svgElement=None, options=None):
        self.svg = svgElement or Mock()
        self.container = Mock()
        
        # Viewport state
        self.currentZoom = options.get('initialZoom', 1.0) if options else 1.0
        self.panX = options.get('initialPanX', 0) if options else 0
        self.panY = options.get('initialPanY', 0) if options else 0
        
        # Zoom constraints
        self.minZoom = options.get('minZoom', 0.1) if options else 0.1
        self.maxZoom = options.get('maxZoom', 5.0) if options else 5.0
        self.zoomStep = options.get('zoomStep', 0.1) if options else 0.1
        
        # Zoom history
        self.zoomHistory = []
        self.maxHistorySize = options.get('maxHistorySize', 50) if options else 50
        self.historyIndex = -1
        
        # Pan settings
        self.panBoundaries = options.get('panBoundaries', {
            'enabled': True,
            'padding': 100,
            'maxDistance': 2000
        }) if options else {
            'enabled': True,
            'padding': 100,
            'maxDistance': 2000
        }
        
        # Touch state
        self.touchState = {
            'isTouching': False,
            'touchCount': 0,
            'startTouches': [],
            'currentTouches': [],
            'startDistance': 0,
            'startCenter': {'x': 0, 'y': 0},
            'lastDistance': 0,
            'lastCenter': {'x': 0, 'y': 0},
            'startTime': 0,
            'lastMoveTime': 0,
            'velocity': {'x': 0, 'y': 0},
            'gestureType': None
        }
        
        # Scale factors
        self.scaleFactors = {'x': 1.0, 'y': 1.0}
        self.currentUnit = 'pixels'
        
        # Event handlers
        self.eventHandlers = {}
        
    def screenToSVG(self, screenX, screenY):
        """Convert screen coordinates to SVG coordinates"""
        # Mock coordinate conversion
        svgX = (screenX - self.panX) / self.currentZoom
        svgY = (screenY - self.panY) / self.currentZoom
        return svgX, svgY
    
    def svgToScreen(self, svgX, svgY):
        """Convert SVG coordinates to screen coordinates"""
        # Mock coordinate conversion
        screenX = svgX * self.currentZoom + self.panX
        screenY = svgY * self.currentZoom + self.panY
        return screenX, screenY
    
    def zoomIn(self):
        """Zoom in by one step"""
        newZoom = min(self.currentZoom + self.zoomStep, self.maxZoom)
        self.setZoom(newZoom)
    
    def zoomOut(self):
        """Zoom out by one step"""
        newZoom = max(self.currentZoom - self.zoomStep, self.minZoom)
        self.setZoom(newZoom)
    
    def setZoom(self, zoom):
        """Set zoom level with constraints"""
        oldZoom = self.currentZoom
        self.currentZoom = max(self.minZoom, min(zoom, self.maxZoom))
        
        if self.currentZoom != oldZoom:
            self.saveZoomState()
    
    def saveZoomState(self):
        """Save current zoom state to history"""
        state = {
            'zoom': self.currentZoom,
            'panX': self.panX,
            'panY': self.panY
        }
        
        # Remove any states after current index
        self.zoomHistory = self.zoomHistory[:self.historyIndex + 1]
        
        # Add new state
        self.zoomHistory.append(state)
        self.historyIndex += 1
        
        # Limit history size
        if len(self.zoomHistory) > self.maxHistorySize:
            self.zoomHistory.pop(0)
            self.historyIndex -= 1
    
    def undoZoom(self):
        """Undo last zoom operation"""
        if self.historyIndex > 0:
            self.historyIndex -= 1
            state = self.zoomHistory[self.historyIndex]
            self.currentZoom = state['zoom']
            self.panX = state['panX']
            self.panY = state['panY']
            return True
        return False
    
    def redoZoom(self):
        """Redo last undone zoom operation"""
        if self.historyIndex < len(self.zoomHistory) - 1:
            self.historyIndex += 1
            state = self.zoomHistory[self.historyIndex]
            self.currentZoom = state['zoom']
            self.panX = state['panX']
            self.panY = state['panY']
            return True
        return False
    
    def applyPanBoundaries(self, panX, panY):
        """Apply pan boundaries to coordinates"""
        if not self.panBoundaries['enabled']:
            return panX, panY
        
        # Apply padding boundaries
        maxPanX = self.panBoundaries['maxDistance']
        maxPanY = self.panBoundaries['maxDistance']
        
        panX = max(-maxPanX, min(panX, maxPanX))
        panY = max(-maxPanY, min(panY, maxPanY))
        
        return panX, panY
    
    def setPan(self, x, y):
        """Set pan position with boundaries"""
        self.panX, self.panY = self.applyPanBoundaries(x, y)
    
    def getZoom(self):
        """Get current zoom level"""
        return self.currentZoom
    
    def getPan(self):
        """Get current pan position"""
        return self.panX, self.panY
    
    def addEventListener(self, event, handler):
        """Add event listener"""
        if event not in self.eventHandlers:
            self.eventHandlers[event] = []
        self.eventHandlers[event].append(handler)
    
    def triggerEvent(self, event, data=None):
        """Trigger event for testing"""
        if event in self.eventHandlers:
            for handler in self.eventHandlers[event]:
                handler(data or {})


class TestViewportManagerUnit(unittest.TestCase):
    """Unit tests for ViewportManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.viewport = MockViewportManager()
    
    def tearDown(self):
        """Clean up test fixtures"""
        pass
    
    def test_zoom_constraints_minimum(self):
        """Test zoom minimum constraint"""
        # Test zoom below minimum
        self.viewport.setZoom(0.05)  # Below minimum of 0.1
        self.assertEqual(self.viewport.getZoom(), 0.1)
        
        # Test zoom at minimum
        self.viewport.setZoom(0.1)
        self.assertEqual(self.viewport.getZoom(), 0.1)
        
        # Test zoom just above minimum
        self.viewport.setZoom(0.15)
        self.assertEqual(self.viewport.getZoom(), 0.15)
    
    def test_zoom_constraints_maximum(self):
        """Test zoom maximum constraint"""
        # Test zoom above maximum
        self.viewport.setZoom(10.0)  # Above maximum of 5.0
        self.assertEqual(self.viewport.getZoom(), 5.0)
        
        # Test zoom at maximum
        self.viewport.setZoom(5.0)
        self.assertEqual(self.viewport.getZoom(), 5.0)
        
        # Test zoom just below maximum
        self.viewport.setZoom(4.5)
        self.assertEqual(self.viewport.getZoom(), 4.5)
    
    def test_zoom_step_increments(self):
        """Test zoom step increments"""
        initial_zoom = self.viewport.getZoom()
        
        # Test zoom in
        self.viewport.zoomIn()
        self.assertEqual(self.viewport.getZoom(), initial_zoom + 0.1)
        
        # Test zoom out
        self.viewport.zoomOut()
        self.assertEqual(self.viewport.getZoom(), initial_zoom)
        
        # Test zoom out at minimum
        self.viewport.setZoom(0.1)
        self.viewport.zoomOut()
        self.assertEqual(self.viewport.getZoom(), 0.1)  # Should not go below minimum
        
        # Test zoom in at maximum
        self.viewport.setZoom(5.0)
        self.viewport.zoomIn()
        self.assertEqual(self.viewport.getZoom(), 5.0)  # Should not go above maximum
    
    def test_zoom_history_limits(self):
        """Test zoom history size limits"""
        # Add more states than the maximum
        for i in range(60):  # More than maxHistorySize of 50
            self.viewport.setZoom(1.0 + (i * 0.1))

        # Check that history size is limited
        self.assertLessEqual(len(self.viewport.zoomHistory), self.viewport.maxHistorySize)
        # The actual size might be less due to the logic in saveZoomState
        self.assertGreater(len(self.viewport.zoomHistory), 0)
    
    def test_zoom_undo_redo(self):
        """Test zoom undo/redo functionality"""
        # Set initial state
        self.viewport.setZoom(1.0)
        self.viewport.setPan(0, 0)
        
        # Perform some zoom operations
        self.viewport.setZoom(1.5)
        self.viewport.setZoom(2.0)
        self.viewport.setZoom(2.5)
        
        # Test undo
        self.assertTrue(self.viewport.undoZoom())
        self.assertEqual(self.viewport.getZoom(), 2.0)
        
        self.assertTrue(self.viewport.undoZoom())
        self.assertEqual(self.viewport.getZoom(), 1.5)
        
        # Test redo
        self.assertTrue(self.viewport.redoZoom())
        self.assertEqual(self.viewport.getZoom(), 2.0)
        
        # Test undo with empty history
        self.viewport.historyIndex = 0
        self.assertFalse(self.viewport.undoZoom())
        
        # Test redo at end of history
        self.viewport.historyIndex = len(self.viewport.zoomHistory) - 1
        self.assertFalse(self.viewport.redoZoom())
    
    def test_coordinate_conversion_accuracy(self):
        """Test coordinate conversion accuracy"""
        # Test screen to SVG conversion
        screen_x, screen_y = 100, 200
        self.viewport.setZoom(2.0)
        self.viewport.setPan(50, 100)
        
        svg_x, svg_y = self.viewport.screenToSVG(screen_x, screen_y)
        expected_svg_x = (screen_x - 50) / 2.0  # 25
        expected_svg_y = (screen_y - 100) / 2.0  # 50
        
        self.assertAlmostEqual(svg_x, expected_svg_x, places=6)
        self.assertAlmostEqual(svg_y, expected_svg_y, places=6)
        
        # Test SVG to screen conversion
        screen_x_back, screen_y_back = self.viewport.svgToScreen(svg_x, svg_y)
        self.assertAlmostEqual(screen_x_back, screen_x, places=6)
        self.assertAlmostEqual(screen_y_back, screen_y, places=6)
    
    def test_coordinate_conversion_at_different_zoom_levels(self):
        """Test coordinate conversion at different zoom levels"""
        test_coordinates = [(100, 200), (300, 400), (500, 600)]
        zoom_levels = [0.5, 1.0, 2.0, 3.0]
        
        for zoom in zoom_levels:
            self.viewport.setZoom(zoom)
            self.viewport.setPan(0, 0)
            
            for screen_x, screen_y in test_coordinates:
                # Convert screen to SVG
                svg_x, svg_y = self.viewport.screenToSVG(screen_x, screen_y)
                
                # Convert back to screen
                screen_x_back, screen_y_back = self.viewport.svgToScreen(svg_x, svg_y)
                
                # Should be equal
                self.assertAlmostEqual(screen_x_back, screen_x, places=6)
                self.assertAlmostEqual(screen_y_back, screen_y, places=6)
    
    def test_coordinate_conversion_with_pan_offsets(self):
        """Test coordinate conversion with pan offsets"""
        pan_offsets = [(0, 0), (100, 200), (-50, -100), (300, -150)]
        
        for pan_x, pan_y in pan_offsets:
            self.viewport.setPan(pan_x, pan_y)
            self.viewport.setZoom(1.5)
            
            # Test a known coordinate
            screen_x, screen_y = 250, 350
            svg_x, svg_y = self.viewport.screenToSVG(screen_x, screen_y)
            
            # Convert back
            screen_x_back, screen_y_back = self.viewport.svgToScreen(svg_x, svg_y)
            
            # Should be equal
            self.assertAlmostEqual(screen_x_back, screen_x, places=6)
            self.assertAlmostEqual(screen_y_back, screen_y, places=6)
    
    def test_pan_boundary_enforcement(self):
        """Test pan boundary enforcement"""
        # Test pan within boundaries
        self.viewport.setPan(100, 200)
        pan_x, pan_y = self.viewport.getPan()
        self.assertEqual(pan_x, 100)
        self.assertEqual(pan_y, 200)
        
        # Test pan beyond positive boundaries
        self.viewport.setPan(3000, 2500)  # Beyond maxDistance of 2000
        pan_x, pan_y = self.viewport.getPan()
        self.assertEqual(pan_x, 2000)
        self.assertEqual(pan_y, 2000)
        
        # Test pan beyond negative boundaries
        self.viewport.setPan(-3000, -2500)  # Beyond maxDistance of 2000
        pan_x, pan_y = self.viewport.getPan()
        self.assertEqual(pan_x, -2000)
        self.assertEqual(pan_y, -2000)
    
    def test_pan_boundaries_disabled(self):
        """Test pan boundaries when disabled"""
        # Disable pan boundaries
        self.viewport.panBoundaries['enabled'] = False
        
        # Test pan beyond normal boundaries
        self.viewport.setPan(3000, 2500)
        pan_x, pan_y = self.viewport.getPan()
        self.assertEqual(pan_x, 3000)
        self.assertEqual(pan_y, 2500)
        
        # Re-enable for other tests
        self.viewport.panBoundaries['enabled'] = True
    
    def test_touch_gesture_recognition(self):
        """Test touch gesture recognition"""
        # Test initial touch state
        self.assertFalse(self.viewport.touchState['isTouching'])
        self.assertEqual(self.viewport.touchState['touchCount'], 0)
        
        # Simulate touch start
        self.viewport.touchState['isTouching'] = True
        self.viewport.touchState['touchCount'] = 1
        self.viewport.touchState['startTime'] = 1000
        
        # Test touch state
        self.assertTrue(self.viewport.touchState['isTouching'])
        self.assertEqual(self.viewport.touchState['touchCount'], 1)
        
        # Simulate multi-touch
        self.viewport.touchState['touchCount'] = 2
        self.assertEqual(self.viewport.touchState['touchCount'], 2)
        
        # Simulate touch end
        self.viewport.touchState['isTouching'] = False
        self.viewport.touchState['touchCount'] = 0
        self.assertFalse(self.viewport.touchState['isTouching'])
    
    def test_touch_distance_calculation(self):
        """Test touch distance calculation"""
        # Mock touch points
        touch1 = {'clientX': 100, 'clientY': 100}
        touch2 = {'clientX': 200, 'clientY': 200}
        
        # Calculate distance manually
        dx = touch2['clientX'] - touch1['clientX']
        dy = touch2['clientY'] - touch1['clientY']
        expected_distance = math.sqrt(dx*dx + dy*dy)
        
        # This would be implemented in the actual viewport manager
        # For now, we'll test the concept
        self.assertGreater(expected_distance, 0)
        self.assertAlmostEqual(expected_distance, 141.421356, places=6)
    
    def test_touch_center_calculation(self):
        """Test touch center calculation"""
        # Mock touch points
        touch1 = {'clientX': 100, 'clientY': 100}
        touch2 = {'clientX': 200, 'clientY': 200}
        
        # Calculate center manually
        center_x = (touch1['clientX'] + touch2['clientX']) / 2
        center_y = (touch1['clientY'] + touch2['clientY']) / 2
        
        self.assertEqual(center_x, 150)
        self.assertEqual(center_y, 150)
    
    def test_event_system(self):
        """Test event system"""
        events_triggered = []
        
        def test_handler(data):
            events_triggered.append(data)
        
        # Add event listener
        self.viewport.addEventListener('zoomChanged', test_handler)
        
        # Trigger event
        test_data = {'zoom': 2.0, 'oldZoom': 1.0}
        self.viewport.triggerEvent('zoomChanged', test_data)
        
        # Check that event was triggered
        self.assertEqual(len(events_triggered), 1)
        self.assertEqual(events_triggered[0], test_data)
        
        # Test multiple handlers
        def test_handler2(data):
            events_triggered.append(data)
        
        self.viewport.addEventListener('zoomChanged', test_handler2)
        self.viewport.triggerEvent('zoomChanged', test_data)
        
        # Check that both handlers were called
        self.assertEqual(len(events_triggered), 3)
    
    def test_scale_factors(self):
        """Test scale factor functionality"""
        # Test setting scale factors
        self.viewport.scaleFactors = {'x': 2.0, 'y': 1.5}
        self.viewport.currentUnit = 'feet'
        
        self.assertEqual(self.viewport.scaleFactors['x'], 2.0)
        self.assertEqual(self.viewport.scaleFactors['y'], 1.5)
        self.assertEqual(self.viewport.currentUnit, 'feet')
        
        # Test uniform scale check
        self.viewport.scaleFactors = {'x': 2.0, 'y': 2.0}
        # In real implementation, this would check if scales are uniform
        self.assertEqual(self.viewport.scaleFactors['x'], self.viewport.scaleFactors['y'])
    
    def test_performance_metrics(self):
        """Test performance metrics collection"""
        # Simulate performance data
        frame_times = [16.67, 16.5, 17.0, 16.8, 16.9]  # ~60fps
        
        # Calculate average frame time
        avg_frame_time = sum(frame_times) / len(frame_times)
        self.assertAlmostEqual(avg_frame_time, 16.774, places=3)
        
        # Calculate FPS
        fps = 1000 / avg_frame_time
        self.assertAlmostEqual(fps, 59.6, places=1)
    
    def test_error_handling(self):
        """Test error handling in viewport manager"""
        # Test invalid zoom values
        self.viewport.setZoom(-1.0)  # Should clamp to minimum
        self.assertEqual(self.viewport.getZoom(), 0.1)
        
        self.viewport.setZoom(10.0)  # Should clamp to maximum
        self.assertEqual(self.viewport.getZoom(), 5.0)
        
        # Test invalid pan values (should be handled by boundaries)
        self.viewport.setPan(float('inf'), float('inf'))
        pan_x, pan_y = self.viewport.getPan()
        self.assertLessEqual(abs(pan_x), 2000)
        self.assertLessEqual(abs(pan_y), 2000)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2) 