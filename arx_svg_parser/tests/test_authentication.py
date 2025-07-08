"""
Comprehensive tests for authentication and security features.

Tests include:
- JWT token creation and validation
- Password hashing and verification
- Role-based access control
- User management endpoints
- Security middleware
- Audit logging
"""

import pytest
import jwt
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from utils.auth import (
    create_access_token, create_refresh_token, decode_token,
    hash_password, verify_password, validate_password_strength,
    TokenUser, revoke_token, is_token_revoked
)
from services.access_control import access_control_service, UserRole
from middleware.auth import AuthenticationMiddleware, RoleBasedAccessMiddleware
from middleware.security import SecurityMiddleware, PasswordSecurity

class TestJWTAuthentication:
    """Test JWT authentication functionality."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        user = TokenUser(
            id="test-user-123",
            username="testuser",
            roles=["viewer"],
            is_active=True
        )
        
        token = create_access_token(user)
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify token
        payload = decode_token(token)
        assert payload["id"] == "test-user-123"
        assert payload["username"] == "testuser"
        assert payload["type"] == "access"
        assert "jti" in payload
        assert "iat" in payload
        assert "exp" in payload
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user = TokenUser(
            id="test-user-123",
            username="testuser",
            roles=["viewer"],
            is_active=True
        )
        
        token = create_refresh_token(user)
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify token
        payload = decode_token(token)
        assert payload["id"] == "test-user-123"
        assert payload["username"] == "testuser"
        assert payload["type"] == "refresh"
        assert "jti" in payload
        assert "iat" in payload
        assert "exp" in payload
    
    def test_token_expiration(self):
        """Test token expiration."""
        user = TokenUser(
            id="test-user-123",
            username="testuser",
            roles=["viewer"],
            is_active=True
        )
        
        # Create token with short expiration
        token = create_access_token(user, expires_delta=timedelta(seconds=1))
        
        # Token should be valid initially
        payload = decode_token(token)
        assert payload["id"] == "test-user-123"
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Token should be expired
        with pytest.raises(Exception):
            decode_token(token)
    
    def test_token_revocation(self):
        """Test token revocation."""
        user = TokenUser(
            id="test-user-123",
            username="testuser",
            roles=["viewer"],
            is_active=True
        )
        
        token = create_access_token(user)
        payload = decode_token(token)
        jti = payload["jti"]
        
        # Token should be valid initially
        assert not is_token_revoked(jti)
        
        # Revoke token
        revoke_token(jti)
        assert is_token_revoked(jti)
        
        # Token should be invalid after revocation
        with pytest.raises(Exception):
            decode_token(token)

class TestPasswordSecurity:
    """Test password security features."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "SecurePassword123!"
        
        # Hash password
        hashed = hash_password(password)
        assert hashed != password
        assert isinstance(hashed, str)
        
        # Verify password
        assert verify_password(password, hashed)
        assert not verify_password("wrongpassword", hashed)
    
    def test_password_strength_validation(self):
        """Test password strength validation."""
        # Valid password
        valid_password = "SecurePassword123!"
        is_valid, message = validate_password_strength(valid_password)
        assert is_valid
        assert "meets strength requirements" in message
        
        # Too short
        short_password = "Abc1!"
        is_valid, message = validate_password_strength(short_password)
        assert not is_valid
        assert "at least 8 characters" in message
        
        # No uppercase
        no_upper = "securepassword123!"
        is_valid, message = validate_password_strength(no_upper)
        assert not is_valid
        assert "uppercase letter" in message
        
        # No lowercase
        no_lower = "SECUREPASSWORD123!"
        is_valid, message = validate_password_strength(no_lower)
        assert not is_valid
        assert "lowercase letter" in message
        
        # No digit
        no_digit = "SecurePassword!"
        is_valid, message = validate_password_strength(no_digit)
        assert not is_valid
        assert "digit" in message
        
        # No special character
        no_special = "SecurePassword123"
        is_valid, message = validate_password_strength(no_special)
        assert not is_valid
        assert "special character" in message
    
    def test_secure_password_generation(self):
        """Test secure password generation."""
        password = PasswordSecurity.generate_secure_password(16)
        assert len(password) == 16
        assert isinstance(password, str)
        
        # Check password strength
        is_valid, message = validate_password_strength(password)
        assert is_valid

class TestRoleBasedAccessControl:
    """Test role-based access control."""
    
    def test_role_hierarchy(self):
        """Test role hierarchy and inheritance."""
        # Test viewer role permissions
        viewer_permissions = access_control_service._get_role_permissions("viewer")
        assert len(viewer_permissions) > 0
        
        # Test editor role permissions (should inherit from viewer)
        editor_permissions = access_control_service._get_role_permissions("editor")
        assert len(editor_permissions) > len(viewer_permissions)
        
        # Test admin role permissions (should inherit from editor)
        admin_permissions = access_control_service._get_role_permissions("admin")
        assert len(admin_permissions) > len(editor_permissions)
    
    def test_permission_checking(self):
        """Test permission checking functionality."""
        # Create test user
        user_result = access_control_service.create_user(
            username="testuser",
            email="test@example.com",
            primary_role=UserRole.VIEWER
        )
        assert user_result["success"]
        user_id = user_result["user_id"]
        
        # Test viewer permissions
        assert access_control_service.check_permission(user_id, "symbol", "read")
        assert not access_control_service.check_permission(user_id, "symbol", "create")
        
        # Test admin permissions
        admin_result = access_control_service.create_user(
            username="adminuser",
            email="admin@example.com",
            primary_role=UserRole.ADMIN
        )
        admin_id = admin_result["user_id"]
        
        assert access_control_service.check_permission(admin_id, "symbol", "read")
        assert access_control_service.check_permission(admin_id, "symbol", "create")
        assert access_control_service.check_permission(admin_id, "user", "manage")
    
    def test_audit_logging(self):
        """Test audit logging functionality."""
        # Log an audit event
        access_control_service.log_audit_event(
            user_id="test-user-123",
            action="test_action",
            resource_type="test_resource",
            resource_id="test-123",
            details={"test": "data"},
            ip_address="127.0.0.1",
            user_agent="test-agent",
            success=True
        )
        
        # Retrieve audit logs
        logs = access_control_service.get_audit_logs(
            user_id="test-user-123",
            action="test_action",
            limit=10
        )
        
        assert len(logs) > 0
        assert logs[0]["user_id"] == "test-user-123"
        assert logs[0]["action"] == "test_action"
        assert logs[0]["success"] is True

class TestUserManagement:
    """Test user management functionality."""
    
    def test_user_creation(self):
        """Test user creation with roles."""
        # Create user with viewer role
        result = access_control_service.create_user(
            username="newuser",
            email="newuser@example.com",
            primary_role=UserRole.VIEWER
        )
        
        assert result["success"]
        assert "user_id" in result
        
        # Verify user was created
        user_data = access_control_service.get_user(result["user_id"])
        assert user_data["success"]
        assert user_data["user"]["username"] == "newuser"
        assert user_data["user"]["primary_role"] == "viewer"
    
    def test_user_role_assignment(self):
        """Test user role assignment."""
        # Create user with multiple roles
        result = access_control_service.create_user(
            username="multiroleuser",
            email="multirole@example.com",
            primary_role=UserRole.EDITOR,
            secondary_roles=[UserRole.VIEWER, UserRole.MAINTENANCE]
        )
        
        assert result["success"]
        user_id = result["user_id"]
        
        # Get user permissions
        permissions = access_control_service._get_user_permissions(user_id)
        assert len(permissions) > 0
        
        # Should have editor permissions
        editor_perms = [p for p in permissions if p["action"] == "create"]
        assert len(editor_perms) > 0
    
    def test_session_management(self):
        """Test user session management."""
        user_id = "test-user-123"
        token = "test-token-123"
        
        # Create session
        session_id = access_control_service.create_session(
            user_id=user_id,
            token=token,
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        
        assert session_id is not None
        
        # Validate session
        session_data = access_control_service.validate_session(session_id)
        assert session_data["valid"]
        assert session_data["user_id"] == user_id
        
        # Revoke session
        success = access_control_service.revoke_session(session_id)
        assert success
        
        # Session should be invalid after revocation
        session_data = access_control_service.validate_session(session_id)
        assert not session_data["valid"]

class TestSecurityMiddleware:
    """Test security middleware functionality."""
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        rate_limiter = RateLimiter(requests_per_minute=5)
        
        # Should allow requests initially
        for i in range(5):
            assert rate_limiter.is_allowed("test-ip")
        
        # Should block after limit
        assert not rate_limiter.is_allowed("test-ip")
        
        # Check remaining requests
        assert rate_limiter.get_remaining_requests("test-ip") == 0
    
    def test_ip_filtering(self):
        """Test IP filtering functionality."""
        # Test with allowed IPs
        security_middleware = SecurityMiddleware(
            app=None,
            allowed_ips=["127.0.0.1", "192.168.1.1"]
        )
        
        assert security_middleware._check_ip_access("127.0.0.1")
        assert not security_middleware._check_ip_access("10.0.0.1")
        
        # Test with blocked IPs
        security_middleware = SecurityMiddleware(
            app=None,
            blocked_ips=["192.168.1.100"]
        )
        
        assert security_middleware._check_ip_access("127.0.0.1")
        assert not security_middleware._check_ip_access("192.168.1.100")
    
    def test_request_validation(self):
        """Test request validation."""
        security_middleware = SecurityMiddleware(app=None)
        
        # Test suspicious user agent
        suspicious_ua = "python-requests/2.25.1"
        assert security_middleware._is_suspicious_user_agent(suspicious_ua)
        
        # Test normal user agent
        normal_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        assert not security_middleware._is_suspicious_user_agent(normal_ua)

class TestAuthenticationMiddleware:
    """Test authentication middleware functionality."""
    
    def test_token_extraction(self):
        """Test token extraction from request."""
        middleware = AuthenticationMiddleware(app=None)
        
        # Mock request with valid token
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer test-token-123"}
        
        token = middleware._extract_token(mock_request)
        assert token == "test-token-123"
        
        # Mock request without token
        mock_request.headers = {}
        token = middleware._extract_token(mock_request)
        assert token is None
        
        # Mock request with invalid format
        mock_request.headers = {"Authorization": "Invalid test-token-123"}
        token = middleware._extract_token(mock_request)
        assert token is None
    
    def test_path_exclusion(self):
        """Test path exclusion from authentication."""
        middleware = AuthenticationMiddleware(app=None)
        
        # Test excluded paths
        assert middleware._is_excluded_path("/auth/login")
        assert middleware._is_excluded_path("/docs")
        assert middleware._is_excluded_path("/openapi.json")
        
        # Test non-excluded paths
        assert not middleware._is_excluded_path("/api/v1/symbols")
        assert not middleware._is_excluded_path("/users/profile")

class TestIntegration:
    """Integration tests for authentication system."""
    
    @pytest.fixture
    def test_client(self):
        """Create test client with authentication."""
        from main import app
        return TestClient(app)
    
    def test_full_authentication_flow(self, test_client):
        """Test complete authentication flow."""
        # Register user
        register_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "full_name": "Test User"
        }
        
        response = test_client.post("/auth/register", json=register_data)
        assert response.status_code == 200
        
        # Login
        login_data = {
            "username": "testuser",
            "password": "SecurePassword123!"
        }
        
        response = test_client.post("/auth/login", data=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        
        # Use token for authenticated request
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        response = test_client.get("/auth/me", headers=headers)
        assert response.status_code == 200
        
        user_data = response.json()
        assert user_data["username"] == "testuser"
        assert user_data["email"] == "test@example.com"
    
    def test_role_based_access(self, test_client):
        """Test role-based access control."""
        # Create admin user
        admin_data = {
            "username": "adminuser",
            "email": "admin@example.com",
            "password": "SecurePassword123!",
            "roles": ["admin"]
        }
        
        response = test_client.post("/auth/register", json=admin_data)
        assert response.status_code == 200
        
        # Login as admin
        login_data = {
            "username": "adminuser",
            "password": "SecurePassword123!"
        }
        
        response = test_client.post("/auth/login", data=login_data)
        assert response.status_code == 200
        
        data = response.json()
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        # Admin should be able to access user management
        response = test_client.get("/auth/users", headers=headers)
        assert response.status_code == 200
        
        # Create regular user
        user_data = {
            "username": "regularuser",
            "email": "regular@example.com",
            "password": "SecurePassword123!"
        }
        
        response = test_client.post("/auth/register", json=user_data)
        assert response.status_code == 200
        
        # Login as regular user
        login_data = {
            "username": "regularuser",
            "password": "SecurePassword123!"
        }
        
        response = test_client.post("/auth/login", data=login_data)
        assert response.status_code == 200
        
        data = response.json()
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        # Regular user should not be able to access user management
        response = test_client.get("/auth/users", headers=headers)
        assert response.status_code == 403

if __name__ == "__main__":
    pytest.main([__file__]) 