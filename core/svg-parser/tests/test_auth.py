"""
Unit tests for authentication functionality.

Tests cover:
- User registration
- Login/logout
- Token refresh
- Password changes
- User management
- Role-based access control
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.api.main
from core.models.database
from core.utils.auth
from core.services.database_service

client = TestClient(app)

@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "roles": ["viewer"]
    }

@pytest.fixture
def admin_user_data():
    """Admin user data."""
    return {
        "username": "admin",
        "email": "admin@example.com",
        "password": "adminpassword123",
        "full_name": "Admin User",
        "roles": ["admin", "viewer"]
    }

@pytest.fixture
def test_user_token():
    """Create a test user token."""
    token_user = TokenUser(
        id=str(uuid.uuid4()),
        username="testuser",
        roles=["viewer"],
        is_active=True
    )
    return create_access_token(token_user)

@pytest.fixture
def admin_token():
    """Create an admin token."""
    token_user = TokenUser(
        id=str(uuid.uuid4()),
        username="admin",
        roles=["admin", "viewer"],
        is_active=True
    )
    return create_access_token(token_user)

class TestUserRegistration:
    """Test user registration functionality."""
    
    def test_register_user_success(self, test_user_data):
        """Test successful user registration."""
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]
        assert data["roles"] == test_user_data["roles"]
        assert data["is_active"] is True
        assert "id" in data
    
    def test_register_user_duplicate_username(self, test_user_data):
        """Test registration with duplicate username."""
        # Register first user
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Try to register with same username
        duplicate_data = test_user_data.copy()
        duplicate_data["email"] = "different@example.com"
        response = client.post("/api/v1/auth/register", json=duplicate_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_register_user_duplicate_email(self, test_user_data):
        """Test registration with duplicate email."""
        # Register first user
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Try to register with same email
        duplicate_data = test_user_data.copy()
        duplicate_data["username"] = "differentuser"
        response = client.post("/api/v1/auth/register", json=duplicate_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_register_user_invalid_email(self, test_user_data):
        """Test registration with invalid email."""
        invalid_data = test_user_data.copy()
        invalid_data["email"] = "invalid-email"
        response = client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422
    
    def test_register_user_missing_fields(self):
        """Test registration with missing required fields."""
        incomplete_data = {
            "username": "testuser"
            # Missing email and password
        }
        response = client.post("/api/v1/auth/register", json=incomplete_data)
        assert response.status_code == 422

class TestUserLogin:
    """Test user login functionality."""
    
    def test_login_success(self, test_user_data):
        """Test successful login."""
        # Register user first
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "expires_in" in data
    
    def test_login_invalid_credentials(self, test_user_data):
        """Test login with invalid credentials."""
        # Register user first
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Try to login with wrong password
        login_data = {
            "username": test_user_data["username"],
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent user."""
        login_data = {
            "username": "nonexistent",
            "password": "password123"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

class TestTokenRefresh:
    """Test token refresh functionality."""
    
    def test_refresh_token_success(self, test_user_data):
        """Test successful token refresh."""
        # Register and login user
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login", data={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "expires_in" in data
    
    def test_refresh_token_invalid(self):
        """Test token refresh with invalid token."""
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid_token"})
        assert response.status_code == 401

class TestUserProfile:
    """Test user profile management."""
    
    def test_get_current_user_profile(self, test_user_data, test_user_token):
        """Test getting current user profile."""
        # Register user first
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Get profile
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
    
    def test_update_current_user_profile(self, test_user_data, test_user_token):
        """Test updating current user profile."""
        # Register user first
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Update profile
        update_data = {
            "full_name": "Updated Name",
            "email": "updated@example.com"
        }
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = client.put("/api/v1/auth/me", json=update_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["email"] == update_data["email"]
    
    def test_change_password(self, test_user_data, test_user_token):
        """Test changing password."""
        # Register user first
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Change password
        password_data = {
            "current_password": test_user_data["password"],
            "new_password": "newpassword123"
        }
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = client.post("/api/v1/auth/change-password", json=password_data, headers=headers)
        assert response.status_code == 200
        assert "Password changed successfully" in response.json()["message"]
    
    def test_change_password_wrong_current(self, test_user_data, test_user_token):
        """Test changing password with wrong current password."""
        # Register user first
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Try to change password with wrong current password
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123"
        }
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = client.post("/api/v1/auth/change-password", json=password_data, headers=headers)
        assert response.status_code == 400
        assert "Current password is incorrect" in response.json()["detail"]

class TestAdminEndpoints:
    """Test admin-only endpoints."""
    
    def test_list_users_admin_access(self, admin_token):
        """Test listing users with admin access."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/auth/users", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_list_users_non_admin_access(self, test_user_token):
        """Test listing users without admin access."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = client.get("/api/v1/auth/users", headers=headers)
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]
    
    def test_update_user_admin_access(self, admin_token):
        """Test updating user with admin access."""
        # First create a user to update
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User",
            "roles": ["viewer"]
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        user_id = register_response.json()["id"]
        
        # Update user
        update_data = {
            "full_name": "Updated Name",
            "roles": ["viewer", "editor"]
        }
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.put(f"/api/v1/auth/users/{user_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["roles"] == update_data["roles"]
    
    def test_update_user_non_admin_access(self, test_user_token):
        """Test updating user without admin access."""
        user_id = str(uuid.uuid4())
        update_data = {"full_name": "Updated Name"}
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = client.put(f"/api/v1/auth/users/{user_id}", json=update_data, headers=headers)
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

class TestAuthenticationMiddleware:
    """Test authentication middleware."""
    
    def test_protected_endpoint_with_token(self, test_user_token):
        """Test accessing protected endpoint with valid token."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
    
    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
    
    def test_protected_endpoint_with_invalid_token(self):
        """Test accessing protected endpoint with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401

class TestDatabaseService:
    """Test database service user methods."""
    
    @patch('arx_svg_parser.services.database_service.DatabaseService')
    def test_create_user(self, mock_db_service):
        """Test creating user through database service."""
        mock_service = Mock()
        mock_db_service.return_value = mock_service
        
        user_data = {
            "id": str(uuid.uuid4()),
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": "hashed_password",
            "full_name": "Test User",
            "roles": ["viewer"],
            "is_active": True
        }
        
        mock_service.create_user.return_value = User(**user_data)
        
        service = DatabaseService()
        user = service.create_user(user_data)
        
        assert user.username == user_data["username"]
        assert user.email == user_data["email"]
        mock_service.create_user.assert_called_once_with(user_data)
    
    @patch('arx_svg_parser.services.database_service.DatabaseService')
    def test_get_user_by_username(self, mock_db_service):
        """Test getting user by username."""
        mock_service = Mock()
        mock_db_service.return_value = mock_service
        
        user_data = {
            "id": str(uuid.uuid4()),
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": "hashed_password",
            "full_name": "Test User",
            "roles": ["viewer"],
            "is_active": True
        }
        
        mock_service.get_user_by_username.return_value = User(**user_data)
        
        service = DatabaseService()
        user = service.get_user_by_username("testuser")
        
        assert user.username == "testuser"
        mock_service.get_user_by_username.assert_called_once_with("testuser")

if __name__ == "__main__":
    pytest.main([__file__]) 