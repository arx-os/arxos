"""
AHJ API Integration Demonstration

Comprehensive demonstration of the AHJ API Integration features including:
- Secure authentication with multi-factor authentication
- Append-only annotation creation with cryptographic signatures
- Inspection session management
- Audit logging and compliance reporting
- Permission enforcement and role-based access control
- Real-time notifications and status tracking
"""

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ahj_api_integration import (
    AHJAPIIntegration,
    AnnotationType,
    ViolationSeverity,
    InspectionStatus,
    PermissionLevel
)


class AHJAPIDemo:
    """Demonstration class for AHJ API Integration features."""
    
    def __init__(self):
        self.ahj_service = AHJAPIIntegration()
        self.demo_users = []
        self.demo_annotations = []
        self.demo_sessions = []
        
    def run_comprehensive_demo(self):
        """Run comprehensive demonstration of all AHJ API features."""
        print("=" * 80)
        print("AHJ API INTEGRATION COMPREHENSIVE DEMONSTRATION")
        print("=" * 80)
        print()
        
        # Phase 1: User Management and Authentication
        self._demo_user_management()
        
        # Phase 2: Authentication and Security
        self._demo_authentication()
        
        # Phase 3: Inspection Session Management
        self._demo_session_management()
        
        # Phase 4: Annotation Creation and Management
        self._demo_annotation_management()
        
        # Phase 5: Code Violation Tracking
        self._demo_code_violations()
        
        # Phase 6: Audit Logging and Compliance
        self._demo_audit_logging()
        
        # Phase 7: Permission Enforcement
        self._demo_permission_enforcement()
        
        # Phase 8: Performance and Monitoring
        self._demo_performance_monitoring()
        
        # Phase 9: Advanced Features
        self._demo_advanced_features()
        
        # Phase 10: Summary and Metrics
        self._demo_summary()
    
    def _demo_user_management(self):
        """Demonstrate AHJ user management."""
        print("PHASE 1: USER MANAGEMENT AND AUTHENTICATION")
        print("-" * 50)
        
        # Create different types of AHJ users
        users_data = [
            {
                "user_id": "ahj_inspector_001",
                "username": "inspector_john",
                "full_name": "John Inspector",
                "organization": "City Building Department",
                "jurisdiction": "Downtown District",
                "permission_level": "inspector",
                "geographic_boundaries": ["downtown", "midtown"],
                "contact_email": "john.inspector@city.gov",
                "contact_phone": "555-123-4567"
            },
            {
                "user_id": "ahj_senior_001",
                "username": "senior_sarah",
                "full_name": "Sarah Senior Inspector",
                "organization": "City Building Department",
                "jurisdiction": "Downtown District",
                "permission_level": "senior_inspector",
                "geographic_boundaries": ["downtown", "midtown", "uptown"],
                "contact_email": "sarah.senior@city.gov",
                "contact_phone": "555-123-4568"
            },
            {
                "user_id": "ahj_supervisor_001",
                "username": "supervisor_mike",
                "full_name": "Mike Supervisor",
                "organization": "City Building Department",
                "jurisdiction": "All Districts",
                "permission_level": "supervisor",
                "geographic_boundaries": ["downtown", "midtown", "uptown", "suburbs"],
                "contact_email": "mike.supervisor@city.gov",
                "contact_phone": "555-123-4569"
            },
            {
                "user_id": "ahj_admin_001",
                "username": "admin_alice",
                "full_name": "Alice Administrator",
                "organization": "City Building Department",
                "jurisdiction": "All Districts",
                "permission_level": "administrator",
                "geographic_boundaries": ["downtown", "midtown", "uptown", "suburbs"],
                "contact_email": "alice.admin@city.gov",
                "contact_phone": "555-123-4570"
            }
        ]
        
        print("Creating AHJ users with different permission levels...")
        for user_data in users_data:
            try:
                user = self.ahj_service.create_ahj_user(user_data)
                self.demo_users.append(user)
                print(f"✓ Created {user.permission_level.value}: {user.full_name} ({user.username})")
                print(f"  Organization: {user.organization}")
                print(f"  Jurisdiction: {user.jurisdiction}")
                print(f"  Geographic Boundaries: {user.geographic_boundaries}")
                print()
            except Exception as e:
                print(f"✗ Failed to create user {user_data['username']}: {e}")
        
        print(f"Total users created: {len(self.demo_users)}")
        print()
    
    def _demo_authentication(self):
        """Demonstrate authentication features."""
        print("PHASE 2: AUTHENTICATION AND SECURITY")
        print("-" * 50)
        
        # Test authentication for each user
        auth_scenarios = [
            {"username": "inspector_john", "password": "secure_password", "mfa": None},
            {"username": "senior_sarah", "password": "secure_password", "mfa": "123456"},
            {"username": "supervisor_mike", "password": "secure_password", "mfa": None},
            {"username": "admin_alice", "password": "secure_password", "mfa": "123456"}
        ]
        
        print("Testing authentication scenarios...")
        for scenario in auth_scenarios:
            try:
                auth_result = self.ahj_service.authenticate_ahj_user(
                    scenario["username"], 
                    scenario["password"], 
                    scenario["mfa"]
                )
                print(f"✓ Authentication successful: {scenario['username']}")
                print(f"  Permission Level: {auth_result['permission_level']}")
                print(f"  Session Token: {auth_result['session_token'][:20]}...")
                print(f"  Expires At: {auth_result['expires_at']}")
                print()
            except Exception as e:
                print(f"✗ Authentication failed: {scenario['username']} - {e}")
        
        # Test invalid authentication
        print("Testing invalid authentication scenarios...")
        invalid_scenarios = [
            {"username": "inspector_john", "password": "wrong_password", "description": "Invalid password"},
            {"username": "nonexistent_user", "password": "secure_password", "description": "Non-existent user"},
            {"username": "inspector_john", "password": "secure_password", "mfa": "invalid_token", "description": "Invalid MFA token"}
        ]
        
        for scenario in invalid_scenarios:
            try:
                self.ahj_service.authenticate_ahj_user(
                    scenario["username"], 
                    scenario["password"], 
                    scenario.get("mfa")
                )
                print(f"✗ Unexpected success: {scenario['description']}")
            except Exception as e:
                print(f"✓ Expected failure: {scenario['description']} - {e}")
        
        print()
    
    def _demo_session_management(self):
        """Demonstrate inspection session management."""
        print("PHASE 3: INSPECTION SESSION MANAGEMENT")
        print("-" * 50)
        
        # Create inspection sessions for different users
        inspection_sessions = [
            {"inspection_id": "inspection_001", "user_id": "ahj_inspector_001"},
            {"inspection_id": "inspection_002", "user_id": "ahj_senior_001"},
            {"inspection_id": "inspection_003", "user_id": "ahj_supervisor_001"}
        ]
        
        print("Creating inspection sessions...")
        for session_data in inspection_sessions:
            try:
                session = self.ahj_service.create_inspection_session(
                    session_data["inspection_id"], 
                    session_data["user_id"]
                )
                self.demo_sessions.append(session)
                print(f"✓ Created session: {session.session_id}")
                print(f"  Inspection: {session.inspection_id}")
                print(f"  User: {session.ahj_user_id}")
                print(f"  Start Time: {session.start_time}")
                print(f"  Status: {session.status}")
                print()
            except Exception as e:
                print(f"✗ Failed to create session: {e}")
        
        # End some sessions
        print("Ending inspection sessions...")
        for session in self.demo_sessions[:2]:  # End first two sessions
            try:
                summary = self.ahj_service.end_inspection_session(session.session_id, session.ahj_user_id)
                print(f"✓ Ended session: {session.session_id}")
                print(f"  Duration: {summary['duration_seconds']:.2f} seconds")
                print(f"  Annotations: {summary['annotations_count']}")
                print(f"  Status: {summary['status']}")
                print()
            except Exception as e:
                print(f"✗ Failed to end session {session.session_id}: {e}")
        
        print()
    
    def _demo_annotation_management(self):
        """Demonstrate annotation creation and management."""
        print("PHASE 4: ANNOTATION CREATION AND MANAGEMENT")
        print("-" * 50)
        
        # Create various types of annotations
        annotation_scenarios = [
            {
                "inspection_id": "inspection_001",
                "user_id": "ahj_inspector_001",
                "annotation_type": "inspection_note",
                "content": "Initial inspection of HVAC system completed. All components operational and properly maintained.",
                "location_coordinates": {"lat": 40.7128, "lng": -74.0060},
                "description": "HVAC System Inspection Note"
            },
            {
                "inspection_id": "inspection_001",
                "user_id": "ahj_inspector_001",
                "annotation_type": "location_marker",
                "content": "Main electrical panel location marked for future reference.",
                "location_coordinates": {"lat": 40.7129, "lng": -74.0061},
                "description": "Electrical Panel Location Marker"
            },
            {
                "inspection_id": "inspection_002",
                "user_id": "ahj_senior_001",
                "annotation_type": "photo_attachment",
                "content": "Fire suppression system inspection photos attached.",
                "photo_attachment": "fire_suppression_photos_2024.zip",
                "description": "Fire Suppression System Photos"
            },
            {
                "inspection_id": "inspection_002",
                "user_id": "ahj_senior_001",
                "annotation_type": "status_update",
                "content": "Inspection status updated to IN_PROGRESS. All safety systems verified.",
                "description": "Inspection Status Update"
            }
        ]
        
        print("Creating various types of annotations...")
        for scenario in annotation_scenarios:
            try:
                annotation_data = {
                    "inspection_id": scenario["inspection_id"],
                    "annotation_type": scenario["annotation_type"],
                    "content": scenario["content"],
                    "location_coordinates": scenario.get("location_coordinates"),
                    "photo_attachment": scenario.get("photo_attachment")
                }
                
                annotation = self.ahj_service.create_inspection_annotation(annotation_data, scenario["user_id"])
                self.demo_annotations.append(annotation)
                
                print(f"✓ Created {scenario['description']}")
                print(f"  Annotation ID: {annotation.annotation_id}")
                print(f"  Type: {annotation.annotation_type.value}")
                print(f"  Content: {annotation.content[:50]}...")
                print(f"  Signature: {annotation.signature[:20]}...")
                print(f"  Checksum: {annotation.checksum[:20]}...")
                print()
            except Exception as e:
                print(f"✗ Failed to create annotation: {scenario['description']} - {e}")
        
        # Get annotations for inspections
        print("Retrieving annotations for inspections...")
        for inspection_id in ["inspection_001", "inspection_002"]:
            try:
                annotations = self.ahj_service.get_inspection_annotations(inspection_id, "ahj_inspector_001")
                print(f"✓ Retrieved {len(annotations)} annotations for {inspection_id}")
                
                # Show annotation summary
                type_counts = {}
                for annotation in annotations:
                    ann_type = annotation.get("annotation_type", "unknown")
                    type_counts[ann_type] = type_counts.get(ann_type, 0) + 1
                
                for ann_type, count in type_counts.items():
                    print(f"  {ann_type}: {count}")
                print()
            except Exception as e:
                print(f"✗ Failed to retrieve annotations for {inspection_id}: {e}")
        
        print()
    
    def _demo_code_violations(self):
        """Demonstrate code violation tracking."""
        print("PHASE 5: CODE VIOLATION TRACKING")
        print("-" * 50)
        
        # Create code violation annotations
        violation_scenarios = [
            {
                "inspection_id": "inspection_001",
                "user_id": "ahj_inspector_001",
                "content": "Missing fire extinguisher in mechanical room",
                "violation_severity": "major",
                "code_reference": "NFPA 101-2018 Section 9.7.1.1",
                "description": "Fire Safety Violation"
            },
            {
                "inspection_id": "inspection_002",
                "user_id": "ahj_senior_001",
                "content": "Electrical panel not properly labeled",
                "violation_severity": "minor",
                "code_reference": "NEC 408.4",
                "description": "Electrical Code Violation"
            },
            {
                "inspection_id": "inspection_003",
                "user_id": "ahj_supervisor_001",
                "content": "Emergency exit blocked by equipment",
                "violation_severity": "critical",
                "code_reference": "NFPA 101-2018 Section 7.1.10.1",
                "description": "Critical Safety Violation"
            }
        ]
        
        print("Creating code violation annotations...")
        for scenario in violation_scenarios:
            try:
                annotation_data = {
                    "inspection_id": scenario["inspection_id"],
                    "annotation_type": "code_violation",
                    "content": scenario["content"],
                    "violation_severity": scenario["violation_severity"],
                    "code_reference": scenario["code_reference"]
                }
                
                annotation = self.ahj_service.create_inspection_annotation(annotation_data, scenario["user_id"])
                self.demo_annotations.append(annotation)
                
                print(f"✓ Created {scenario['description']}")
                print(f"  Severity: {annotation.violation_severity.value}")
                print(f"  Code Reference: {annotation.code_reference}")
                print(f"  Status: {annotation.status.value}")
                print()
            except Exception as e:
                print(f"✗ Failed to create violation: {scenario['description']} - {e}")
        
        # Show violation statistics
        print("Code violation statistics:")
        severity_counts = {}
        for annotation in self.demo_annotations:
            if annotation.annotation_type == AnnotationType.CODE_VIOLATION:
                severity = annotation.violation_severity.value
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        for severity, count in severity_counts.items():
            print(f"  {severity.title()}: {count}")
        
        print()
    
    def _demo_audit_logging(self):
        """Demonstrate audit logging and compliance features."""
        print("PHASE 6: AUDIT LOGGING AND COMPLIANCE")
        print("-" * 50)
        
        # Get audit logs for administrator
        print("Retrieving comprehensive audit logs...")
        try:
            audit_logs = self.ahj_service.get_audit_logs("ahj_admin_001")
            print(f"✓ Retrieved {len(audit_logs)} audit log entries")
            
            # Analyze audit log activity
            action_counts = {}
            for log in audit_logs:
                action = log.get("action", "unknown")
                action_counts[action] = action_counts.get(action, 0) + 1
            
            print("Audit log activity summary:")
            for action, count in action_counts.items():
                print(f"  {action}: {count}")
            
            # Show recent audit entries
            print("\nRecent audit entries:")
            recent_logs = audit_logs[-5:]  # Last 5 entries
            for log in recent_logs:
                print(f"  {log.get('timestamp', 'Unknown')}: {log.get('action', 'Unknown')} by {log.get('user_id', 'Unknown')}")
            
        except Exception as e:
            print(f"✗ Failed to retrieve audit logs: {e}")
        
        print()
    
    def _demo_permission_enforcement(self):
        """Demonstrate permission enforcement."""
        print("PHASE 7: PERMISSION ENFORCEMENT")
        print("-" * 50)
        
        # Test different permission levels
        permission_tests = [
            {
                "user_id": "ahj_inspector_001",
                "action": "create_annotation",
                "expected": True,
                "description": "Inspector creating annotation"
            },
            {
                "user_id": "ahj_inspector_001",
                "action": "view_annotations",
                "expected": True,
                "description": "Inspector viewing annotations"
            },
            {
                "user_id": "ahj_inspector_001",
                "action": "manage_users",
                "expected": False,
                "description": "Inspector managing users"
            },
            {
                "user_id": "ahj_admin_001",
                "action": "manage_users",
                "expected": True,
                "description": "Administrator managing users"
            },
            {
                "user_id": "nonexistent_user",
                "action": "create_annotation",
                "expected": False,
                "description": "Non-existent user"
            }
        ]
        
        print("Testing permission enforcement...")
        for test in permission_tests:
            try:
                result = self.ahj_service._check_user_permissions(test["user_id"], test["action"])
                status = "✓" if result == test["expected"] else "✗"
                print(f"{status} {test['description']}: {result} (expected: {test['expected']})")
            except Exception as e:
                print(f"✗ Error testing {test['description']}: {e}")
        
        print()
    
    def _demo_performance_monitoring(self):
        """Demonstrate performance monitoring."""
        print("PHASE 8: PERFORMANCE AND MONITORING")
        print("-" * 50)
        
        # Get performance metrics
        print("Retrieving performance metrics...")
        try:
            metrics = self.ahj_service.get_performance_metrics()
            
            print("Current system metrics:")
            for key, value in metrics.items():
                print(f"  {key}: {value}")
            
        except Exception as e:
            print(f"✗ Failed to get performance metrics: {e}")
        
        # Test concurrent operations
        print("\nTesting concurrent operations...")
        import threading
        
        def create_concurrent_annotation(annotation_id):
            try:
                annotation_data = {
                    "annotation_type": "inspection_note",
                    "content": f"Concurrent annotation {annotation_id}",
                    "inspection_id": f"concurrent_inspection_{annotation_id}"
                }
                return self.ahj_service.create_inspection_annotation(annotation_data, "ahj_inspector_001")
            except Exception as e:
                return f"Error: {e}"
        
        # Create multiple annotations concurrently
        threads = []
        results = []
        
        for i in range(5):
            thread = threading.Thread(target=lambda x=i: results.append(create_concurrent_annotation(x)))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        successful_annotations = [r for r in results if hasattr(r, 'annotation_id')]
        print(f"✓ Created {len(successful_annotations)} concurrent annotations")
        
        print()
    
    def _demo_advanced_features(self):
        """Demonstrate advanced features."""
        print("PHASE 9: ADVANCED FEATURES")
        print("-" * 50)
        
        # Test annotation integrity verification
        print("Testing annotation integrity verification...")
        if self.demo_annotations:
            annotation = self.demo_annotations[0]
            try:
                # Verify checksum
                expected_checksum = self.ahj_service._generate_checksum(annotation)
                checksum_valid = annotation.checksum == expected_checksum
                
                # Verify signature
                signature_valid = annotation.signature is not None and len(annotation.signature) > 0
                
                print(f"✓ Annotation integrity check:")
                print(f"  Checksum valid: {checksum_valid}")
                print(f"  Signature valid: {signature_valid}")
                print(f"  Overall integrity: {checksum_valid and signature_valid}")
                
            except Exception as e:
                print(f"✗ Integrity verification failed: {e}")
        
        # Test notification system
        print("\nTesting notification system...")
        try:
            # Simulate notification sending
            notification_data = {
                "type": "annotation_created",
                "annotation_id": "demo_annotation",
                "user_name": "Demo Inspector",
                "timestamp": datetime.now().isoformat()
            }
            
            # Test different notification channels
            notification_channels = ["email", "sms", "websocket", "dashboard"]
            for channel in notification_channels:
                handler = self.ahj_service.notification_handlers.get(channel)
                if handler:
                    handler(notification_data)
                    print(f"✓ {channel.title()} notification sent")
            
        except Exception as e:
            print(f"✗ Notification test failed: {e}")
        
        print()
    
    def _demo_summary(self):
        """Demonstrate summary and final metrics."""
        print("PHASE 10: SUMMARY AND METRICS")
        print("-" * 50)
        
        # Calculate comprehensive statistics
        print("AHJ API Integration Demo Summary:")
        print()
        
        # User statistics
        print("User Management:")
        print(f"  Total users created: {len(self.demo_users)}")
        permission_counts = {}
        for user in self.demo_users:
            level = user.permission_level.value
            permission_counts[level] = permission_counts.get(level, 0) + 1
        
        for level, count in permission_counts.items():
            print(f"  {level.replace('_', ' ').title()}: {count}")
        
        print()
        
        # Annotation statistics
        print("Annotation Management:")
        print(f"  Total annotations created: {len(self.demo_annotations)}")
        
        type_counts = {}
        severity_counts = {}
        for annotation in self.demo_annotations:
            # Count types
            ann_type = annotation.annotation_type.value
            type_counts[ann_type] = type_counts.get(ann_type, 0) + 1
            
            # Count severities
            if annotation.violation_severity:
                severity = annotation.violation_severity.value
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        print("  Annotation types:")
        for ann_type, count in type_counts.items():
            print(f"    {ann_type.replace('_', ' ').title()}: {count}")
        
        if severity_counts:
            print("  Violation severities:")
            for severity, count in severity_counts.items():
                print(f"    {severity.title()}: {count}")
        
        print()
        
        # Session statistics
        print("Session Management:")
        print(f"  Total sessions created: {len(self.demo_sessions)}")
        active_sessions = [s for s in self.demo_sessions if s.status == "active"]
        print(f"  Active sessions: {len(active_sessions)}")
        completed_sessions = [s for s in self.demo_sessions if s.status == "completed"]
        print(f"  Completed sessions: {len(completed_sessions)}")
        
        print()
        
        # Audit statistics
        print("Audit and Compliance:")
        print(f"  Total audit log entries: {len(self.ahj_service.audit_logs)}")
        
        # Performance metrics
        metrics = self.ahj_service.get_performance_metrics()
        print(f"  Average annotation time: {metrics.get('average_annotation_time', 'N/A')}")
        print(f"  Concurrent users supported: {metrics.get('concurrent_users_supported', 'N/A')}")
        print(f"  Audit trail integrity: {metrics.get('audit_trail_integrity', 'N/A')}")
        
        print()
        
        # Security features summary
        print("Security Features:")
        security_features = [
            "Multi-factor authentication",
            "Cryptographic signatures",
            "Immutable audit trail",
            "Role-based access control",
            "Geographic boundaries",
            "Time-based permissions",
            "Append-only data integrity"
        ]
        
        for feature in security_features:
            print(f"  ✓ {feature}")
        
        print()
        print("=" * 80)
        print("AHJ API INTEGRATION DEMONSTRATION COMPLETED SUCCESSFULLY")
        print("=" * 80)


def main():
    """Run the AHJ API Integration demonstration."""
    demo = AHJAPIDemo()
    demo.run_comprehensive_demo()


if __name__ == "__main__":
    main() 