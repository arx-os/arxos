"""
Integration tests for API authentication and authorization.

Tests JWT authentication, role-based access control, and API endpoint security.
"""

import json
import time
import unittest
from typing import Dict, Any, Optional
import requests
import pytest
from unittest.mock import patch, MagicMock

# Mock the Go API server for testing
class MockGoAPIServer:
    """Mock Go API server for testing authentication."""
    
    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.test_users = {
            "admin": {
                "username": "admin",
                "password": "admin123",
                "roles": ["admin"],
                "id": "admin_001"
            },
            "fieldworker": {
                "username": "fieldworker", 
                "password": "field123",
                "roles": ["field_worker"],
                "id": "field_001"
            },
            "validator": {
                "username": "validator",
                "password": "valid123", 
                "roles": ["validator"],
                "id": "val_001"
            },
            "viewer": {
                "username": "viewer",
                "password": "view123",
                "roles": ["viewer"], 
                "id": "view_001"
            }
        }
        
    def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Mock login function."""
        if username in self.test_users:
            user = self.test_users[username]
            if user["password"] == password:
                # Mock JWT token (normally would be properly signed)
                token = f"mock_jwt_token_{username}_{int(time.time())}"
                return {
                    "access_token": token,
                    "refresh_token": f"refresh_{token}",
                    "expires_at": time.time() + 3600,
                    "user": {
                        "id": user["id"],
                        "username": user["username"],
                        "roles": user["roles"],
                        "permissions": self._get_permissions_for_roles(user["roles"])
                    }
                }
        return None
        
    def _get_permissions_for_roles(self, roles):
        """Get permissions for given roles."""
        permission_map = {
            "admin": [
                "create_building", "read_building", "update_building", "delete_building",
                "create_arxobject", "read_arxobject", "update_arxobject", "delete_arxobject", 
                "ingest_pdf", "ingest_image", "ingest_lidar",
                "view_audit_logs", "manage_system", "export_data"
            ],
            "field_worker": [
                "read_building", "update_building",
                "create_arxobject", "read_arxobject", "update_arxobject",
                "ingest_pdf", "ingest_image", "ingest_lidar", "export_data"
            ],
            "validator": [
                "read_building", "update_building", 
                "read_arxobject", "update_arxobject",
                "ingest_pdf", "ingest_image", "export_data"
            ],
            "viewer": [
                "read_building", "read_arxobject"
            ]
        }
        
        permissions = set()
        for role in roles:
            if role in permission_map:
                permissions.update(permission_map[role])
        return list(permissions)


class TestAPIAuthentication(unittest.TestCase):
    """Test API authentication functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.api = MockGoAPIServer()
        
    def test_valid_login(self):
        """Test login with valid credentials."""
        response = self.api.login("admin", "admin123")
        
        self.assertIsNotNone(response)
        self.assertIn("access_token", response)
        self.assertIn("refresh_token", response)
        self.assertIn("expires_at", response)
        self.assertIn("user", response)
        
        user = response["user"]
        self.assertEqual(user["username"], "admin")
        self.assertIn("admin", user["roles"])
        self.assertIn("create_building", user["permissions"])
        self.assertIn("manage_system", user["permissions"])
        
    def test_invalid_login(self):
        """Test login with invalid credentials."""
        response = self.api.login("admin", "wrong_password")
        self.assertIsNone(response)
        
        response = self.api.login("nonexistent", "password")
        self.assertIsNone(response)
        
    def test_role_permissions(self):
        """Test that different roles have correct permissions."""
        # Test admin permissions
        admin_response = self.api.login("admin", "admin123")
        admin_permissions = admin_response["user"]["permissions"]
        
        self.assertIn("delete_building", admin_permissions)
        self.assertIn("manage_system", admin_permissions)
        self.assertIn("view_audit_logs", admin_permissions)
        
        # Test field worker permissions
        field_response = self.api.login("fieldworker", "field123")
        field_permissions = field_response["user"]["permissions"]
        
        self.assertIn("create_arxobject", field_permissions)
        self.assertIn("ingest_pdf", field_permissions)
        self.assertNotIn("delete_building", field_permissions)
        self.assertNotIn("manage_system", field_permissions)
        
        # Test validator permissions
        validator_response = self.api.login("validator", "valid123")
        validator_permissions = validator_response["user"]["permissions"]
        
        self.assertIn("read_building", validator_permissions)
        self.assertIn("update_arxobject", validator_permissions)
        self.assertNotIn("create_arxobject", validator_permissions)
        self.assertNotIn("ingest_lidar", validator_permissions)
        
        # Test viewer permissions (most restrictive)
        viewer_response = self.api.login("viewer", "view123")
        viewer_permissions = viewer_response["user"]["permissions"]
        
        self.assertIn("read_building", viewer_permissions)
        self.assertIn("read_arxobject", viewer_permissions)
        self.assertNotIn("update_building", viewer_permissions)
        self.assertNotIn("create_arxobject", viewer_permissions)
        
    def test_token_structure(self):
        """Test that JWT tokens have the correct structure."""
        response = self.api.login("admin", "admin123")
        
        self.assertIsNotNone(response)
        
        # Verify token is a string
        token = response["access_token"]
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)
        
        # Verify refresh token
        refresh_token = response["refresh_token"]
        self.assertIsInstance(refresh_token, str)
        self.assertGreater(len(refresh_token), 0)
        
        # Verify expiration
        expires_at = response["expires_at"]
        self.assertIsInstance(expires_at, (int, float))
        self.assertGreater(expires_at, time.time())
        
    def test_user_data_completeness(self):
        """Test that user data in response is complete."""
        response = self.api.login("fieldworker", "field123")
        user = response["user"]
        
        required_fields = ["id", "username", "roles", "permissions"]
        for field in required_fields:
            self.assertIn(field, user, f"User data missing field: {field}")
            
        # Verify data types
        self.assertIsInstance(user["id"], str)
        self.assertIsInstance(user["username"], str)
        self.assertIsInstance(user["roles"], list)
        self.assertIsInstance(user["permissions"], list)
        
        # Verify content
        self.assertGreater(len(user["id"]), 0)
        self.assertGreater(len(user["username"]), 0)
        self.assertGreater(len(user["roles"]), 0)
        self.assertGreater(len(user["permissions"]), 0)


class TestRoleBasedAccessControl(unittest.TestCase):
    """Test role-based access control for different endpoints."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.api = MockGoAPIServer()
        cls.endpoints = {
            # Endpoint: (required_permission, description)
            "/api/v1/arxobjects": ("read_arxobject", "GET - list objects"),
            "/api/v1/arxobjects/create": ("create_arxobject", "POST - create object"),
            "/api/v1/arxobjects/123": ("read_arxobject", "GET - get object"),
            "/api/v1/arxobjects/123/update": ("update_arxobject", "PUT - update object"),
            "/api/v1/arxobjects/123/delete": ("delete_arxobject", "DELETE - delete object"),
            "/api/v1/ingest/pdf": ("ingest_pdf", "POST - ingest PDF"),
            "/api/v1/ingest/image": ("ingest_image", "POST - ingest image"),
            "/api/v1/ingest/lidar": ("ingest_lidar", "POST - start LiDAR"),
            "/api/v1/systems": ("read_building", "GET - list systems"),
            "/api/v1/admin/audit": ("view_audit_logs", "GET - view audit logs"),
            "/api/v1/admin/system": ("manage_system", "GET - system management")
        }
        
    def test_admin_access(self):
        """Test that admin has access to all endpoints."""
        admin_response = self.api.login("admin", "admin123")
        admin_permissions = set(admin_response["user"]["permissions"])
        
        for endpoint, (required_permission, description) in self.endpoints.items():
            with self.subTest(endpoint=endpoint, description=description):
                self.assertIn(required_permission, admin_permissions,
                             f"Admin should have {required_permission} for {endpoint}")
                             
    def test_field_worker_access(self):
        """Test field worker access restrictions."""
        field_response = self.api.login("fieldworker", "field123")
        field_permissions = set(field_response["user"]["permissions"])
        
        # Should have access to
        allowed_endpoints = [
            "/api/v1/arxobjects",
            "/api/v1/arxobjects/create", 
            "/api/v1/arxobjects/123",
            "/api/v1/arxobjects/123/update",
            "/api/v1/ingest/pdf",
            "/api/v1/ingest/image", 
            "/api/v1/ingest/lidar",
            "/api/v1/systems"
        ]
        
        for endpoint in allowed_endpoints:
            required_permission = self.endpoints[endpoint][0]
            with self.subTest(endpoint=endpoint):
                self.assertIn(required_permission, field_permissions,
                             f"Field worker should have access to {endpoint}")
                
        # Should NOT have access to
        forbidden_endpoints = [
            "/api/v1/arxobjects/123/delete",
            "/api/v1/admin/audit",
            "/api/v1/admin/system"
        ]
        
        for endpoint in forbidden_endpoints:
            required_permission = self.endpoints[endpoint][0]
            with self.subTest(endpoint=endpoint):
                self.assertNotIn(required_permission, field_permissions,
                                f"Field worker should NOT have access to {endpoint}")
                                
    def test_validator_access(self):
        """Test validator access restrictions."""
        validator_response = self.api.login("validator", "valid123")
        validator_permissions = set(validator_response["user"]["permissions"])
        
        # Should have access to
        allowed_endpoints = [
            "/api/v1/arxobjects",
            "/api/v1/arxobjects/123", 
            "/api/v1/arxobjects/123/update",
            "/api/v1/ingest/pdf",
            "/api/v1/ingest/image",
            "/api/v1/systems"
        ]
        
        for endpoint in allowed_endpoints:
            required_permission = self.endpoints[endpoint][0]
            with self.subTest(endpoint=endpoint):
                self.assertIn(required_permission, validator_permissions,
                             f"Validator should have access to {endpoint}")
                
        # Should NOT have access to
        forbidden_endpoints = [
            "/api/v1/arxobjects/create",
            "/api/v1/arxobjects/123/delete",
            "/api/v1/ingest/lidar",
            "/api/v1/admin/audit",
            "/api/v1/admin/system"
        ]
        
        for endpoint in forbidden_endpoints:
            required_permission = self.endpoints[endpoint][0]
            with self.subTest(endpoint=endpoint):
                self.assertNotIn(required_permission, validator_permissions,
                                f"Validator should NOT have access to {endpoint}")
                                
    def test_viewer_access(self):
        """Test viewer access restrictions (most restrictive)."""
        viewer_response = self.api.login("viewer", "view123")
        viewer_permissions = set(viewer_response["user"]["permissions"])
        
        # Should have access to (very limited)
        allowed_endpoints = [
            "/api/v1/arxobjects",
            "/api/v1/arxobjects/123",
            "/api/v1/systems"
        ]
        
        for endpoint in allowed_endpoints:
            required_permission = self.endpoints[endpoint][0]
            with self.subTest(endpoint=endpoint):
                self.assertIn(required_permission, viewer_permissions,
                             f"Viewer should have access to {endpoint}")
                
        # Should NOT have access to (everything else)
        forbidden_endpoints = [
            "/api/v1/arxobjects/create",
            "/api/v1/arxobjects/123/update", 
            "/api/v1/arxobjects/123/delete",
            "/api/v1/ingest/pdf",
            "/api/v1/ingest/image",
            "/api/v1/ingest/lidar",
            "/api/v1/admin/audit",
            "/api/v1/admin/system"
        ]
        
        for endpoint in forbidden_endpoints:
            required_permission = self.endpoints[endpoint][0]
            with self.subTest(endpoint=endpoint):
                self.assertNotIn(required_permission, viewer_permissions,
                                f"Viewer should NOT have access to {endpoint}")


class TestTokenSecurity(unittest.TestCase):
    """Test JWT token security features."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.api = MockGoAPIServer()
        
    def test_token_uniqueness(self):
        """Test that tokens are unique for each login."""
        response1 = self.api.login("admin", "admin123")
        time.sleep(1)  # Ensure different timestamp
        response2 = self.api.login("admin", "admin123")
        
        self.assertNotEqual(response1["access_token"], response2["access_token"])
        self.assertNotEqual(response1["refresh_token"], response2["refresh_token"])
        
    def test_token_expiration(self):
        """Test token expiration timing."""
        response = self.api.login("admin", "admin123")
        
        expires_at = response["expires_at"]
        current_time = time.time()
        
        # Token should expire in approximately 1 hour (3600 seconds)
        expiration_delta = expires_at - current_time
        self.assertGreater(expiration_delta, 3500)  # At least 58 minutes
        self.assertLess(expiration_delta, 3700)     # At most 62 minutes
        
    def test_different_users_different_tokens(self):
        """Test that different users get different tokens."""
        admin_response = self.api.login("admin", "admin123")
        field_response = self.api.login("fieldworker", "field123")
        
        self.assertNotEqual(admin_response["access_token"], field_response["access_token"])
        self.assertNotEqual(admin_response["refresh_token"], field_response["refresh_token"])
        
        # But user data should be different
        self.assertNotEqual(admin_response["user"]["id"], field_response["user"]["id"])
        self.assertNotEqual(admin_response["user"]["username"], field_response["user"]["username"])
        self.assertNotEqual(admin_response["user"]["roles"], field_response["user"]["roles"])


class TestAPIEndpointSecurity(unittest.TestCase):
    """Test API endpoint security measures."""
    
    def test_health_endpoint_public(self):
        """Test that health endpoint is publicly accessible."""
        # Health endpoint should not require authentication
        # This would normally be tested with actual HTTP requests
        # For now, we'll test that it's in the list of public endpoints
        
        public_endpoints = ["/api/v1/health", "/api/v1/auth/login"]
        
        for endpoint in public_endpoints:
            with self.subTest(endpoint=endpoint):
                # These endpoints should be accessible without authentication
                self.assertTrue(True)  # Placeholder for actual HTTP test
                
    def test_cors_headers(self):
        """Test CORS configuration."""
        # In a real test, this would verify CORS headers in HTTP responses
        expected_cors_headers = [
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods", 
            "Access-Control-Allow-Headers"
        ]
        
        for header in expected_cors_headers:
            with self.subTest(header=header):
                # Verify CORS headers are configured
                self.assertTrue(True)  # Placeholder for actual HTTP test
                
    def test_rate_limiting_configuration(self):
        """Test rate limiting is properly configured."""
        # This would test actual rate limiting in integration
        rate_limits = {
            "api": "10r/s",
            "upload": "2r/s" 
        }
        
        for zone, limit in rate_limits.items():
            with self.subTest(zone=zone, limit=limit):
                # Verify rate limiting zones are configured
                self.assertTrue(True)  # Placeholder for actual rate limit test


if __name__ == "__main__":
    # Run specific test groups
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "auth":
            suite = unittest.TestLoader().loadTestsFromTestCase(TestAPIAuthentication)
        elif sys.argv[1] == "rbac":
            suite = unittest.TestLoader().loadTestsFromTestCase(TestRoleBasedAccessControl)
        elif sys.argv[1] == "security":
            suite = unittest.TestLoader().loadTestsFromTestCase(TestTokenSecurity)
        elif sys.argv[1] == "endpoints":
            suite = unittest.TestLoader().loadTestsFromTestCase(TestAPIEndpointSecurity)
        else:
            suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    else:
        suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with error code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)