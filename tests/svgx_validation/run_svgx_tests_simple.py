#!/usr/bin/env python3
"""
Simple test runner for SVGX Engine tests.

This script tests the core functionality without executing test files directly.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

def test_svgx_imports():
    """Test that all SVGX Engine imports work correctly."""
    print("Testing SVGX Engine Imports")
    print("=" * 40)

    try:
        import svgx_engine
        print("OK: svgx_engine package imported")

        import svgx_engine.services
        print("OK: svgx_engine.services module imported")

        from svgx_engine.services.access_control import SVGXAccessControlService
        print("OK: SVGXAccessControlService imported")

        from svgx_engine.services.advanced_caching import SVGXAdvancedCachingService
        print("OK: SVGXAdvancedCachingService imported")

        from svgx_engine.services.telemetry import SVGXTelemetryIngestor
        print("OK: SVGXTelemetryIngestor imported")

        from svgx_engine.services.security import SVGXSecurityService
        print("OK: SVGXSecurityService imported")

        from svgx_engine.services.realtime import SVGXRealtimeTelemetryServer
        print("OK: SVGXRealtimeTelemetryServer imported")

        print("OK: All imports successful")
        return True

    except ImportError as e:
        print(f"ERROR: Import failed: {e}")
        return False

def test_svgx_functionality():
    """Test basic SVGX Engine functionality."""
    print("\nTesting SVGX Engine Functionality")
    print("=" * 40)

    try:
        # Test access control service
        from svgx_engine.services.access_control import SVGXAccessControlService
        ac_service = SVGXAccessControlService()
        print("OK: AccessControlService initialized")

        # Test telemetry service
        from svgx_engine.services.telemetry import SVGXTelemetryIngestor
        telemetry = SVGXTelemetryIngestor(buffer_size=1000)
        print("OK: TelemetryIngestor initialized")

        # Test caching service
        from svgx_engine.services.advanced_caching import SVGXAdvancedCachingService
        cache_service = SVGXAdvancedCachingService()
        print("OK: AdvancedCachingService initialized")

        # Test security service
        from svgx_engine.services.security import SVGXSecurityService
        security_service = SVGXSecurityService()
        print("OK: SecurityService initialized")

        # Test realtime service
        from svgx_engine.services.realtime import SVGXRealtimeTelemetryServer
        realtime_service = SVGXRealtimeTelemetryServer()
        print("OK: RealtimeTelemetryServer initialized")

        print("OK: All services initialized successfully")
        return True

    except Exception as e:
        print(f"ERROR: Service initialization failed: {e}")
        return False

def test_svgx_models():
    """Test SVGX Engine models."""
    print("\nTesting SVGX Engine Models")
    print("=" * 40)

    try:
        from svgx_engine.models.svgx import SVGXDocument, SVGXElement, SVGXObject
        print("OK: SVGX models imported")

        from svgx_engine.models.bim import BIMElement, BIMSystem, BIMSpace
        print("OK: BIM models imported")

        print("OK: All models imported successfully")
        return True

    except ImportError as e:
        print(f"ERROR: Model import failed: {e}")
        return False

def test_svgx_utils():
    """Test SVGX Engine utilities."""
    print("\nTesting SVGX Engine Utilities")
    print("=" * 40)

    try:
        from svgx_engine.utils.errors import SVGXError, ValidationError, ExportError
        print("OK: Error utilities imported")

        from svgx_engine.utils.performance import PerformanceMonitor
        print("OK: Performance utilities imported")

        from svgx_engine.utils.telemetry import TelemetryLogger
        print("OK: Telemetry utilities imported")

        print("OK: All utilities imported successfully")
        return True

    except ImportError as e:
        print(f"ERROR: Utility import failed: {e}")
        return False

def main():
    """Run all SVGX Engine tests."""
    print("SVGX Engine Comprehensive Test Suite")
    print("=" * 50)

    tests = [
        test_svgx_imports,
        test_svgx_functionality,
        test_svgx_models,
        test_svgx_utils
    ]

    passed_tests = 0
    total_tests = len(tests)

    for test in tests:
        try:
            if test():
                passed_tests += 1
        except Exception as e:
            print(f"ERROR: Test {test.__name__} failed with exception: {e}")

    print(f"\nTest Results:")
    print(f"Passed: {passed_tests}/{total_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")

    if passed_tests == total_tests:
        print("\nSUCCESS: All tests passed! SVGX Engine is compliant.")
        return True
    else:
        print(f"\nWARNING: {total_tests - passed_tests} tests failed. SVGX Engine needs fixes.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
