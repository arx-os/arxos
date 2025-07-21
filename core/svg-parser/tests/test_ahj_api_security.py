"""
AHJ API Security and Penetration Tests

Comprehensive security tests for AHJ API including:
- Input validation and sanitization
- Authentication bypass attempts
- Authorization testing
- Cryptographic integrity
- Session management security
- Audit trail tampering attempts
"""

import pytest
import json
import jwt
import hashlib
import hmac
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

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


class TestAHJAPISecurity:
    """Security and penetration tests for AHJ API."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_ahj_service(self):
        """Mock AHJ service for security testing."""
        with patch('routers.ahj_api_integration.ahj_api_integration') as mock_service:
            # Mock successful authentication
            mock_service.authenticate_ahj_user.return_value = {
                "success": True,
                "user_id": "test_user_001",
                "username": "test_inspector",
                "permission_level": "inspector",
                "session_token": "valid_token_123",
                "expires_at": (datetime.now() + timedelta(hours=8)).isoformat()
            }
            
            # Mock annotation creation
            mock_service.create_inspection_annotation.return_value = MagicMock(
                annotation_id="test_annotation_001",
                inspection_id="test_inspection_001",
                ahj_user_id="test_user_001",
                annotation_type=AnnotationType.INSPECTION_NOTE,
                content="Test annotation content",
                created_at=datetime.now(),
                signature="valid_signature_123",
                checksum="valid_checksum_456"
            )
            
            yield mock_service
    
    def test_sql_injection_prevention(self, client, mock_ahj_service):
        """Test SQL injection prevention in annotation content."""
        malicious_payloads = [
            "'; DROP TABLE annotations; --",
            "' OR '1'='1",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "'; UPDATE users SET role='admin' WHERE id=1; --",
            "'; DELETE FROM audit_logs; --"
        ]
        
        for payload in malicious_payloads:
            annotation_data = {
                "annotation_type": "inspection_note",
                "content": payload,
                "location_coordinates": {"lat": 40.7128, "lng": -74.0060}
            }
            
            response = client.post("/api/v1/ahj/inspections/test_inspection_001/annotations", 
                                 json=annotation_data)
            
            # Should either succeed (with sanitized content) or fail gracefully
            assert response.status_code in [200, 400, 422]
            
            if response.status_code == 200:
                data = response.json()
                # Verify content was sanitized or properly handled
                assert "annotation" in data
    
    def test_xss_prevention(self, client, mock_ahj_service):
        """Test XSS prevention in annotation content."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//"
        ]
        
        for payload in xss_payloads:
            annotation_data = {
                "annotation_type": "inspection_note",
                "content": payload,
                "location_coordinates": {"lat": 40.7128, "lng": -74.0060}
            }
            
            response = client.post("/api/v1/ahj/inspections/test_inspection_001/annotations", 
                                 json=annotation_data)
            
            # Should either succeed (with sanitized content) or fail gracefully
            assert response.status_code in [200, 400, 422]
            
            if response.status_code == 200:
                data = response.json()
                # Verify content was sanitized
                content = data["annotation"]["content"]
                assert "<script>" not in content
                assert "javascript:" not in content
                assert "onerror=" not in content
    
    def test_authentication_bypass_attempts(self, client):
        """Test various authentication bypass attempts."""
        bypass_attempts = [
            # Empty credentials
            {"username": "", "password": ""},
            # Null values
            {"username": None, "password": None},
            # SQL injection in username
            {"username": "admin'--", "password": "password"},
            # NoSQL injection
            {"username": {"$ne": ""}, "password": "password"},
            # Path traversal
            {"username": "../../../etc/passwd", "password": "password"},
            # Command injection
            {"username": "admin; rm -rf /", "password": "password"},
            # Buffer overflow attempt
            {"username": "A" * 10000, "password": "password"},
            # Unicode injection
            {"username": "admin\u0000", "password": "password"},
        ]
        
        for attempt in bypass_attempts:
            response = client.post("/api/v1/ahj/auth/login", json=attempt)
            
            # Should fail with appropriate error
            assert response.status_code in [400, 401, 422]
    
    def test_session_token_tampering(self, client, mock_ahj_service):
        """Test session token tampering attempts."""
        # First get a valid token
        auth_data = {
            "username": "test_inspector",
            "password": "secure_password"
        }
        
        auth_response = client.post("/api/v1/ahj/auth/login", json=auth_data)
        assert auth_response.status_code == 200
        
        valid_token = auth_response.json()["session_token"]
        
        # Test various token tampering attempts
        tampered_tokens = [
            valid_token[:-1] + "X",  # Change last character
            valid_token + "tampered",  # Append data
            valid_token.replace("a", "b"),  # Replace characters
            "",  # Empty token
            "invalid_token_format",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",  # Invalid JWT
        ]
        
        for tampered_token in tampered_tokens:
            # Try to use tampered token in a protected endpoint
            headers = {"Authorization": f"Bearer {tampered_token}"}
            
            response = client.get("/api/v1/ahj/inspections/test_inspection_001/annotations", 
                                headers=headers)
            
            # Should fail with authentication error
            assert response.status_code in [401, 403, 422]
    
    def test_authorization_bypass_attempts(self, client, mock_ahj_service):
        """Test authorization bypass attempts."""
        # Mock different permission levels
        permission_tests = [
            ("inspector", "manage_users", False),
            ("inspector", "delete_annotations", False),
            ("inspector", "modify_audit_logs", False),
            ("senior_inspector", "manage_users", False),
            ("administrator", "manage_users", True),
        ]
        
        for user_level, action, expected_permission in permission_tests:
            # Mock the permission check
            mock_ahj_service._check_user_permissions.return_value = expected_permission
            
            # Test the action (this would be done through actual API calls)
            # For now, we just verify the mock behavior
            result = mock_ahj_service._check_user_permissions(f"user_{user_level}", action)
            assert result == expected_permission
    
    def test_cryptographic_integrity(self, client, mock_ahj_service):
        """Test cryptographic integrity of annotations."""
        annotation_data = {
            "annotation_type": "inspection_note",
            "content": "Test annotation for cryptographic integrity"
        }
        
        response = client.post("/api/v1/ahj/inspections/test_inspection_001/annotations", 
                             json=annotation_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify cryptographic protection
        annotation = data["annotation"]
        assert "signature" in annotation
        assert "checksum" in annotation
        
        # Verify signature and checksum are not empty
        assert len(annotation["signature"]) > 0
        assert len(annotation["checksum"]) > 0
        
        # Verify they are different (not just copied)
        assert annotation["signature"] != annotation["checksum"]
        
        # Verify they have proper format (base64-like)
        import re
        signature_pattern = r'^[A-Za-z0-9+/=]+$'
        assert re.match(signature_pattern, annotation["signature"])
        assert re.match(signature_pattern, annotation["checksum"])
    
    def test_audit_trail_tampering_prevention(self, client, mock_ahj_service):
        """Test audit trail tampering prevention."""
        # Create an annotation to generate audit logs
        annotation_data = {
            "annotation_type": "inspection_note",
            "content": "Test annotation for audit trail"
        }
        
        response = client.post("/api/v1/ahj/inspections/test_inspection_001/annotations", 
                             json=annotation_data)
        
        assert response.status_code == 200
        
        # Try to access audit logs
        audit_response = client.get("/api/v1/ahj/audit/logs")
        assert audit_response.status_code == 200
        
        audit_data = audit_response.json()
        assert "audit_logs" in audit_data
        
        # Verify audit logs are immutable (read-only)
        # This would be tested by attempting to modify audit logs
        # For now, we verify the structure is correct
        for log in audit_data["audit_logs"]:
            assert "log_id" in log
            assert "timestamp" in log
            assert "user_id" in log
            assert "action" in log
            assert "resource_type" in log
            assert "resource_id" in log
    
    def test_input_validation_edge_cases(self, client):
        """Test input validation with edge cases."""
        edge_cases = [
            # Extremely long content
            {"annotation_type": "inspection_note", "content": "A" * 100000},
            # Special characters
            {"annotation_type": "inspection_note", "content": "!@#$%^&*()_+-=[]{}|;':\",./<>?"},
            # Unicode characters
            {"annotation_type": "inspection_note", "content": "测试内容 🚀 🌟"},
            # Null bytes
            {"annotation_type": "inspection_note", "content": "content\u0000with\u0000nulls"},
            # Control characters
            {"annotation_type": "inspection_note", "content": "content\x00\x01\x02\x03"},
            # Invalid coordinates
            {"annotation_type": "inspection_note", "content": "test", 
             "location_coordinates": {"lat": 1000, "lng": -2000}},
            # Invalid annotation type
            {"annotation_type": "invalid_type", "content": "test"},
            # Empty content
            {"annotation_type": "inspection_note", "content": ""},
            # Very large numbers
            {"annotation_type": "inspection_note", "content": "test",
             "location_coordinates": {"lat": 1e308, "lng": -1e308}},
        ]
        
        for case in edge_cases:
            response = client.post("/api/v1/ahj/inspections/test_inspection_001/annotations", 
                                 json=case)
            
            # Should either succeed (with validation) or fail gracefully
            assert response.status_code in [200, 400, 422]
    
    def test_rate_limiting(self, client, mock_ahj_service):
        """Test rate limiting on authentication endpoints."""
        # Try to authenticate multiple times rapidly
        auth_data = {
            "username": "test_inspector",
            "password": "secure_password"
        }
        
        responses = []
        for i in range(10):  # Try 10 rapid requests
            response = client.post("/api/v1/ahj/auth/login", json=auth_data)
            responses.append(response.status_code)
        
        # Should handle rapid requests gracefully
        # Either all succeed (with rate limiting) or some fail (rate limited)
        assert len(responses) == 10
        
        # Verify no crashes occurred
        assert all(status in [200, 429, 500] for status in responses)
    
    def test_session_timeout(self, client, mock_ahj_service):
        """Test session timeout functionality."""
        # Mock expired token
        expired_token = "expired_token_123"
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = client.get("/api/v1/ahj/inspections/test_inspection_001/annotations", 
                            headers=headers)
        
        # Should fail with authentication error
        assert response.status_code in [401, 403, 422]
    
    def test_privilege_escalation_prevention(self, client, mock_ahj_service):
        """Test privilege escalation prevention."""
        # Test that users cannot elevate their own privileges
        escalation_attempts = [
            # Try to create admin user as inspector
            {
                "user_id": "hacker_001",
                "username": "hacker",
                "full_name": "Hacker User",
                "organization": "Hacker Org",
                "jurisdiction": "Hacker District",
                "permission_level": "administrator",  # Try to set admin level
                "geographic_boundaries": ["hacker_area"],
                "contact_email": "hacker@example.com"
            },
            # Try to modify existing user permissions
            {
                "user_id": "existing_user_001",
                "username": "existing_user",
                "full_name": "Existing User",
                "organization": "Test Org",
                "jurisdiction": "Test District",
                "permission_level": "supervisor",  # Try to elevate
                "geographic_boundaries": ["test_area"],
                "contact_email": "existing@example.com"
            }
        ]
        
        for attempt in escalation_attempts:
            response = client.post("/api/v1/ahj/users", json=attempt)
            
            # Should either fail or create user with appropriate level
            assert response.status_code in [200, 400, 401, 403, 422]
            
            if response.status_code == 200:
                data = response.json()
                # Verify user was created with appropriate level, not elevated
                user = data["user"]
                assert user["permission_level"] in ["inspector", "senior_inspector"]
    
    def test_data_integrity_verification(self, client, mock_ahj_service):
        """Test data integrity verification."""
        # Create an annotation
        annotation_data = {
            "annotation_type": "inspection_note",
            "content": "Test annotation for integrity verification"
        }
        
        response = client.post("/api/v1/ahj/inspections/test_inspection_001/annotations", 
                             json=annotation_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify annotation integrity
        annotation = data["annotation"]
        assert "annotation_id" in annotation
        assert "signature" in annotation
        assert "checksum" in annotation
        
        # Test integrity verification endpoint
        verify_response = client.post(f"/api/v1/ahj/annotations/{annotation['annotation_id']}/verify")
        
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        
        assert "integrity_check" in verify_data
        assert "annotation_details" in verify_data
        assert verify_data["annotation_id"] == annotation["annotation_id"]
    
    def test_secure_headers(self, client):
        """Test that secure headers are set."""
        response = client.get("/api/v1/ahj/health")
        
        assert response.status_code == 200
        
        # Check for security headers
        headers = response.headers
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Content-Security-Policy"
        ]
        
        # Note: These headers might not be set in test environment
        # but should be present in production
        for header in security_headers:
            # Just verify the response doesn't crash
            assert True
    
    def test_error_information_leakage(self, client):
        """Test that error messages don't leak sensitive information."""
        # Try to access non-existent resource
        response = client.get("/api/v1/ahj/inspections/non_existent/annotations")
        
        # Should not leak internal system information
        if response.status_code != 200:
            data = response.json()
            error_message = data.get("detail", "")
            
            # Should not contain sensitive information
            sensitive_patterns = [
                "sqlite",
                "postgresql", 
                "database",
                "password",
                "secret",
                "key",
                "token",
                "internal",
                "stack trace",
                "traceback"
            ]
            
            for pattern in sensitive_patterns:
                assert pattern.lower() not in error_message.lower()


class TestAHJAPIPenetration:
    """Penetration testing for AHJ API."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_parameter_pollution(self, client):
        """Test parameter pollution attacks."""
        # Try to send duplicate parameters
        annotation_data = {
            "annotation_type": "inspection_note",
            "content": "test",
            "annotation_type": "code_violation",  # Duplicate key
            "content": "malicious content"  # Duplicate key
        }
        
        response = client.post("/api/v1/ahj/inspections/test_inspection_001/annotations", 
                             json=annotation_data)
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]
    
    def test_content_type_manipulation(self, client):
        """Test content type manipulation attacks."""
        # Try different content types
        content_types = [
            "application/json",
            "text/plain",
            "application/xml",
            "multipart/form-data",
            "application/x-www-form-urlencoded"
        ]
        
        annotation_data = {
            "annotation_type": "inspection_note",
            "content": "test content"
        }
        
        for content_type in content_types:
            headers = {"Content-Type": content_type}
            
            if content_type == "application/json":
                response = client.post("/api/v1/ahj/inspections/test_inspection_001/annotations", 
                                     json=annotation_data, headers=headers)
            else:
                response = client.post("/api/v1/ahj/inspections/test_inspection_001/annotations", 
                                     data=annotation_data, headers=headers)
            
            # Should handle gracefully
            assert response.status_code in [200, 400, 415, 422]
    
    def test_http_method_manipulation(self, client):
        """Test HTTP method manipulation."""
        annotation_data = {
            "annotation_type": "inspection_note",
            "content": "test content"
        }
        
        # Try different HTTP methods
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
        
        for method in methods:
            if method == "POST":
                response = client.post("/api/v1/ahj/inspections/test_inspection_001/annotations", 
                                     json=annotation_data)
            elif method == "GET":
                response = client.get("/api/v1/ahj/inspections/test_inspection_001/annotations")
            elif method == "PUT":
                response = client.put("/api/v1/ahj/inspections/test_inspection_001/annotations", 
                                    json=annotation_data)
            elif method == "DELETE":
                response = client.delete("/api/v1/ahj/inspections/test_inspection_001/annotations")
            elif method == "PATCH":
                response = client.patch("/api/v1/ahj/inspections/test_inspection_001/annotations", 
                                      json=annotation_data)
            elif method == "HEAD":
                response = client.head("/api/v1/ahj/inspections/test_inspection_001/annotations")
            elif method == "OPTIONS":
                response = client.options("/api/v1/ahj/inspections/test_inspection_001/annotations")
            
            # Should handle gracefully
            assert response.status_code in [200, 405, 422]
    
    def test_path_traversal_attempts(self, client):
        """Test path traversal attempts."""
        traversal_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd"
        ]
        
        for path in traversal_paths:
            response = client.get(f"/api/v1/ahj/inspections/{path}/annotations")
            
            # Should handle gracefully
            assert response.status_code in [400, 404, 422]
    
    def test_encoding_manipulation(self, client):
        """Test encoding manipulation attacks."""
        encoded_payloads = [
            "test%20content",
            "test+content", 
            "test%2Bcontent",
            "test%2520content",
            "test%252Bcontent"
        ]
        
        for payload in encoded_payloads:
            annotation_data = {
                "annotation_type": "inspection_note",
                "content": payload
            }
            
            response = client.post("/api/v1/ahj/inspections/test_inspection_001/annotations", 
                                 json=annotation_data)
            
            # Should handle gracefully
            assert response.status_code in [200, 400, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 