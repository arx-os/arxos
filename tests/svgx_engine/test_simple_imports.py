#!/usr/bin/env python3
"""
Simple import test for SVGX Engine services.

This script tests that the migrated services can be imported
without requiring the package to be installed in development mode.
"""

import sys
import os
from pathlib import Path

# Ensure svgx_engine is on sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def test_direct_imports():
    """Test direct imports of the migrated services."""
    print("🔍 Testing direct imports...")

    import_tests = [
        ("svgx_engine.services.export_integration", "SVGXExportIntegrationService"),
        ("svgx_engine.services.metadata_service", "SVGXMetadataService"),
        ("svgx_engine.services.bim_health", "SVGXBIMHealthCheckerService"),
        ("svgx_engine.services.logic_engine", "LogicEngine"),
        ("svgx_engine.services.bim_assembly", "SVGXBIMAssemblyService"),
    ]

    successful_imports = []
    failed_imports = []

    for module_path, class_name in import_tests:
        try:
            # Import the module
            module = __import__(module_path, fromlist=[class_name])

            # Try to get the class
            service_class = getattr(module, class_name)

            successful_imports.append(class_name)
            print(f"  ✅ {class_name} imported successfully")

        except Exception as e:
            failed_imports.append((class_name, str(e)))
            print(f"  ❌ {class_name} import failed: {str(e)}")

    print(f"\n📊 Import Results:")
    print(f"  Successful: {len(successful_imports)}")
    print(f"  Failed: {len(failed_imports)}")

    if failed_imports:
        print("\n❌ Failed imports:")
        for class_name, error in failed_imports:
            print(f"  - {class_name}: {error}")

    return len(failed_imports) == 0


def test_service_instantiation():
    """Test that services can be instantiated."""
    print("\n🔧 Testing service instantiation...")

    instantiation_tests = [
        ("svgx_engine.services.export_integration", "SVGXExportIntegrationService", {}),
        (
            "svgx_engine.services.metadata_service",
            "SVGXMetadataService",
            {"cache_ttl": 300},
        ),
        (
            "svgx_engine.services.bim_health",
            "SVGXBIMHealthCheckerService",
            {"db_path": ":memory:"},
        ),
        ("svgx_engine.services.logic_engine", "LogicEngine", {"db_path": ":memory:"}),
    ]

    successful_instantiations = []
    failed_instantiations = []

    for module_path, class_name, init_params in instantiation_tests:
        try:
            # Import the module and class
            module = __import__(module_path, fromlist=[class_name])
            service_class = getattr(module, class_name)

            # Try to instantiate
            instance = service_class(**init_params)

            successful_instantiations.append(class_name)
            print(f"  ✅ {class_name} instantiated successfully")

        except Exception as e:
            failed_instantiations.append((class_name, str(e)))
            print(f"  ❌ {class_name} instantiation failed: {str(e)}")

    print(f"\n📊 Instantiation Results:")
    print(f"  Successful: {len(successful_instantiations)}")
    print(f"  Failed: {len(failed_instantiations)}")

    if failed_instantiations:
        print("\n❌ Failed instantiations:")
        for class_name, error in failed_instantiations:
            print(f"  - {class_name}: {error}")

    return len(failed_instantiations) == 0


def test_basic_functionality():
    """Test basic functionality of the services."""
    print("\n⚡ Testing basic functionality...")

    functionality_tests = []

    # Test Export Integration Service
    try:
        from svgx_engine.services.export_integration import (
            SVGXExportIntegrationService,
            ScaleMetadata,
        )

        service = SVGXExportIntegrationService()

        # Test scale metadata creation
        scale_metadata = service.create_scale_metadata(
            original_scale=1.0,
            current_scale=2.0,
            zoom_level=1.5,
            viewport_size=(800, 600),
            units="mm",
        )

        functionality_tests.append(("Export Integration - Scale Metadata", True))
        print(f"  ✅ Export Integration Service: Scale metadata creation")

    except Exception as e:
        functionality_tests.append(("Export Integration - Scale Metadata", False))
        print(f"  ❌ Export Integration Service: {str(e)}")

    # Test Metadata Service
    try:
        from svgx_engine.services.metadata_service import (
            SVGXMetadataService,
            SVGXObjectMetadata,
        )

        service = SVGXMetadataService()

        # Test metadata creation
        metadata = SVGXObjectMetadata(
            object_id="test_object",
            object_type="svgx_element",
            name="Test Object",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            created_by="test_user",
        )

        functionality_tests.append(("Metadata Service - Object Metadata", True))
        print(f"  ✅ Metadata Service: Object metadata creation")

    except Exception as e:
        functionality_tests.append(("Metadata Service - Object Metadata", False))
        print(f"  ❌ Metadata Service: {str(e)}")

    # Test Logic Engine Service
    try:
        from svgx_engine.services.logic_engine import LogicEngine, RuleType

        service = LogicEngine(db_path=":memory:")

        # Test rule type enum
        rule_type = RuleType.CONDITIONAL

        functionality_tests.append(("Logic Engine - Rule Type", True))
        print(f"  ✅ Logic Engine Service: Rule type")

    except Exception as e:
        functionality_tests.append(("Logic Engine - Rule Type", False))
        print(f"  ❌ Logic Engine Service: {str(e)}")

    successful_tests = sum(1 for _, success in functionality_tests if success)
    failed_tests = len(functionality_tests) - successful_tests

    print(f"\n📊 Functionality Results:")
    print(f"  Successful: {successful_tests}")
    print(f"  Failed: {failed_tests}")

    if failed_tests > 0:
        print("\n❌ Failed functionality tests:")
        for test_name, success in functionality_tests:
            if not success:
                print(f"  - {test_name}")

    return failed_tests == 0


def main():
    """Run all tests."""
    print("🚀 SVGX Engine Simple Import Test")
    print("=" * 50)

    # Run tests
    import_success = test_direct_imports()
    instantiation_success = test_service_instantiation()
    functionality_success = test_basic_functionality()

    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)

    tests = [
        ("Import Tests", import_success),
        ("Instantiation Tests", instantiation_success),
        ("Functionality Tests", functionality_success),
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
        print(
            f"\n⚠️  {total_tests - passed_tests} test(s) failed. Migration needs attention."
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
