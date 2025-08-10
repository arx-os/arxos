import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from api.dependencies import (
    require_building_permission,
    require_building_read_permission,
    require_building_create_permission,
    require_building_update_permission,
    require_building_delete_permission,
    check_building_permission,
    get_user_permissions
)
from api.main import app


class TestBuildingPermissions:
    """Test cases for building permission enforcement."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request with state."""
        request = Mock()
        request.state = Mock()
        return request

    @pytest.fixture
    def mock_user(self):
        """Create a mock user with permissions."""
        return {
            "user_id": "test-user-123",
            "email": "test@example.com",
            "permissions": ["buildings:read"]
        }

    @pytest.fixture
    def test_client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    def test_require_building_permission_with_valid_permission(self, mock_request, mock_user):
        """Test permission requirement with valid permission."""
        # Arrange
        mock_request.state.permissions = ["buildings:read", "buildings:create"]

        with patch('api.dependencies.get_current_user', return_value=mock_user):
            # Act
            permission_func = require_building_permission("buildings:read")
            result = await permission_func(mock_request)

            # Assert
            assert result == mock_user

    def test_require_building_permission_with_invalid_permission(self, mock_request, mock_user):
        """Test permission requirement with invalid permission."""
        # Arrange
        mock_request.state.permissions = ["buildings:read"]

        with patch('api.dependencies.get_current_user', return_value=mock_user):
            # Act & Assert
            permission_func = require_building_permission("buildings:create")
            with pytest.raises(HTTPException) as exc_info:
                await permission_func(mock_request)

            assert exc_info.value.status_code == 403
            assert "buildings:create required" in exc_info.value.detail

    def test_require_building_permission_with_no_state_permissions(self, mock_request, mock_user):
        """Test permission requirement when request state has no permissions."""
        # Arrange
        mock_request.state.permissions = None
        mock_user["permissions"] = ["buildings:read"]

        with patch('api.dependencies.get_current_user', return_value=mock_user):
            # Act
            permission_func = require_building_permission("buildings:read")
            result = await permission_func(mock_request)

            # Assert
            assert result == mock_user

    def test_require_building_permission_with_string_permission(self, mock_request, mock_user):
        """Test permission requirement with string permission in state."""
        # Arrange
        mock_request.state.permissions = "buildings:read"

        with patch('api.dependencies.get_current_user', return_value=mock_user):
            # Act
            permission_func = require_building_permission("buildings:read")
            result = await permission_func(mock_request)

            # Assert
            assert result == mock_user

    def test_require_building_read_permission_success(self, mock_request, mock_user):
        """Test buildings:read permission requirement success."""
        # Arrange
        mock_request.state.permissions = ["buildings:read"]

        with patch('api.dependencies.get_current_user', return_value=mock_user):
            # Act
            result = await require_building_read_permission(mock_request)

            # Assert
            assert result == mock_user

    def test_require_building_read_permission_failure(self, mock_request, mock_user):
        """Test buildings:read permission requirement failure."""
        # Arrange
        mock_request.state.permissions = ["buildings:create"]

        with patch('api.dependencies.get_current_user', return_value=mock_user):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await require_building_read_permission(mock_request)

            assert exc_info.value.status_code == 403
            assert "buildings:read required" in exc_info.value.detail

    def test_require_building_create_permission_success(self, mock_request, mock_user):
        """Test buildings:create permission requirement success."""
        # Arrange
        mock_request.state.permissions = ["buildings:create"]

        with patch('api.dependencies.get_current_user', return_value=mock_user):
            # Act
            result = await require_building_create_permission(mock_request)

            # Assert
            assert result == mock_user

    def test_require_building_create_permission_failure(self, mock_request, mock_user):
        """Test buildings:create permission requirement failure."""
        # Arrange
        mock_request.state.permissions = ["buildings:read"]

        with patch('api.dependencies.get_current_user', return_value=mock_user):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await require_building_create_permission(mock_request)

            assert exc_info.value.status_code == 403
            assert "buildings:create required" in exc_info.value.detail

    def test_require_building_update_permission_success(self, mock_request, mock_user):
        """Test buildings:update permission requirement success."""
        # Arrange
        mock_request.state.permissions = ["buildings:update"]

        with patch('api.dependencies.get_current_user', return_value=mock_user):
            # Act
            result = await require_building_update_permission(mock_request)

            # Assert
            assert result == mock_user

    def test_require_building_update_permission_failure(self, mock_request, mock_user):
        """Test buildings:update permission requirement failure."""
        # Arrange
        mock_request.state.permissions = ["buildings:read"]

        with patch('api.dependencies.get_current_user', return_value=mock_user):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await require_building_update_permission(mock_request)

            assert exc_info.value.status_code == 403
            assert "buildings:update required" in exc_info.value.detail

    def test_require_building_delete_permission_success(self, mock_request, mock_user):
        """Test buildings:delete permission requirement success."""
        # Arrange
        mock_request.state.permissions = ["buildings:delete"]

        with patch('api.dependencies.get_current_user', return_value=mock_user):
            # Act
            result = await require_building_delete_permission(mock_request)

            # Assert
            assert result == mock_user

    def test_require_building_delete_permission_failure(self, mock_request, mock_user):
        """Test buildings:delete permission requirement failure."""
        # Arrange
        mock_request.state.permissions = ["buildings:read"]

        with patch('api.dependencies.get_current_user', return_value=mock_user):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await require_building_delete_permission(mock_request)

            assert exc_info.value.status_code == 403
            assert "buildings:delete required" in exc_info.value.detail

    def test_get_user_permissions_from_state(self, mock_request):
        """Test getting user permissions from request state."""
        # Arrange
        mock_request.state.permissions = ["buildings:read", "buildings:create"]

        # Act
        permissions = await get_user_permissions(mock_request)

        # Assert
        assert permissions == ["buildings:read", "buildings:create"]

    def test_get_user_permissions_from_user_object(self, mock_request, mock_user):
        """Test getting user permissions from user object when state is None."""
        # Arrange
        mock_request.state.permissions = None
        mock_user["permissions"] = ["buildings:read", "buildings:create"]

        with patch('api.dependencies.get_current_user', return_value=mock_user):
            # Act
            permissions = await get_user_permissions(mock_request)

            # Assert
            assert permissions == ["buildings:read", "buildings:create"]

    def test_get_user_permissions_string_conversion(self, mock_request):
        """Test converting string permissions to list."""
        # Arrange
        mock_request.state.permissions = "buildings:read"

        # Act
        permissions = await get_user_permissions(mock_request)

        # Assert
        assert permissions == ["buildings:read"]

    def test_get_user_permissions_exception_handling(self, mock_request):
        """Test handling exceptions when getting permissions."""
        # Arrange
        mock_request.state.permissions = None

        with patch('api.dependencies.get_current_user', side_effect=Exception("Auth error")):
            # Act
            permissions = await get_user_permissions(mock_request)

            # Assert
            assert permissions == []

    def test_check_building_permission_success(self, mock_request):
        """Test successful permission check."""
        # Arrange
        mock_request.state.permissions = ["buildings:read"]

        # Act
        result = await check_building_permission(mock_request, "buildings:read")

        # Assert
        assert result is True

    def test_check_building_permission_failure(self, mock_request):
        """Test failed permission check."""
        # Arrange
        mock_request.state.permissions = ["buildings:read"]

        # Act
        result = await check_building_permission(mock_request, "buildings:create")

        # Assert
        assert result is False

    def test_check_building_permission_exception_handling(self, mock_request):
        """Test handling exceptions during permission check."""
        # Arrange
        mock_request.state.permissions = None

        with patch('api.dependencies.get_current_user', side_effect=Exception("Auth error")):
            # Act
            result = await check_building_permission(mock_request, "buildings:read")

            # Assert
            assert result is False

    @pytest.mark.asyncio
    async def test_permission_dependencies_integration(self, test_client):
        """Test permission dependencies integration with FastAPI."""
        # This test would require a more complex setup with authentication middleware
        # For now, we'll test the basic structure

        # Arrange
        headers = {"Authorization": "Bearer invalid-token"}

        # Act & Assert - should get 401 or 403 depending on auth setup
        response = test_client.get("/api/v1/buildings/", headers=headers)
        assert response.status_code in [401, 403]

    def test_permission_error_messages(self, mock_request, mock_user):
        """Test that permission error messages are descriptive."""
        # Arrange
        mock_request.state.permissions = ["buildings:read"]

        with patch('api.dependencies.get_current_user', return_value=mock_user):
            # Act & Assert
            permission_func = require_building_permission("buildings:create")
            with pytest.raises(HTTPException) as exc_info:
                await permission_func(mock_request)

            error_detail = exc_info.value.detail
            assert "Permission denied" in error_detail
            assert "buildings:create required" in error_detail
            assert "for this operation" in error_detail

    def test_multiple_permission_requirements(self, mock_request, mock_user):
        """Test that multiple permission requirements work correctly."""
        # Arrange
        mock_request.state.permissions = ["buildings:read", "buildings:create", "buildings:update"]

        with patch('api.dependencies.get_current_user', return_value=mock_user):
            # Test read permission
            read_func = require_building_permission("buildings:read")
            read_result = await read_func(mock_request)
            assert read_result == mock_user

            # Test create permission
            create_func = require_building_permission("buildings:create")
            create_result = await create_func(mock_request)
            assert create_result == mock_user

            # Test update permission
            update_func = require_building_permission("buildings:update")
            update_result = await update_func(mock_request)
            assert update_result == mock_user

    def test_permission_denied_response_format(self, mock_request):
        """Test that permission denied responses are properly formatted."""
        from api.dependencies import format_permission_denied_response

        # Act
        response = format_permission_denied_response(
            permission="buildings:create",
            request=mock_request
        )

        # Assert
        assert response["success"] is False
        assert response["error"] is True
        assert response["error_code"] == "PERMISSION_DENIED"
        assert response["message"] == "Insufficient permissions"
        assert response["details"]["required_permission"] == "buildings:create"
        assert "timestamp" in response
