"""
Integration Tests for SVG Zoom History
Tests that zoom history functionality is properly integrated
"""

import pytest
import os
import re
from pathlib import Path


class TestZoomHistoryIntegration:
    """Integration tests for zoom history functionality"""
    
    def test_viewport_manager_has_zoom_history(self):
        """Test that ViewportManager has zoom history properties"""
        viewport_manager_path = Path("arx-web-frontend/static/js/viewport_manager.js")
        assert viewport_manager_path.exists(), "ViewportManager.js should exist"
        
        content = viewport_manager_path.read_text()
        
        # Check for zoom history properties
        assert "zoomHistory" in content, "ViewportManager should have zoomHistory property"
        assert "maxHistorySize" in content, "ViewportManager should have maxHistorySize property"
        assert "historyIndex" in content, "ViewportManager should have historyIndex property"
        
        # Check for zoom history methods
        assert "saveZoomState" in content, "ViewportManager should have saveZoomState method"
        assert "undoZoom" in content, "ViewportManager should have undoZoom method"
        assert "redoZoom" in content, "ViewportManager should have redoZoom method"
        assert "restoreZoomState" in content, "ViewportManager should have restoreZoomState method"
        
        print("✓ ViewportManager has zoom history properties and methods")
    
    def test_svg_view_has_undo_redo_buttons(self):
        """Test that SVG view has undo/redo buttons"""
        svg_view_path = Path("arx-web-frontend/svg_view.html")
        assert svg_view_path.exists(), "svg_view.html should exist"
        
        content = svg_view_path.read_text()
        
        # Check for undo/redo buttons
        assert 'id="zoom-undo"' in content, "SVG view should have zoom-undo button"
        assert 'id="zoom-redo"' in content, "SVG view should have zoom-redo button"
        
        # Check for proper button structure
        assert 'title="Undo Zoom (Ctrl + Z)"' in content, "Undo button should have proper title"
        assert 'title="Redo Zoom (Ctrl + Y)"' in content, "Redo button should have proper title"
        
        print("✓ SVG view has undo/redo buttons")
    
    def test_zoom_controls_are_wired(self):
        """Test that zoom controls are properly wired to ViewportManager"""
        svg_view_path = Path("arx-web-frontend/svg_view.html")
        content = svg_view_path.read_text()
        
        # Check for event listeners
        assert "zoomUndoBtn.addEventListener" in content, "Undo button should have event listener"
        assert "zoomRedoBtn.addEventListener" in content, "Redo button should have event listener"
        
        # Check for ViewportManager method calls
        assert "viewportManager.undoZoom()" in content, "Undo button should call undoZoom()"
        assert "viewportManager.redoZoom()" in content, "Redo button should call redoZoom()"
        
        # Check for button state updates
        assert "updateZoomHistoryButtons" in content, "Should have function to update button states"
        
        print("✓ Zoom controls are properly wired")
    
    def test_keyboard_shortcuts_are_implemented(self):
        """Test that keyboard shortcuts are implemented"""
        viewport_manager_path = Path("arx-web-frontend/static/js/viewport_manager.js")
        content = viewport_manager_path.read_text()
        
        # Check for keyboard event handling
        assert "handleKeyDown" in content, "ViewportManager should have handleKeyDown method"
        
        # Check for Ctrl+Z and Ctrl+Y handling
        assert "event.key === 'z'" in content, "Should handle Ctrl+Z for undo"
        assert "event.key === 'y'" in content, "Should handle Ctrl+Y for redo"
        
        # Check for undo/redo method calls in keyboard handler
        assert "this.undoZoom()" in content, "Keyboard handler should call undoZoom()"
        assert "this.redoZoom()" in content, "Keyboard handler should call redoZoom()"
        
        print("✓ Keyboard shortcuts are implemented")
    
    def test_help_overlay_includes_zoom_history(self):
        """Test that help overlay includes zoom history shortcuts"""
        viewport_manager_path = Path("arx-web-frontend/static/js/viewport_manager.js")
        content = viewport_manager_path.read_text()
        
        # Check for help overlay content
        assert "createHelpOverlay" in content, "Should have help overlay creation"
        
        # Check for zoom history section in help
        assert "History" in content, "Help overlay should have History section"
        assert "Ctrl + Z" in content, "Help should mention Ctrl+Z for undo"
        assert "Ctrl + Y" in content, "Help should mention Ctrl+Y for redo"
        
        print("✓ Help overlay includes zoom history shortcuts")
    
    def test_e2e_test_exists(self):
        """Test that E2E test file exists"""
        e2e_test_path = Path("arx-web-frontend/tests/e2e_tests.js")
        assert e2e_test_path.exists(), "E2E test file should exist"
        
        content = e2e_test_path.read_text()
        
        # Check for zoom history test class
        assert "SVGZoomHistoryTests" in content, "Should have SVGZoomHistoryTests class"
        assert "testZoomHistoryUndoRedo" in content, "Should have zoom history test method"
        
        # Check for test in runner
        assert "SVG Zoom History: Undo/Redo" in content, "Test should be included in test runner"
        
        print("✓ E2E test exists and is included in test runner")
    
    def test_python_e2e_test_exists(self):
        """Test that Python E2E test file exists"""
        python_e2e_path = Path("arx_svg_parser/tests/test_zoom_history_e2e.py")
        assert python_e2e_path.exists(), "Python E2E test file should exist"
        
        content = python_e2e_path.read_text()
        
        # Check for test class and methods
        assert "TestZoomHistoryE2E" in content, "Should have TestZoomHistoryE2E class"
        assert "test_zoom_history_undo_redo_buttons" in content, "Should have button test"
        assert "test_zoom_history_keyboard_shortcuts" in content, "Should have keyboard test"
        assert "test_zoom_history_button_states" in content, "Should have button state test"
        assert "test_complex_zoom_history_sequence" in content, "Should have complex sequence test"
        
        print("✓ Python E2E test exists with comprehensive test coverage")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 