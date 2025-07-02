#!/usr/bin/env python3
"""
Simple Test Runner for Arxos Platform

This script provides a simple way to run comprehensive tests for the Arxos platform.
It runs all test suites and provides a summary of results.

Usage:
    python run_tests.py
"""

import sys
import os
import subprocess
import time
from datetime import datetime

def run_test_suite(test_file, description):
    """Run a test suite and return results"""
    print(f"\n{'='*60}")
    print(f"Running {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Run pytest for the test file
        result = subprocess.run([
            sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ {description} PASSED ({duration:.2f}s)")
            return True, duration, result.stdout
        else:
            print(f"❌ {description} FAILED ({duration:.2f}s)")
            print(f"Error output:\n{result.stderr}")
            return False, duration, result.stderr
            
    except Exception as e:
        print(f"❌ {description} ERROR: {e}")
        return False, 0, str(e)

def main():
    """Main function to run all tests"""
    print("Arxos Platform - Comprehensive Test Runner")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Define test suites
    test_suites = [
        ("tests/test_comprehensive_unit.py", "Unit Tests"),
        ("tests/test_integration_comprehensive.py", "Integration Tests"),
        ("tests/test_edge_cases_comprehensive.py", "Edge Case Tests"),
        ("tests/test_stress_performance.py", "Performance Tests")
    ]
    
    results = []
    total_duration = 0
    
    # Run each test suite
    for test_file, description in test_suites:
        success, duration, output = run_test_suite(test_file, description)
        results.append({
            "description": description,
            "success": success,
            "duration": duration,
            "output": output
        })
        total_duration += duration
    
    # Calculate summary
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["success"])
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    # Print summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Total Test Suites: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Total Duration: {total_duration:.2f}s")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Print detailed results
    print(f"\nDetailed Results:")
    print(f"{'-'*40}")
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status} {result['description']} ({result['duration']:.2f}s)")
    
    # Final status
    print(f"\n{'='*80}")
    if failed_tests == 0:
        print("🎉 ALL TESTS PASSED!")
        print("Arxos platform is ready for production deployment.")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("Please review the failing tests before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 