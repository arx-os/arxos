#!/usr/bin/env python3
"""
Unit Tests for Zoom Constraints and Boundaries
"""

import unittest
from unittest.mock import Mock
import math

# Mock ViewportManager for these tests
class MockViewportManager:
    def __init__(self, minZoom=0.1, maxZoom=5.0, zoomStep=0.1, maxHistorySize=50, panBoundaries=None):
        self.currentZoom = 1.0
        self.minZoom = minZoom
        self.maxZoom = maxZoom
        self.zoomStep = zoomStep
        self.zoomHistory = []
        self.maxHistorySize = maxHistorySize
        self.historyIndex = -1
        self.panX = 0
        self.panY = 0
        self.panBoundaries = panBoundaries or {'enabled': True, 'padding': 100, 'maxDistance': 2000}
    def setZoom(self, zoom):
        oldZoom = self.currentZoom
        self.currentZoom = max(self.minZoom, min(zoom, self.maxZoom))
        if self.currentZoom != oldZoom:
            self.saveZoomState()
    def zoomIn(self):
        self.setZoom(self.currentZoom + self.zoomStep)
    def zoomOut(self):
        self.setZoom(self.currentZoom - self.zoomStep)
    def saveZoomState(self):
        state = {'zoom': self.currentZoom, 'panX': self.panX, 'panY': self.panY}
        self.zoomHistory = self.zoomHistory[:self.historyIndex + 1]
        self.zoomHistory.append(state)
        self.historyIndex += 1
        if len(self.zoomHistory) > self.maxHistorySize:
            self.zoomHistory.pop(0)
            self.historyIndex -= 1
    def undoZoom(self):
        if self.historyIndex > 0:
            self.historyIndex -= 1
            state = self.zoomHistory[self.historyIndex]
            self.currentZoom = state['zoom']
            self.panX = state['panX']
            self.panY = state['panY']
            return True
        return False
    def redoZoom(self):
        if self.historyIndex < len(self.zoomHistory) - 1:
            self.historyIndex += 1
            state = self.zoomHistory[self.historyIndex]
            self.currentZoom = state['zoom']
            self.panX = state['panX']
            self.panY = state['panY']
            return True
        return False
    def setPan(self, x, y):
        if not self.panBoundaries['enabled']:
            self.panX, self.panY = x, y
        else:
            maxPan = self.panBoundaries['maxDistance']
            self.panX = max(-maxPan, min(x, maxPan))
            self.panY = max(-maxPan, min(y, maxPan))
    def getPan(self):
        return self.panX, self.panY

class TestZoomConstraints(unittest.TestCase):
    def setUp(self):
        self.viewport = MockViewportManager()
    def test_zoom_minimum_constraint(self):
        self.viewport.setZoom(0.05)
        self.assertEqual(self.viewport.currentZoom, 0.1)
    def test_zoom_maximum_constraint(self):
        self.viewport.setZoom(10.0)
        self.assertEqual(self.viewport.currentZoom, 5.0)
    def test_zoom_step_increments(self):
        self.viewport.setZoom(1.0)
        self.viewport.zoomIn()
        self.assertEqual(self.viewport.currentZoom, 1.1)
        self.viewport.zoomOut()
        self.assertEqual(self.viewport.currentZoom, 1.0)
    def test_zoom_history_max_size(self):
        for i in range(60):
            self.viewport.setZoom(1.0 + i * 0.1)
        self.assertLessEqual(len(self.viewport.zoomHistory), self.viewport.maxHistorySize)
    def test_zoom_undo_redo_edge_cases(self):
        self.viewport.setZoom(1.0)
        self.viewport.setZoom(1.5)
        self.viewport.setZoom(2.0)
        self.viewport.setZoom(2.5)
        self.assertTrue(self.viewport.undoZoom())
        self.assertEqual(self.viewport.currentZoom, 2.0)
        self.assertTrue(self.viewport.undoZoom())
        self.assertEqual(self.viewport.currentZoom, 1.5)
        self.viewport.historyIndex = 0
        self.assertFalse(self.viewport.undoZoom())
        self.viewport.historyIndex = len(self.viewport.zoomHistory) - 1
        self.assertFalse(self.viewport.redoZoom())
    def test_pan_within_boundaries(self):
        self.viewport.setPan(100, 200)
        pan_x, pan_y = self.viewport.getPan()
        self.assertEqual(pan_x, 100)
        self.assertEqual(pan_y, 200)
    def test_pan_beyond_boundaries(self):
        self.viewport.setPan(3000, 2500)
        pan_x, pan_y = self.viewport.getPan()
        self.assertEqual(pan_x, 2000)
        self.assertEqual(pan_y, 2000)
    def test_pan_negative_boundaries(self):
        self.viewport.setPan(-3000, -2500)
        pan_x, pan_y = self.viewport.getPan()
        self.assertEqual(pan_x, -2000)
        self.assertEqual(pan_y, -2000)
    def test_pan_boundaries_disabled(self):
        self.viewport.panBoundaries['enabled'] = False
        self.viewport.setPan(3000, 2500)
        pan_x, pan_y = self.viewport.getPan()
        self.assertEqual(pan_x, 3000)
        self.assertEqual(pan_y, 2500)
        self.viewport.panBoundaries['enabled'] = True

if __name__ == '__main__':
    unittest.main(verbosity=2) 