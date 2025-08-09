#!/usr/bin/env python3
"""
Basic import test for SVGX Engine core components.

This script tests that the core components can be imported
without requiring all the complex service dependencies.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

def test_core_imports():
    """Test core component imports."""
    print("🔍 Testing core imports...")

    try:
        # Test models
        from svgx_engine.models.svgx import SVGXDocument, SVGXElement, SVGXObject
        print("  ✅ SVGX models imported successfully")

        from svgx_engine.models.bim import BIMElement, BIMSystem, BIMSpace
        print("  ✅ BIM models imported successfully")

        from svgx_engine.models.database import DatabaseManager, DatabaseConfig
        print("  ✅ Database models imported successfully")

        # Test utils
        from svgx_engine.utils.errors import SVGXError, ValidationError
        print("  ✅ Error classes imported successfully")

        # Test basic services
        from svgx_engine.services.export_integration import SVGXExportIntegrationService
        print("  ✅ Export integration service imported successfully")

        from svgx_engine.services.metadata_service import SVGXMetadataService
        print("  ✅ Metadata service imported successfully")

        print("\n✅ All core imports successful!")
        return True

    except Exception as e:
        print(f"  ❌ Import failed: {str(e)}")
        return False

def test_basic_functionality():
    """Test basic functionality."""
    print("\n🔍 Testing basic functionality...")

    try:
        # Test creating a basic SVGX document
        from svgx_engine.models.svgx import SVGXDocument, SVGXElement

        doc = SVGXDocument()
        element = SVGXElement(tag="rect", attributes={"width": "100", "height": "100"})
        doc.add_element(element)

        print("  ✅ SVGX document creation successful")
        print(f"  ✅ Document has {len(doc.elements)} elements")

        return True

    except Exception as e:
        print(f"  ❌ Functionality test failed: {str(e)}")
        return False

def main():
    """Main test function."""
    print("🚀 SVGX Engine Basic Import Test")
    print("=" * 40)

    # Test imports
    import_success = test_core_imports()

    # Test functionality
    if import_success:
        functionality_success = test_basic_functionality()
    else:
        functionality_success = False

    print("\n📊 Test Results:")
    print(f"  Imports: {'✅ PASS' if import_success else '❌ FAIL'}")
    print(f"  Functionality: {'✅ PASS' if functionality_success else '❌ FAIL'}")

    if import_success and functionality_success:
        print("\n🎉 All tests passed! SVGX Engine is ready for development.")
        return True
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
