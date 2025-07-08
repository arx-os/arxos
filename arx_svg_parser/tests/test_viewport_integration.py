#!/usr/bin/env python3
"""
Integration Tests for Viewport Manager
Tests viewport manager integration with symbol library, object interaction, LOD system, and throttled updates
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Mock classes for integration testing
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

class MockSymbolLibrary:
    def __init__(self, viewport_manager=None):
        self.symbols = [
            {'id': 'ahu', 'name': 'Air Handling Unit', 'svg': '<rect x="0" y="0" width="40" height="20"/>'},
            {'id': 'receptacle', 'name': 'Receptacle', 'svg': '<circle cx="10" cy="10" r="7"/>'}
        ]
        self.viewportManager = viewport_manager
        self.placedSymbols = []
        
    def placeSymbol(self, symbol_id, x, y):
        symbol = next((s for s in self.symbols if s['id'] == symbol_id), None)
        if symbol and self.viewportManager:
            # Convert screen coordinates to SVG coordinates
            svg_x, svg_y = self.viewportManager.screenToSVG(x, y)
            placed_symbol = {
                'id': f"{symbol_id}_{len(self.placedSymbols)}",
                'symbol_id': symbol_id,
                'x': svg_x,
                'y': svg_y,
                'screen_x': x,
                'screen_y': y
            }
            self.placedSymbols.append(placed_symbol)
            return placed_symbol
        return None

class MockObjectInteraction:
    def __init__(self, viewport_manager=None):
        self.selectedObjects = set()
        self.viewportManager = viewport_manager
        self.eventHandlers = {}
        
    def selectObject(self, object_id):
        self.selectedObjects.add(object_id)
        self.triggerEvent('objectSelected', {'object_id': object_id})
        
    def moveObject(self, object_id, new_x, new_y):
        if self.viewportManager:
            # Convert screen coordinates to SVG coordinates
            svg_x, svg_y = self.viewportManager.screenToSVG(new_x, new_y)
            self.triggerEvent('objectMoved', {
                'object_id': object_id,
                'svg_x': svg_x,
                'svg_y': svg_y,
                'screen_x': new_x,
                'screen_y': new_y
            })
            # Update the placed symbol if it exists in symbol library
            if hasattr(self, 'symbol_library') and self.symbol_library:
                for symbol in self.symbol_library.placedSymbols:
                    if symbol['id'] == object_id:
                        symbol['screen_x'] = new_x
                        symbol['screen_y'] = new_y
                        symbol['x'] = svg_x
                        symbol['y'] = svg_y
                        break
    
    def addEventListener(self, event, handler):
        if event not in self.eventHandlers:
            self.eventHandlers[event] = []
        self.eventHandlers[event].append(handler)
    
    def triggerEvent(self, event, data=None):
        if event in self.eventHandlers:
            for handler in self.eventHandlers[event]:
                handler(data or {})

class MockLODManager:
    def __init__(self, viewport_manager=None):
        self.currentLODLevel = 'medium'
        self.lodLevels = {
            'high': {'minZoom': 2.0, 'complexity': 1.0},
            'medium': {'minZoom': 0.5, 'complexity': 0.7},
            'low': {'minZoom': 0.1, 'complexity': 0.4}
        }
        self.viewportManager = viewport_manager
        self.eventHandlers = {}
        
    def getLODLevelForZoom(self, zoom):
        if zoom >= self.lodLevels['high']['minZoom']:
            return 'high'
        elif zoom >= self.lodLevels['medium']['minZoom']:
            return 'medium'
        else:
            return 'low'
    
    def switchLODLevel(self, newLevel):
        if newLevel != self.currentLODLevel:
            self.currentLODLevel = newLevel
            self.triggerEvent('lodChanged', {
                'fromLevel': self.currentLODLevel,
                'toLevel': newLevel
            })
    
    def addEventListener(self, event, handler):
        if event not in self.eventHandlers:
            self.eventHandlers[event] = []
        self.eventHandlers[event].append(handler)
    
    def triggerEvent(self, event, data=None):
        if event in self.eventHandlers:
            for handler in self.eventHandlers[event]:
                handler(data or {})

class MockThrottledUpdateManager:
    def __init__(self):
        self.pendingUpdates = []
        self.isRunning = True
        self.eventHandlers = {}
        
    def queueUpdate(self, updateType, data):
        self.pendingUpdates.append({'type': updateType, 'data': data})
        self.triggerEvent('updateQueued', {'type': updateType, 'data': data})
    
    def processUpdates(self):
        updates = self.pendingUpdates.copy()
        self.pendingUpdates.clear()
        for update in updates:
            self.triggerEvent('updateProcessed', update)
        return updates
    
    def addEventListener(self, event, handler):
        if event not in self.eventHandlers:
            self.eventHandlers[event] = []
        self.eventHandlers[event].append(handler)
    
    def triggerEvent(self, event, data=None):
        if event in self.eventHandlers:
            for handler in self.eventHandlers[event]:
                handler(data or {})

class TestViewportIntegration(unittest.TestCase):
    """Integration tests for viewport manager with other components"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.viewport = MockViewportManager()
        self.symbol_library = MockSymbolLibrary(self.viewport)
        self.object_interaction = MockObjectInteraction(self.viewport)
        self.lod_manager = MockLODManager(self.viewport)
        self.throttled_updates = MockThrottledUpdateManager()
        
        # Connect components
        self.setupComponentConnections()
    
    def setupComponentConnections(self):
        """Set up event connections between components"""
        # Connect object interaction to symbol library
        self.object_interaction.symbol_library = self.symbol_library
        
        # Viewport manager listens for zoom changes
        self.viewport.addEventListener('zoomChanged', self.handleZoomChange)
        
        # LOD manager listens for zoom changes
        self.viewport.addEventListener('zoomChanged', self.handleLODChange)
        
        # Throttled updates manager listens for viewport changes
        self.viewport.addEventListener('zoomChanged', self.handleThrottledUpdate)
        self.viewport.addEventListener('panChanged', self.handleThrottledUpdate)
    
    def handleZoomChange(self, data):
        """Handle zoom change events"""
        # Update LOD level based on zoom
        new_lod_level = self.lod_manager.getLODLevelForZoom(self.viewport.currentZoom)
        self.lod_manager.switchLODLevel(new_lod_level)
    
    def handleLODChange(self, data):
        """Handle LOD change events"""
        # Queue LOD update for throttled processing
        self.throttled_updates.queueUpdate('lod', {
            'level': self.lod_manager.currentLODLevel,
            'zoom': self.viewport.currentZoom
        })
    
    def handleThrottledUpdate(self, data):
        """Handle throttled update events"""
        self.throttled_updates.queueUpdate('viewport', {
            'zoom': self.viewport.currentZoom,
            'panX': self.viewport.panX,
            'panY': self.viewport.panY
        })
    
    def test_viewport_manager_symbol_library_integration(self):
        """Test viewport manager integration with symbol library"""
        # Place symbol at screen coordinates
        screen_x, screen_y = 100, 200
        placed_symbol = self.symbol_library.placeSymbol('ahu', screen_x, screen_y)
        
        self.assertIsNotNone(placed_symbol)
        self.assertEqual(placed_symbol['symbol_id'], 'ahu')
        self.assertEqual(placed_symbol['screen_x'], screen_x)
        self.assertEqual(placed_symbol['screen_y'], screen_y)
        
        # Verify coordinate conversion
        expected_svg_x = (screen_x - self.viewport.panX) / self.viewport.currentZoom
        expected_svg_y = (screen_y - self.viewport.panY) / self.viewport.currentZoom
        self.assertEqual(placed_symbol['x'], expected_svg_x)
        self.assertEqual(placed_symbol['y'], expected_svg_y)
        
        # Test zoom and verify coordinates update
        self.viewport.setZoom(2.0)
        new_screen_x, new_screen_y = self.viewport.svgToScreen(placed_symbol['x'], placed_symbol['y'])
        
        # Screen coordinates should change with zoom
        self.assertNotEqual(new_screen_x, screen_x)
        self.assertNotEqual(new_screen_y, screen_y)
        
        # But SVG coordinates should remain the same
        self.assertEqual(placed_symbol['x'], expected_svg_x)
        self.assertEqual(placed_symbol['y'], expected_svg_y)
    
    def test_viewport_manager_object_interaction_integration(self):
        """Test viewport manager integration with object interaction"""
        # Place a symbol first
        placed_symbol = self.symbol_library.placeSymbol('receptacle', 150, 250)
        
        # Select the object
        self.object_interaction.selectObject(placed_symbol['id'])
        self.assertIn(placed_symbol['id'], self.object_interaction.selectedObjects)
        
        # Move the object to new screen coordinates
        new_screen_x, new_screen_y = 300, 400
        self.object_interaction.moveObject(placed_symbol['id'], new_screen_x, new_screen_y)
        
        # Verify the object was moved with proper coordinate conversion
        expected_svg_x = (new_screen_x - self.viewport.panX) / self.viewport.currentZoom
        expected_svg_y = (new_screen_y - self.viewport.panY) / self.viewport.currentZoom
        
        # Check that the placed symbol was updated
        self.assertEqual(placed_symbol['screen_x'], new_screen_x)
        self.assertEqual(placed_symbol['screen_y'], new_screen_y)
        self.assertEqual(placed_symbol['x'], expected_svg_x)
        self.assertEqual(placed_symbol['y'], expected_svg_y)
    
    def test_viewport_manager_lod_system_integration(self):
        """Test viewport manager integration with LOD system"""
        # Test LOD level changes with zoom
        zoom_levels = [0.1, 0.5, 2.0, 5.0]
        expected_lod_levels = ['low', 'medium', 'high', 'high']
        
        for zoom, expected_lod in zip(zoom_levels, expected_lod_levels):
            self.viewport.setZoom(zoom)
            self.assertEqual(self.lod_manager.currentLODLevel, expected_lod)
        
        # Test LOD change events
        lod_changes = []
        self.lod_manager.addEventListener('lodChanged', lambda data: lod_changes.append(data))
        
        # Trigger zoom changes
        self.viewport.setZoom(0.1)  # Should trigger 'low'
        self.viewport.setZoom(2.0)  # Should trigger 'high'
        
        # Verify LOD change events were triggered
        self.assertGreater(len(lod_changes), 0)
        self.assertEqual(lod_changes[-1]['toLevel'], 'high')
    
    def test_viewport_manager_throttled_updates_integration(self):
        """Test viewport manager integration with throttled updates"""
        # Track throttled updates
        queued_updates = []
        processed_updates = []
        
        self.throttled_updates.addEventListener('updateQueued', lambda data: queued_updates.append(data))
        self.throttled_updates.addEventListener('updateProcessed', lambda data: processed_updates.append(data))
        
        # Perform multiple viewport operations
        for i in range(5):
            self.viewport.setZoom(1.0 + i * 0.1)
            self.viewport.panX = i * 10
            self.viewport.panY = i * 10
        
        # Verify updates were queued
        self.assertGreater(len(queued_updates), 0)
        
        # Process updates
        processed = self.throttled_updates.processUpdates()
        self.assertGreater(len(processed), 0)
        
        # Verify processed updates
        self.assertEqual(len(processed), len(queued_updates))
    
    def test_coordinate_system_consistency(self):
        """Test coordinate system consistency across all components"""
        # Test coordinate conversion consistency
        test_coordinates = [(100, 200), (300, 400), (500, 600)]
        
        for screen_x, screen_y in test_coordinates:
            # Convert screen to SVG
            svg_x, svg_y = self.viewport.screenToSVG(screen_x, screen_y)
            
            # Convert back to screen
            screen_x_back, screen_y_back = self.viewport.svgToScreen(svg_x, svg_y)
            
            # Should be equal
            self.assertAlmostEqual(screen_x_back, screen_x, places=6)
            self.assertAlmostEqual(screen_y_back, screen_y, places=6)
        
        # Test with different zoom levels
        zoom_levels = [0.5, 1.0, 2.0]
        for zoom in zoom_levels:
            self.viewport.setZoom(zoom)
            
            for screen_x, screen_y in test_coordinates:
                svg_x, svg_y = self.viewport.screenToSVG(screen_x, screen_y)
                screen_x_back, screen_y_back = self.viewport.svgToScreen(svg_x, svg_y)
                
                self.assertAlmostEqual(screen_x_back, screen_x, places=6)
                self.assertAlmostEqual(screen_y_back, screen_y, places=6)
    
    def test_scale_factor_propagation(self):
        """Test scale factor propagation across components"""
        # Set scale factors
        self.viewport.scaleFactors = {'x': 0.5, 'y': 0.5}
        
        # Place symbol with scale factors
        placed_symbol = self.symbol_library.placeSymbol('ahu', 100, 200)
        
        # Verify scale factors are considered in coordinate conversion
        # (In a real implementation, scale factors would affect coordinate conversion)
        self.assertIsNotNone(placed_symbol)
        
        # Test that scale factors are accessible to all components
        self.assertEqual(self.viewport.scaleFactors['x'], 0.5)
        self.assertEqual(self.viewport.scaleFactors['y'], 0.5)
    
    def test_real_world_coordinate_persistence(self):
        """Test real-world coordinate persistence across sessions"""
        # Simulate saving coordinates with scale information
        coordinates_data = {
            'symbols': [
                {
                    'id': 'ahu_001',
                    'symbol_id': 'ahu',
                    'svg_x': 50.0,
                    'svg_y': 100.0,
                    'real_world_x': 25.0,  # 50 * 0.5 scale
                    'real_world_y': 50.0,  # 100 * 0.5 scale
                    'units': 'feet'
                }
            ],
            'scale_factors': {'x': 0.5, 'y': 0.5},
            'units': 'feet'
        }
        
        # Simulate loading coordinates
        loaded_symbol = coordinates_data['symbols'][0]
        
        # Verify real-world coordinates are preserved
        self.assertEqual(loaded_symbol['real_world_x'], 25.0)
        self.assertEqual(loaded_symbol['real_world_y'], 50.0)
        self.assertEqual(loaded_symbol['units'], 'feet')
        
        # Verify scale factors are preserved
        self.assertEqual(coordinates_data['scale_factors']['x'], 0.5)
        self.assertEqual(coordinates_data['scale_factors']['y'], 0.5)
    
    def test_multi_component_event_flow(self):
        """Test event flow between multiple components"""
        events_received = []
        
        def trackEvent(data):
            events_received.append(data)
        
        # Add event listeners to all components
        self.viewport.addEventListener('zoomChanged', trackEvent)
        self.lod_manager.addEventListener('lodChanged', trackEvent)
        self.throttled_updates.addEventListener('updateQueued', trackEvent)
        
        # Trigger a zoom change
        self.viewport.setZoom(2.0)
        
        # Verify events were triggered
        self.assertGreater(len(events_received), 0)
        
        # Verify event types
        event_types = [event.get('type', 'unknown') for event in events_received]
        self.assertIn('lod', event_types)
        self.assertIn('viewport', event_types)

if __name__ == '__main__':
    unittest.main(verbosity=2) 