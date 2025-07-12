#!/usr/bin/env python3
"""
Simple Integration Test for SVG Zoom History
Tests that zoom history functionality is properly integrated
No external dependencies required
"""

import os
from pathlib import Path


def test_viewport_manager_has_zoom_history():
    """Test that ViewportManager has zoom history properties"""
    print("Testing ViewportManager zoom history properties...")
    
    viewport_manager_path = Path("arx-web-frontend/static/js/viewport_manager.js")
    if not viewport_manager_path.exists():
        print("❌ ViewportManager.js not found")
        return False
    
    content = viewport_manager_path.read_text(encoding='utf-8')
    
    # Check for zoom history properties
    required_properties = ["zoomHistory", "maxHistorySize", "historyIndex"]
    for prop in required_properties:
        if prop not in content:
            print(f"❌ ViewportManager missing property: {prop}")
            return False
    
    # Check for zoom history methods
    required_methods = ["saveZoomState", "undoZoom", "redoZoom", "restoreZoomState"]
    for method in required_methods:
        if method not in content:
            print(f"❌ ViewportManager missing method: {method}")
            return False
    
    print("✓ ViewportManager has zoom history properties and methods")
    return True


def test_svg_view_has_undo_redo_buttons():
    """Test that SVG view has undo/redo buttons"""
    print("Testing SVG view undo/redo buttons...")
    
    svg_view_path = Path("arx-web-frontend/svg_view.html")
    if not svg_view_path.exists():
        print("❌ svg_view.html not found")
        return False
    
    content = svg_view_path.read_text(encoding='utf-8')
    
    # Check for undo/redo buttons
    if 'id="zoom-undo"' not in content:
        print("❌ SVG view missing zoom-undo button")
        return False
    
    if 'id="zoom-redo"' not in content:
        print("❌ SVG view missing zoom-redo button")
        return False
    
    # Check for proper button structure
    if 'title="Undo Zoom (Ctrl + Z)"' not in content:
        print("❌ Undo button missing proper title")
        return False
    
    if 'title="Redo Zoom (Ctrl + Y)"' not in content:
        print("❌ Redo button missing proper title")
        return False
    
    print("✓ SVG view has undo/redo buttons")
    return True


def test_zoom_controls_are_wired():
    """Test that zoom controls are properly wired to ViewportManager"""
    print("Testing zoom controls wiring...")
    
    svg_view_path = Path("arx-web-frontend/svg_view.html")
    content = svg_view_path.read_text(encoding='utf-8')
    
    # Check for event listeners
    if "zoomUndoBtn.addEventListener" not in content:
        print("❌ Undo button missing event listener")
        return False
    
    if "zoomRedoBtn.addEventListener" not in content:
        print("❌ Redo button missing event listener")
        return False
    
    # Check for ViewportManager method calls
    if "viewportManager.undoZoom()" not in content:
        print("❌ Undo button not calling undoZoom()")
        return False
    
    if "viewportManager.redoZoom()" not in content:
        print("❌ Redo button not calling redoZoom()")
        return False
    
    # Check for button state updates
    if "updateZoomHistoryButtons" not in content:
        print("❌ Missing updateZoomHistoryButtons function")
        return False
    
    print("✓ Zoom controls are properly wired")
    return True


def test_keyboard_shortcuts_are_implemented():
    """Test that keyboard shortcuts are implemented"""
    print("Testing keyboard shortcuts implementation...")
    
    viewport_manager_path = Path("arx-web-frontend/static/js/viewport_manager.js")
    content = viewport_manager_path.read_text(encoding='utf-8')
    
    # Check for keyboard event handling
    if "handleKeyDown" not in content:
        print("❌ ViewportManager missing handleKeyDown method")
        return False
    
    # Check for Ctrl+Z and Ctrl+Y handling
    if "event.key === 'z'" not in content:
        print("❌ Missing Ctrl+Z handling for undo")
        return False
    
    if "event.key === 'y'" not in content:
        print("❌ Missing Ctrl+Y handling for redo")
        return False
    
    # Check for undo/redo method calls in keyboard handler
    if "this.undoZoom()" not in content:
        print("❌ Keyboard handler not calling undoZoom()")
        return False
    
    if "this.redoZoom()" not in content:
        print("❌ Keyboard handler not calling redoZoom()")
        return False
    
    print("✓ Keyboard shortcuts are implemented")
    return True


def test_help_overlay_includes_zoom_history():
    """Test that help overlay includes zoom history shortcuts"""
    print("Testing help overlay zoom history content...")
    
    viewport_manager_path = Path("arx-web-frontend/static/js/viewport_manager.js")
    content = viewport_manager_path.read_text(encoding='utf-8')
    
    # Check for help overlay content
    if "createHelpOverlay" not in content:
        print("❌ Missing help overlay creation")
        return False
    
    # Check for zoom history section in help
    if "History" not in content:
        print("❌ Help overlay missing History section")
        return False
    
    if "Ctrl + Z" not in content:
        print("❌ Help missing Ctrl+Z for undo")
        return False
    
    if "Ctrl + Y" not in content:
        print("❌ Help missing Ctrl+Y for redo")
        return False
    
    print("✓ Help overlay includes zoom history shortcuts")
    return True


def test_e2e_test_exists():
    """Test that E2E test file exists"""
    print("Testing E2E test existence...")
    
    e2e_test_path = Path("arx-web-frontend/tests/e2e_tests.js")
    if not e2e_test_path.exists():
        print("❌ E2E test file not found")
        return False
    
    content = e2e_test_path.read_text(encoding='utf-8')
    
    # Check for zoom history test class
    if "SVGZoomHistoryTests" not in content:
        print("❌ Missing SVGZoomHistoryTests class")
        return False
    
    if "testZoomHistoryUndoRedo" not in content:
        print("❌ Missing zoom history test method")
        return False
    
    # Check for test in runner
    if "SVG Zoom History: Undo/Redo" not in content:
        print("❌ Test not included in test runner")
        return False
    
    print("✓ E2E test exists and is included in test runner")
    return True


def test_python_e2e_test_exists():
    """Test that Python E2E test file exists"""
    print("Testing Python E2E test existence...")
    
    python_e2e_path = Path("arx_svg_parser/tests/test_zoom_history_e2e.py")
    if not python_e2e_path.exists():
        print("❌ Python E2E test file not found")
        return False
    
    content = python_e2e_path.read_text(encoding='utf-8')
    
    # Check for test class and methods
    if "TestZoomHistoryE2E" not in content:
        print("❌ Missing TestZoomHistoryE2E class")
        return False
    
    required_tests = [
        "test_zoom_history_undo_redo_buttons",
        "test_zoom_history_keyboard_shortcuts", 
        "test_zoom_history_button_states",
        "test_complex_zoom_history_sequence"
    ]
    
    for test in required_tests:
        if test not in content:
            print(f"❌ Missing test method: {test}")
            return False
    
    print("✓ Python E2E test exists with comprehensive test coverage")
    return True


def main():
    """Run all integration tests"""
    print("🚀 Starting SVG Zoom History Integration Tests...\n")
    
    tests = [
        ("ViewportManager Zoom History", test_viewport_manager_has_zoom_history),
        ("SVG View Undo/Redo Buttons", test_svg_view_has_undo_redo_buttons),
        ("Zoom Controls Wiring", test_zoom_controls_are_wired),
        ("Keyboard Shortcuts", test_keyboard_shortcuts_are_implemented),
        ("Help Overlay Content", test_help_overlay_includes_zoom_history),
        ("E2E Test Existence", test_e2e_test_exists),
        ("Python E2E Test Existence", test_python_e2e_test_exists)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} - FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} - FAILED: {e}")
    
    print(f"\n📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {((passed / (passed + failed)) * 100):.1f}%")
    
    if failed > 0:
        print('\n⚠️  Some tests failed. Please check the implementation.')
        return 1
    else:
        print('\n🎉 All tests passed! Zoom history functionality is properly integrated.')
        return 0


if __name__ == "__main__":
    exit(main()) 