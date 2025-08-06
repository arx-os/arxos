#!/usr/bin/env python3
"""
Test runner for SVGX Engine tests.

This script sets up the proper Python path and runs the SVGX Engine test suite.
"""

import sys
import os
import subprocess
import importlib.util

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())


def run_svgx_tests():
    """Run the SVGX Engine test suite."""
    print("Running SVGX Engine Test Suite")
    print("=" * 50)

    # Test imports first
    print("1. Testing imports...")
    try:
        import svgx_engine

        print("   OK: svgx_engine package imported")

        import svgx_engine.services

        print("   OK: svgx_engine.services module imported")

        from svgx_engine.services.access_control import SVGXAccessControlService

        print("   OK: SVGXAccessControlService imported")

        from svgx_engine.services.advanced_caching import SVGXAdvancedCachingService

        print("   OK: SVGXAdvancedCachingService imported")

        from svgx_engine.services.telemetry import SVGXTelemetryIngestor

        print("   OK: SVGXTelemetryIngestor imported")

        print("   OK: All imports successful")

    except ImportError as e:
        print(f"   ERROR: Import failed: {e}")
        return False

    # Run individual test files
    test_files = [
        "tests/svgx_engine/test_access_control_migration.py",
        "tests/svgx_engine/test_advanced_caching_migration.py",
        "tests/svgx_engine/test_telemetry_migration.py",
        "tests/svgx_engine/test_security_migration.py",
        "tests/svgx_engine/test_realtime_migration.py",
    ]

    print("\n2. Running individual tests...")
    passed_tests = 0
    total_tests = len(test_files)

    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n   Running {test_file}...")
            try:
                # Execute the test file with UTF-8 encoding
                with open(test_file, "r", encoding="utf-8") as f:
                    test_code = f.read()

                # Create a new namespace for the test
                test_namespace = {}
                exec(test_code, test_namespace)

                # Look for test functions and run them
                for name, obj in test_namespace.items():
                    if callable(obj) and name.startswith("test_"):
                        print(f"     Running {name}...")
                        try:
                            result = obj()
                            if result is not False:
                                print(f"     OK: {name} passed")
                                passed_tests += 1
                            else:
                                print(f"     ERROR: {name} failed")
                        except Exception as e:
                            print(f"     ERROR: {name} failed with error: {e}")

            except Exception as e:
                print(f"     ERROR: Failed to run {test_file}: {e}")
        else:
            print(f"   WARNING: Test file not found: {test_file}")

    print(f"\n3. Test Results:")
    print(f"   Passed: {passed_tests}/{total_tests}")
    print(f"   Success rate: {(passed_tests/total_tests)*100:.1f}%")

    if passed_tests == total_tests:
        print("\nSUCCESS: All tests passed! SVGX Engine is compliant.")
        return True
    else:
        print(
            f"\nWARNING: {total_tests - passed_tests} tests failed. SVGX Engine needs fixes."
        )
        return False


if __name__ == "__main__":
    success = run_svgx_tests()
    sys.exit(0 if success else 1)
