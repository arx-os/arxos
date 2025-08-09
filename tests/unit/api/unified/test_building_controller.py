"""
Unit Tests for Unified Building Controller

This module provides comprehensive unit tests for the unified building controller,
ensuring proper functionality, error handling, and validation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, Optional

from api.unified.controllers.building_controller import BuildingController
from application.unified.use_cases.building_use_cases import (
    CreateBuildingUseCase,
    GetBuildingUseCase,
    ListBuildingsUseCase,
    UpdateBuildingUseCase,
    DeleteBuildingUseCase
)
from application.unified.dto.building_dto import BuildingDTO
from api.unified.controllers.exceptions import ValidationError, NotFoundError


class TestBuildingController:
    """Test cases for BuildingController."""

    @pytest.fixture
def mock_use_cases(self):
        """Create mock use cases for testing."""
        return {
            'create': Mock(spec=CreateBuildingUseCase),
            'get': Mock(spec=GetBuildingUseCase),
            'list': Mock(spec=ListBuildingsUseCase),
            'update': Mock(spec=UpdateBuildingUseCase),
            'delete': Mock(spec=DeleteBuildingUseCase)
        }

    @pytest.fixture
def mock_validator(self):
        """Create mock validator for testing."""
        validator = Mock()
        validator.validate_create_request = AsyncMock()
        validator.validate_update_request = AsyncMock()
        validator.validate_building_id = AsyncMock()
        validator.validate_filters = AsyncMock()
        validator.validate_pagination = AsyncMock()
        return validator

    @pytest.fixture
def building_controller(self, mock_use_cases, mock_validator):
        """Create building controller with mocked dependencies."""
        with patch('api.unified.controllers.building_controller.BuildingValidator', return_value=mock_validator):
            controller = BuildingController(
                create_use_case=mock_use_cases['create'],
                get_use_case=mock_use_cases['get'],
                list_use_case=mock_use_cases['list'],
                update_use_case=mock_use_cases['update'],
                delete_use_case=mock_use_cases['delete']
            )
            return controller

    @pytest.fixture
def sample_building_dto(self):
        """Create sample building DTO for testing."""
        return BuildingDTO(
            id="building_123",
            name="Test Building",
            description="Test building description",
            building_type="commercial",
            status="active",
            address=None,
            coordinates=None,
            dimensions=None,
            year_built=2020,
            total_floors=5,
            owner_id="owner_123",
            tags=["test", "commercial"],
            metadata={"test": "value"},
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )

    @pytest.fixture
def sample_create_request(self):
        """Create sample create request data."""
        return {
            "name": "Test Building",
            "description": "Test building description",
            "building_type": "commercial",
            "status": "active",
            "address": {
                "street": "123 Test Street",
                "city": "Test City",
                "state": "TS",
                "postal_code": "12345",
                "country": "Test Country"
            },
            "year_built": 2020,
            "total_floors": 5,
            "owner_id": "owner_123",
            "tags": ["test", "commercial"],
            "metadata": {"test": "value"}
        }

    @pytest.fixture
def sample_update_request(self):
        """Create sample update request data."""
        return {
            "name": "Updated Building",
            "description": "Updated description",
            "status": "maintenance"
        }

    def test_entity_name_property(self, building_controller):
        """Test that entity_name property returns correct value."""
        assert building_controller.entity_name == "Building"

    @pytest.mark.asyncio
    async def test_create_building_success(self, building_controller, mock_use_cases,
                                         mock_validator, sample_create_request, sample_building_dto):
        """Test successful building creation."""
        # Arrange
        mock_validator.validate_create_request.return_value = sample_create_request
        mock_use_cases['create'].execute.return_value = sample_building_dto

        # Act
        result = await building_controller.create(sample_create_request)

        # Assert
        assert result == sample_building_dto
        mock_validator.validate_create_request.assert_called_once_with(sample_create_request)
        mock_use_cases['create'].execute.assert_called_once_with(sample_create_request)

    @pytest.mark.asyncio
    async def test_create_building_validation_error(self, building_controller, mock_validator,
                                                  sample_create_request):
        """Test building creation with validation error."""
        # Arrange
        mock_validator.validate_create_request.side_effect = ValidationError("Invalid data")

        # Act & Assert
        with pytest.raises(ValidationError):
            await building_controller.create(sample_create_request)

        mock_validator.validate_create_request.assert_called_once_with(sample_create_request)

    @pytest.mark.asyncio
    async def test_get_building_success(self, building_controller, mock_use_cases,
                                      mock_validator, sample_building_dto):
        """Test successful building retrieval."""
        # Arrange
        building_id = "building_123"
        mock_validator.validate_building_id.return_value = building_id
        mock_use_cases['get'].execute.return_value = sample_building_dto

        # Act
        result = await building_controller.get_by_id(building_id)

        # Assert
        assert result == sample_building_dto
        mock_validator.validate_building_id.assert_called_once_with(building_id)
        mock_use_cases['get'].execute.assert_called_once_with(building_id)

    @pytest.mark.asyncio
    async def test_get_building_not_found(self, building_controller, mock_use_cases,
                                        mock_validator):
        """Test building retrieval when building not found."""
        # Arrange
        building_id = "building_123"
        mock_validator.validate_building_id.return_value = building_id
        mock_use_cases['get'].execute.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError, match="Building not found"):
            await building_controller.get_by_id(building_id)

    @pytest.mark.asyncio
    async def test_get_building_validation_error(self, building_controller, mock_validator):
        """Test building retrieval with validation error."""
        # Arrange
        building_id = "invalid_id"
        mock_validator.validate_building_id.side_effect = ValidationError("Invalid ID")

        # Act & Assert
        with pytest.raises(ValidationError):
            await building_controller.get_by_id(building_id)

    @pytest.mark.asyncio
    async def test_get_all_buildings_success(self, building_controller, mock_use_cases,
                                           mock_validator, sample_building_dto):
        """Test successful building list retrieval."""
        # Arrange
        filters = {"status": "active"}
        pagination = {"page": 1, "page_size": 10}
        building_dtos = [sample_building_dto]

        mock_validator.validate_filters.return_value = filters
        mock_validator.validate_pagination.return_value = pagination
        mock_use_cases['list'].execute.return_value = building_dtos

        # Act
        result = await building_controller.get_all(filters, pagination)

        # Assert
        assert result == building_dtos
        mock_validator.validate_filters.assert_called_once_with(filters)
        mock_validator.validate_pagination.assert_called_once_with(pagination)
        mock_use_cases['list'].execute.assert_called_once_with(filters, pagination)

    @pytest.mark.asyncio
    async def test_get_all_buildings_validation_error(self, building_controller,
                                                    mock_validator):
        """Test building list retrieval with validation error."""
        # Arrange
        filters = {"invalid": "filter"}
        pagination = {"page": 1, "page_size": 10}
        mock_validator.validate_filters.side_effect = ValidationError("Invalid filters")

        # Act & Assert
        with pytest.raises(ValidationError):
            await building_controller.get_all(filters, pagination)

    @pytest.mark.asyncio
    async def test_update_building_success(self, building_controller, mock_use_cases,
                                         mock_validator, sample_update_request, sample_building_dto):
        """Test successful building update."""
        # Arrange
        building_id = "building_123"
        mock_validator.validate_building_id.return_value = building_id
        mock_validator.validate_update_request.return_value = sample_update_request
        mock_use_cases['update'].execute.return_value = sample_building_dto

        # Act
        result = await building_controller.update(building_id, sample_update_request)

        # Assert
        assert result == sample_building_dto
        mock_validator.validate_building_id.assert_called_once_with(building_id)
        mock_validator.validate_update_request.assert_called_once_with(sample_update_request)
        mock_use_cases['update'].execute.assert_called_once_with(building_id, sample_update_request)

    @pytest.mark.asyncio
    async def test_update_building_not_found(self, building_controller, mock_use_cases,
                                           mock_validator, sample_update_request):
        """Test building update when building not found."""
        # Arrange
        building_id = "building_123"
        mock_validator.validate_building_id.return_value = building_id
        mock_validator.validate_update_request.return_value = sample_update_request
        mock_use_cases['update'].execute.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError, match="Building not found"):
            await building_controller.update(building_id, sample_update_request)

    @pytest.mark.asyncio
    async def test_delete_building_success(self, building_controller, mock_use_cases,
                                         mock_validator):
        """Test successful building deletion."""
        # Arrange
        building_id = "building_123"
        mock_validator.validate_building_id.return_value = building_id
        mock_use_cases['delete'].execute.return_value = True

        # Act
        result = await building_controller.delete(building_id)

        # Assert
        assert result is True
        mock_validator.validate_building_id.assert_called_once_with(building_id)
        mock_use_cases['delete'].execute.assert_called_once_with(building_id)

    @pytest.mark.asyncio
    async def test_delete_building_not_found(self, building_controller, mock_use_cases,
                                           mock_validator):
        """Test building deletion when building not found."""
        # Arrange
        building_id = "building_123"
        mock_validator.validate_building_id.return_value = building_id
        mock_use_cases['delete'].execute.return_value = False

        # Act & Assert
        with pytest.raises(NotFoundError, match="Building not found"):
            await building_controller.delete(building_id)

    @pytest.mark.asyncio
    async def test_validate_create_request(self, building_controller, mock_validator,
                                         sample_create_request):
        """Test create request validation."""
        # Arrange
        mock_validator.validate_create_request.return_value = sample_create_request

        # Act
        result = await building_controller._validate_create_request(sample_create_request)

        # Assert
        assert result == sample_create_request
        mock_validator.validate_create_request.assert_called_once_with(sample_create_request)

    @pytest.mark.asyncio
    async def test_validate_update_request(self, building_controller, mock_validator,
                                         sample_update_request):
        """Test update request validation."""
        # Arrange
        mock_validator.validate_update_request.return_value = sample_update_request

        # Act
        result = await building_controller._validate_update_request(sample_update_request)

        # Assert
        assert result == sample_update_request
        mock_validator.validate_update_request.assert_called_once_with(sample_update_request)

    @pytest.mark.asyncio
    async def test_validate_entity_id(self, building_controller, mock_validator):
        """Test entity ID validation."""
        # Arrange
        building_id = "building_123"
        mock_validator.validate_building_id.return_value = building_id

        # Act
        result = await building_controller._validate_entity_id(building_id)

        # Assert
        assert result == building_id
        mock_validator.validate_building_id.assert_called_once_with(building_id)

    @pytest.mark.asyncio
    async def test_validate_filters(self, building_controller, mock_validator):
        """Test filters validation."""
        # Arrange
        filters = {"status": "active"}
        mock_validator.validate_filters.return_value = filters

        # Act
        result = await building_controller._validate_filters(filters)

        # Assert
        assert result == filters
        mock_validator.validate_filters.assert_called_once_with(filters)

    @pytest.mark.asyncio
    async def test_validate_pagination(self, building_controller, mock_validator):
        """Test pagination validation."""
        # Arrange
        pagination = {"page": 1, "page_size": 10}
        mock_validator.validate_pagination.return_value = pagination

        # Act
        result = await building_controller._validate_pagination(pagination)

        # Assert
        assert result == pagination
        mock_validator.validate_pagination.assert_called_once_with(pagination)
