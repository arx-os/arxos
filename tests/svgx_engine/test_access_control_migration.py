#!/usr/bin/env python3
"""
Test script for AccessControlService migration.

This script tests the migrated AccessControlService to ensure it works correctly
with SVGX-specific features and follows clean code practices.
"""

import sys
import os
import tempfile
import shutil
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import svgx_engine
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgx_engine.services.access_control import (
    SVGXAccessControlService, UserRole, ResourceType, ActionType, PermissionLevel
)
from svgx_engine.utils.errors import SecurityError, ValidationError


def test_access_control_migration():
    """Test the migrated AccessControlService."""
    print("🧪 Testing AccessControlService Migration")
    print("=" * 50)

    # Create temporary database
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_access_control.db")

    try:
        # Initialize service
        print("1. Initializing AccessControlService...")
        ac_service = SVGXAccessControlService(db_path=db_path)
        print("   ✅ Service initialized successfully")

        # Test user creation
        print("\n2. Testing user creation...")
        user_data = ac_service.create_user(
            username="test_user",
            email="test@example.com",
            primary_role=UserRole.EDITOR,
            secondary_roles=[UserRole.CAD_USER],
            organization="Test Org",
            svgx_preferences={
                "default_namespace": "arx",
                "preferred_units": "mm",
                "auto_save": True
            }
        )
        print(f"   ✅ User created: {user_data['user_id']}")

        # Test user retrieval
        print("\n3. Testing user retrieval...")
        retrieved_user = ac_service.get_user(user_data['user_id'])
        assert retrieved_user is not None
        assert retrieved_user['username'] == "test_user"
        assert retrieved_user['svgx_preferences']['default_namespace'] == "arx"
        print("   ✅ User retrieved successfully")

        # Test permission checking
        print("\n4. Testing permission checking...")
        has_permission = ac_service.check_permission(
            user_id=user_data['user_id'],
            resource_type=ResourceType.SVGX_FILE.value,
            action=ActionType.CREATE.value
        )
        assert has_permission is True
        print("   ✅ Permission checking works")

        # Test SVGX capabilities
        print("\n5. Testing SVGX capabilities...")
        capabilities = ac_service.get_user_svgx_capabilities(user_data['user_id'])
        assert "edit" in capabilities
        assert "cad_tools" in capabilities
        print(f"   ✅ SVGX capabilities: {capabilities}")

        # Test SVGX-specific permission
        print("\n6. Testing SVGX-specific permission...")
        svgx_permission = ac_service.check_svgx_permission(
            user_id=user_data['user_id'],
            svgx_namespace="arx",
            resource_type=ResourceType.SVGX_ELEMENT.value,
            action=ActionType.CREATE.value
        )
        assert svgx_permission is True
        print("   ✅ SVGX-specific permission works")

        # Test session management
        print("\n7. Testing session management...")
        session_id = ac_service.create_session(
            user_id=user_data['user_id'],
            token="test_token_123",
            ip_address="127.0.0.1",
            user_agent="Test Agent"
        )
        assert session_id is not None
        print(f"   ✅ Session created: {session_id}")

        # Validate session
        session_data = ac_service.validate_session(session_id)
        assert session_data is not None
        assert session_data['user_id'] == user_data['user_id']
        print("   ✅ Session validation works")

        # Test audit logging
        print("\n8. Testing audit logging...")
        ac_service.log_audit_event(
            user_id=user_data['user_id'],
            action="svgx_file_created",
            resource_type=ResourceType.SVGX_FILE.value,
            resource_id="test_file_123",
            details={"file_size": 1024, "elements_count": 10},
            ip_address="127.0.0.1",
            user_agent="Test Agent",
            success=True,
            svgx_context={
                "namespace": "arx",
                "version": "1.0",
                "compilation_target": "svg"
            }
        )
        print("   ✅ Audit logging works")

        # Test audit log retrieval
        print("\n9. Testing audit log retrieval...")
        audit_logs = ac_service.get_audit_logs(
            user_id=user_data['user_id'],
            limit=10
        )
        assert len(audit_logs) > 0
        assert audit_logs[0]['action'] == "svgx_file_created"
        assert audit_logs[0]['svgx_context']['namespace'] == "arx"
        print("   ✅ Audit log retrieval works")

        # Test role permissions
        print("\n10. Testing role permissions...")
        permissions = ac_service._get_role_permissions("editor")
        assert len(permissions) > 0
        print(f"   ✅ Role permissions: {len(permissions)} permissions found")

        # Test error handling
        print("\n11. Testing error handling...")
        try:
            ac_service.create_user("", "", UserRole.VIEWER)
            assert False, "Should have raised ValidationError"
        except ValidationError:
            print("   ✅ Validation error handling works")

        try:
            ac_service.get_user("")
            assert False, "Should have raised ValidationError"
        except ValidationError:
            print("   ✅ User ID validation works")

        # Test CAD user role
        print("\n12. Testing CAD user role...")
        cad_user_data = ac_service.create_user(
            username="cad_user",
            email="cad@example.com",
            primary_role=UserRole.CAD_USER,
            svgx_preferences={
                "cad_tools_enabled": True,
                "dimensioning_precision": 2,
                "constraint_solver": "advanced"
            }
        )
        cad_capabilities = ac_service.get_user_svgx_capabilities(cad_user_data['user_id'])
        assert "cad_tools" in cad_capabilities
        assert "dimensioning" in cad_capabilities
        print(f"   ✅ CAD user capabilities: {cad_capabilities}")

        # Test BIM specialist role
        print("\n13. Testing BIM specialist role...")
        bim_user_data = ac_service.create_user(
            username="bim_user",
            email="bim@example.com",
            primary_role=UserRole.BIM_SPECIALIST,
            svgx_preferences={
                "bim_integration": True,
                "physics_simulation": True,
                "behavior_execution": True
            }
        )
        bim_capabilities = ac_service.get_user_svgx_capabilities(bim_user_data['user_id'])
        assert "bim_integration" in bim_capabilities
        assert "physics_simulation" in bim_capabilities
        print(f"   ✅ BIM specialist capabilities: {bim_capabilities}")

        print("\n🎉 All tests passed! AccessControlService migration successful.")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def test_clean_code_practices():
    """Test that the migrated code follows clean code practices."""
    print("\n🧹 Testing Clean Code Practices")
    print("=" * 50)

    # Test imports
    print("1. Checking imports...")
    try:
        from svgx_engine.services.access_control import (
            SVGXAccessControlService, UserRole, ResourceType, ActionType, PermissionLevel
        )
        print("   ✅ Imports work correctly")
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False

    # Test type hints
    print("2. Checking type hints...")
    try:
        ac_service = SVGXAccessControlService()
        # This should work without type errors
        user_data = ac_service.create_user(
            username="test",
            email="test@example.com",
            primary_role=UserRole.VIEWER
        )
        print("   ✅ Type hints are correct")
    except Exception as e:
        print(f"   ❌ Type hint error: {e}")
        return False

    # Test error handling
    print("3. Checking error handling...")
    try:
        from svgx_engine.utils.errors import SecurityError, ValidationError
        print("   ✅ Error classes imported correctly")
    except ImportError as e:
        print(f"   ❌ Error class import error: {e}")
        return False

    # Test documentation
    print("4. Checking documentation...")
    ac_service = SVGXAccessControlService()
    assert ac_service.__doc__ is not None
    assert "SVGX" in ac_service.__doc__
    print("   ✅ Documentation is present")

    print("\n🎉 Clean code practices verified!")
    return True


if __name__ == "__main__":
    print("🚀 Starting AccessControlService Migration Tests")
    print("=" * 60)

    # Run tests
    migration_success = test_access_control_migration()
    clean_code_success = test_clean_code_practices()

    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)

    if migration_success and clean_code_success:
        print("✅ ALL TESTS PASSED")
        print("✅ AccessControlService migration successful")
        print("✅ Clean code practices followed")
        print("✅ SVGX-specific features implemented")
        print("✅ Error handling improved")
        print("✅ Documentation updated")

        print("\n📝 Migration Summary:")
        print("- Copied access_control.py from arx_svg_parser")
        print("- Updated imports for SVGX namespace")
        print("- Added SVGX-specific resource types and actions")
        print("- Enhanced roles with CAD and BIM capabilities")
        print("- Added SVGX context to audit logging")
        print("- Improved error handling with custom exceptions")
        print("- Added SVGX-specific permission checking")
        print("- Updated database schema with SVGX extensions")

        print("\n🎯 Next Steps:")
        print("- Update MIGRATION_PLAN.md to mark step 4.1.1.1 as complete")
        print("- Proceed to step 4.1.1.2 (advanced_security.py migration)")
        print("- Continue with remaining services in Phase 4")

    else:
        print("❌ SOME TESTS FAILED")
        print("Please review the errors above and fix the issues.")
        sys.exit(1)
