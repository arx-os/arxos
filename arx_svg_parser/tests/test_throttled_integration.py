#!/usr/bin/env python3
"""
Simple Integration Test for Throttled Updates (Phase 5.3)
Verifies that all components are properly integrated and accessible
"""

import os
import sys
import json

def test_file_existence():
    """Test that all required files exist"""
    print("=== Testing File Existence ===")
    
    required_files = [
        '../arx-web-frontend/static/js/throttled_update_manager.js',
        '../arx-web-frontend/static/js/throttled_update_tester.js',
        '../arx-web-frontend/svg_view.html',
        'test_throttled_updates.py',
        'PHASE_5_3_SUMMARY.md'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✓ {file_path}")
    
    if missing_files:
        print(f"✗ Missing files: {missing_files}")
        return False
    else:
        print("✓ All required files exist")
        return True

def test_js_file_content():
    """Test that JavaScript files contain expected content"""
    print("\n=== Testing JavaScript File Content ===")
    
    # Test throttled update manager
    manager_file = '../arx-web-frontend/static/js/throttled_update_manager.js'
    if os.path.exists(manager_file):
        with open(manager_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        expected_classes = ['ThrottledUpdateManager']
        expected_methods = ['queueUpdate', 'start', 'stop', 'getPerformanceMetrics']
        
        for class_name in expected_classes:
            if f'class {class_name}' in content:
                print(f"✓ Found class: {class_name}")
            else:
                print(f"✗ Missing class: {class_name}")
                return False
        
        for method_name in expected_methods:
            if method_name in content:
                print(f"✓ Found method: {method_name}")
            else:
                print(f"✗ Missing method: {method_name}")
                return False
    else:
        print(f"✗ File not found: {manager_file}")
        return False
    
    # Test throttled update tester
    tester_file = '../arx-web-frontend/static/js/throttled_update_tester.js'
    if os.path.exists(tester_file):
        with open(tester_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        expected_classes = ['ThrottledUpdateTester']
        expected_methods = ['runTest', 'calculateSmoothnessScore', 'getTestResultsSummary']
        
        for class_name in expected_classes:
            if f'class {class_name}' in content:
                print(f"✓ Found class: {class_name}")
            else:
                print(f"✗ Missing class: {class_name}")
                return False
        
        for method_name in expected_methods:
            if method_name in content:
                print(f"✓ Found method: {method_name}")
            else:
                print(f"✗ Missing method: {method_name}")
                return False
    else:
        print(f"✗ File not found: {tester_file}")
        return False
    
    return True

def test_html_integration():
    """Test that HTML file includes throttled update components"""
    print("\n=== Testing HTML Integration ===")
    
    html_file = '../arx-web-frontend/svg_view.html'
    if os.path.exists(html_file):
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for script includes
        expected_scripts = [
            'throttled_update_manager.js',
            'throttled_update_tester.js'
        ]
        
        for script in expected_scripts:
            if script in content:
                print(f"✓ Found script include: {script}")
            else:
                print(f"✗ Missing script include: {script}")
                return False
        
        # Check for UI controls
        expected_controls = [
            'test-throttled-toggle',
            'test-throttled-zoom',
            'test-throttled-pan',
            'test-throttled-batch',
            'test-throttled-device',
            'test-throttled-comprehensive',
            'test-throttled-report'
        ]
        
        for control in expected_controls:
            if control in content:
                print(f"✓ Found UI control: {control}")
            else:
                print(f"✗ Missing UI control: {control}")
                return False
        
        # Check for JavaScript functions
        expected_functions = [
            'initializeThrottledUpdateComponents',
            'toggleThrottledUpdates',
            'runThrottledTest',
            'generateThrottledReport'
        ]
        
        for function in expected_functions:
            if function in content:
                print(f"✓ Found function: {function}")
            else:
                print(f"✗ Missing function: {function}")
                return False
    else:
        print(f"✗ File not found: {html_file}")
        return False
    
    return True

def test_viewport_manager_integration():
    """Test that viewport manager includes throttled update integration"""
    print("\n=== Testing Viewport Manager Integration ===")
    
    viewport_file = '../arx-web-frontend/static/js/viewport_manager.js'
    if os.path.exists(viewport_file):
        with open(viewport_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for throttled update integration
        expected_integration = [
            'throttledUpdateManager',
            'enableThrottledUpdates',
            'connectToThrottledUpdateManager',
            'handleThrottledUpdate',
            'handleBatchedUpdate',
            'performViewportUpdate'
        ]
        
        for integration in expected_integration:
            if integration in content:
                print(f"✓ Found integration: {integration}")
            else:
                print(f"✗ Missing integration: {integration}")
                return False
    else:
        print(f"✗ File not found: {viewport_file}")
        return False
    
    return True

def test_summary_document():
    """Test that summary document is comprehensive"""
    print("\n=== Testing Summary Document ===")
    
    summary_file = 'PHASE_5_3_SUMMARY.md'
    if os.path.exists(summary_file):
        with open(summary_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required sections
        expected_sections = [
            '## Overview',
            '## Components Implemented',
            '## Technical Specifications',
            '## Integration Points',
            '## Performance Results',
            '## Testing',
            '## Usage Instructions'
        ]
        
        for section in expected_sections:
            if section in content:
                print(f"✓ Found section: {section}")
            else:
                print(f"✗ Missing section: {section}")
                return False
        
        # Check for component descriptions
        expected_components = [
            'Throttled Update Manager',
            'Throttled Update Tester',
            'Enhanced Viewport Manager Integration',
            'Frontend Integration'
        ]
        
        for component in expected_components:
            if component in content:
                print(f"✓ Found component: {component}")
            else:
                print(f"✗ Missing component: {component}")
                return False
    else:
        print(f"✗ File not found: {summary_file}")
        return False
    
    return True

def main():
    """Run all integration tests"""
    print("THROTTLED UPDATES INTEGRATION TEST")
    print("=" * 50)
    
    tests = [
        test_file_existence,
        test_js_file_content,
        test_html_integration,
        test_viewport_manager_integration,
        test_summary_document
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
    
    print("\n" + "=" * 50)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 50)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All integration tests passed!")
        print("Phase 5.3 - Throttled Updates is properly integrated!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("Please check the implementation and fix any issues.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 