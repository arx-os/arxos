"""
Advanced Security & Compliance Tests

Comprehensive test suite for enterprise-grade security features including:
- Advanced privacy controls and data classification
- Multi-layer encryption (AES-256, TLS 1.3)
- Comprehensive audit trail system
- Role-based access control (RBAC)
- AHJ API integration
- Data retention policies
"""

import unittest
import time
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from core.services.advanced_security
    PrivacyControlsService, EncryptionService, AuditTrailService,
    RBACService, AdvancedSecurityService, DataClassification,
    AuditEventType, PermissionLevel
)

from services.ahj_api_integration import (
    AHJAPIService, AHJInspectionStatus, ViolationSeverity,
    AHJInspectionLayer, AHJAnnotation, CodeViolation
)

from services.data_retention import (
    DataRetentionService, RetentionPolicyType, DeletionStrategy,
    DataType, RetentionPolicy, DataLifecycle, DeletionJob
)


class TestPrivacyControlsService(unittest.TestCase):
    """Test privacy controls and data classification"""
    
    def setUp(self):
        self.privacy_service = PrivacyControlsService()
    
    def test_data_classification(self):
        """Test data classification based on type and content"""
        # Test basic classification
        classification = self.privacy_service.classify_data("building_data", "test content")
        self.assertEqual(classification, DataClassification.INTERNAL)
        
        # Test sensitive content classification
        sensitive_content = "This contains a password: secret123"
        classification = self.privacy_service.classify_data("user_data", sensitive_content)
        self.assertEqual(classification, DataClassification.RESTRICTED)
        
        # Test sensitive field classification
        sensitive_data = {"password": "secret123", "email": "test@example.com"}
        classification = self.privacy_service.classify_data("user_credentials", sensitive_data)
        self.assertEqual(classification, DataClassification.CLASSIFIED)
    
    def test_privacy_controls_application(self):
        """Test privacy controls application"""
        data = {"test": "data"}
        classification = DataClassification.CONFIDENTIAL
        
        result = self.privacy_service.apply_privacy_controls(data, classification)
        
        self.assertIn("data", result)
        self.assertIn("privacy_metadata", result)
        self.assertEqual(result["privacy_metadata"]["classification"], "confidential")
        self.assertTrue(result["privacy_metadata"]["encryption_required"])
    
    def test_data_anonymization(self):
        """Test data anonymization"""
        data = {
            "user_id": "user123",
            "email": "test@example.com",
            "name": "John Doe",
            "building_data": "non-sensitive"
        }
        
        anonymized = self.privacy_service.anonymize_data(data)
        
        self.assertNotEqual(anonymized["user_id"], "user123")
        self.assertNotEqual(anonymized["email"], "test@example.com")
        self.assertNotEqual(anonymized["name"], "John Doe")
        self.assertEqual(anonymized["building_data"], "non-sensitive")


class TestEncryptionService(unittest.TestCase):
    """Test multi-layer encryption service"""
    
    def setUp(self):
        self.encryption_service = EncryptionService()
    
    def test_encryption_decryption(self):
        """Test basic encryption and decryption"""
        test_data = "sensitive building data"
        
        # Encrypt data
        encrypted = self.encryption_service.encrypt_data(test_data, "storage")
        self.assertIsInstance(encrypted, bytes)
        self.assertNotEqual(encrypted, test_data.encode())
        
        # Decrypt data
        decrypted = self.encryption_service.decrypt_data(encrypted, "storage")
        self.assertEqual(decrypted, test_data.encode())
    
    def test_different_encryption_layers(self):
        """Test different encryption layers"""
        test_data = "test data"
        
        # Test storage encryption
        storage_encrypted = self.encryption_service.encrypt_data(test_data, "storage")
        
        # Test transport encryption
        transport_encrypted = self.encryption_service.encrypt_data(test_data, "transport")
        
        # Test database encryption
        database_encrypted = self.encryption_service.encrypt_data(test_data, "database")
        
        # All should be different
        self.assertNotEqual(storage_encrypted, transport_encrypted)
        self.assertNotEqual(storage_encrypted, database_encrypted)
        self.assertNotEqual(transport_encrypted, database_encrypted)
    
    def test_key_rotation(self):
        """Test encryption key rotation"""
        # Store original key
        original_key = self.encryption_service.master_key
        
        # Rotate keys
        self.encryption_service.rotate_keys("all")
        
        # Verify key changed
        self.assertNotEqual(original_key, self.encryption_service.master_key)
    
    def test_encryption_metrics(self):
        """Test encryption performance metrics"""
        test_data = "test data"
        
        # Perform encryption operations
        for _ in range(5):
            self.encryption_service.encrypt_data(test_data, "storage")
        
        metrics = self.encryption_service.get_metrics()
        
        self.assertEqual(metrics["total_operations"], 5)
        self.assertGreater(metrics["average_time_ms"], 0)


class TestAuditTrailService(unittest.TestCase):
    """Test comprehensive audit trail system"""
    
    def setUp(self):
        self.audit_service = AuditTrailService()
    
    def test_event_logging(self):
        """Test audit event logging"""
        event_id = self.audit_service.log_event(
            AuditEventType.DATA_ACCESS,
            user_id="user123",
            resource_id="building_001",
            action="read",
            details={"data_type": "building_data"}
        )
        
        self.assertIsInstance(event_id, str)
        
        # Verify event was logged
        logs = self.audit_service.get_audit_logs()
        self.assertGreater(len(logs), 0)
        
        # Find our event
        event = next((log for log in logs if log["event_id"] == event_id), None)
        self.assertIsNotNone(event)
        self.assertEqual(event["user_id"], "user123")
        self.assertEqual(event["resource_id"], "building_001")
    
    def test_audit_log_filtering(self):
        """Test audit log filtering"""
        # Log multiple events
        self.audit_service.log_event(
            AuditEventType.DATA_ACCESS, "user1", "resource1", "read"
        )
        self.audit_service.log_event(
            AuditEventType.USER_LOGIN, "user2", "auth", "login"
        )
        
        # Filter by event type
        data_access_logs = self.audit_service.get_audit_logs({
            "event_type": "data_access"
        })
        
        self.assertEqual(len(data_access_logs), 1)
        self.assertEqual(data_access_logs[0]["event_type"], "data_access")
    
    def test_compliance_reporting(self):
        """Test compliance report generation"""
        # Log various events
        self.audit_service.log_event(
            AuditEventType.DATA_ACCESS, "user1", "resource1", "read"
        )
        self.audit_service.log_event(
            AuditEventType.USER_LOGIN, "user2", "auth", "login"
        )
        self.audit_service.log_event(
            AuditEventType.DATA_MODIFICATION, "user1", "resource1", "update"
        )
        
        # Generate compliance report
        date_range = (datetime.now() - timedelta(days=1), datetime.now() + timedelta(days=1))
        report = self.audit_service.generate_compliance_report("data_access", date_range)
        
        self.assertIn("total_events", report)
        self.assertIn("unique_users", report)
        self.assertIn("successful_access", report)
    
    def test_retention_policy_enforcement(self):
        """Test retention policy enforcement"""
        # Log events
        for i in range(10):
            self.audit_service.log_event(
                AuditEventType.DATA_ACCESS, f"user{i}", f"resource{i}", "read"
            )
        
        initial_count = len(self.audit_service.get_audit_logs())
        
        # Enforce retention policies
        self.audit_service.enforce_retention_policies()
        
        # Verify no events were removed (all are recent)
        final_count = len(self.audit_service.get_audit_logs())
        self.assertEqual(initial_count, final_count)


class TestRBACService(unittest.TestCase):
    """Test role-based access control"""
    
    def setUp(self):
        self.rbac_service = RBACService()
    
    def test_role_creation(self):
        """Test role creation"""
        permissions = ["building:read", "building:write", "user:read"]
        role_id = self.rbac_service.create_role("Test Role", permissions, "Test description")
        
        self.assertIsInstance(role_id, str)
        
        # Verify role exists
        user_permissions = self.rbac_service.get_user_permissions("test_user")
        # Should be empty since no user assigned yet
        self.assertEqual(len(user_permissions), 0)
    
    def test_user_role_assignment(self):
        """Test user role assignment"""
        # Create role
        permissions = ["building:read", "building:write"]
        role_id = self.rbac_service.create_role("Building Admin", permissions)
        
        # Assign user to role
        success = self.rbac_service.assign_user_to_role("user123", role_id)
        self.assertTrue(success)
        
        # Verify user has permissions
        user_permissions = self.rbac_service.get_user_permissions("user123")
        self.assertEqual(len(user_permissions), 2)
        self.assertIn("building:read", user_permissions)
        self.assertIn("building:write", user_permissions)
    
    def test_permission_checking(self):
        """Test permission checking"""
        # Create role and assign user
        role_id = self.rbac_service.create_role("Test Role", ["building:read"])
        self.rbac_service.assign_user_to_role("user123", role_id)
        
        # Test permission checks
        self.assertTrue(self.rbac_service.check_permission("user123", "building", "read"))
        self.assertFalse(self.rbac_service.check_permission("user123", "building", "write"))
        self.assertFalse(self.rbac_service.check_permission("user456", "building", "read"))
    
    def test_wildcard_permissions(self):
        """Test wildcard permission handling"""
        # Create role with wildcard permissions
        role_id = self.rbac_service.create_role("Admin", ["*:*"])
        self.rbac_service.assign_user_to_role("admin", role_id)
        
        # Test wildcard permissions
        self.assertTrue(self.rbac_service.check_permission("admin", "building", "read"))
        self.assertTrue(self.rbac_service.check_permission("admin", "user", "write"))
        self.assertTrue(self.rbac_service.check_permission("admin", "any", "any"))
    
    def test_role_removal(self):
        """Test user role removal"""
        # Create role and assign user
        role_id = self.rbac_service.create_role("Test Role", ["building:read"])
        self.rbac_service.assign_user_to_role("user123", role_id)
        
        # Verify user has permissions
        user_permissions = self.rbac_service.get_user_permissions("user123")
        self.assertIn("building:read", user_permissions)
        
        # Remove role
        success = self.rbac_service.remove_user_from_role("user123", role_id)
        self.assertTrue(success)
        
        # Verify permissions removed
        user_permissions = self.rbac_service.get_user_permissions("user123")
        self.assertNotIn("building:read", user_permissions)


class TestAHJAPIService(unittest.TestCase):
    """Test AHJ API integration"""
    
    def setUp(self):
        self.ahj_service = AHJAPIService()
    
    def test_inspection_layer_creation(self):
        """Test AHJ inspection layer creation"""
        layer_id = self.ahj_service.create_inspection_layer(
            building_id="building_001",
            ahj_id="ahj_001",
            inspector_id="inspector_123"
        )
        
        self.assertIsInstance(layer_id, str)
        
        # Verify layer exists
        history = self.ahj_service.get_inspection_history(layer_id)
        self.assertEqual(history["building_id"], "building_001")
        self.assertEqual(history["ahj_id"], "ahj_001")
    
    def test_inspection_annotation(self):
        """Test inspection annotation addition"""
        # Create inspection layer
        layer_id = self.ahj_service.create_inspection_layer(
            "building_001", "ahj_001", "inspector_123"
        )
        
        # Add annotation
        annotation_id = self.ahj_service.add_inspection_annotation(
            layer_id=layer_id,
            inspector_id="inspector_123",
            location={"floor": 1, "room": "101"},
            annotation_type="violation",
            description="Missing fire extinguisher",
            severity=ViolationSeverity.MAJOR,
            code_reference="IFC 906.1"
        )
        
        self.assertIsInstance(annotation_id, str)
        
        # Verify annotation in history
        history = self.ahj_service.get_inspection_history(layer_id)
        self.assertEqual(len(history["annotations"]), 1)
        self.assertEqual(history["annotations"][0]["description"], "Missing fire extinguisher")
    
    def test_code_violation_creation(self):
        """Test code violation creation"""
        # Create inspection layer
        layer_id = self.ahj_service.create_inspection_layer(
            "building_001", "ahj_001", "inspector_123"
        )
        
        # Add violation
        violation_id = self.ahj_service.add_code_violation(
            layer_id=layer_id,
            inspector_id="inspector_123",
            code_section="IFC 906.1",
            description="Missing fire extinguisher",
            severity=ViolationSeverity.CRITICAL,
            location={"floor": 1, "room": "101"},
            required_action="Install fire extinguisher within 30 days"
        )
        
        self.assertIsInstance(violation_id, str)
        
        # Verify violation in history
        history = self.ahj_service.get_inspection_history(layer_id)
        self.assertEqual(len(history["violations"]), 1)
        self.assertEqual(history["violations"][0]["severity"], "critical")
    
    def test_ahj_permissions_validation(self):
        """Test AHJ permissions validation"""
        # Test valid permission
        self.assertTrue(self.ahj_service.validate_ahj_permissions("ahj_001", "building_001"))
        
        # Test invalid permission
        self.assertFalse(self.ahj_service.validate_ahj_permissions("invalid_ahj", "building_001"))
    
    def test_compliance_report_generation(self):
        """Test compliance report generation"""
        # Create inspection with violations
        layer_id = self.ahj_service.create_inspection_layer(
            "building_001", "ahj_001", "inspector_123"
        )
        
        self.ahj_service.add_code_violation(
            layer_id=layer_id,
            inspector_id="inspector_123",
            code_section="IFC 906.1",
            description="Missing fire extinguisher",
            severity=ViolationSeverity.CRITICAL,
            location={"floor": 1, "room": "101"},
            required_action="Install fire extinguisher"
        )
        
        # Generate compliance report
        report = self.ahj_service.generate_compliance_report("building_001")
        
        self.assertIn("building_id", report)
        self.assertIn("total_inspections", report)
        self.assertIn("total_violations", report)
        self.assertIn("compliance_score", report)
        self.assertEqual(report["total_violations"], 1)


class TestDataRetentionService(unittest.TestCase):
    """Test data retention policies"""
    
    def setUp(self):
        self.retention_service = DataRetentionService()
    
    def test_retention_policy_creation(self):
        """Test retention policy creation"""
        policy_id = self.retention_service.create_retention_policy(
            data_type=DataType.BUILDING_DATA,
            retention_period_days=1825,
            deletion_strategy=DeletionStrategy.ARCHIVE_DELETE,
            description="Building data - 5 years"
        )
        
        self.assertIsInstance(policy_id, str)
        
        # Verify policy exists
        policies = self.retention_service.get_retention_policies()
        policy = next((p for p in policies if p["policy_id"] == policy_id), None)
        self.assertIsNotNone(policy)
        self.assertEqual(policy["data_type"], "building_data")
    
    def test_policy_application(self):
        """Test retention policy application"""
        # Create policy
        policy_id = self.retention_service.create_retention_policy(
            DataType.USER_DATA, 365, DeletionStrategy.SOFT_DELETE
        )
        
        # Apply policy to data
        success = self.retention_service.apply_retention_policy("data_123", policy_id)
        self.assertTrue(success)
        
        # Verify lifecycle created
        lifecycle = self.retention_service.get_data_lifecycle("data_123")
        self.assertEqual(len(lifecycle), 1)
        self.assertEqual(lifecycle[0]["data_id"], "data_123")
    
    def test_data_deletion_scheduling(self):
        """Test data deletion scheduling"""
        # Create policy and apply to data
        policy_id = self.retention_service.create_retention_policy(
            DataType.TEMPORARY_DATA, 30, DeletionStrategy.HARD_DELETE
        )
        self.retention_service.apply_retention_policy("temp_data_123", policy_id)
        
        # Schedule deletion
        job_id = self.retention_service.schedule_data_deletion("temp_data_123")
        self.assertIsInstance(job_id, str)
    
    def test_retention_policy_execution(self):
        """Test retention policy execution"""
        # Create policy with short retention
        policy_id = self.retention_service.create_retention_policy(
            DataType.TEMPORARY_DATA, 1, DeletionStrategy.SOFT_DELETE
        )
        
        # Apply policy
        self.retention_service.apply_retention_policy("test_data", policy_id)
        
        # Manually trigger execution
        results = self.retention_service.execute_retention_policies()
        
        self.assertIn("jobs_executed", results)
        self.assertIn("data_deleted", results)
    
    def test_data_archiving(self):
        """Test data archiving"""
        # Create temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test data")
            temp_path = temp_file.name
        
        try:
            # Archive data
            success = self.retention_service.archive_data("test_data_123")
            self.assertTrue(success)
            
            # Verify archive created
            archive_dir = self.retention_service.archive_config["archive_path"]
            self.assertTrue(os.path.exists(archive_dir))
            
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_compliance_reporting(self):
        """Test compliance report generation"""
        # Create policies and apply to data
        policy_id = self.retention_service.create_retention_policy(
            DataType.BUILDING_DATA, 1825, DeletionStrategy.ARCHIVE_DELETE
        )
        self.retention_service.apply_retention_policy("building_data_123", policy_id)
        
        # Generate compliance report
        report = self.retention_service.generate_compliance_report()
        
        self.assertIn("total_data_items", report)
        self.assertIn("compliance_score", report)
        self.assertIn("compliance_violations", report)
        self.assertIn("data_by_type", report)


class TestAdvancedSecurityService(unittest.TestCase):
    """Test integrated advanced security service"""
    
    def setUp(self):
        self.security_service = AdvancedSecurityService()
    
    def test_secure_data_access(self):
        """Test secure data access with full security controls"""
        # Create role and assign user
        role_id = self.security_service.rbac_service.create_role(
            "Test Role", ["building:read"]
        )
        self.security_service.rbac_service.assign_user_to_role("user123", role_id)
        
        # Test secure data access
        data = {"building_info": "test data"}
        result = self.security_service.secure_data_access(
            user_id="user123",
            resource_id="building",
            action="read",
            data=data,
            data_type="building_data"
        )
        
        self.assertIn("data", result)
        self.assertIn("privacy_metadata", result)
        self.assertEqual(result["privacy_metadata"]["classification"], "internal")
    
    def test_permission_denied_access(self):
        """Test secure data access with insufficient permissions"""
        # Try to access data without permissions
        with self.assertRaises(PermissionError):
            self.security_service.secure_data_access(
                user_id="user456",
                resource_id="building",
                action="write",
                data={"test": "data"},
                data_type="building_data"
            )
    
    def test_security_metrics(self):
        """Test security metrics collection"""
        # Perform some operations
        role_id = self.security_service.rbac_service.create_role("Test", ["building:read"])
        self.security_service.rbac_service.assign_user_to_role("user123", role_id)
        
        # Get metrics
        metrics = self.security_service.get_security_metrics()
        
        self.assertIn("privacy_controls", metrics)
        self.assertIn("encryption", metrics)
        self.assertIn("audit_trail", metrics)
        self.assertIn("rbac", metrics)
        self.assertIn("overall", metrics)


class TestSecurityIntegration(unittest.TestCase):
    """Test integration between security components"""
    
    def setUp(self):
        self.privacy_service = PrivacyControlsService()
        self.encryption_service = EncryptionService()
        self.audit_service = AuditTrailService()
        self.rbac_service = RBACService()
        self.ahj_service = AHJAPIService()
        self.retention_service = DataRetentionService()
    
    def test_end_to_end_security_workflow(self):
        """Test complete security workflow"""
        # 1. Create user and assign role
        role_id = self.rbac_service.create_role("Building Inspector", ["building:read", "inspection:write"])
        self.rbac_service.assign_user_to_role("inspector_123", role_id)
        
        # 2. Classify and encrypt data
        building_data = {"floors": 5, "systems": ["electrical", "plumbing"]}
        classification = self.privacy_service.classify_data("building_data", building_data)
        secured_data = self.privacy_service.apply_privacy_controls(building_data, classification)
        
        # 3. Log audit event
        event_id = self.audit_service.log_event(
            AuditEventType.DATA_ACCESS,
            user_id="inspector_123",
            resource_id="building_001",
            action="read",
            details={"classification": classification.value}
        )
        
        # 4. Create AHJ inspection
        layer_id = self.ahj_service.create_inspection_layer(
            "building_001", "ahj_001", "inspector_123"
        )
        
        # 5. Apply retention policy
        policy_id = self.retention_service.create_retention_policy(
            DataType.AHJ_DATA, 3650, DeletionStrategy.ARCHIVE_DELETE
        )
        self.retention_service.apply_retention_policy(layer_id, policy_id)
        
        # 6. Verify all components worked together
        self.assertTrue(self.rbac_service.check_permission("inspector_123", "building", "read"))
        self.assertEqual(classification, DataClassification.INTERNAL)
        self.assertIsInstance(event_id, str)
        self.assertIsInstance(layer_id, str)
        
        # Verify audit trail
        logs = self.audit_service.get_audit_logs({"user_id": "inspector_123"})
        self.assertGreater(len(logs), 0)
        
        # Verify AHJ inspection
        history = self.ahj_service.get_inspection_history(layer_id)
        self.assertEqual(history["building_id"], "building_001")
        
        # Verify retention policy
        lifecycle = self.retention_service.get_data_lifecycle(layer_id)
        self.assertEqual(len(lifecycle), 1)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2) 