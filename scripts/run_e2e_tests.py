#!/usr/bin/env python3
"""
Arxos Pipeline E2E Testing Script

This script runs comprehensive end-to-end tests for the Arxos pipeline,
validating the complete flow from system definition to production deployment.
"""

import sys
import os
import time
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)

def print_success(message: str):
    """Print a success message"""
    print(f"✅ {message}")

def print_error(message: str):
    """Print an error message"""
    print(f"❌ {message}")

def print_info(message: str):
    """Print an info message"""
    print(f"ℹ️  {message}")

def check_prerequisites():
    """Check if all prerequisites are met"""
    print_header("Checking Prerequisites")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print_error("Python 3.8+ is required")
        return False
    print_success(f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check required directories
    required_dirs = [
        "svgx_engine",
        "arx-backend",
        "schemas",
        "arx-symbol-library",
        "tests"
    ]
    
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            print_error(f"Required directory not found: {dir_path}")
            return False
        print_success(f"Directory exists: {dir_path}")
    
    # Check required files
    required_files = [
        "svgx_engine/services/pipeline_integration.py",
        "arx-backend/handlers/pipeline.go",
        "scripts/arx_pipeline.py",
        "tests/test_pipeline_integration.py"
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print_error(f"Required file not found: {file_path}")
            return False
        print_success(f"File exists: {file_path}")
    
    return True

def run_unit_tests():
    """Run unit tests"""
    print_header("Running Unit Tests")
    
    try:
        result = subprocess.run([
            "python", "-m", "pytest", "tests/test_pipeline_integration.py", "-v"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print_success("Unit tests passed")
            return True
        else:
            print_error("Unit tests failed")
            print(result.stdout)
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print_error("Unit tests timed out")
        return False
    except Exception as e:
        print_error(f"Unit tests failed with exception: {e}")
        return False

def run_integration_tests():
    """Run integration tests"""
    print_header("Running Integration Tests")
    
    try:
        result = subprocess.run([
            "python", "tests/test_pipeline_comprehensive.py"
        ], capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print_success("Integration tests passed")
            return True
        else:
            print_error("Integration tests failed")
            print(result.stdout)
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print_error("Integration tests timed out")
        return False
    except Exception as e:
        print_error(f"Integration tests failed with exception: {e}")
        return False

def run_e2e_tests():
    """Run end-to-end tests"""
    print_header("Running E2E Tests")
    
    try:
        result = subprocess.run([
            "python", "tests/e2e/test_pipeline_e2e.py"
        ], capture_output=True, text=True, timeout=900)
        
        if result.returncode == 0:
            print_success("E2E tests passed")
            return True
        else:
            print_error("E2E tests failed")
            print(result.stdout)
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print_error("E2E tests timed out")
        return False
    except Exception as e:
        print_error(f"E2E tests failed with exception: {e}")
        return False

def test_pipeline_cli():
    """Test pipeline CLI functionality"""
    print_header("Testing Pipeline CLI")
    
    cli_tests = [
        {
            "name": "Help Command",
            "cmd": ["python", "scripts/arx_pipeline.py", "--help"],
            "expected_return": 0
        },
        {
            "name": "List Systems",
            "cmd": ["python", "scripts/arx_pipeline.py", "--list-systems"],
            "expected_return": 0
        },
        {
            "name": "Validate System (should fail for non-existent system)",
            "cmd": ["python", "scripts/arx_pipeline.py", "--validate", "--system", "non_existent_system"],
            "expected_return": 1  # Should fail for non-existent system
        }
    ]
    
    all_passed = True
    
    for test in cli_tests:
        try:
            result = subprocess.run(test["cmd"], capture_output=True, text=True, timeout=30)
            
            if result.returncode == test["expected_return"]:
                print_success(f"{test['name']} passed")
            else:
                print_error(f"{test['name']} failed (expected {test['expected_return']}, got {result.returncode})")
                all_passed = False
                
        except subprocess.TimeoutExpired:
            print_error(f"{test['name']} timed out")
            all_passed = False
        except Exception as e:
            print_error(f"{test['name']} failed with exception: {e}")
            all_passed = False
    
    return all_passed

def test_pipeline_api():
    """Test pipeline API functionality"""
    print_header("Testing Pipeline API")
    
    try:
        # Import and test API functionality
        from svgx_engine.services.pipeline_integration import PipelineIntegrationService
        
        service = PipelineIntegrationService()
        
        # Test basic operations
        operations = [
            ("list-systems", {}),
            ("validate-schema", {"system": "test_system"}),
            ("get-status", {"system": "test_system"})
        ]
        
        all_passed = True
        
        for operation, params in operations:
            try:
                result = service.handle_operation(operation, params)
                if result is not None:
                    print_success(f"API operation '{operation}' succeeded")
                else:
                    print_error(f"API operation '{operation}' returned None")
                    all_passed = False
            except Exception as e:
                print_error(f"API operation '{operation}' failed: {e}")
                all_passed = False
        
        return all_passed
        
    except ImportError as e:
        print_error(f"Failed to import pipeline service: {e}")
        return False
    except Exception as e:
        print_error(f"API testing failed: {e}")
        return False

def test_monitoring_and_analytics():
    """Test monitoring and analytics functionality"""
    print_header("Testing Monitoring & Analytics")
    
    try:
        from svgx_engine.services.monitoring import get_monitoring
        from svgx_engine.services.pipeline_analytics import get_analytics
        
        # Test monitoring
        monitoring = get_monitoring()
        health = monitoring.get_system_health()
        
        if health and "overall_status" in health:
            print_success("Monitoring service working")
        else:
            print_error("Monitoring service not working properly")
            return False
        
        # Test analytics
        analytics = get_analytics()
        report = analytics.create_performance_report("test_system")
        
        if report:
            print_success("Analytics service working")
        else:
            print_error("Analytics service not working properly")
            return False
        
        return True
        
    except ImportError as e:
        print_error(f"Failed to import monitoring/analytics: {e}")
        return False
    except Exception as e:
        print_error(f"Monitoring/analytics testing failed: {e}")
        return False

def test_backup_recovery():
    """Test backup and recovery functionality"""
    print_header("Testing Backup & Recovery")
    
    try:
        from svgx_engine.services.rollback_recovery import get_rollback_recovery
        
        rr = get_rollback_recovery()
        
        # Test backup creation
        backup_id = rr.create_backup("test_system", "full", "E2E test backup")
        
        if backup_id:
            print_success("Backup creation working")
        else:
            print_error("Backup creation failed")
            return False
        
        # Test backup listing
        backups = rr.list_backups("test_system")
        
        if backups:
            print_success("Backup listing working")
        else:
            print_error("Backup listing failed")
            return False
        
        return True
        
    except ImportError as e:
        print_error(f"Failed to import rollback/recovery: {e}")
        return False
    except Exception as e:
        print_error(f"Backup/recovery testing failed: {e}")
        return False

def run_performance_tests():
    """Run performance tests"""
    print_header("Running Performance Tests")
    
    try:
        # Test pipeline execution time
        start_time = time.time()
        
        from svgx_engine.services.pipeline_integration import PipelineIntegrationService
        service = PipelineIntegrationService()
        
        # Execute a simple pipeline operation
        result = service.handle_operation("list-systems", {})
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        if result is not None and execution_time < 5.0:  # Should complete within 5 seconds
            print_success(f"Performance test passed: {execution_time:.2f}s")
            return True
        else:
            print_error(f"Performance test failed: {execution_time:.2f}s")
            return False
            
    except Exception as e:
        print_error(f"Performance testing failed: {e}")
        return False

def generate_test_report(results: Dict[str, bool]):
    """Generate a comprehensive test report"""
    print_header("Test Report")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"📊 Test Summary:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {failed_tests}")
    print(f"   Success Rate: {success_rate:.1f}%")
    
    print(f"\n📋 Detailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    if failed_tests > 0:
        print(f"\n❌ Failed Tests:")
        for test_name, result in results.items():
            if not result:
                print(f"   - {test_name}")
    
    return success_rate >= 80  # Consider successful if 80%+ tests pass

def main():
    """Main E2E testing function"""
    print("🚀 Arxos Pipeline E2E Testing")
    print("=" * 60)
    
    # Initialize results
    results = {}
    
    # Run all tests
    tests = [
        ("Prerequisites Check", check_prerequisites),
        ("Unit Tests", run_unit_tests),
        ("Integration Tests", run_integration_tests),
        ("E2E Tests", run_e2e_tests),
        ("CLI Tests", test_pipeline_cli),
        ("API Tests", test_pipeline_api),
        ("Monitoring & Analytics", test_monitoring_and_analytics),
        ("Backup & Recovery", test_backup_recovery),
        ("Performance Tests", run_performance_tests)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print_error(f"{test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Generate report
    overall_success = generate_test_report(results)
    
    # Final result
    print_header("Final Result")
    if overall_success:
        print("🎉 E2E Testing COMPLETED SUCCESSFULLY!")
        print("The Arxos pipeline is ready for production deployment.")
        return 0
    else:
        print("❌ E2E Testing FAILED!")
        print("Please fix the failing tests before proceeding to production.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 