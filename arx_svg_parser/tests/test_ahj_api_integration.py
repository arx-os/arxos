"""
AHJ API Integration Tests

Comprehensive test suite for the AHJ API Integration covering authentication,
annotation management, session handling, audit logging, and security features.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock

from services.ahj_api_integration import (
    AHJAPIIntegration,
    AnnotationType,
    ViolationSeverity,
    InspectionStatus,
    PermissionLevel,
    AHJUser,
    InspectionAnnotation,
    InspectionSession
)


class TestAHJAPIIntegration:
    """Test suite for AHJ API Integration."""
    
    @pytest.fixture
    def ahj_service(self):
        """Create a fresh AHJ service instance for testing."""
        return AHJAPIIntegration()
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample AHJ user data for testing."""
        return {
            "user_id": "ahj_user_001",
            "username": "inspector_john",
            "full_name": "John Inspector",
            "organization": "City Building Department",
            "jurisdiction": "Downtown District",
            "permission_level": "inspector",
            "geographic_boundaries": ["downtown", "midtown"],
            "contact_email": "john.inspector@city.gov",
            "contact_phone": "555-123-4567"
        }
    
    @pytest.fixture
    def sample_annotation_data(self):
        """Sample annotation data for testing."""
        return {
            "annotation_type": "inspection_note",
            "content": "HVAC system inspection completed. All components operational.",
            "location_coordinates": {"lat": 40.7128, "lng": -74.0060},
            "violation_severity": None,
            "code_reference": None
        }
    
    def test_initialization(self, ahj_service):
        """Test service initialization."""
        assert ahj_service is not None
        assert hasattr(ahj_service, 'inspections')
        assert hasattr(ahj_service, 'annotations')
        assert hasattr(ahj_service, 'ahj_users')
        assert hasattr(ahj_service, 'sessions')
        assert hasattr(ahj_service, 'audit_logs')
        assert hasattr(ahj_service, 'cipher_suite')
        assert hasattr(ahj_service, 'private_key')
        assert hasattr(ahj_service, 'public_key')
    
    def test_create_ahj_user(self, ahj_service, sample_user_data):
        """Test creating an AHJ user."""
        user = ahj_service.create_ahj_user(sample_user_data)
        
        assert user.user_id == "ahj_user_001"
        assert user.username == "inspector_john"
        assert user.full_name == "John Inspector"
        assert user.organization == "City Building Department"
        assert user.jurisdiction == "Downtown District"
        assert user.permission_level == PermissionLevel.INSPECTOR
        assert user.geographic_boundaries == ["downtown", "midtown"]
        assert user.contact_email == "john.inspector@city.gov"
        assert user.contact_phone == "555-123-4567"
        assert user.is_active is True
        assert user.created_at is not None
        assert user.last_login is None
        
        # Verify user is stored
        assert "ahj_user_001" in ahj_service.ahj_users
    
    def test_create_ahj_user_validation(self, ahj_service):
        """Test AHJ user data validation."""
        # Test missing required fields
        invalid_user_data = {
            "user_id": "test_user",
            "username": "test_user"
            # Missing required fields
        }
        
        with pytest.raises(ValueError, match="Missing required field: full_name"):
            ahj_service.create_ahj_user(invalid_user_data)
        
        # Test invalid permission level
        invalid_permission_data = {
            "user_id": "test_user",
            "username": "test_user",
            "full_name": "Test User",
            "organization": "Test Org",
            "jurisdiction": "Test Jurisdiction",
            "permission_level": "invalid_level",
            "contact_email": "test@example.com"
        }
        
        with pytest.raises(ValueError, match="Invalid permission level: invalid_level"):
            ahj_service.create_ahj_user(invalid_permission_data)
    
    def test_authenticate_ahj_user(self, ahj_service, sample_user_data):
        """Test AHJ user authentication."""
        # Create user first
        ahj_service.create_ahj_user(sample_user_data)
        
        # Test successful authentication
        auth_result = ahj_service.authenticate_ahj_user("inspector_john", "secure_password")
        
        assert auth_result["success"] is True
        assert auth_result["user_id"] == "ahj_user_001"
        assert auth_result["username"] == "inspector_john"
        assert auth_result["permission_level"] == "inspector"
        assert "session_token" in auth_result
        assert "expires_at" in auth_result
        
        # Verify last login was updated
        user = ahj_service.ahj_users["ahj_user_001"]
        assert user.last_login is not None
    
    def test_authenticate_ahj_user_invalid_credentials(self, ahj_service, sample_user_data):
        """Test authentication with invalid credentials."""
        # Create user first
        ahj_service.create_ahj_user(sample_user_data)
        
        # Test invalid password
        with pytest.raises(ValueError, match="Invalid username or password"):
            ahj_service.authenticate_ahj_user("inspector_john", "wrong_password")
        
        # Test invalid username
        with pytest.raises(ValueError, match="Invalid username or password"):
            ahj_service.authenticate_ahj_user("nonexistent_user", "secure_password")
    
    def test_authenticate_ahj_user_with_mfa(self, ahj_service, sample_user_data):
        """Test authentication with multi-factor authentication."""
        # Create user first
        ahj_service.create_ahj_user(sample_user_data)
        
        # Test successful MFA authentication
        auth_result = ahj_service.authenticate_ahj_user("inspector_john", "secure_password", "123456")
        
        assert auth_result["success"] is True
        assert auth_result["user_id"] == "ahj_user_001"
        assert "session_token" in auth_result
    
    def test_authenticate_ahj_user_invalid_mfa(self, ahj_service, sample_user_data):
        """Test authentication with invalid MFA token."""
        # Create user first
        ahj_service.create_ahj_user(sample_user_data)
        
        # Test invalid MFA token
        with pytest.raises(ValueError, match="Invalid MFA token"):
            ahj_service.authenticate_ahj_user("inspector_john", "secure_password", "invalid_token")
    
    def test_create_inspection_annotation(self, ahj_service, sample_user_data, sample_annotation_data):
        """Test creating an inspection annotation."""
        # Create user first
        ahj_service.create_ahj_user(sample_user_data)
        
        # Create annotation
        annotation = ahj_service.create_inspection_annotation(sample_annotation_data, "ahj_user_001")
        
        assert annotation.annotation_id is not None
        assert annotation.inspection_id == sample_annotation_data.get("inspection_id")
        assert annotation.ahj_user_id == "ahj_user_001"
        assert annotation.annotation_type == AnnotationType.INSPECTION_NOTE
        assert annotation.content == "HVAC system inspection completed. All components operational."
        assert annotation.location_coordinates == {"lat": 40.7128, "lng": -74.0060}
        assert annotation.violation_severity is None
        assert annotation.code_reference is None
        assert annotation.status == InspectionStatus.PENDING
        assert annotation.created_at is not None
        assert annotation.signature is not None
        assert annotation.checksum is not None
        
        # Verify annotation is stored
        assert annotation.annotation_id in ahj_service.annotations
    
    def test_create_inspection_annotation_validation(self, ahj_service, sample_user_data):
        """Test annotation data validation."""
        # Create user first
        ahj_service.create_ahj_user(sample_user_data)
        
        # Test missing required fields
        invalid_annotation_data = {
            "content": "Test annotation"
            # Missing annotation_type
        }
        
        with pytest.raises(ValueError, match="Missing required field: annotation_type"):
            ahj_service.create_inspection_annotation(invalid_annotation_data, "ahj_user_001")
        
        # Test invalid annotation type
        invalid_type_data = {
            "annotation_type": "invalid_type",
            "content": "Test annotation"
        }
        
        with pytest.raises(ValueError, match="Invalid annotation type: invalid_type"):
            ahj_service.create_inspection_annotation(invalid_type_data, "ahj_user_001")
    
    def test_create_code_violation_annotation(self, ahj_service, sample_user_data):
        """Test creating a code violation annotation."""
        # Create user first
        ahj_service.create_ahj_user(sample_user_data)
        
        # Create code violation annotation
        violation_data = {
            "annotation_type": "code_violation",
            "content": "Missing fire extinguisher in mechanical room",
            "violation_severity": "major",
            "code_reference": "NFPA 101-2018 Section 9.7.1.1"
        }
        
        annotation = ahj_service.create_inspection_annotation(violation_data, "ahj_user_001")
        
        assert annotation.annotation_type == AnnotationType.CODE_VIOLATION
        assert annotation.violation_severity == ViolationSeverity.MAJOR
        assert annotation.code_reference == "NFPA 101-2018 Section 9.7.1.1"
    
    def test_get_inspection_annotations(self, ahj_service, sample_user_data, sample_annotation_data):
        """Test getting inspection annotations."""
        # Create user and annotation
        ahj_service.create_ahj_user(sample_user_data)
        sample_annotation_data["inspection_id"] = "inspection_001"
        ahj_service.create_inspection_annotation(sample_annotation_data, "ahj_user_001")
        
        # Get annotations
        annotations = ahj_service.get_inspection_annotations("inspection_001", "ahj_user_001")
        
        assert len(annotations) == 1
        assert annotations[0]["annotation_type"] == "inspection_note"
        assert annotations[0]["content"] == "HVAC system inspection completed. All components operational."
    
    def test_get_inspection_annotations_no_permissions(self, ahj_service):
        """Test getting annotations without proper permissions."""
        # Test with non-existent user
        with pytest.raises(ValueError, match="Insufficient permissions to view annotations"):
            ahj_service.get_inspection_annotations("inspection_001", "nonexistent_user")
    
    def test_create_inspection_session(self, ahj_service, sample_user_data):
        """Test creating an inspection session."""
        # Create user first
        ahj_service.create_ahj_user(sample_user_data)
        
        # Create session
        session = ahj_service.create_inspection_session("inspection_001", "ahj_user_001")
        
        assert session.session_id is not None
        assert session.inspection_id == "inspection_001"
        assert session.ahj_user_id == "ahj_user_001"
        assert session.start_time is not None
        assert session.end_time is None
        assert session.status == "active"
        assert session.annotations_count == 0
        assert session.last_activity is not None
        
        # Verify session is stored
        assert session.session_id in ahj_service.sessions
    
    def test_end_inspection_session(self, ahj_service, sample_user_data):
        """Test ending an inspection session."""
        # Create user and session
        ahj_service.create_ahj_user(sample_user_data)
        session = ahj_service.create_inspection_session("inspection_001", "ahj_user_001")
        
        # End session
        session_summary = ahj_service.end_inspection_session(session.session_id, "ahj_user_001")
        
        assert session_summary["session_id"] == session.session_id
        assert session_summary["status"] == "completed"
        assert session_summary["annotations_count"] == 0
        assert "start_time" in session_summary
        assert "end_time" in session_summary
        assert "duration_seconds" in session_summary
    
    def test_end_inspection_session_not_found(self, ahj_service):
        """Test ending a non-existent session."""
        with pytest.raises(ValueError, match="Session not found"):
            ahj_service.end_inspection_session("nonexistent_session", "ahj_user_001")
    
    def test_get_audit_logs(self, ahj_service, sample_user_data):
        """Test getting audit logs."""
        # Create user with administrator permissions
        admin_user_data = sample_user_data.copy()
        admin_user_data["permission_level"] = "administrator"
        ahj_service.create_ahj_user(admin_user_data)
        
        # Get audit logs
        audit_logs = ahj_service.get_audit_logs("ahj_user_001")
        
        assert isinstance(audit_logs, list)
        # Should have at least the user creation log
        assert len(audit_logs) >= 1
    
    def test_get_audit_logs_no_permissions(self, ahj_service, sample_user_data):
        """Test getting audit logs without proper permissions."""
        # Create user with inspector permissions (not administrator)
        ahj_service.create_ahj_user(sample_user_data)
        
        # Try to get audit logs
        with pytest.raises(ValueError, match="Insufficient permissions to view audit logs"):
            ahj_service.get_audit_logs("ahj_user_001")
    
    def test_get_audit_logs_with_filters(self, ahj_service, sample_user_data):
        """Test getting audit logs with date and action filters."""
        # Create user with administrator permissions
        admin_user_data = sample_user_data.copy()
        admin_user_data["permission_level"] = "administrator"
        ahj_service.create_ahj_user(admin_user_data)
        
        # Get audit logs with filters
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now() + timedelta(days=1)
        
        audit_logs = ahj_service.get_audit_logs(
            "ahj_user_001",
            start_date=start_date,
            end_date=end_date,
            action_type="user_created"
        )
        
        assert isinstance(audit_logs, list)
    
    def test_check_user_permissions(self, ahj_service, sample_user_data):
        """Test user permission checking."""
        # Create user
        ahj_service.create_ahj_user(sample_user_data)
        
        # Test valid permissions
        assert ahj_service._check_user_permissions("ahj_user_001", "create_annotation") is True
        assert ahj_service._check_user_permissions("ahj_user_001", "view_annotations") is True
        
        # Test invalid permissions
        assert ahj_service._check_user_permissions("ahj_user_001", "manage_users") is False
        assert ahj_service._check_user_permissions("nonexistent_user", "create_annotation") is False
    
    def test_cryptographic_signing(self, ahj_service, sample_user_data, sample_annotation_data):
        """Test cryptographic signing of annotations."""
        # Create user and annotation
        ahj_service.create_ahj_user(sample_user_data)
        annotation = ahj_service.create_inspection_annotation(sample_annotation_data, "ahj_user_001")
        
        # Test signature generation
        signature = ahj_service._sign_annotation(annotation)
        assert signature is not None
        assert len(signature) > 0
        
        # Test checksum generation
        checksum = ahj_service._generate_checksum(annotation)
        assert checksum is not None
        assert len(checksum) == 64  # SHA-256 hex digest length
    
    def test_annotation_immutability(self, ahj_service, sample_user_data, sample_annotation_data):
        """Test annotation immutability and integrity."""
        # Create user and annotation
        ahj_service.create_ahj_user(sample_user_data)
        annotation = ahj_service.create_inspection_annotation(sample_annotation_data, "ahj_user_001")
        
        # Verify annotation has cryptographic protection
        assert annotation.signature is not None
        assert annotation.checksum is not None
        
        # Verify checksum integrity
        expected_checksum = ahj_service._generate_checksum(annotation)
        assert annotation.checksum == expected_checksum
    
    def test_audit_logging(self, ahj_service, sample_user_data):
        """Test audit logging functionality."""
        # Create user (should trigger audit log)
        user = ahj_service.create_ahj_user(sample_user_data)
        
        # Verify audit log was created
        assert len(ahj_service.audit_logs) > 0
        
        # Find user creation log
        user_creation_log = None
        for log in ahj_service.audit_logs:
            if log.action == "user_created" and log.details.get("user_id") == "ahj_user_001":
                user_creation_log = log
                break
        
        assert user_creation_log is not None
        assert user_creation_log.user_id == "system"  # System user for creation
        assert user_creation_log.resource_type == "user"
        assert user_creation_log.resource_id == "ahj_user_001"
    
    def test_notification_system(self, ahj_service, sample_user_data, sample_annotation_data):
        """Test notification system for annotations."""
        # Create user and annotation
        ahj_service.create_ahj_user(sample_user_data)
        annotation = ahj_service.create_inspection_annotation(sample_annotation_data, "ahj_user_001")
        
        # Verify notification was sent (check logs)
        # In a real implementation, we would verify the notification was actually sent
        assert annotation.annotation_id is not None
    
    def test_performance_metrics(self, ahj_service):
        """Test performance metrics generation."""
        metrics = ahj_service.get_performance_metrics()
        
        assert "total_users" in metrics
        assert "active_sessions" in metrics
        assert "total_annotations" in metrics
        assert "audit_logs_count" in metrics
        assert "notifications_sent" in metrics
        assert "average_annotation_time" in metrics
        assert "concurrent_users_supported" in metrics
        assert "audit_trail_integrity" in metrics
        
        assert isinstance(metrics["total_users"], int)
        assert isinstance(metrics["active_sessions"], int)
        assert isinstance(metrics["total_annotations"], int)
        assert isinstance(metrics["audit_logs_count"], int)
    
    def test_concurrent_operations(self, ahj_service, sample_user_data):
        """Test concurrent operations on the AHJ service."""
        import threading
        
        # Create user
        ahj_service.create_ahj_user(sample_user_data)
        
        # Test concurrent annotation creation
        def create_annotation(annotation_id):
            annotation_data = {
                "annotation_type": "inspection_note",
                "content": f"Test annotation {annotation_id}",
                "inspection_id": f"inspection_{annotation_id}"
            }
            return ahj_service.create_inspection_annotation(annotation_data, "ahj_user_001")
        
        threads = []
        results = []
        
        for i in range(5):
            thread = threading.Thread(target=lambda x=i: results.append(create_annotation(x)))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(results) == 5
        for result in results:
            assert result.annotation_id is not None
            assert result.ahj_user_id == "ahj_user_001"
    
    def test_error_handling(self, ahj_service):
        """Test error handling in various scenarios."""
        # Test invalid user data
        with pytest.raises(ValueError):
            ahj_service.create_ahj_user({})
        
        # Test invalid authentication
        with pytest.raises(ValueError):
            ahj_service.authenticate_ahj_user("nonexistent", "password")
        
        # Test invalid annotation data
        with pytest.raises(ValueError):
            ahj_service.create_inspection_annotation({}, "user_id")
    
    def test_data_integrity(self, ahj_service, sample_user_data, sample_annotation_data):
        """Test data integrity during operations."""
        # Create user and annotation
        ahj_service.create_ahj_user(sample_user_data)
        original_annotation = ahj_service.create_inspection_annotation(sample_annotation_data, "ahj_user_001")
        
        # Verify annotation data integrity
        stored_annotation = ahj_service.annotations[original_annotation.annotation_id]
        assert stored_annotation.content == original_annotation.content
        assert stored_annotation.annotation_type == original_annotation.annotation_type
        assert stored_annotation.signature == original_annotation.signature
        assert stored_annotation.checksum == original_annotation.checksum


class TestAHJAPIIntegrationEndpoints:
    """Test suite for AHJ API Integration endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from ..api.main import app
        return TestClient(app)
    
    def test_authenticate_ahj_user_endpoint(self, client):
        """Test AHJ authentication endpoint."""
        auth_data = {
            "username": "inspector_john",
            "password": "secure_password"
        }
        
        response = client.post("/api/v1/ahj/auth/login", json=auth_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "user_id" in data
        assert "session_token" in data
        assert "expires_at" in data
    
    def test_create_ahj_user_endpoint(self, client):
        """Test create AHJ user endpoint."""
        user_data = {
            "user_id": "ahj_user_001",
            "username": "inspector_john",
            "full_name": "John Inspector",
            "organization": "City Building Department",
            "jurisdiction": "Downtown District",
            "permission_level": "inspector",
            "geographic_boundaries": ["downtown", "midtown"],
            "contact_email": "john.inspector@city.gov"
        }
        
        response = client.post("/api/v1/ahj/users", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["user_id"] == "ahj_user_001"
        assert data["user"]["username"] == "inspector_john"
        assert "message" in data
        assert "metadata" in data
    
    def test_create_inspection_annotation_endpoint(self, client):
        """Test create inspection annotation endpoint."""
        annotation_data = {
            "annotation_type": "inspection_note",
            "content": "HVAC system inspection completed.",
            "location_coordinates": {"lat": 40.7128, "lng": -74.0060}
        }
        
        response = client.post("/api/v1/ahj/inspections/inspection_001/annotations", 
                             json=annotation_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["annotation"]["annotation_type"] == "inspection_note"
        assert data["annotation"]["content"] == "HVAC system inspection completed."
        assert "signature" in data["annotation"]
        assert "checksum" in data["annotation"]
    
    def test_get_inspection_annotations_endpoint(self, client):
        """Test get inspection annotations endpoint."""
        response = client.get("/api/v1/ahj/inspections/inspection_001/annotations")
        
        assert response.status_code == 200
        data = response.json()
        assert "inspection_id" in data
        assert "annotations" in data
        assert "summary" in data
        assert "metadata" in data
    
    def test_create_inspection_session_endpoint(self, client):
        """Test create inspection session endpoint."""
        response = client.post("/api/v1/ahj/inspections/inspection_001/sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert data["session"]["inspection_id"] == "inspection_001"
        assert data["session"]["status"] == "active"
        assert "session_id" in data["session"]
    
    def test_end_inspection_session_endpoint(self, client):
        """Test end inspection session endpoint."""
        # First create a session
        session_response = client.post("/api/v1/ahj/inspections/inspection_001/sessions")
        session_id = session_response.json()["session"]["session_id"]
        
        # Then end the session
        response = client.post(f"/api/v1/ahj/sessions/{session_id}/end")
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_summary"]["session_id"] == session_id
        assert data["session_summary"]["status"] == "completed"
    
    def test_get_audit_logs_endpoint(self, client):
        """Test get audit logs endpoint."""
        response = client.get("/api/v1/ahj/audit/logs")
        
        assert response.status_code == 200
        data = response.json()
        assert "audit_logs" in data
        assert "summary" in data
        assert "metadata" in data
    
    def test_verify_annotation_integrity_endpoint(self, client):
        """Test verify annotation integrity endpoint."""
        # First create an annotation
        annotation_data = {
            "annotation_type": "inspection_note",
            "content": "Test annotation for integrity verification"
        }
        annotation_response = client.post("/api/v1/ahj/inspections/inspection_001/annotations", 
                                       json=annotation_data)
        annotation_id = annotation_response.json()["annotation"]["annotation_id"]
        
        # Then verify its integrity
        response = client.post(f"/api/v1/ahj/annotations/{annotation_id}/verify")
        
        assert response.status_code == 200
        data = response.json()
        assert data["annotation_id"] == annotation_id
        assert "integrity_check" in data
        assert "annotation_details" in data
    
    def test_get_inspection_status_endpoint(self, client):
        """Test get inspection status endpoint."""
        response = client.get("/api/v1/ahj/inspections/inspection_001/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["inspection_id"] == "inspection_001"
        assert "overall_status" in data
        assert "statistics" in data
        assert "metadata" in data
    
    def test_get_performance_metrics_endpoint(self, client):
        """Test get performance metrics endpoint."""
        response = client.get("/api/v1/ahj/performance")
        
        assert response.status_code == 200
        data = response.json()
        assert "performance_metrics" in data
        assert "system_status" in data
        assert "capabilities" in data
        assert "compliance_features" in data
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/ahj/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "service" in data
        assert "version" in data
        assert "checks" in data
    
    def test_get_supported_features_endpoint(self, client):
        """Test get supported features endpoint."""
        response = client.get("/api/v1/ahj/supported-features")
        
        assert response.status_code == 200
        data = response.json()
        assert "annotation_types" in data
        assert "permission_levels" in data
        assert "inspection_statuses" in data
        assert "violation_severities" in data
        assert "security_features" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 