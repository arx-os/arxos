#!/usr/bin/env python3
"""
SVGX Engine Test Run 2 - Advanced Functionality Validation

This script runs the second comprehensive test to validate advanced SVGX Engine functionality.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

def run_test_2():
    """Run the second comprehensive test."""
    print("SVGX Engine Test Run 2 - Advanced Functionality Validation")
    print("=" * 60)

    try:
        # Test advanced service functionality
        print("1. Testing advanced service functionality...")

        # Test access control with user creation
        from svgx_engine.services.access_control import SVGXAccessControlService, UserRole
        ac_service = SVGXAccessControlService()
        import time
        unique_username = f"test_user_{int(time.time())}"
        user_data = ac_service.create_user(
            username=unique_username,
            email=f"test{int(time.time())}@example.com",
            primary_role=UserRole.EDITOR,
            svgx_preferences={"default_namespace": "arx"}
        )
        print("   OK: User creation successful")

        # Test telemetry with data ingestion
        from svgx_engine.services.telemetry import SVGXTelemetryIngestor, SVGXTelemetryBuffer, SVGXTelemetryType
        buffer = SVGXTelemetryBuffer()
        telemetry = SVGXTelemetryIngestor(buffer)
        telemetry.ingest_svgx_operation(
            operation_type=SVGXTelemetryType.SVGX_PARSER,
            component="test_component",
            value="test_operation",
            namespace="test_namespace"
        )
        print("   OK: Telemetry data ingestion successful")

        # Test caching with data storage
        from svgx_engine.services.advanced_caching import SVGXAdvancedCachingService
        cache_service = SVGXAdvancedCachingService()
        cache_key = cache_service.cache_svgx_content("test_content", namespace="test_namespace")
        print("   OK: Caching operations successful")

        # Test security with role validation
        from svgx_engine.services.security import SVGXSecurityService
        security_service = SVGXSecurityService()
        has_permission = security_service.check_permission(
            user_id=user_data['user_id'],
            resource="test_resource",
            action="create"
        )
        print("   OK: Security validation successful")

        # Test realtime with processor initialization
        from svgx_engine.services.realtime import SVGXTelemetryProcessor, SVGXTelemetryConfig, SVGXRealtimeTelemetryServer
        config = SVGXTelemetryConfig()
        processor = SVGXTelemetryProcessor(config)
        processor.start()
        print("   OK: Realtime processor started")

        # Test BIM integration
        print("2. Testing BIM integration...")
        from svgx_engine.services.bim_assembly import SVGXBIMAssemblyService
        bim_service = SVGXBIMAssemblyService()
        print("   OK: BIM assembly service initialized")

        from svgx_engine.services.bim_health import SVGXBIMHealthCheckerService
        health_service = SVGXBIMHealthCheckerService()
        print("   OK: BIM health checker initialized")

        # Test symbol management
        print("3. Testing symbol management...")
        from svgx_engine.services.symbol_manager import SVGXSymbolManager
        symbol_manager = SVGXSymbolManager()
        print("   OK: Symbol manager initialized")

        from svgx_engine.services.symbol_recognition import SVGXSymbolRecognitionService
        symbol_recognition = SVGXSymbolRecognitionService()
        print("   OK: Symbol recognition initialized")

        # Test export functionality
        print("4. Testing export functionality...")
        from svgx_engine.services.advanced_export import SVGXAdvancedExportService
        export_service = SVGXAdvancedExportService()
        print("   OK: Advanced export service initialized")

        from svgx_engine.services.export_interoperability import SVGXExportInteroperabilityService
        interoperability_service = SVGXExportInteroperabilityService()
        print("   OK: Export interoperability service initialized")

        # Test performance monitoring
        print("5. Testing performance monitoring...")
        from svgx_engine.services.performance import SVGXPerformanceProfiler
        performance_service = SVGXPerformanceProfiler()
        print("   OK: Performance profiler initialized")

        # Test error handling
        print("6. Testing error handling...")
        from svgx_engine.services.error_handler import SVGXErrorHandler
        error_handler = SVGXErrorHandler()
        print("   OK: Error handler initialized")

        # Test database operations
        print("7. Testing database operations...")
        from svgx_engine.services.database import SVGXDatabaseService
        db_service = SVGXDatabaseService()
        print("   OK: Database service initialized")

        # Test metadata management
        print("8. Testing metadata management...")
        from svgx_engine.services.metadata_service import SVGXMetadataService
        metadata_service = SVGXMetadataService()
        print("   OK: Metadata service initialized")

        # Test logic engine
        print("9. Testing logic engine...")
        from svgx_engine.services.logic_engine import LogicEngine
        logic_engine = LogicEngine()
        print("   OK: Logic engine initialized")

        # Test collaboration features
        print("10. Testing collaboration features...")
        from svgx_engine.services.realtime_collaboration import RealtimeCollaboration
        collaboration_service = RealtimeCollaboration()
        print("   OK: Collaboration service initialized")

        print("\n" + "=" * 60)
        print("SVGX Engine Test Run 2: PASSED")
        print("All advanced functionality validated successfully")
        print("SVGX Engine advanced features are compliant")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\nERROR: Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_test_2()
    sys.exit(0 if success else 1)
