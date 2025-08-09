#!/usr/bin/env python3
"""
Test script for migrated SVGX Engine services.

This script tests the migrated services to ensure they:
1. Can be imported without errors
2. Can be instantiated properly
3. Have the expected methods and attributes
4. Can perform basic operations

Run this script to verify the migration was successful.
"""

import sys
import os
import asyncio
import traceback
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

# Ensure svgx_engine is on sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all migrated services can be imported."""
    print("🔍 Testing service imports...")

    import_tests = [
        ("SVGXExportIntegrationService", "svgx_engine.services.export_integration"),
        ("SVGXMetadataService", "svgx_engine.services.metadata_service"),
        ("SVGXBIMHealthCheckerService", "svgx_engine.services.bim_health"),
        ("LogicEngine", "svgx_engine.services.logic_engine"),
        ("SVGXBIMAssemblyService", "svgx_engine.services.bim_assembly"),
        ("SVGXExportIntegrationService", "svgx_engine.services.export_integration"),
    ]

    failed_imports = []
    successful_imports = []

    for service_name, module_path in import_tests:
        try:
            module = __import__(module_path, fromlist=[service_name])
            service_class = getattr(module, service_name)
            successful_imports.append(service_name)
            print(f"  ✅ {service_name} imported successfully")
        except Exception as e:
            failed_imports.append((service_name, str(e)))
            print(f"  ❌ {service_name} import failed: {str(e)}")

    print(f"\n📊 Import Results:")
    print(f"  Successful: {len(successful_imports)}")
    print(f"  Failed: {len(failed_imports)}")

    if failed_imports:
        print("\n❌ Failed imports:")
        for service_name, error in failed_imports:
            print(f"  - {service_name}: {error}")

    return len(failed_imports) == 0

def test_service_instantiation():
    """Test that services can be instantiated."""
    print("\n🔧 Testing service instantiation...")

    instantiation_tests = [
        ("SVGXExportIntegrationService", "svgx_engine.services.export_integration", {}),
        ("SVGXMetadataService", "svgx_engine.services.metadata_service", {"cache_ttl": 300}),
        ("SVGXBIMHealthCheckerService", "svgx_engine.services.bim_health", {"db_path": ":memory:"}),
        ("LogicEngine", "svgx_engine.services.logic_engine", {"db_path": ":memory:"}),
    ]

    failed_instantiations = []
    successful_instantiations = []

    for service_name, module_path, init_params in instantiation_tests:
        try:
            module = __import__(module_path, fromlist=[service_name])
            service_class = getattr(module, service_name)
            instance = service_class(**init_params)
            successful_instantiations.append(service_name)
            print(f"  ✅ {service_name} instantiated successfully")
        except Exception as e:
            failed_instantiations.append((service_name, str(e)))
            print(f"  ❌ {service_name} instantiation failed: {str(e)}")

    print(f"\n📊 Instantiation Results:")
    print(f"  Successful: {len(successful_instantiations)}")
    print(f"  Failed: {len(failed_instantiations)}")

    if failed_instantiations:
        print("\n❌ Failed instantiations:")
        for service_name, error in failed_instantiations:
            print(f"  - {service_name}: {error}")

    return len(failed_instantiations) == 0

def test_basic_operations():
    """Test basic operations on migrated services."""
    print("\n⚡ Testing basic operations...")

    operation_tests = []

    # Test Export Integration Service
    try:
        from svgx_engine.services.export_integration import SVGXExportIntegrationService, ScaleMetadata, ExportOptions
        service = SVGXExportIntegrationService()

        # Test scale metadata creation
        scale_metadata = service.create_scale_metadata(
            original_scale=1.0,
            current_scale=2.0,
            zoom_level=1.5,
            viewport_size=(800, 600),
            units="mm"
        )

        operation_tests.append(("Export Integration - Scale Metadata", True))
        print(f"  ✅ Export Integration Service: Scale metadata creation")

    except Exception as e:
        operation_tests.append(("Export Integration - Scale Metadata", False))
        print(f"  ❌ Export Integration Service: {str(e)}")

    # Test Metadata Service
    try:
        from svgx_engine.services.metadata_service import SVGXMetadataService, SVGXObjectMetadata
        service = SVGXMetadataService()

        # Test metadata creation
        metadata = SVGXObjectMetadata(
            object_id="test_object",
            object_type="svgx_element",
            name="Test Object",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            created_by="test_user"
        )

        operation_tests.append(("Metadata Service - Object Metadata", True))
        print(f"  ✅ Metadata Service: Object metadata creation")

    except Exception as e:
        operation_tests.append(("Metadata Service - Object Metadata", False))
        print(f"  ❌ Metadata Service: {str(e)}")

    # Test BIM Health Checker Service
    try:
        from svgx_engine.services.bim_health import SVGXBIMHealthCheckerService
        service = SVGXBIMHealthCheckerService(db_path=":memory:")

        # Test validation status enum
        from svgx_engine.services.bim_health import ValidationStatus
        status = ValidationStatus.COMPLETED

        operation_tests.append(("BIM Health Checker - Validation Status", True))
        print(f"  ✅ BIM Health Checker Service: Validation status")

    except Exception as e:
        operation_tests.append(("BIM Health Checker - Validation Status", False))
        print(f"  ❌ BIM Health Checker Service: {str(e)}")

    # Test Logic Engine Service
    try:
        from svgx_engine.services.logic_engine import LogicEngine, RuleType, RuleStatus
        service = LogicEngine(db_path=":memory:")

        # Test rule type enum
        rule_type = RuleType.CONDITIONAL

        operation_tests.append(("Logic Engine - Rule Type", True))
        print(f"  ✅ Logic Engine Service: Rule type")

    except Exception as e:
        operation_tests.append(("Logic Engine - Rule Type", False))
        print(f"  ❌ Logic Engine Service: {str(e)}")

    successful_operations = sum(1 for _, success in operation_tests if success)
    failed_operations = len(operation_tests) - successful_operations

    print(f"\n📊 Operation Results:")
    print(f"  Successful: {successful_operations}")
    print(f"  Failed: {failed_operations}")

    if failed_operations > 0:
        print("\n❌ Failed operations:")
        for operation_name, success in operation_tests:
            if not success:
                print(f"  - {operation_name}")

    return failed_operations == 0

def test_service_integration():
    """Test that services can work together."""
    print("\n🔗 Testing service integration...")

    integration_tests = []

    try:
        # Test that services can be imported together
        from svgx_engine.services.export_integration import SVGXExportIntegrationService
        from svgx_engine.services.metadata_service import SVGXMetadataService
        from svgx_engine.services.bim_health import SVGXBIMHealthCheckerService
        from svgx_engine.services.logic_engine import LogicEngine

        # Create instances
        export_service = SVGXExportIntegrationService()
        metadata_service = SVGXMetadataService()
        health_service = SVGXBIMHealthCheckerService(db_path=":memory:")
        logic_service = LogicEngine(db_path=":memory:")

        integration_tests.append(("Service Integration - Import Together", True))
        print(f"  ✅ All services can be imported and instantiated together")

    except Exception as e:
        integration_tests.append(("Service Integration - Import Together", False))
        print(f"  ❌ Service integration failed: {str(e)}")

    successful_integrations = sum(1 for _, success in integration_tests if success)
    failed_integrations = len(integration_tests) - successful_integrations

    print(f"\n📊 Integration Results:")
    print(f"  Successful: {successful_integrations}")
    print(f"  Failed: {failed_integrations}")

    return failed_integrations == 0

def generate_migration_report():
    """Generate a comprehensive migration report."""
    print("\n📋 Generating migration report...")

    report = {
        "timestamp": datetime.now().isoformat(),
        "migration_status": "IN_PROGRESS",
        "migrated_services": [
            "SVGXExportIntegrationService",
            "SVGXMetadataService",
            "SVGXBIMHealthCheckerService",
            "LogicEngine",
            "SVGXBIMAssemblyService"
        ],
        "pending_services": [
            "PDFProcessor",
            "BIMExportService",
            "ExportInteroperabilityService",
            "PersistenceExportInteroperabilityService",
            "AdvancedExportInteroperabilityService"
        ],
        "known_issues": [
            "Import errors in some services due to relative imports",
            "Missing dependencies for some advanced features",
            "Need to complete integration of migrated services"
        ],
        "next_steps": [
            "Fix remaining import issues",
            "Complete migration of pending services",
            "Add comprehensive unit tests",
            "Update documentation",
            "Performance testing and optimization"
        ]
    }

    print(f"📊 Migration Report:")
    print(f"  Timestamp: {report['timestamp']}")
    print(f"  Status: {report['migration_status']}")
    print(f"  Migrated Services: {len(report['migrated_services'])}")
    print(f"  Pending Services: {len(report['pending_services'])}")
    print(f"  Known Issues: {len(report['known_issues'])}")
    print(f"  Next Steps: {len(report['next_steps'])}")

    return report

def main():
    """Run all tests and generate report."""
    print("🚀 SVGX Engine Service Migration Test Suite")
    print("=" * 50)

    # Run tests
    import_success = test_imports()
    instantiation_success = test_service_instantiation()
    operation_success = test_basic_operations()
    integration_success = test_service_integration()

    # Generate report
    report = generate_migration_report()

    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)

    tests = [
        ("Import Tests", import_success),
        ("Instantiation Tests", instantiation_success),
        ("Operation Tests", operation_success),
        ("Integration Tests", integration_success)
    ]

    passed_tests = sum(1 for _, success in tests if success)
    total_tests = len(tests)

    for test_name, success in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name}: {status}")

    print(f"\n📊 Overall Results:")
    print(f"  Passed: {passed_tests}/{total_tests}")
    print(f"  Failed: {total_tests - passed_tests}/{total_tests}")

    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Migration is successful.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Migration needs attention.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
