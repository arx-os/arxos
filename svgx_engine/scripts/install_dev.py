#!/usr/bin/env python3
"""
Development installation script for SVGX Engine.

This script installs the SVGX Engine package in development mode,
which resolves relative import issues and enables proper module resolution.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def install_package_in_dev_mode():
    """Install the SVGX Engine package in development mode."""
    print("🔧 Installing SVGX Engine in development mode...")

    # Get the current directory (svgx_engine)
    current_dir = Path(__file__).parent
    print(f"📁 Package directory: {current_dir}")

    try:
        # Install in development mode
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            cwd=current_dir,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ SVGX Engine installed successfully in development mode")
            print(f"📦 Package location: {current_dir}")
            return True
        else:
            print(f"❌ Installation failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False


def verify_installation():
    """Verify that the package can be imported correctly."""
    print("\n🔍 Verifying installation...")

    try:
        # Test basic imports
        import svgx_engine

        print("✅ svgx_engine package imported successfully")

        # Test service imports
        from svgx_engine.services import SVGXExportIntegrationService

        print("✅ SVGXExportIntegrationService imported successfully")

        from svgx_engine.services import SVGXMetadataService

        print("✅ SVGXMetadataService imported successfully")

        from svgx_engine.services import SVGXBIMHealthCheckerService

        print("✅ SVGXBIMHealthCheckerService imported successfully")

        from svgx_engine.services import LogicEngine

        print("✅ LogicEngine imported successfully")

        print("✅ All core services imported successfully")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False


def create_test_script():
    """Create a test script to verify the installation."""
    test_script = """
#!/usr/bin/env python3
\"\"\"
Test script to verify SVGX Engine installation.
\"\"\"

import sys
import os

def test_imports():
    \"\"\"Test that all core modules can be imported.\"\"\"
    print("🔍 Testing SVGX Engine imports...")
    
    try:
        import svgx_engine
        print("✅ svgx_engine package")
        
        from svgx_engine.services import SVGXExportIntegrationService
        print("✅ SVGXExportIntegrationService")
        
        from svgx_engine.services import SVGXMetadataService
        print("✅ SVGXMetadataService")
        
        from svgx_engine.services import SVGXBIMHealthCheckerService
        print("✅ SVGXBIMHealthCheckerService")
        
        from svgx_engine.services import LogicEngine
        print("✅ LogicEngine")
        
        from svgx_engine.models import SVGXDocument, SVGXElement
        print("✅ SVGXDocument, SVGXElement")
        
        from svgx_engine.utils import errors
        print("✅ utils.errors")
        
        print("\\n🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_service_instantiation():
    \"\"\"Test that services can be instantiated.\"\"\"
    print("\\n🔧 Testing service instantiation...")
    
    try:
        from svgx_engine.services import SVGXExportIntegrationService
        service = SVGXExportIntegrationService()
        print("✅ SVGXExportIntegrationService instantiated")
        
        from svgx_engine.services import SVGXMetadataService
        service = SVGXMetadataService()
        print("✅ SVGXMetadataService instantiated")
        
        print("\\n🎉 All services instantiated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Instantiation failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 SVGX Engine Installation Test")
    print("=" * 40)
    
    imports_ok = test_imports()
    instantiation_ok = test_service_instantiation()
    
    if imports_ok and instantiation_ok:
        print("\\n🎉 All tests passed! SVGX Engine is ready to use.")
        sys.exit(0)
    else:
        print("\\n❌ Some tests failed. Please check the installation.")
        sys.exit(1)
"""

    test_file = Path(__file__).parent / "test_installation.py"
    with open(test_file, "w") as f:
        f.write(test_script)

    print(f"📝 Created test script: {test_file}")
    return test_file


def main():
    """Main installation function."""
    print("🚀 SVGX Engine Development Installation")
    print("=" * 50)

    # Install the package
    if not install_package_in_dev_mode():
        print("❌ Installation failed. Exiting.")
        return False

    # Verify the installation
    if not verify_installation():
        print("❌ Verification failed. Exiting.")
        return False

    # Create test script
    test_file = create_test_script()

    print("\n" + "=" * 50)
    print("✅ Installation completed successfully!")
    print(f"📝 Test script created: {test_file}")
    print("\nTo test the installation, run:")
    print(f"  python {test_file}")
    print("\nTo use SVGX Engine in your code:")
    print("  from svgx_engine.services import SVGXExportIntegrationService")
    print("  service = SVGXExportIntegrationService()")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
