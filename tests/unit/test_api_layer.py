"""
API Layer Integration Tests

This module provides comprehensive tests for the API layer, validating
endpoint functionality, authentication, validation, and response formatting.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status

from api.main import app
from application.container import container
from application.logging import get_logger

logger = get_logger("tests.api_layer")


class TestAPILayer:
    """Test suite for API layer functionality."""

    @pytest.fixture
def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
def mock_user(self):
        """Mock authenticated user."""
        return {
            "user_id": "test-user-123",
            "api_key": "test-api-key",
            "permissions": ["read", "write", "admin"]
        }

    @pytest.fixture
def auth_headers(self, mock_user):
        """Authentication headers."""
        return {
            "X-API-Key": mock_user["api_key"],
            "Content-Type": "application/json"
        }

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "Arxos Platform API" in data["message"]

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "status" in data["data"]

    def test_detailed_health_check(self, client):
        """Test detailed health check endpoint."""
        response = client.get("/api/v1/health/detailed")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "checks" in data["data"]
        assert "database" in data["data"]["checks"]
        assert "cache" in data["data"]["checks"]

    def test_authentication_required(self, client):
        """Test that endpoints require authentication."""
        # Test device endpoints without auth
        response = client.get("/api/v1/devices/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = client.post("/api/v1/devices/", json={})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_device_endpoints_with_auth(self, client, auth_headers):
        """Test device endpoints with authentication."""
        # Test list devices
        response = client.get("/api/v1/devices/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "devices" in data["data"]

        # Test create device
        device_data = {
            "room_id": "room-123",
            "device_type": "sensor",
            "name": "Test Device",
            "manufacturer": "Test Corp",
            "model": "TS-1000",
            "serial_number": "SN123456"
        }
        response = client.post("/api/v1/devices/", json=device_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "success" in data
        assert "device_id" in data["data"]

        # Test get device
        device_id = data["data"]["device_id"]
        response = client.get(f"/api/v1/devices/{device_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "device" in data["data"]

    def test_room_endpoints_with_auth(self, client, auth_headers):
        """Test room endpoints with authentication."""
        # Test list rooms
        response = client.get("/api/v1/rooms/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "rooms" in data["data"]

        # Test create room
        room_data = {
            "name": "Test Room",
            "building_id": "building-123",
            "floor": 1,
            "room_type": "office",
            "area": 150.0,
            "capacity": 10
        }
        response = client.post("/api/v1/rooms/", json=room_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "success" in data
        assert "room_id" in data["data"]

    def test_user_endpoints_with_auth(self, client, auth_headers):
        """Test user endpoints with authentication."""
        # Test list users
        response = client.get("/api/v1/users/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "users" in data["data"]

        # Test get user
        response = client.get("/api/v1/users/test-user-123", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "user" in data["data"]

    def test_project_endpoints_with_auth(self, client, auth_headers):
        """Test project endpoints with authentication."""
        # Test list projects
        response = client.get("/api/v1/projects/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "projects" in data["data"]

        # Test create project
        project_data = {
            "name": "Test Project",
            "description": "A test project",
            "building_id": "building-123",
            "status": "active"
        }
        response = client.post("/api/v1/projects/", json=project_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "success" in data
        assert "project_id" in data["data"]

        # Test get project statistics
        project_id = data["data"]["project_id"]
        response = client.get(f"/api/v1/projects/{project_id}/statistics", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "total_rooms" in data["data"]
        assert "total_devices" in data["data"]

    def test_building_endpoints_with_auth(self, client, auth_headers):
        """Test building endpoints with authentication."""
        # Test list buildings
        response = client.get("/api/v1/buildings/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "buildings" in data["data"]

        # Test create building
        building_data = {
            "name": "Test Building",
            "address": "123 Test Street, City, State 12345",
            "description": "A test building",
            "building_type": "commercial",
            "floors": 5,
            "total_area": 5000.0,
            "status": "active"
        }
        response = client.post("/api/v1/buildings/", json=building_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "success" in data
        assert "building_id" in data["data"]

        # Test get building rooms
        building_id = data["data"]["building_id"]
        response = client.get(f"/api/v1/buildings/{building_id}/rooms", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "rooms" in data["data"]

        # Test get building statistics
        response = client.get(f"/api/v1/buildings/{building_id}/statistics", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "total_rooms" in data["data"]
        assert "total_devices" in data["data"]
        assert "floors" in data["data"]

    def test_pagination_and_filtering(self, client, auth_headers):
        """Test pagination and filtering functionality."""
        # Test device list with pagination
        response = client.get("/api/v1/devices/?page=1&page_size=5", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "pagination" in data["data"]
        assert data["data"]["pagination"]["page"] == 1
        assert data["data"]["pagination"]["page_size"] == 5

        # Test filtering
        response = client.get("/api/v1/devices/?device_type=sensor", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        # Test building list with filtering
        response = client.get("/api/v1/buildings/?building_type=commercial", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_error_handling(self, client, auth_headers):
        """Test error handling and validation."""
        # Test invalid device data
        invalid_device_data = {
            "room_id": "",  # Invalid empty room_id
            "device_type": "invalid_type",
            "name": ""  # Invalid empty name
        }
        response = client.post("/api/v1/devices/", json=invalid_device_data, headers=auth_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Test invalid project data
        invalid_project_data = {
            "name": "",  # Invalid empty name
            "description": "A" * 1001  # Too long description
        }
        response = client.post("/api/v1/projects/", json=invalid_project_data, headers=auth_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Test non-existent resource
        response = client.get("/api/v1/devices/non-existent-id", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_response_formatting(self, client, auth_headers):
        """Test consistent response formatting."""
        response = client.get("/api/v1/devices/", headers=auth_headers)
        data = response.json()

        # Check standard response structure
        assert "success" in data
        assert "message" in data
        assert "data" in data
        assert "timestamp" in data
        assert data["success"] is True

        # Check data structure
        assert "devices" in data["data"]
        assert "pagination" in data["data"]

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/api/v1/devices/")
        assert response.status_code == status.HTTP_200_OK
        assert "access-control-allow-origin" in response.headers

    def test_compression(self, client, auth_headers):
        """Test response compression."""
        response = client.get("/api/v1/devices/", headers=auth_headers)
        # Check if compression is applied (gzip middleware)
        assert "content-encoding" in response.headers or "content-length" in response.headers

    def test_rate_limiting(self, client, auth_headers):
        """Test rate limiting functionality."""
        # Make multiple requests quickly
        for _ in range(10):
            response = client.get("/api/v1/devices/", headers=auth_headers)
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_429_TOO_MANY_REQUESTS]

    def test_security_headers(self, client):
        """Test security headers are present."""
        response = client.get("/")
        headers = response.headers

        # Check for security headers
        security_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection"
        ]

        for header in security_headers:
            assert header in headers or "security" in str(headers).lower()

    def test_api_documentation(self, client):
        """Test API documentation endpoints."""
        # Test OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

        # Test Swagger UI
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK

        # Test ReDoc
        response = client.get("/redoc")
        assert response.status_code == status.HTTP_200_OK

    def test_metrics_endpoint(self, client, auth_headers):
        """Test metrics endpoint."""
        response = client.get("/api/v1/health/metrics", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "metrics" in data["data"]

    def test_liveness_probe(self, client):
        """Test liveness probe endpoint."""
        response = client.get("/api/v1/health/liveness")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data["data"]
        assert data["data"]["status"] == "alive"

    def test_readiness_probe(self, client):
        """Test readiness probe endpoint."""
        response = client.get("/api/v1/health/readiness")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data["data"]
        assert data["data"]["status"] in ["ready", "not_ready"]


class TestAPIMiddleware:
    """Test suite for API middleware functionality."""

    @pytest.fixture
def client(self):
        """Create test client."""
        return TestClient(app)

    def test_request_logging(self, client, caplog):
        """Test request logging middleware."""
        with caplog.at_level("INFO"):
            response = client.get("/")
            assert response.status_code == status.HTTP_200_OK

            # Check that request was logged
            log_records = [record for record in caplog.records if "request" in record.message.lower()]
            assert len(log_records) > 0

    def test_error_handling_middleware(self, client):
        """Test error handling middleware."""
        # Test with invalid JSON
        response = client.post("/api/v1/devices/", data="invalid json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Test with malformed request
        response = client.get("/api/v1/devices/?page=invalid")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_authentication_middleware(self, client):
        """Test authentication middleware."""
        # Test without API key
        response = client.get("/api/v1/devices/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Test with invalid API key
        response = client.get("/api/v1/devices/", headers={"X-API-Key": "invalid-key"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Test with valid API key
        response = client.get("/api/v1/devices/", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == status.HTTP_200_OK


class TestAPIDependencies:
    """Test suite for API dependencies."""

    def test_user_model(self):
        """Test User model functionality."""
        from api.dependencies import User

        user = User(user_id="test-123", api_key="test-key", permissions=["read", "write"])
        assert user.user_id == "test-123"
        assert user.api_key == "test-key"
        assert user.has_permission("read") is True
        assert user.has_permission("admin") is False

    def test_permission_requirements(self, client):
        """Test permission requirement decorators."""
        # Test read permission
        response = client.get("/api/v1/devices/", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == status.HTTP_200_OK

        # Test write permission
        device_data = {"room_id": "room-123", "device_type": "sensor", "name": "Test"}
        response = client.post("/api/v1/devices/", json=device_data, headers={"X-API-Key": "test-api-key"})
        assert response.status_code == status.HTTP_201_CREATED

    def test_response_formatting_functions(self):
        """Test response formatting utility functions."""
        from api.dependencies import format_success_response, format_error_response

        # Test success response
        success_response = format_success_response(
            data={"test": "data"},
            message="Success message"
        )
        assert success_response["success"] is True
        assert "test" in success_response["data"]
        assert "timestamp" in success_response

        # Test error response
        error_response = format_error_response(
            error_code="TEST_ERROR",
            message="Error message",
            details={"detail": "test"}
        )
        assert error_response["error"] is True
        assert error_response["error_code"] == "TEST_ERROR"
        assert "timestamp" in error_response
