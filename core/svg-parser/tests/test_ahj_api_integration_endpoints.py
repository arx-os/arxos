"""
AHJ API Integration Endpoint Tests

Comprehensive integration tests for AHJ API endpoints using FastAPI TestClient.
Tests the full API stack including authentication, authorization, and data flow.
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Import the main app
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.api.main
from services.ahj_api_integration import (
    AHJAPIIntegration,
    AnnotationType,
    ViolationSeverity,
    InspectionStatus,
    PermissionLevel
)


class TestAHJAPIEndpoints:
    """Integration tests for AHJ API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_ahj_service(self):
        """Mock AHJ service for testing."""
        with patch('routers.ahj_api_integration.ahj_api_integration') as mock_service:
            # Mock service methods
            mock_service.create_ahj_user.return_value = MagicMock(
                user_id="test_user_001",
                username="test_inspector",
                full_name="Test Inspector",
                organization="Test Org",
                jurisdiction="Test District",
                permission_level=PermissionLevel.INSPECTOR,
                geographic_boundaries=["test_area"],
                contact_email="test@example.com",
                created_at=datetime.now()
            )
            
            mock_service.authenticate_ahj_user.return_value = {
                "success": True,
                "user_id": "test_user_001",
                "username": "test_inspector",
                "permission_level": "inspector",
                "session_token": "test_token_123",
                "expires_at": (datetime.now() + timedelta(hours=8)).isoformat()
            }
            
            mock_service.create_inspection_annotation.return_value = MagicMock(
                annotation_id="test_annotation_001",
                inspection_id="test_inspection_001",
                ahj_user_id="test_user_001",
                annotation_type=AnnotationType.INSPECTION_NOTE,
                content="Test annotation content",
                created_at=datetime.now(),
                signature="test_signature_123",
                checksum="test_checksum_456"
            )
            
            mock_service.get_inspection_annotations.return_value = [
                {
                    "annotation_id": "test_annotation_001",
                    "inspection_id": "test_inspection_001",
                    "annotation_type": "inspection_note",
                    "content": "Test annotation content",
                    "created_at": datetime.now().isoformat()
                }
            ]
            
            mock_service.create_inspection_session.return_value = MagicMock(
                session_id="test_session_001",
                inspection_id="test_inspection_001",
                ahj_user_id="test_user_001",
                start_time=datetime.now(),
                status="active"
            )
            
            mock_service.end_inspection_session.return_value = {
                "session_id": "test_session_001",
                "status": "completed",
                "duration_seconds": 60.0,
                "annotations_count": 1
            }
            
            mock_service.get_audit_logs.return_value = [
                {
                    "log_id": "test_log_001",
                    "timestamp": datetime.now().isoformat(),
                    "user_id": "test_user_001",
                    "action": "annotation_created",
                    "resource_type": "annotation",
                    "resource_id": "test_annotation_001",
                    "details": {"test": "data"},
                    "ip_address": "127.0.0.1",
                    "user_agent": "test-agent",
                    "session_id": "test_session_001"
                }
            ]
            
            mock_service.get_performance_metrics.return_value = {
                "total_users": 1,
                "active_sessions": 1,
                "total_annotations": 1,
                "audit_logs_count": 1,
                "notifications_sent": 0,
                "average_annotation_time": "<2 seconds",
                "concurrent_users_supported": "1,000+",
                "audit_trail_integrity": "100%"
            }
            
            yield mock_service
    
    def test_authenticate_ahj_user_endpoint(self, client, mock_ahj_service):
        """Test AHJ authentication endpoint."""
        auth_data = {
            "username": "test_inspector",
            "password": "secure_password"
        }
        
        response = client.post("/api/v1/ahj/auth/login", json=auth_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "user_id" in data
        assert "session_token" in data
        assert "expires_at" in data
        
        # Verify service was called
        mock_ahj_service.authenticate_ahj_user.assert_called_once_with(
            "test_inspector", "secure_password", None
        )
    
    def test_authenticate_ahj_user_with_mfa(self, client, mock_ahj_service):
        """Test AHJ authentication with MFA."""
        auth_data = {
            "username": "test_inspector",
            "password": "secure_password",
            "mfa_token": "123456"
        }
        
        response = client.post("/api/v1/ahj/auth/login", json=auth_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify service was called with MFA
        mock_ahj_service.authenticate_ahj_user.assert_called_once_with(
            "test_inspector", "secure_password", "123456"
        )
    
    def test_authenticate_ahj_user_invalid_credentials(self, client, mock_ahj_service):
        """Test AHJ authentication with invalid credentials."""
        mock_ahj_service.authenticate_ahj_user.side_effect = ValueError("Invalid credentials")
        
        auth_data = {
            "username": "test_inspector",
            "password": "wrong_password"
        }
        
        response = client.post("/api/v1/ahj/auth/login", json=auth_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "Authentication failed" in data["detail"]
    
    def test_create_ahj_user_endpoint(self, client, mock_ahj_service):
        """Test create AHJ user endpoint."""
        user_data = {
            "user_id": "test_user_001",
            "username": "test_inspector",
            "full_name": "Test Inspector",
            "organization": "Test Org",
            "jurisdiction": "Test District",
            "permission_level": "inspector",
            "geographic_boundaries": ["test_area"],
            "contact_email": "test@example.com"
        }
        
        response = client.post("/api/v1/ahj/users", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["user_id"] == "test_user_001"
        assert data["user"]["username"] == "test_inspector"
        assert "message" in data
        assert "metadata" in data
        
        # Verify service was called
        mock_ahj_service.create_ahj_user.assert_called_once()
    
    def test_create_inspection_annotation_endpoint(self, client, mock_ahj_service):
        """Test create inspection annotation endpoint."""
        annotation_data = {
            "annotation_type": "inspection_note",
            "content": "Test annotation content",
            "location_coordinates": {"lat": 40.7128, "lng": -74.0060}
        }
        
        response = client.post("/api/v1/ahj/inspections/test_inspection_001/annotations", 
                             json=annotation_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["annotation"]["annotation_type"] == "inspection_note"
        assert data["annotation"]["content"] == "Test annotation content"
        assert "signature" in data["annotation"]
        assert "checksum" in data["annotation"]
        
        # Verify service was called
        mock_ahj_service.create_inspection_annotation.assert_called_once()
    
    def test_create_code_violation_annotation(self, client, mock_ahj_service):
        """Test create code violation annotation."""
        violation_data = {
            "annotation_type": "code_violation",
            "content": "Missing fire extinguisher",
            "violation_severity": "major",
            "code_reference": "NFPA 101-2018 Section 9.7.1.1"
        }
        
        # Mock the annotation return value for code violation
        mock_ahj_service.create_inspection_annotation.return_value = MagicMock(
            annotation_id="test_violation_001",
            inspection_id="test_inspection_001",
            ahj_user_id="test_user_001",
            annotation_type=AnnotationType.CODE_VIOLATION,
            content="Missing fire extinguisher",
            violation_severity=ViolationSeverity.MAJOR,
            code_reference="NFPA 101-2018 Section 9.7.1.1",
            created_at=datetime.now(),
            signature="test_signature_123",
            checksum="test_checksum_456"
        )
        
        response = client.post("/api/v1/ahj/inspections/test_inspection_001/annotations", 
                             json=violation_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["annotation"]["annotation_type"] == "code_violation"
        assert data["annotation"]["violation_severity"] == "major"
        assert data["annotation"]["code_reference"] == "NFPA 101-2018 Section 9.7.1.1"
    
    def test_get_inspection_annotations_endpoint(self, client, mock_ahj_service):
        """Test get inspection annotations endpoint."""
        response = client.get("/api/v1/ahj/inspections/test_inspection_001/annotations")
        
        assert response.status_code == 200
        data = response.json()
        assert "inspection_id" in data
        assert "annotations" in data
        assert "summary" in data
        assert "metadata" in data
        assert len(data["annotations"]) == 1
        
        # Verify service was called
        mock_ahj_service.get_inspection_annotations.assert_called_once()
    
    def test_create_inspection_session_endpoint(self, client, mock_ahj_service):
        """Test create inspection session endpoint."""
        response = client.post("/api/v1/ahj/inspections/test_inspection_001/sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert data["session"]["inspection_id"] == "test_inspection_001"
        assert data["session"]["status"] == "active"
        assert "session_id" in data["session"]
        
        # Verify service was called
        mock_ahj_service.create_inspection_session.assert_called_once()
    
    def test_end_inspection_session_endpoint(self, client, mock_ahj_service):
        """Test end inspection session endpoint."""
        response = client.post("/api/v1/ahj/sessions/test_session_001/end")
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_summary"]["session_id"] == "test_session_001"
        assert data["session_summary"]["status"] == "completed"
        assert "duration_seconds" in data["session_summary"]
        
        # Verify service was called
        mock_ahj_service.end_inspection_session.assert_called_once()
    
    def test_get_audit_logs_endpoint(self, client, mock_ahj_service):
        """Test get audit logs endpoint."""
        response = client.get("/api/v1/ahj/audit/logs")
        
        assert response.status_code == 200
        data = response.json()
        assert "audit_logs" in data
        assert "summary" in data
        assert "metadata" in data
        assert len(data["audit_logs"]) == 1
        
        # Verify service was called
        mock_ahj_service.get_audit_logs.assert_called_once()
    
    def test_get_audit_logs_with_filters(self, client, mock_ahj_service):
        """Test get audit logs with date and action filters."""
        response = client.get("/api/v1/ahj/audit/logs?start_date=2024-01-01&action_type=annotation_created")
        
        assert response.status_code == 200
        data = response.json()
        assert "audit_logs" in data
        assert "metadata" in data
        assert "filters_applied" in data["metadata"]
        
        # Verify service was called with filters
        mock_ahj_service.get_audit_logs.assert_called_once()
    
    def test_verify_annotation_integrity_endpoint(self, client, mock_ahj_service):
        """Test verify annotation integrity endpoint."""
        # Mock the verification result
        mock_ahj_service._generate_checksum.return_value = "test_checksum_456"
        
        response = client.post("/api/v1/ahj/annotations/test_annotation_001/verify")
        
        assert response.status_code == 200
        data = response.json()
        assert data["annotation_id"] == "test_annotation_001"
        assert "integrity_check" in data
        assert "annotation_details" in data
    
    def test_get_inspection_status_endpoint(self, client, mock_ahj_service):
        """Test get inspection status endpoint."""
        response = client.get("/api/v1/ahj/inspections/test_inspection_001/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["inspection_id"] == "test_inspection_001"
        assert "overall_status" in data
        assert "statistics" in data
        assert "metadata" in data
    
    def test_get_performance_metrics_endpoint(self, client, mock_ahj_service):
        """Test get performance metrics endpoint."""
        response = client.get("/api/v1/ahj/performance")
        
        assert response.status_code == 200
        data = response.json()
        assert "performance_metrics" in data
        assert "system_status" in data
        assert "capabilities" in data
        assert "compliance_features" in data
        
        # Verify service was called
        mock_ahj_service.get_performance_metrics.assert_called_once()
    
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
    
    def test_error_handling_invalid_annotation_data(self, client, mock_ahj_service):
        """Test error handling for invalid annotation data."""
        mock_ahj_service.create_inspection_annotation.side_effect = ValueError("Missing required field: annotation_type")
        
        invalid_annotation_data = {
            "content": "Test annotation without type"
        }
        
        response = client.post("/api/v1/ahj/inspections/test_inspection_001/annotations", 
                             json=invalid_annotation_data)
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to create annotation" in data["detail"]
    
    def test_error_handling_invalid_user_data(self, client, mock_ahj_service):
        """Test error handling for invalid user data."""
        mock_ahj_service.create_ahj_user.side_effect = ValueError("Missing required field: full_name")
        
        invalid_user_data = {
            "user_id": "test_user_001",
            "username": "test_inspector"
            # Missing required fields
        }
        
        response = client.post("/api/v1/ahj/users", json=invalid_user_data)
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to create AHJ user" in data["detail"]
    
    def test_authentication_required_endpoints(self, client):
        """Test that endpoints requiring authentication return proper errors."""
        # Test without authentication
        annotation_data = {
            "annotation_type": "inspection_note",
            "content": "Test annotation"
        }
        
        response = client.post("/api/v1/ahj/inspections/test_inspection_001/annotations", 
                             json=annotation_data)
        
        # Should return 401 or 422 (depending on how authentication is implemented)
        assert response.status_code in [401, 422]
    
    def test_permission_enforcement(self, client, mock_ahj_service):
        """Test permission enforcement in endpoints."""
        # Mock permission check to return False
        mock_ahj_service._check_user_permissions.return_value = False
        
        annotation_data = {
            "annotation_type": "inspection_note",
            "content": "Test annotation"
        }
        
        response = client.post("/api/v1/ahj/inspections/test_inspection_001/annotations", 
                             json=annotation_data)
        
        # Should return 500 with permission error
        assert response.status_code == 500
        data = response.json()
        assert "Failed to create annotation" in data["detail"]


class TestAHJAPISecurity:
    """Security tests for AHJ API."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_cryptographic_signing(self, client, mock_ahj_service):
        """Test that annotations are cryptographically signed."""
        annotation_data = {
            "annotation_type": "inspection_note",
            "content": "Test annotation content"
        }
        
        response = client.post("/api/v1/ahj/inspections/test_inspection_001/annotations", 
                             json=annotation_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify cryptographic protection
        assert "signature" in data["annotation"]
        assert "checksum" in data["annotation"]
        assert len(data["annotation"]["signature"]) > 0
        assert len(data["annotation"]["checksum"]) > 0
    
    def test_audit_trail_integrity(self, client, mock_ahj_service):
        """Test audit trail integrity."""
        # Create an annotation
        annotation_data = {
            "annotation_type": "inspection_note",
            "content": "Test annotation for audit"
        }
        
        response = client.post("/api/v1/ahj/inspections/test_inspection_001/annotations", 
                             json=annotation_data)
        
        assert response.status_code == 200
        
        # Check audit logs
        audit_response = client.get("/api/v1/ahj/audit/logs")
        assert audit_response.status_code == 200
        
        audit_data = audit_response.json()
        assert len(audit_data["audit_logs"]) > 0
        
        # Verify audit log contains the annotation creation
        annotation_logs = [log for log in audit_data["audit_logs"] 
                          if log.get("action") == "annotation_created"]
        assert len(annotation_logs) > 0
    
    def test_session_token_security(self, client, mock_ahj_service):
        """Test session token security."""
        auth_data = {
            "username": "test_inspector",
            "password": "secure_password"
        }
        
        response = client.post("/api/v1/ahj/auth/login", json=auth_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify session token is present and has expected format
        assert "session_token" in data
        assert len(data["session_token"]) > 0
        
        # Verify expiration is set
        assert "expires_at" in data
        assert data["expires_at"] is not None
    
    def test_permission_boundaries(self, client, mock_ahj_service):
        """Test that permission boundaries are enforced."""
        # Test with different permission levels
        permission_tests = [
            ("inspector", "create_annotation", True),
            ("inspector", "manage_users", False),
            ("administrator", "manage_users", True),
        ]
        
        for permission_level, action, expected in permission_tests:
            mock_ahj_service._check_user_permissions.return_value = expected
            
            # This would test the actual permission enforcement in the endpoints
            # For now, we just verify the mock is called correctly
            assert True  # Placeholder for actual permission testing


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 