"""
Advanced Security & Compliance Demonstration

This script demonstrates the enterprise-grade security features including:
- Advanced privacy controls and data classification
- Multi-layer encryption (AES-256, TLS 1.3)
- Comprehensive audit trail system
- Role-based access control (RBAC)
- AHJ API integration
- Data retention policies
"""

import sys
import os
import time
import json
from datetime import datetime, timedelta

# Add the parent directory to the path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.advanced_security import (
    PrivacyControlsService, EncryptionService, AuditTrailService,
    RBACService, AdvancedSecurityService, DataClassification,
    AuditEventType, PermissionLevel
)

from services.ahj_api_integration import (
    AHJAPIService, AHJInspectionStatus, ViolationSeverity
)

from services.data_retention import (
    DataRetentionService, RetentionPolicyType, DeletionStrategy, DataType
)

from utils.logger import get_logger

logger = get_logger(__name__)


class AdvancedSecurityDemo:
    """Demonstration of advanced security and compliance features"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Initialize security services
        self.privacy_service = PrivacyControlsService()
        self.encryption_service = EncryptionService()
        self.audit_service = AuditTrailService()
        self.rbac_service = RBACService()
        self.ahj_service = AHJAPIService()
        self.retention_service = DataRetentionService()
        self.security_service = AdvancedSecurityService()
        
        # Demo data
        self.demo_building_data = {
            "building_id": "demo_building_001",
            "floors": 5,
            "systems": ["electrical", "plumbing", "hvac", "fire_safety"],
            "address": "123 Demo Street, Seattle, WA 98101",
            "owner": "Demo Properties LLC"
        }
        
        self.demo_user_data = {
            "user_id": "demo_user_123",
            "email": "demo@example.com",
            "name": "Demo User",
            "role": "building_admin",
            "last_login": datetime.now().isoformat()
        }
        
        self.demo_ahj_data = {
            "ahj_id": "demo_ahj_001",
            "jurisdiction": "City of Seattle",
            "inspector_id": "demo_inspector_456",
            "inspection_date": datetime.now().isoformat(),
            "findings": ["Missing fire extinguisher", "Electrical panel needs labeling"]
        }
    
    def run_comprehensive_demo(self):
        """Run comprehensive security demonstration"""
        print("🔐 Advanced Security & Compliance Demonstration")
        print("=" * 60)
        
        try:
            # 1. Privacy Controls Demo
            self.demo_privacy_controls()
            
            # 2. Encryption Demo
            self.demo_encryption()
            
            # 3. RBAC Demo
            self.demo_rbac()
            
            # 4. Audit Trail Demo
            self.demo_audit_trail()
            
            # 5. AHJ API Demo
            self.demo_ahj_api()
            
            # 6. Data Retention Demo
            self.demo_data_retention()
            
            # 7. Integrated Security Demo
            self.demo_integrated_security()
            
            # 8. Performance Metrics Demo
            self.demo_performance_metrics()
            
            print("\n✅ Advanced Security & Compliance demonstration completed successfully!")
            
        except Exception as e:
            self.logger.error(f"Demo failed: {e}")
            print(f"\n❌ Demo failed: {e}")
    
    def demo_privacy_controls(self):
        """Demonstrate privacy controls and data classification"""
        print("\n📊 1. Privacy Controls & Data Classification")
        print("-" * 40)
        
        # Test data classification
        print("🔍 Classifying different types of data:")
        
        # Building data
        building_classification = self.privacy_service.classify_data(
            "building_data", self.demo_building_data
        )
        print(f"   Building data: {building_classification.value}")
        
        # User data with sensitive content
        sensitive_user_data = "User password: secret123, SSN: 123-45-6789"
        user_classification = self.privacy_service.classify_data(
            "user_data", sensitive_user_data
        )
        print(f"   User data with sensitive content: {user_classification.value}")
        
        # AHJ data
        ahj_classification = self.privacy_service.classify_data(
            "ahj_annotations", self.demo_ahj_data
        )
        print(f"   AHJ data: {ahj_classification.value}")
        
        # Apply privacy controls
        print("\n🛡️ Applying privacy controls:")
        secured_building_data = self.privacy_service.apply_privacy_controls(
            self.demo_building_data, building_classification
        )
        print(f"   Building data secured: {secured_building_data['privacy_metadata']['encryption_required']}")
        
        # Data anonymization
        print("\n🔒 Anonymizing sensitive data:")
        anonymized_user_data = self.privacy_service.anonymize_data(
            self.demo_user_data, ["user_id", "email", "name"]
        )
        print(f"   Original user ID: {self.demo_user_data['user_id']}")
        print(f"   Anonymized user ID: {anonymized_user_data['user_id']}")
    
    def demo_encryption(self):
        """Demonstrate multi-layer encryption"""
        print("\n🔐 2. Multi-Layer Encryption")
        print("-" * 40)
        
        sensitive_data = "Highly sensitive building security information"
        
        print("🔒 Encrypting data with different layers:")
        
        # Storage encryption
        start_time = time.time()
        storage_encrypted = self.encryption_service.encrypt_data(sensitive_data, "storage")
        storage_time = (time.time() - start_time) * 1000
        print(f"   Storage encryption: {len(storage_encrypted)} bytes in {storage_time:.2f}ms")
        
        # Transport encryption
        start_time = time.time()
        transport_encrypted = self.encryption_service.encrypt_data(sensitive_data, "transport")
        transport_time = (time.time() - start_time) * 1000
        print(f"   Transport encryption: {len(transport_encrypted)} bytes in {transport_time:.2f}ms")
        
        # Database encryption
        start_time = time.time()
        database_encrypted = self.encryption_service.encrypt_data(sensitive_data, "database")
        database_time = (time.time() - start_time) * 1000
        print(f"   Database encryption: {len(database_encrypted)} bytes in {database_time:.2f}ms")
        
        # Decryption test
        print("\n🔓 Decrypting data:")
        decrypted = self.encryption_service.decrypt_data(storage_encrypted, "storage")
        print(f"   Decryption successful: {decrypted.decode() == sensitive_data}")
        
        # Key rotation
        print("\n🔄 Rotating encryption keys:")
        original_key = self.encryption_service.master_key[:10]  # First 10 bytes for display
        self.encryption_service.rotate_keys("all")
        new_key = self.encryption_service.master_key[:10]
        print(f"   Key rotated: {original_key}... → {new_key}...")
        
        # Performance metrics
        metrics = self.encryption_service.get_metrics()
        print(f"\n📈 Encryption metrics:")
        print(f"   Total operations: {metrics['total_operations']}")
        print(f"   Average time: {metrics['average_time_ms']:.2f}ms")
    
    def demo_rbac(self):
        """Demonstrate role-based access control"""
        print("\n👥 3. Role-Based Access Control (RBAC)")
        print("-" * 40)
        
        # Create custom roles
        print("🏗️ Creating custom roles:")
        
        building_admin_role = self.rbac_service.create_role(
            "Building Administrator",
            ["building:read", "building:write", "floor:read", "system:read"],
            "Full building management permissions"
        )
        print(f"   Building Admin role created: {building_admin_role}")
        
        inspector_role = self.rbac_service.create_role(
            "AHJ Inspector",
            ["inspection:read", "inspection:write", "violation:read", "violation:write"],
            "AHJ inspection permissions"
        )
        print(f"   Inspector role created: {inspector_role}")
        
        # Assign users to roles
        print("\n👤 Assigning users to roles:")
        self.rbac_service.assign_user_to_role("demo_admin", building_admin_role)
        self.rbac_service.assign_user_to_role("demo_inspector", inspector_role)
        print("   Users assigned to roles")
        
        # Test permissions
        print("\n🔍 Testing permissions:")
        
        # Building admin permissions
        can_read_building = self.rbac_service.check_permission("demo_admin", "building", "read")
        can_write_building = self.rbac_service.check_permission("demo_admin", "building", "write")
        can_read_inspection = self.rbac_service.check_permission("demo_admin", "inspection", "read")
        
        print(f"   Building admin - read building: {can_read_building}")
        print(f"   Building admin - write building: {can_write_building}")
        print(f"   Building admin - read inspection: {can_read_inspection}")
        
        # Inspector permissions
        can_read_inspection = self.rbac_service.check_permission("demo_inspector", "inspection", "read")
        can_write_inspection = self.rbac_service.check_permission("demo_inspector", "inspection", "write")
        can_write_building = self.rbac_service.check_permission("demo_inspector", "building", "write")
        
        print(f"   Inspector - read inspection: {can_read_inspection}")
        print(f"   Inspector - write inspection: {can_write_inspection}")
        print(f"   Inspector - write building: {can_write_building}")
        
        # Get user permissions
        admin_permissions = self.rbac_service.get_user_permissions("demo_admin")
        inspector_permissions = self.rbac_service.get_user_permissions("demo_inspector")
        
        print(f"\n📋 User permissions:")
        print(f"   Building admin: {len(admin_permissions)} permissions")
        print(f"   Inspector: {len(inspector_permissions)} permissions")
    
    def demo_audit_trail(self):
        """Demonstrate comprehensive audit trail"""
        print("\n📝 4. Comprehensive Audit Trail")
        print("-" * 40)
        
        # Log various events
        print("📊 Logging audit events:")
        
        # Data access events
        self.audit_service.log_event(
            AuditEventType.DATA_ACCESS,
            user_id="demo_admin",
            resource_id="building_001",
            action="read",
            details={"data_type": "building_data", "classification": "internal"}
        )
        
        self.audit_service.log_event(
            AuditEventType.DATA_MODIFICATION,
            user_id="demo_admin",
            resource_id="building_001",
            action="update",
            details={"field": "systems", "old_value": "electrical", "new_value": "electrical,security"}
        )
        
        # User authentication events
        self.audit_service.log_event(
            AuditEventType.USER_LOGIN,
            user_id="demo_inspector",
            resource_id="auth",
            action="login",
            details={"ip_address": "192.168.1.100", "user_agent": "Mozilla/5.0"}
        )
        
        self.audit_service.log_event(
            AuditEventType.USER_LOGOUT,
            user_id="demo_admin",
            resource_id="auth",
            action="logout",
            details={"session_duration": "2h 15m"}
        )
        
        # Permission changes
        self.audit_service.log_event(
            AuditEventType.PERMISSION_CHANGE,
            user_id="system_admin",
            resource_id="demo_inspector",
            action="role_assignment",
            details={"role": "AHJ Inspector", "assigned_by": "system_admin"}
        )
        
        print("   ✅ 5 audit events logged")
        
        # Retrieve and display audit logs
        print("\n📋 Retrieving audit logs:")
        all_logs = self.audit_service.get_audit_logs()
        print(f"   Total audit events: {len(all_logs)}")
        
        # Filter logs by user
        admin_logs = self.audit_service.get_audit_logs({"user_id": "demo_admin"})
        print(f"   Events by demo_admin: {len(admin_logs)}")
        
        # Generate compliance report
        print("\n📊 Generating compliance report:")
        date_range = (datetime.now() - timedelta(days=1), datetime.now() + timedelta(days=1))
        compliance_report = self.audit_service.generate_compliance_report("data_access", date_range)
        
        print(f"   Total events: {compliance_report['total_events']}")
        print(f"   Unique users: {compliance_report['unique_users']}")
        print(f"   Successful access: {compliance_report['successful_access']}")
        print(f"   Failed access: {compliance_report['failed_access']}")
    
    def demo_ahj_api(self):
        """Demonstrate AHJ API integration"""
        print("\n🏛️ 5. AHJ API Integration")
        print("-" * 40)
        
        # Get available jurisdictions
        print("🏛️ Available AHJ jurisdictions:")
        jurisdictions = self.ahj_service.get_ahj_jurisdictions()
        for jurisdiction in jurisdictions:
            print(f"   {jurisdiction['name']} ({jurisdiction['state']})")
        
        # Create inspection layer
        print("\n📋 Creating AHJ inspection layer:")
        layer_id = self.ahj_service.create_inspection_layer(
            building_id="demo_building_001",
            ahj_id="ahj_001",
            inspector_id="demo_inspector_456"
        )
        print(f"   Inspection layer created: {layer_id}")
        
        # Add inspection annotations
        print("\n📝 Adding inspection annotations:")
        
        annotation_id = self.ahj_service.add_inspection_annotation(
            layer_id=layer_id,
            inspector_id="demo_inspector_456",
            location={"floor": 1, "room": "101", "system": "fire_safety"},
            annotation_type="violation",
            description="Missing fire extinguisher in room 101",
            severity=ViolationSeverity.CRITICAL,
            code_reference="IFC 906.1",
            image_attachments=["violation_photo_001.jpg"]
        )
        print(f"   Annotation added: {annotation_id}")
        
        # Add code violation
        violation_id = self.ahj_service.add_code_violation(
            layer_id=layer_id,
            inspector_id="demo_inspector_456",
            code_section="IFC 906.1",
            description="Fire extinguisher required but not present",
            severity=ViolationSeverity.CRITICAL,
            location={"floor": 1, "room": "101"},
            required_action="Install fire extinguisher within 30 days",
            deadline=datetime.now() + timedelta(days=30)
        )
        print(f"   Code violation added: {violation_id}")
        
        # Get inspection history
        print("\n📋 Inspection history:")
        history = self.ahj_service.get_inspection_history(layer_id)
        print(f"   Building: {history['building_id']}")
        print(f"   AHJ: {history['ahj_id']}")
        print(f"   Annotations: {len(history['annotations'])}")
        print(f"   Violations: {len(history['violations'])}")
        
        # Generate compliance report
        print("\n📊 Generating compliance report:")
        compliance_report = self.ahj_service.generate_compliance_report("demo_building_001")
        print(f"   Total inspections: {compliance_report['total_inspections']}")
        print(f"   Total violations: {compliance_report['total_violations']}")
        print(f"   Compliance score: {compliance_report['compliance_score']:.1f}%")
        
        # Update violation status
        print("\n✅ Updating violation status:")
        success = self.ahj_service.update_violation_status(
            violation_id, "in_progress", "Fire extinguisher ordered"
        )
        print(f"   Violation status updated: {success}")
    
    def demo_data_retention(self):
        """Demonstrate data retention policies"""
        print("\n🗂️ 6. Data Retention Policies")
        print("-" * 40)
        
        # Create retention policies
        print("📋 Creating retention policies:")
        
        building_policy = self.retention_service.create_retention_policy(
            DataType.BUILDING_DATA,
            retention_period_days=1825,  # 5 years
            deletion_strategy=DeletionStrategy.ARCHIVE_DELETE,
            description="Building data - 5 year retention"
        )
        print(f"   Building data policy: {building_policy}")
        
        user_policy = self.retention_service.create_retention_policy(
            DataType.USER_DATA,
            retention_period_days=1095,  # 3 years
            deletion_strategy=DeletionStrategy.SOFT_DELETE,
            description="User data - 3 year retention"
        )
        print(f"   User data policy: {user_policy}")
        
        audit_policy = self.retention_service.create_retention_policy(
            DataType.AUDIT_LOGS,
            retention_period_days=3650,  # 10 years
            deletion_strategy=DeletionStrategy.SECURE_DELETE,
            description="Audit logs - 10 year retention"
        )
        print(f"   Audit logs policy: {audit_policy}")
        
        # Apply policies to data
        print("\n📝 Applying retention policies:")
        
        self.retention_service.apply_retention_policy("building_001", building_policy)
        self.retention_service.apply_retention_policy("user_123", user_policy)
        self.retention_service.apply_retention_policy("audit_session_456", audit_policy)
        print("   ✅ Policies applied to data")
        
        # Schedule data deletion
        print("\n⏰ Scheduling data deletion:")
        deletion_job = self.retention_service.schedule_data_deletion(
            "temp_data_789",
            deletion_date=datetime.now() + timedelta(days=1)
        )
        print(f"   Deletion job scheduled: {deletion_job}")
        
        # Archive data
        print("\n📦 Archiving data:")
        archive_success = self.retention_service.archive_data("old_building_data")
        print(f"   Data archived: {archive_success}")
        
        # Get data lifecycle
        print("\n📊 Data lifecycle information:")
        lifecycle = self.retention_service.get_data_lifecycle()
        print(f"   Total data items: {len(lifecycle)}")
        
        for item in lifecycle[:3]:  # Show first 3 items
            print(f"     {item['data_id']}: {item['data_type']} - {item['status']}")
        
        # Generate compliance report
        print("\n📋 Retention compliance report:")
        compliance_report = self.retention_service.generate_compliance_report()
        print(f"   Total data items: {compliance_report['total_data_items']}")
        print(f"   Active data: {compliance_report['active_data']}")
        print(f"   Archived data: {compliance_report['archived_data']}")
        print(f"   Compliance score: {compliance_report['compliance_score']:.1f}%")
        print(f"   Compliance violations: {compliance_report['compliance_violations']}")
    
    def demo_integrated_security(self):
        """Demonstrate integrated security workflow"""
        print("\n🔗 7. Integrated Security Workflow")
        print("-" * 40)
        
        print("🔄 Running complete security workflow:")
        
        # 1. Create user and assign role
        role_id = self.rbac_service.create_role(
            "Security Demo User",
            ["building:read", "inspection:read", "audit:read"]
        )
        self.rbac_service.assign_user_to_role("demo_security_user", role_id)
        print("   ✅ User created and role assigned")
        
        # 2. Secure data access
        building_data = {"floors": 3, "systems": ["electrical", "plumbing"]}
        secured_data = self.security_service.secure_data_access(
            user_id="demo_security_user",
            resource_id="building",
            action="read",
            data=building_data,
            data_type="building_data"
        )
        print("   ✅ Data access secured with privacy controls")
        
        # 3. Create AHJ inspection
        layer_id = self.ahj_service.create_inspection_layer(
            "demo_building_001", "ahj_001", "demo_security_user"
        )
        print("   ✅ AHJ inspection layer created")
        
        # 4. Apply retention policy
        policy_id = self.retention_service.create_retention_policy(
            DataType.AHJ_DATA, 3650, DeletionStrategy.ARCHIVE_DELETE
        )
        self.retention_service.apply_retention_policy(layer_id, policy_id)
        print("   ✅ Retention policy applied")
        
        # 5. Verify all components worked together
        print("\n🔍 Verifying integrated security:")
        
        # Check permissions
        has_permission = self.rbac_service.check_permission("demo_security_user", "building", "read")
        print(f"   User has building read permission: {has_permission}")
        
        # Check audit trail
        audit_logs = self.audit_service.get_audit_logs({"user_id": "demo_security_user"})
        print(f"   Audit events for user: {len(audit_logs)}")
        
        # Check AHJ inspection
        history = self.ahj_service.get_inspection_history(layer_id)
        print(f"   AHJ inspection status: {history['status']}")
        
        # Check retention policy
        lifecycle = self.retention_service.get_data_lifecycle(layer_id)
        print(f"   Data retention status: {lifecycle[0]['status'] if lifecycle else 'Not found'}")
        
        print("   ✅ All security components integrated successfully")
    
    def demo_performance_metrics(self):
        """Demonstrate security performance metrics"""
        print("\n📈 8. Security Performance Metrics")
        print("-" * 40)
        
        # Get metrics from all services
        print("📊 Collecting performance metrics:")
        
        # Encryption metrics
        encryption_metrics = self.encryption_service.get_metrics()
        print(f"   Encryption operations: {encryption_metrics['total_operations']}")
        print(f"   Average encryption time: {encryption_metrics['average_time_ms']:.2f}ms")
        
        # Audit trail metrics
        audit_metrics = self.audit_service.get_metrics()
        print(f"   Audit events logged: {audit_metrics['total_events']}")
        print(f"   Average audit time: {audit_metrics['average_logging_time_ms']:.2f}ms")
        
        # RBAC metrics
        rbac_metrics = self.rbac_service.get_metrics()
        print(f"   Permission checks: {rbac_metrics['total_permission_checks']}")
        print(f"   Average check time: {rbac_metrics['average_check_time_ms']:.2f}ms")
        
        # AHJ metrics
        ahj_metrics = self.ahj_service.get_metrics()
        print(f"   AHJ inspections: {ahj_metrics['total_inspections']}")
        print(f"   AHJ annotations: {ahj_metrics['total_annotations']}")
        print(f"   AHJ violations: {ahj_metrics['total_violations']}")
        
        # Retention metrics
        retention_metrics = self.retention_service.get_metrics()
        print(f"   Retention policies: {retention_metrics['total_policies']}")
        print(f"   Data items: {retention_metrics['total_data_items']}")
        print(f"   Data deletions: {retention_metrics['total_deletions']}")
        
        # Overall security metrics
        security_metrics = self.security_service.get_security_metrics()
        print(f"\n🔐 Overall security metrics:")
        print(f"   Total operations: {security_metrics['overall']['total_operations']}")
        print(f"   Average operation time: {security_metrics['overall']['average_operation_time_ms']:.2f}ms")
        
        print("\n✅ Performance metrics collected successfully")


def main():
    """Run the advanced security demonstration"""
    demo = AdvancedSecurityDemo()
    demo.run_comprehensive_demo()


if __name__ == "__main__":
    main() 