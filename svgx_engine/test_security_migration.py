"""
Security Service Migration Test for SVGX Engine

This test validates the security service migration from arx_svg_parser
to svgx_engine, ensuring all functionality is preserved and enhanced.
"""

import sys
import os
import json
import logging
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

# Add the svgx_engine directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from svgx_engine.services.security import SecurityService
from svgx_engine.services.advanced_security import (
    DataClassification, PermissionLevel, AuditEventType, SecurityError
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityMigrationTest:
    """Test class to validate security service migration."""
    
    def __init__(self):
        self.results = {
            'completed': [],
            'in_progress': [],
            'missing': [],
            'errors': []
        }
        self.security_service = SecurityService()
        self.test_user_id = "test_user_123"
        self.test_resource_id = "test_svgx_document"
        self.test_correlation_id = "test_correlation_456"
    
    def test_security_service_initialization(self):
        """Test security service initialization."""
        try:
            logger.info("Testing Security Service Initialization...")
            
            # Test basic initialization
            security_service = SecurityService()
            self.results['completed'].append("Security Service - Basic initialization")
            
            # Test all components are available
            assert hasattr(security_service, 'advanced_security')
            assert hasattr(security_service, 'privacy_controls')
            assert hasattr(security_service, 'encryption')
            assert hasattr(security_service, 'audit_trail')
            assert hasattr(security_service, 'rbac')
            
            self.results['completed'].append("Security Service - All components available")
            
            logger.info("✓ Security Service initialization tests completed")
            
        except Exception as e:
            logger.error(f"✗ Security Service initialization test failed: {e}")
            self.results['errors'].append(f"Security Service Initialization: {e}")
    
    def test_data_classification(self):
        """Test data classification functionality."""
        try:
            logger.info("Testing Data Classification...")
            
            # Test public data classification
            public_content = "<svg><rect x='10' y='10' width='100' height='50'/></svg>"
            classification = self.security_service.classify_data("svgx_content", public_content)
            assert classification == "public"
            self.results['completed'].append("Data Classification - Public content")
            
            # Test confidential data classification
            confidential_content = "<svg><rect x='10' y='10' width='100' height='50'/><svgx:behavior><variables><password>secret123</password></variables></svgx:behavior></svg>"
            classification = self.security_service.classify_data("svgx_content", confidential_content)
            assert classification == "restricted"
            self.results['completed'].append("Data Classification - Confidential content")
            
            # Test metadata classification
            metadata = {"user_id": "user123", "email": "user@example.com", "password": "secret"}
            classification = self.security_service.classify_data("svgx_metadata", metadata)
            assert classification == "classified"
            self.results['completed'].append("Data Classification - Metadata")
            
            logger.info("✓ Data classification tests completed")
            
        except Exception as e:
            logger.error(f"✗ Data classification test failed: {e}")
            self.results['errors'].append(f"Data Classification: {e}")
    
    def test_content_validation(self):
        """Test SVGX content validation."""
        try:
            logger.info("Testing Content Validation...")
            
            # Test valid SVGX content
            valid_content = "<svg xmlns='http://www.w3.org/2000/svg'><rect x='10' y='10' width='100' height='50'/></svg>"
            is_valid, issues = self.security_service.validate_svgx_content(valid_content)
            assert is_valid
            assert len(issues) == 0
            self.results['completed'].append("Content Validation - Valid SVGX content")
            
            # Test invalid SVGX content with security issues
            invalid_content = "<svg><script>alert('xss')</script><rect x='10' y='10' width='100' height='50'/></svg>"
            is_valid, issues = self.security_service.validate_svgx_content(invalid_content)
            assert not is_valid
            assert len(issues) > 0
            self.results['completed'].append("Content Validation - Invalid SVGX content")
            
            logger.info("✓ Content validation tests completed")
            
        except Exception as e:
            logger.error(f"✗ Content validation test failed: {e}")
            self.results['errors'].append(f"Content Validation: {e}")
    
    def test_encryption_decryption(self):
        """Test encryption and decryption functionality."""
        try:
            logger.info("Testing Encryption/Decryption...")
            
            # Test data encryption
            test_data = {"svgx_content": "<svg><rect x='10' y='10' width='100' height='50'/></svg>"}
            encrypted_data = self.security_service.encrypt_svgx_data(test_data, "storage")
            assert isinstance(encrypted_data, bytes)
            assert len(encrypted_data) > 0
            self.results['completed'].append("Encryption - Data encryption")
            
            # Test data decryption
            decrypted_data = self.security_service.decrypt_svgx_data(encrypted_data, "storage")
            assert decrypted_data == test_data
            self.results['completed'].append("Decryption - Data decryption")
            
            # Test different encryption layers
            transport_encrypted = self.security_service.encrypt_svgx_data(test_data, "transport")
            transport_decrypted = self.security_service.decrypt_svgx_data(transport_encrypted, "transport")
            assert transport_decrypted == test_data
            self.results['completed'].append("Encryption - Transport layer")
            
            logger.info("✓ Encryption/Decryption tests completed")
            
        except Exception as e:
            logger.error(f"✗ Encryption/Decryption test failed: {e}")
            self.results['errors'].append(f"Encryption/Decryption: {e}")
    
    def test_role_based_access_control(self):
        """Test RBAC functionality."""
        try:
            logger.info("Testing Role-Based Access Control...")
            
            # Test role creation
            role_id = self.security_service.create_user_role(
                self.test_user_id, "test_role", ["read", "write"], "Test role"
            )
            assert role_id is not None
            self.results['completed'].append("RBAC - Role creation")
            
            # Test permission checking
            has_permission = self.security_service.check_permission(self.test_user_id, self.test_resource_id, "read")
            assert has_permission
            self.results['completed'].append("RBAC - Permission checking")
            
            # Test getting user permissions
            permissions = self.security_service.get_user_permissions(self.test_user_id)
            assert "read" in permissions
            assert "write" in permissions
            self.results['completed'].append("RBAC - User permissions")
            
            logger.info("✓ RBAC tests completed")
            
        except Exception as e:
            logger.error(f"✗ RBAC test failed: {e}")
            self.results['errors'].append(f"RBAC: {e}")
    
    def test_secure_operations(self):
        """Test secure SVGX operations."""
        try:
            logger.info("Testing Secure SVGX Operations...")
            
            # Test successful secure operation
            test_data = {"svgx_content": "<svg><rect x='10' y='10' width='100' height='50'/></svg>"}
            result = self.security_service.secure_svgx_operation(
                self.test_user_id, self.test_resource_id, "read", test_data, "svgx_content", self.test_correlation_id
            )
            assert result is not None
            self.results['completed'].append("Secure Operations - Successful operation")
            
            # Test operation with invalid permissions (should fail)
            try:
                self.security_service.secure_svgx_operation(
                    "unauthorized_user", self.test_resource_id, "delete", test_data, "svgx_content", self.test_correlation_id
                )
                # Should not reach here
                assert False, "Expected SecurityError for unauthorized user"
            except SecurityError:
                # Expected behavior
                self.results['completed'].append("Secure Operations - Unauthorized access blocked")
            
            logger.info("✓ Secure operations tests completed")
            
        except Exception as e:
            logger.error(f"✗ Secure operations test failed: {e}")
            self.results['errors'].append(f"Secure Operations: {e}")
    
    def test_audit_logging(self):
        """Test audit logging functionality."""
        try:
            logger.info("Testing Audit Logging...")
            
            # Test event logging
            event_id = self.security_service.log_event(
                "svgx_access", self.test_user_id, self.test_resource_id, "read",
                {"details": "test event"}, self.test_correlation_id
            )
            assert event_id is not None
            self.results['completed'].append("Audit Logging - Event logging")
            
            # Test getting audit logs
            logs = self.security_service.get_audit_logs({"user_id": self.test_user_id})
            assert len(logs) > 0
            self.results['completed'].append("Audit Logging - Log retrieval")
            
            # Test compliance report generation
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)
            report = self.security_service.generate_compliance_report("data_access", (start_date, end_date))
            assert report is not None
            self.results['completed'].append("Audit Logging - Compliance report")
            
            logger.info("✓ Audit logging tests completed")
            
        except Exception as e:
            logger.error(f"✗ Audit logging test failed: {e}")
            self.results['errors'].append(f"Audit Logging: {e}")
    
    def test_data_anonymization(self):
        """Test data anonymization functionality."""
        try:
            logger.info("Testing Data Anonymization...")
            
            # Test data anonymization
            sensitive_data = {
                "user_id": "user123",
                "email": "user@example.com",
                "password": "secret123",
                "svgx_content": "<svg><rect x='10' y='10' width='100' height='50'/></svg>"
            }
            
            anonymized_data = self.security_service.anonymize_data(
                sensitive_data, ["user_id", "email", "password"]
            )
            
            assert anonymized_data["user_id"] != "user123"
            assert anonymized_data["email"] != "user@example.com"
            assert anonymized_data["password"] != "secret123"
            assert anonymized_data["svgx_content"] == sensitive_data["svgx_content"]  # Should not be anonymized
            
            self.results['completed'].append("Data Anonymization - Sensitive data anonymization")
            
            logger.info("✓ Data anonymization tests completed")
            
        except Exception as e:
            logger.error(f"✗ Data anonymization test failed: {e}")
            self.results['errors'].append(f"Data Anonymization: {e}")
    
    def test_security_metrics(self):
        """Test security metrics collection."""
        try:
            logger.info("Testing Security Metrics...")
            
            # Test metrics collection
            metrics = self.security_service.get_security_metrics()
            assert metrics is not None
            assert isinstance(metrics, dict)
            
            # Check for expected metric keys
            expected_keys = ["encryption_operations", "audit_events_logged", "permission_checks"]
            for key in expected_keys:
                assert key in metrics
            
            self.results['completed'].append("Security Metrics - Metrics collection")
            
            logger.info("✓ Security metrics tests completed")
            
        except Exception as e:
            logger.error(f"✗ Security metrics test failed: {e}")
            self.results['errors'].append(f"Security Metrics: {e}")
    
    def test_key_rotation(self):
        """Test encryption key rotation."""
        try:
            logger.info("Testing Key Rotation...")
            
            # Test key rotation
            self.security_service.rotate_encryption_keys("all")
            self.results['completed'].append("Key Rotation - Key rotation")
            
            # Test that encryption still works after rotation
            test_data = {"test": "data"}
            encrypted_data = self.security_service.encrypt_svgx_data(test_data, "storage")
            decrypted_data = self.security_service.decrypt_svgx_data(encrypted_data, "storage")
            assert decrypted_data == test_data
            
            self.results['completed'].append("Key Rotation - Post-rotation functionality")
            
            logger.info("✓ Key rotation tests completed")
            
        except Exception as e:
            logger.error(f"✗ Key rotation test failed: {e}")
            self.results['errors'].append(f"Key Rotation: {e}")
    
    def run_all_tests(self):
        """Run all security migration tests."""
        logger.info("Starting Security Service Migration Tests...")
        
        test_methods = [
            self.test_security_service_initialization,
            self.test_data_classification,
            self.test_content_validation,
            self.test_encryption_decryption,
            self.test_role_based_access_control,
            self.test_secure_operations,
            self.test_audit_logging,
            self.test_data_anonymization,
            self.test_security_metrics,
            self.test_key_rotation
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                logger.error(f"Test method {test_method.__name__} failed: {e}")
                self.results['errors'].append(f"{test_method.__name__}: {e}")
        
        self.generate_report()
    
    def generate_report(self):
        """Generate a comprehensive test report."""
        logger.info("\n" + "="*60)
        logger.info("SECURITY SERVICE MIGRATION TEST REPORT")
        logger.info("="*60)
        
        logger.info(f"\n✅ Completed Tests: {len(self.results['completed'])}")
        for test in self.results['completed']:
            logger.info(f"  ✓ {test}")
        
        if self.results['in_progress']:
            logger.info(f"\n🔄 In Progress: {len(self.results['in_progress'])}")
            for test in self.results['in_progress']:
                logger.info(f"  🔄 {test}")
        
        if self.results['missing']:
            logger.info(f"\n❌ Missing: {len(self.results['missing'])}")
            for test in self.results['missing']:
                logger.info(f"  ❌ {test}")
        
        if self.results['errors']:
            logger.info(f"\n💥 Errors: {len(self.results['errors'])}")
            for error in self.results['errors']:
                logger.info(f"  💥 {error}")
        
        # Calculate success rate
        total_tests = len(self.results['completed']) + len(self.results['errors'])
        success_rate = (len(self.results['completed']) / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"\n📊 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            logger.info("🎉 Security Service Migration: SUCCESS")
        elif success_rate >= 70:
            logger.info("⚠️  Security Service Migration: PARTIAL SUCCESS")
        else:
            logger.info("❌ Security Service Migration: FAILED")
        
        logger.info("="*60)


if __name__ == "__main__":
    test = SecurityMigrationTest()
    test.run_all_tests() 