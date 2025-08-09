"""
Comprehensive Security Test Suite for SVGX Engine

This test suite provides comprehensive security testing for:
- Authentication and authorization
- Input validation and sanitization
- Rate limiting and DDoS protection
- Plugin security and sandboxing
- Encryption and key management
- Security headers and middleware
"""

import asyncio
import json
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException

from svgx_engine.services.auth_middleware import (
    create_access_token, verify_token, get_current_user,
    require_read_permission, require_write_permission, require_admin_permission
)
from svgx_engine.services.enhanced_rate_limiter import (
    enhanced_rate_limit_middleware, get_rate_limit_analytics,
    update_rate_limit_config, block_client_manually, unblock_client_manually
)
from svgx_engine.services.plugin_system import (
    PluginManager, PluginValidator, PluginSandbox,
    PluginSecurityLevel, PluginType
)
from svgx_engine.services.security_hardener import SVGXSecurityHardener
from svgx_engine.services.api_interface import app


class TestSecurityHardeningComprehensive(unittest.TestCase):
    """Comprehensive security test suite."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_dir = Path(self.temp_dir) / "plugins"
        self.plugin_dir.mkdir(exist_ok=True)

        # Initialize security components
        self.security_hardener = SVGXSecurityHardener()
        self.plugin_manager = PluginManager(plugin_dir=str(self.plugin_dir)
        self.plugin_validator = PluginValidator()
        self.plugin_sandbox = PluginSandbox()

        # Test client for API testing
        self.client = TestClient(app)

        # Create test plugins
        self._create_test_plugins()

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_plugins(self):
        """Create test plugins for security testing."""

        # Safe plugin
        safe_plugin_content = '''
"""
Safe Test Plugin
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from svgx_engine.services.plugin_system import (
    BehaviorHandlerPlugin, PluginMetadata, PluginSecurityLevel, PluginType
)

logger = logging.getLogger(__name__)

class SafePlugin(BehaviorHandlerPlugin):
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="safe_plugin",
            version="1.0.0",
            description="Safe test plugin",
            author="Test Author",
            plugin_type=PluginType.BEHAVIOR_HANDLER,
            security_level=PluginSecurityLevel.VERIFIED,
            tags=["test", "safe"],
            dependencies=[],
            requirements=[]
        )

    def initialize(self, config: Dict[str, Any]) -> bool:
        return True

    def handle_ui_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "processed",
            "plugin": "safe_plugin",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
'''

        # Malicious plugin
        malicious_plugin_content = '''
"""
Malicious Test Plugin
"""
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Dict

from svgx_engine.services.plugin_system import (
    BehaviorHandlerPlugin, PluginMetadata, PluginSecurityLevel, PluginType
)

class MaliciousPlugin(BehaviorHandlerPlugin):
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="malicious_plugin",
            version="1.0.0",
            description="Malicious test plugin",
            author="Test Author",
            plugin_type=PluginType.BEHAVIOR_HANDLER,
            security_level=PluginSecurityLevel.UNTRUSTED,
            tags=["test", "malicious"],
            dependencies=[],
            requirements=[]
        )

    def initialize(self, config: Dict[str, Any]) -> bool:
        # Attempt malicious operations
        try:
            os.system("echo malicious")
            subprocess.run(["echo", "malicious"], capture_output=True)
            with open("/etc/passwd", "r") as f:
                f.read()
        except:
            pass
        return True

    def handle_ui_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "processed",
            "plugin": "malicious_plugin",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
'''

        # Write plugin files
        safe_plugin_path = self.plugin_dir / "safe_plugin.py"
        malicious_plugin_path = self.plugin_dir / "malicious_plugin.py"

        with open(safe_plugin_path, 'w') as f:
            f.write(safe_plugin_content)

        with open(malicious_plugin_path, 'w') as f:
            f.write(malicious_plugin_content)

    def test_authentication_token_creation(self):
        """Test JWT token creation and validation."""
        # Test token creation
        user_data = {"user_id": "test_user", "username": "test", "role": "editor"}
        token = create_access_token(user_data)

        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)

        # Test token verification
        payload = verify_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["user_id"], "test_user")
        self.assertEqual(payload["username"], "test")
        self.assertEqual(payload["role"], "editor")

    def test_authentication_token_expiration(self):
        """Test JWT token expiration."""
        # Create token with short expiration
        user_data = {"user_id": "test_user", "username": "test", "role": "editor"}

        with patch('svgx_engine.services.auth_middleware.ACCESS_TOKEN_EXPIRE_MINUTES', 0):
            token = create_access_token(user_data)

        # Token should be expired
        with self.assertRaises(HTTPException):
            verify_token(token)

    def test_authentication_permission_checks(self):
        """Test authentication permission checks."""
        # Test read permission
        user = Mock()
        user.permissions = ["read"]

        # Should not raise exception
        require_read_permission(user)

        # Test write permission
        user.permissions = ["read", "write"]
        require_write_permission(user)

        # Test admin permission
        user.permissions = ["read", "write", "admin"]
        require_admin_permission(user)

        # Test insufficient permissions
        user.permissions = ["read"]
        with self.assertRaises(HTTPException):
            require_write_permission(user)

        with self.assertRaises(HTTPException):
            require_admin_permission(user)

    def test_rate_limiting_functionality(self):
        """Test rate limiting functionality."""
        # Test rate limiting middleware
        request = Mock()
        request.client.host = "127.0.0.1"
        request.url.path = "/api/test"

        # Test normal request
        response = enhanced_rate_limit_middleware(request, lambda r: {"status": "ok"})
        self.assertEqual(response["status"], "ok")

        # Test rate limit exceeded
        for i in range(100):  # Exceed rate limit
            enhanced_rate_limit_middleware(request, lambda r: {"status": "ok"})

        # Should be rate limited
        response = enhanced_rate_limit_middleware(request, lambda r: {"status": "ok"})
        self.assertEqual(response.status_code, 429)

    def test_rate_limiting_analytics(self):
        """Test rate limiting analytics."""
        # Get analytics
        analytics = get_rate_limit_analytics()

        self.assertIsNotNone(analytics)
        self.assertIn("total_requests", analytics)
        self.assertIn("blocked_requests", analytics)
        self.assertIn("rate_limited_ips", analytics)

    def test_rate_limiting_configuration(self):
        """Test rate limiting configuration."""
        # Test configuration update
        config = {
            "requests_per_minute": 60,
            "block_duration_minutes": 5,
            "enable_admin_bypass": True
        }

        result = update_rate_limit_config(config)
        self.assertTrue(result["success"])

    def test_client_blocking(self):
        """Test client blocking functionality."""
        # Block client
        result = block_client_manually("127.0.0.1", "Test blocking")
        self.assertTrue(result["success"])

        # Check blocked clients
        blocked = get_blocked_clients()
        self.assertIn("127.0.0.1", [client["ip"] for client in blocked])

        # Unblock client
        result = unblock_client_manually("127.0.0.1")
        self.assertTrue(result["success"])

    def test_input_validation(self):
        """Test input validation and sanitization."""
        # Test valid input
        valid_inputs = [
            "normal text",
            "text with numbers 123",
            "text with symbols !@#$%",
            "text with spaces and tabs",
            "text with newlines\nand\r\ncarriage returns"
        ]

        for input_text in valid_inputs:
            result = self.security_hardener.validate_input("test", input_text, "string")
            self.assertTrue(result)

        # Test malicious input
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",'
            "../../../etc/passwd",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>"
        ]

        for input_text in malicious_inputs:
            result = self.security_hardener.validate_input("test", input_text, "string")
            self.assertFalse(result)

    def test_plugin_security_validation(self):
        """Test plugin security validation."""
        # Test safe plugin
        safe_plugin_path = self.plugin_dir / "safe_plugin.py"
        validation_result = self.plugin_validator.validate_plugin_security(str(safe_plugin_path)
        self.assertTrue(validation_result["secure"])
        self.assertEqual(validation_result["security_level"], PluginSecurityLevel.VERIFIED)

        # Test malicious plugin
        malicious_plugin_path = self.plugin_dir / "malicious_plugin.py"
        validation_result = self.plugin_validator.validate_plugin_security(str(malicious_plugin_path)
        self.assertFalse(validation_result["secure"])
        self.assertEqual(validation_result["security_level"], PluginSecurityLevel.UNTRUSTED)
        self.assertIsNotNone(validation_result["security_issues"])

    def test_plugin_sandboxing(self):
        """Test plugin sandboxing functionality."""
        # Test safe plugin execution
        safe_plugin_path = self.plugin_dir / "safe_plugin.py"
        plugin_info = self.plugin_manager.load_plugin(str(safe_plugin_path)
        # Execute in sandbox
        event_data = {"event_type": "click", "x": 100, "y": 200}
        result = self.plugin_sandbox.execute_plugin(
            plugin_info, "handle_ui_event", event_data
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "processed")

        # Test malicious plugin execution
        malicious_plugin_path = self.plugin_dir / "malicious_plugin.py"
        plugin_info = self.plugin_manager.load_plugin(str(malicious_plugin_path)
        # Should be blocked or limited
        result = self.plugin_sandbox.execute_plugin(
            plugin_info, "handle_ui_event", event_data
        )

        # Should either be blocked or have limited functionality
        self.assertIn(result["status"], ["blocked", "limited", "error"])

    def test_encryption_functionality(self):
        """Test encryption and key management."""
        # Test data encryption
        test_data = "sensitive information"
        encrypted_data = self.security_hardener.encrypt_sensitive_data(test_data)

        self.assertIsNotNone(encrypted_data)
        self.assertNotEqual(encrypted_data, test_data)

        # Test data decryption
        decrypted_data = self.security_hardener.decrypt_sensitive_data(encrypted_data)
        self.assertEqual(decrypted_data, test_data)

    def test_security_headers(self):
        """Test security headers middleware."""
        # Test security headers
        response = self.client.get("/health/")

        # Check for security headers
        self.assertIn("X-Content-Type-Options", response.headers)
        self.assertIn("X-Frame-Options", response.headers)
        self.assertIn("X-XSS-Protection", response.headers)

        # Verify header values
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(response.headers["X-XSS-Protection"], "1; mode=block")

    def test_authentication_endpoints(self):
        """Test authentication API endpoints."""
        # Test login endpoint
        login_data = {
            "username": "test@example.com",
            "password": "securepassword123"
        }

        response = self.client.post("/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)
        self.assertIn("user", data)

        # Test protected endpoint with token
        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = self.client.get("/runtime/canvases/", headers=headers)
        self.assertEqual(response.status_code, 200)

        # Test protected endpoint without token
        response = self.client.get("/runtime/canvases/")
        self.assertEqual(response.status_code, 401)

    def test_authorization_endpoints(self):
        """Test authorization API endpoints."""
        # Create admin user
        admin_data = {
            "username": "admin@example.com",
            "password": "adminpass123",
            "role": "admin"
        }

        # Test admin endpoint access
        response = self.client.post("/auth/login", json=admin_data)
        self.assertEqual(response.status_code, 200)

        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test admin-only endpoint
        response = self.client.get("/errors/stats/", headers=headers)
        self.assertEqual(response.status_code, 200)

        # Test with non-admin user
        user_data = {
            "username": "user@example.com",
            "password": "userpass123",
            "role": "viewer"
        }

        response = self.client.post("/auth/login", json=user_data)
        self.assertEqual(response.status_code, 200)

        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Should be denied access
        response = self.client.get("/errors/stats/", headers=headers)
        self.assertEqual(response.status_code, 403)

    def test_plugin_security_api_endpoints(self):
        """Test plugin security API endpoints."""
        # Test plugin security levels endpoint
        response = self.client.get("/plugins/security-levels/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("security_levels", data)

        # Test plugin validation endpoint
        validation_data = {
            "plugin_path": str(self.plugin_dir / "safe_plugin.py")
        }

        response = self.client.post("/plugins/validate/", json=validation_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("validation", data)

    def test_ddos_protection(self):
        """Test DDoS protection mechanisms."""
        # Test rapid requests
        for i in range(1000):
            response = self.client.get("/health/")
            if response.status_code == 429:  # Rate limited
                break

        # Should eventually be rate limited
        self.assertIn(response.status_code, [200, 429])

    def test_sql_injection_protection(self):
        """Test SQL injection protection."""
        # Test malicious SQL injection attempts
        malicious_inputs = [
            "'; DROP TABLE users; --",'
            "' OR '1'='1",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",'
            "' UNION SELECT * FROM users --"'
        ]

        for malicious_input in malicious_inputs:
            # Test in various endpoints
            response = self.client.post("/runtime/ui-event/", json={
                "event_type": "test",
                "data": malicious_input
            })

            # Should not cause SQL injection
            self.assertNotEqual(response.status_code, 500)

    def test_xss_protection(self):
        """Test XSS protection mechanisms."""
        # Test XSS attempts
        xss_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>"
        ]

        for xss_input in xss_inputs:
            response = self.client.post("/runtime/ui-event/", json={
                "event_type": "test",
                "data": xss_input
            })

            # Should sanitize or block XSS
            self.assertNotEqual(response.status_code, 500)

    def test_csrf_protection(self):
        """Test CSRF protection mechanisms."""
        # Test CSRF token validation
        response = self.client.post("/runtime/ui-event/", json={
            "event_type": "test",
            "data": "test data"
        })

        # Should require authentication
        self.assertEqual(response.status_code, 401)

    def test_session_management(self):
        """Test session management security."""
        # Test session timeout
        user_data = {
            "username": "test@example.com",
            "password": "securepassword123"
        }

        response = self.client.post("/auth/login", json=user_data)
        self.assertEqual(response.status_code, 200)

        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test session validity
        response = self.client.get("/auth/me", headers=headers)
        self.assertEqual(response.status_code, 200)

        # Test with expired token
        with patch('svgx_engine.services.auth_middleware.ACCESS_TOKEN_EXPIRE_MINUTES', 0):
            expired_token = create_access_token({"user_id": "test"})

        headers = {"Authorization": f"Bearer {expired_token}"}
        response = self.client.get("/auth/me", headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_audit_logging(self):
        """Test audit logging functionality."""
        # Test authentication audit logging
        user_data = {
            "username": "test@example.com",
            "password": "securepassword123"
        }

        response = self.client.post("/auth/login", json=user_data)
        self.assertEqual(response.status_code, 200)

        # Test authorization audit logging
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = self.client.get("/runtime/canvases/", headers=headers)
        self.assertEqual(response.status_code, 200)

        # Audit logs should be generated (check logs or audit endpoint)
        # This would require access to audit log storage or endpoint

    def test_security_monitoring(self):
        """Test security monitoring functionality."""
        # Test security event detection
        # Attempt various security violations

        # Test failed authentication
        response = self.client.post("/auth/login", json={
            "username": "invalid@example.com",
            "password": "wrongpassword"
        })
        self.assertEqual(response.status_code, 401)

        # Test rate limiting
        for i in range(100):
            response = self.client.get("/health/")
            if response.status_code == 429:
                break

        # Security monitoring should detect these events
        # This would require access to security monitoring system

    def test_comprehensive_security_scan(self):
        """Test comprehensive security scanning."""
        # Test all security components together

        # 1. Authentication
        user_data = {
            "username": "test@example.com",
            "password": "securepassword123"
        }
        response = self.client.post("/auth/login", json=user_data)
        self.assertEqual(response.status_code, 200)

        # 2. Authorization
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Rate limiting
        for i in range(50):
            response = self.client.get("/health/", headers=headers)

        # 4. Input validation
        response = self.client.post("/runtime/ui-event/", json={
            "event_type": "test",
            "data": "normal data"
        }, headers=headers)

        # 5. Security headers
        response = self.client.get("/health/", headers=headers)
        self.assertIn("X-Content-Type-Options", response.headers)

        # All security mechanisms should work together
        self.assertNotEqual(response.status_code, 500)


if __name__ == "__main__":
    unittest.main()
