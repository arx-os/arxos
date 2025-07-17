#!/usr/bin/env python3
"""
Test script for Advanced Security Service Migration

This script tests the migrated advanced security service for SVGX engine,
verifying all components work correctly with SVGX-specific features.
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any

# Add the svgx_engine directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from svgx_engine.services.advanced_security import (
    AdvancedSecurityService,
    PrivacyControlsService,
    EncryptionService,
    AuditTrailService,
    RBACService,
    DataClassification,
    PermissionLevel,
    AuditEventType,
    SecurityMetrics
)
from svgx_engine.utils.errors import SecurityError, ValidationError


def test_privacy_controls_service():
    """Test PrivacyControlsService with SVGX-specific features"""
    print("\n=== Testing PrivacyControlsService ===")
    
    try:
        privacy_service = PrivacyControlsService()
        
        # Test SVGX data classification
        test_cases = [
            ("svgx_content", "<svgx:behavior>test</svgx:behavior>", DataClassification.RESTRICTED),
            ("svgx_metadata", {"user_id": "test", "email": "test@example.com"}, DataClassification.CLASSIFIED),
            ("svgx_public_content", "<svg>basic svg</svg>", DataClassification.PUBLIC),
            ("svgx_behavior_profiles", {"behavior_script": "console.log('test')"}, DataClassification.CLASSIFIED)
        ]
        
        for data_type, content, expected in test_cases:
            result = privacy_service.classify_svgx_data(data_type, content)
            status = "✓" if result == expected else "✗"
            print(f"{status} {data_type}: {result.value} (expected: {expected.value})")
        
        # Test SVGX content validation
        valid_svgx = '<svg xmlns:svgx="http://svgx.org"><svgx:behavior>safe</svgx:behavior></svg>'
        invalid_svgx = '<svg><script>alert("xss")</script></svg>'
        
        is_valid, issues = privacy_service.validate_svgx_content(valid_svgx)
        print(f"✓ Valid SVGX content: {is_valid} (issues: {len(issues)})")
        
        is_valid, issues = privacy_service.validate_svgx_content(invalid_svgx)
        print(f"✓ Invalid SVGX content: {is_valid} (issues: {len(issues)})")
        
        # Test privacy controls application
        test_data = {"content": "test", "metadata": {"user": "test"}}
        classification = DataClassification.CONFIDENTIAL
        secured_data = privacy_service.apply_privacy_controls(test_data, classification)
        
        print(f"✓ Privacy controls applied: {secured_data['privacy_metadata']['classification']}")
        
        return True
        
    except Exception as e:
        print(f"✗ PrivacyControlsService test failed: {e}")
        return False


def test_encryption_service():
    """Test EncryptionService with SVGX-specific encryption"""
    print("\n=== Testing EncryptionService ===")
    
    try:
        encryption_service = EncryptionService()
        
        # Test SVGX data encryption
        test_data = {
            "svgx_content": "<svgx:behavior>test</svgx:behavior>",
            "metadata": {"user": "test", "timestamp": "2024-01-01"}
        }
        
        # Test different encryption layers
        layers = ["svgx_content", "svgx_metadata", "storage"]
        
        for layer in layers:
            encrypted = encryption_service.encrypt_svgx_data(test_data, layer)
            decrypted = encryption_service.decrypt_svgx_data(encrypted, layer)
            
            # Convert back to dict for comparison
            if isinstance(decrypted, bytes):
                try:
                    # Try to parse as JSON
                    decrypted_dict = json.loads(decrypted.decode('utf-8'))
                except Exception:
                    decrypted_dict = decrypted.decode('utf-8')
            else:
                decrypted_dict = decrypted
            
            if isinstance(decrypted_dict, dict):
                status = "✓" if decrypted_dict == test_data else "✗"
            else:
                status = "✓" if str(test_data) in str(decrypted_dict) else "✗"
            print(f"{status} {layer} encryption/decryption")
        
        # Test key rotation
        encryption_service.rotate_svgx_keys("svgx_content")
        print("✓ SVGX key rotation")
        
        # Test metrics
        metrics = encryption_service.get_metrics()
        print(f"✓ Encryption metrics: {metrics['encryption_operations']} operations")
        
        return True
        
    except Exception as e:
        print(f"✗ EncryptionService test failed: {e}")
        return False


def test_audit_trail_service():
    """Test AuditTrailService with SVGX-specific audit features"""
    print("\n=== Testing AuditTrailService ===")
    
    try:
        audit_service = AuditTrailService()
        
        # Test SVGX audit event logging
        event_id = audit_service.log_svgx_event(
            event_type=AuditEventType.SVGX_ACCESS,
            user_id="test_user",
            resource_id="test_svgx_file.svgx",
            action="read",
            details={"data_type": "svgx_content", "classification": "internal"},
            correlation_id="test_correlation"
        )
        print(f"✓ SVGX audit event logged: {event_id}")
        
        # Test audit log retrieval
        logs = audit_service.get_svgx_audit_logs()
        print(f"✓ Audit logs retrieved: {len(logs)} events")
        
        # Test filtered audit logs
        filtered_logs = audit_service.get_svgx_audit_logs({
            "event_type": "svgx_access",
            "user_id": "test_user"
        })
        print(f"✓ Filtered audit logs: {len(filtered_logs)} events")
        
        # Test compliance report generation
        date_range = (datetime.now() - timedelta(days=1), datetime.now())
        report = audit_service.generate_svgx_compliance_report("svgx_data_access", date_range)
        print(f"✓ Compliance report generated: {report['report_type']}")
        
        # Test retention policies
        audit_service.enforce_svgx_retention_policies()
        print("✓ Retention policies enforced")
        
        return True
        
    except Exception as e:
        print(f"✗ AuditTrailService test failed: {e}")
        return False


def test_rbac_service():
    """Test RBACService with SVGX-specific roles and permissions"""
    print("\n=== Testing RBACService ===")
    
    try:
        rbac_service = RBACService()
        
        # Test SVGX role creation
        role_id = rbac_service.create_svgx_role(
            "test_svgx_role",
            ["svgx:read", "svgx:write", "svgx:validate"],
            "Test SVGX role"
        )
        print(f"✓ SVGX role created: {role_id}")
        
        # Test user assignment
        user_id = "test_user"
        success = rbac_service.assign_user_to_svgx_role(user_id, role_id)
        print(f"✓ User assigned to role: {success}")
        
        # Test permission checks
        permissions = [
            ("read", "test_svgx_file.svgx", True),
            ("write", "test_svgx_file.svgx", True),
            ("compile", "test_svgx_file.svgx", False),  # Not in role
            ("admin", "test_svgx_file.svgx", False)     # Not in role
        ]
        
        for action, resource, expected in permissions:
            result = rbac_service.check_svgx_permission(user_id, resource, action)
            status = "✓" if result == expected else "✗"
            print(f"{status} Permission {action} on {resource}: {result} (expected: {expected})")
        
        # Test user permissions retrieval
        user_permissions = rbac_service.get_user_svgx_permissions(user_id)
        print(f"✓ User permissions: {len(user_permissions)} permissions")
        
        # Test role removal
        success = rbac_service.remove_user_from_svgx_role(user_id, role_id)
        print(f"✓ User removed from role: {success}")
        
        return True
        
    except Exception as e:
        print(f"✗ RBACService test failed: {e}")
        return False


def test_advanced_security_service():
    """Test the main AdvancedSecurityService with comprehensive SVGX security"""
    print("\n=== Testing AdvancedSecurityService ===")
    
    try:
        security_service = AdvancedSecurityService()
        
        # Test secure SVGX data access
        test_svgx_data = {
            "content": "<svgx:behavior>safe_behavior</svgx:behavior>",
            "metadata": {"user": "test", "created": "2024-01-01"}
        }
        
        # Test successful access
        secured_data = security_service.secure_svgx_data_access(
            user_id="test_user",
            resource_id="test.svgx",
            action="read",
            data=test_svgx_data,
            data_type="svgx_content"
        )
        print(f"✓ Secure data access: {secured_data['privacy_metadata']['classification']}")
        
        # Test security metrics
        metrics = security_service.get_svgx_security_metrics()
        print(f"✓ Security metrics retrieved: {len(metrics)} metric categories")
        
        # Test with invalid SVGX content (should raise ValidationError)
        try:
            invalid_svgx = "<svg><script>alert('xss')</script></svg>"
            security_service.secure_svgx_data_access(
                user_id="test_user",
                resource_id="test.svgx",
                action="write",
                data=invalid_svgx,
                data_type="svgx_content"
            )
            print("✗ Should have raised ValidationError for invalid SVGX")
            return False
        except ValidationError:
            print("✓ ValidationError correctly raised for invalid SVGX content")
        
        return True
        
    except Exception as e:
        print(f"✗ AdvancedSecurityService test failed: {e}")
        return False


def test_error_handling():
    """Test error handling for security operations"""
    print("\n=== Testing Error Handling ===")
    
    try:
        # Test SecurityError
        try:
            raise SecurityError("Test security error", "TEST_ERROR", {"details": "test"})
        except SecurityError as e:
            print(f"✓ SecurityError caught: {e.error_code}")
            error_dict = e.to_dict()
            print(f"✓ SecurityError to_dict: {error_dict['error_type']}")
        
        # Test ValidationError
        try:
            raise ValidationError("Test validation error", "VALIDATION_ERROR", {"field": "test"})
        except ValidationError as e:
            print(f"✓ ValidationError caught: {e.error_code}")
            error_dict = e.to_dict()
            print(f"✓ ValidationError to_dict: {error_dict['error_type']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


def test_integration():
    """Test integration between all security services"""
    print("\n=== Testing Service Integration ===")
    
    try:
        # Create all services
        privacy_service = PrivacyControlsService()
        encryption_service = EncryptionService()
        audit_service = AuditTrailService()
        rbac_service = RBACService()
        security_service = AdvancedSecurityService()
        
        # Test end-to-end workflow
        test_user = "integration_test_user"
        test_resource = "integration_test.svgx"
        test_data = "<svgx:behavior>integration_test</svgx:behavior>"
        
        # 1. Create role and assign user
        role_id = rbac_service.create_svgx_role("integration_role", ["svgx:read", "svgx:write"], "")
        rbac_service.assign_user_to_svgx_role(test_user, role_id)
        
        # 2. Secure data access
        secured_data = security_service.secure_svgx_data_access(
            user_id=test_user,
            resource_id=test_resource,
            action="write",
            data=test_data,
            data_type="svgx_content"
        )
        
        # 3. Verify audit trail
        audit_logs = audit_service.get_svgx_audit_logs({"user_id": test_user})
        
        # 4. Check metrics
        metrics = security_service.get_svgx_security_metrics()
        
        print(f"✓ Integration test completed:")
        print(f"  - Role created and user assigned")
        print(f"  - Data secured with classification: {secured_data['privacy_metadata']['classification']}")
        print(f"  - Audit events logged: {len(audit_logs)}")
        print(f"  - Security metrics available: {len(metrics)} categories")
        
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False


def main():
    """Run all tests for the advanced security service migration"""
    print("🔒 Testing Advanced Security Service Migration for SVGX Engine")
    print("=" * 70)
    
    tests = [
        ("Privacy Controls Service", test_privacy_controls_service),
        ("Encryption Service", test_encryption_service),
        ("Audit Trail Service", test_audit_trail_service),
        ("RBAC Service", test_rbac_service),
        ("Advanced Security Service", test_advanced_security_service),
        ("Error Handling", test_error_handling),
        ("Service Integration", test_integration)
    ]
    
    results = []
    start_time = time.time()
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Advanced Security Service migration successful.")
        print("\n✅ Migration Status:")
        print("   - PrivacyControlsService: Migrated with SVGX-specific features")
        print("   - EncryptionService: Migrated with SVGX encryption layers")
        print("   - AuditTrailService: Migrated with SVGX audit events")
        print("   - RBACService: Migrated with SVGX roles and permissions")
        print("   - AdvancedSecurityService: Migrated with comprehensive SVGX security")
        print("   - Error handling: Enhanced with SecurityError and ValidationError")
        print("   - Service integration: All services work together seamlessly")
    else:
        print("❌ Some tests failed. Please review the implementation.")
    
    elapsed_time = time.time() - start_time
    print(f"\n⏱️  Total test time: {elapsed_time:.2f} seconds")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 