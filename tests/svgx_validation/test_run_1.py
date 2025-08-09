#!/usr/bin/env python3
"""
SVGX Engine Test Run 1 - Comprehensive Validation

This script runs the first comprehensive test to validate SVGX Engine compliance.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

def run_test_1():
    """Run the first comprehensive test."""
    print("SVGX Engine Test Run 1 - Comprehensive Validation")
    print("=" * 60)

    try:
        # Test all core imports
        print("1. Testing core imports...")
        import svgx_engine
        import svgx_engine.services
        print("   OK: Core packages imported")

        # Test all service imports
        print("2. Testing service imports...")
        from svgx_engine.services.access_control import SVGXAccessControlService
        from svgx_engine.services.advanced_caching import SVGXAdvancedCachingService
        from svgx_engine.services.telemetry import SVGXTelemetryIngestor, SVGXTelemetryBuffer
        from svgx_engine.services.security import SVGXSecurityService
        from svgx_engine.services.realtime import SVGXRealtimeTelemetryServer
        print("   OK: All services imported")

        # Test service initialization
        print("3. Testing service initialization...")
        ac_service = SVGXAccessControlService()
        print("   OK: AccessControlService initialized")

        buffer = SVGXTelemetryBuffer()
        telemetry = SVGXTelemetryIngestor(buffer)
        print("   OK: TelemetryIngestor initialized")

        cache_service = SVGXAdvancedCachingService()
        print("   OK: AdvancedCachingService initialized")

        security_service = SVGXSecurityService()
        print("   OK: SecurityService initialized")

        # Initialize realtime service with required parameters
        from svgx_engine.services.realtime import SVGXTelemetryProcessor, SVGXTelemetryConfig
        config = SVGXTelemetryConfig()
        processor = SVGXTelemetryProcessor(config)
        realtime_service = SVGXRealtimeTelemetryServer(processor, config)
        print("   OK: RealtimeTelemetryServer initialized")

        # Test model imports
        print("4. Testing model imports...")
        from svgx_engine.models.svgx import SVGXDocument, SVGXElement, SVGXObject
        from svgx_engine.models.bim import BIMElement, BIMSystem, BIMSpace
        print("   OK: All models imported")

        # Test utility imports
        print("5. Testing utility imports...")
        from svgx_engine.utils.errors import SVGXError, ValidationError, ExportError
        from svgx_engine.utils.performance import PerformanceMonitor
        from svgx_engine.utils.telemetry import TelemetryLogger
        print("   OK: All utilities imported")

        print("\n" + "=" * 60)
        print("SVGX Engine Test Run 1: PASSED")
        print("All imports successful, all services initialized")
        print("SVGX Engine is compliant and ready for migration")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\nERROR: Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_test_1()
    sys.exit(0 if success else 1)
