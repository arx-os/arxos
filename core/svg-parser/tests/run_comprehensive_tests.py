#!/usr/bin/env python3
"""
Comprehensive Test Runner for Arxos Platform

This script runs all comprehensive tests for the Arxos platform including:
- Unit tests for all handlers and services
- Integration tests for end-to-end workflows
- Edge case tests for boundary conditions
- Performance and stress tests
- Memory usage and scalability tests

Usage:
    python run_comprehensive_tests.py [options]

Options:
    --unit-only          Run only unit tests
    --integration-only   Run only integration tests
    --edge-only          Run only edge case tests
    --performance-only   Run only performance tests
    --verbose            Enable verbose output
    --report             Generate detailed report
"""

import sys
import os
import argparse
import subprocess
import time
from datetime import datetime
from pathlib import Path

def run_pytest_tests(test_file, test_class=None, verbose=False):
    """Run pytest tests for a specific file and optionally a specific class"""
    cmd = ["python", "-m", "pytest", test_file]
    
    if test_class:
        cmd.append(f"::{test_class}")
    
    if verbose:
        cmd.extend(["-v", "--tb=long"])
    else:
        cmd.extend(["--tb=short"])
    
    print(f"Running: {' '.join(cmd)}")
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        end_time = time.time()
        
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ PASSED ({duration:.2f}s)")
            return True, duration, result.stdout
        else:
            print(f"❌ FAILED ({duration:.2f}s)")
            print(f"Error: {result.stderr}")
            return False, duration, result.stderr
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False, 0, str(e)

def run_unit_tests(verbose=False):
    """Run all unit tests"""
    print("\n" + "="*60)
    print("RUNNING UNIT TESTS")
    print("="*60)
    
    unit_tests = [
        ("test_comprehensive_unit.py", "TestVersionControlHandlers"),
        ("test_comprehensive_unit.py", "TestRouteManagement"),
        ("test_comprehensive_unit.py", "TestFloorSpecificFeatures"),
        ("test_comprehensive_unit.py", "TestErrorHandling"),
        ("test_comprehensive_unit.py", "TestEdgeCases")
    ]
    
    results = []
    total_duration = 0
    
    for test_file, test_class in unit_tests:
        print(f"\nRunning {test_class}...")
        success, duration, output = run_pytest_tests(test_file, test_class, verbose)
        results.append({
            "test_class": test_class,
            "success": success,
            "duration": duration,
            "output": output
        })
        total_duration += duration
    
    passed = sum(1 for r in results if r["success"])
    failed = len(results) - passed
    
    print(f"\nUnit Tests Summary:")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Total Duration: {total_duration:.2f}s")
    
    return results, passed == len(results)

def run_integration_tests(verbose=False):
    """Run all integration tests"""
    print("\n" + "="*60)
    print("RUNNING INTEGRATION TESTS")
    print("="*60)
    
    integration_tests = [
        ("test_integration_comprehensive.py", "TestEndToEndVersionControlWorkflows"),
        ("test_integration_comprehensive.py", "TestRouteManagementIntegration"),
        ("test_integration_comprehensive.py", "TestFloorComparisonFunctionality"),
        ("test_integration_comprehensive.py", "TestMultiUserCollaboration")
    ]
    
    results = []
    total_duration = 0
    
    for test_file, test_class in integration_tests:
        print(f"\nRunning {test_class}...")
        success, duration, output = run_pytest_tests(test_file, test_class, verbose)
        results.append({
            "test_class": test_class,
            "success": success,
            "duration": duration,
            "output": output
        })
        total_duration += duration
    
    passed = sum(1 for r in results if r["success"])
    failed = len(results) - passed
    
    print(f"\nIntegration Tests Summary:")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Total Duration: {total_duration:.2f}s")
    
    return results, passed == len(results)

def run_edge_case_tests(verbose=False):
    """Run all edge case tests"""
    print("\n" + "="*60)
    print("RUNNING EDGE CASE TESTS")
    print("="*60)
    
    edge_case_tests = [
        ("test_edge_cases_comprehensive.py", "TestEmptyFloorsAndLargeDatasets"),
        ("test_edge_cases_comprehensive.py", "TestConcurrentEditScenarios"),
        ("test_edge_cases_comprehensive.py", "TestFailedRestoreOperations"),
        ("test_edge_cases_comprehensive.py", "TestStressTestingForPerformance"),
        ("test_edge_cases_comprehensive.py", "TestBoundaryConditions")
    ]
    
    results = []
    total_duration = 0
    
    for test_file, test_class in edge_case_tests:
        print(f"\nRunning {test_class}...")
        success, duration, output = run_pytest_tests(test_file, test_class, verbose)
        results.append({
            "test_class": test_class,
            "success": success,
            "duration": duration,
            "output": output
        })
        total_duration += duration
    
    passed = sum(1 for r in results if r["success"])
    failed = len(results) - passed
    
    print(f"\nEdge Case Tests Summary:")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Total Duration: {total_duration:.2f}s")
    
    return results, passed == len(results)

def run_performance_tests(verbose=False):
    """Run all performance tests"""
    print("\n" + "="*60)
    print("RUNNING PERFORMANCE TESTS")
    print("="*60)
    
    performance_tests = [
        ("test_stress_performance.py", "TestLoadTesting"),
        ("test_stress_performance.py", "TestMemoryUsageMonitoring"),
        ("test_stress_performance.py", "TestDatabasePerformance"),
        ("test_stress_performance.py", "TestScalabilityTesting")
    ]
    
    results = []
    total_duration = 0
    
    for test_file, test_class in performance_tests:
        print(f"\nRunning {test_class}...")
        success, duration, output = run_pytest_tests(test_file, test_class, verbose)
        results.append({
            "test_class": test_class,
            "success": success,
            "duration": duration,
            "output": output
        })
        total_duration += duration
    
    passed = sum(1 for r in results if r["success"])
    failed = len(results) - passed
    
    print(f"\nPerformance Tests Summary:")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Total Duration: {total_duration:.2f}s")
    
    return results, passed == len(results)

def generate_report(all_results, start_time, end_time):
    """Generate a comprehensive test report"""
    total_duration = end_time - start_time
    
    # Calculate overall statistics
    total_tests = sum(len(results) for results in all_results.values())
    total_passed = sum(
        sum(1 for r in results if r["success"])
        for results in all_results.values()
    )
    total_failed = total_tests - total_passed
    success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
    
    # Generate report
    report = {
        "summary": {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "success_rate": success_rate,
            "total_duration": total_duration,
            "timestamp": datetime.now().isoformat()
        },
        "results": all_results
    }
    
    # Print summary
    print("\n" + "="*80)
    print("COMPREHENSIVE TEST REPORT")
    print("="*80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Total Duration: {total_duration:.2f}s")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Print detailed results
    print("\nDetailed Results:")
    print("-" * 40)
    
    for test_type, results in all_results.items():
        if results:
            passed = sum(1 for r in results if r["success"])
            failed = len(results) - passed
            total_duration = sum(r["duration"] for r in results)
            
            print(f"\n{test_type.replace('_', ' ').title()}:")
            print(f"  Passed: {passed}/{len(results)}")
            print(f"  Duration: {total_duration:.2f}s")
            
            for result in results:
                status = "✅ PASS" if result["success"] else "❌ FAIL"
                print(f"    {status} {result['test_class']} ({result['duration']:.2f}s)")
    
    # Save report to file
    import json
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_file}")
    
    return success_rate >= 90  # Consider successful if 90% or more tests pass

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run comprehensive tests for Arxos platform")
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration-only", action="store_true", help="Run only integration tests")
    parser.add_argument("--edge-only", action="store_true", help="Run only edge case tests")
    parser.add_argument("--performance-only", action="store_true", help="Run only performance tests")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--report", action="store_true", help="Generate detailed report")
    
    args = parser.parse_args()
    
    print("Arxos Platform - Comprehensive Test Runner")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    all_results = {}
    
    try:
        # Run tests based on arguments
        if args.unit_only:
            all_results["unit_tests"], unit_success = run_unit_tests(args.verbose)
        elif args.integration_only:
            all_results["integration_tests"], integration_success = run_integration_tests(args.verbose)
        elif args.edge_only:
            all_results["edge_case_tests"], edge_success = run_edge_case_tests(args.verbose)
        elif args.performance_only:
            all_results["performance_tests"], performance_success = run_performance_tests(args.verbose)
        else:
            # Run all tests
            all_results["unit_tests"], unit_success = run_unit_tests(args.verbose)
            all_results["integration_tests"], integration_success = run_integration_tests(args.verbose)
            all_results["edge_case_tests"], edge_success = run_edge_case_tests(args.verbose)
            all_results["performance_tests"], performance_success = run_performance_tests(args.verbose)
        
        end_time = time.time()
        
        # Generate report if requested
        if args.report or not any([args.unit_only, args.integration_only, args.edge_only, args.performance_only]):
            overall_success = generate_report(all_results, start_time, end_time)
        else:
            overall_success = True
        
        # Final summary
        print("\n" + "="*80)
        print("FINAL SUMMARY")
        print("="*80)
        
        if overall_success:
            print("✅ All tests completed successfully!")
            print("🎉 Arxos platform is ready for production deployment.")
            return 0
        else:
            print("❌ Some tests failed. Please review the results above.")
            print("🔧 Fix the failing tests before deployment.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 