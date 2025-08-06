"""
Tests for Application Layer Components

This module contains tests for the application layer components including
use cases, application services, and DTOs.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from domain.entities import Building, Floor
from domain.value_objects import (
    BuildingId,
    FloorId,
    Address,
    BuildingStatus,
    Coordinates,
    Dimensions,
)
from domain.repositories import BuildingRepository
from application.dto.building_dto import (
    CreateBuildingRequest,
    CreateBuildingResponse,
    UpdateBuildingRequest,
    UpdateBuildingResponse,
    GetBuildingResponse,
    ListBuildingsResponse,
    DeleteBuildingResponse,
)
from application.use_cases.building_use_cases import (
    CreateBuildingUseCase,
    UpdateBuildingUseCase,
    GetBuildingUseCase,
    ListBuildingsUseCase,
    DeleteBuildingUseCase,
)
from application.services.building_service import BuildingApplicationService


class TestBuildingDTOs:
    """Test building DTOs."""

    def test_create_building_request(self):
        """Test CreateBuildingRequest DTO."""
        request = CreateBuildingRequest(
            name="Test Building",
            address="123 Test St, Test City, TS 12345",
            description="A test building",
            coordinates={"latitude": 40.7128, "longitude": -74.0060},
            dimensions={"width": 100.0, "length": 200.0, "height": 50.0},
            created_by="test_user",
            metadata={"type": "office"},
        )

        assert request.name == "Test Building"
        assert request.address == "123 Test St, Test City, TS 12345"
        assert request.description == "A test building"
        assert request.coordinates == {"latitude": 40.7128, "longitude": -74.0060}
        assert request.dimensions == {"width": 100.0, "length": 200.0, "height": 50.0}
        assert request.created_by == "test_user"
        assert request.metadata == {"type": "office"}

    def test_create_building_response(self):
        """Test CreateBuildingResponse DTO."""
        response = CreateBuildingResponse(
            success=True,
            building_id="test-id",
            message="Building created successfully",
            created_at=datetime.utcnow(),
        )

        assert response.success is True
        assert response.building_id == "test-id"
        assert response.message == "Building created successfully"
        assert response.created_at is not None

    def test_update_building_request(self):
        """Test UpdateBuildingRequest DTO."""
        request = UpdateBuildingRequest(
            building_id="test-id",
            name="Updated Building",
            status="operational",
            updated_by="test_user",
        )

        assert request.building_id == "test-id"
        assert request.name == "Updated Building"
        assert request.status == "operational"
        assert request.updated_by == "test_user"

    def test_get_building_response(self):
        """Test GetBuildingResponse DTO."""
        building_data = {
            "id": "test-id",
            "name": "Test Building",
            "address": "123 Test St",
            "status": "planned",
        }

        response = GetBuildingResponse(success=True, building=building_data)

        assert response.success is True
        assert response.building == building_data


class TestBuildingUseCases:
    """Test building use cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_repository = Mock(spec=BuildingRepository)
        self.create_use_case = CreateBuildingUseCase(self.mock_repository)
        self.update_use_case = UpdateBuildingUseCase(self.mock_repository)
        self.get_use_case = GetBuildingUseCase(self.mock_repository)
        self.list_use_case = ListBuildingsUseCase(self.mock_repository)
        self.delete_use_case = DeleteBuildingUseCase(self.mock_repository)

    def test_create_building_use_case_success(self):
        """Test successful building creation."""
        # Arrange
        request = CreateBuildingRequest(
            name="Test Building",
            address="123 Test St, Test City, TS 12345",
            description="A test building",
            created_by="test_user",
        )

        # Act
        response = self.create_use_case.execute(request)

        # Assert
        assert response.success is True
        assert response.building_id is not None
        assert response.message == "Building created successfully"
        assert response.created_at is not None
        self.mock_repository.save.assert_called_once()

    def test_create_building_use_case_validation_failure(self):
        """Test building creation with validation failure."""
        # Arrange
        request = CreateBuildingRequest(
            name="",  # Empty name should fail validation
            address="123 Test St, Test City, TS 12345",
        )

        # Act
        response = self.create_use_case.execute(request)

        # Assert
        assert response.success is False
        assert response.error_message == "Building name is required"
        self.mock_repository.save.assert_not_called()

    def test_get_building_use_case_success(self):
        """Test successful building retrieval."""
        # Arrange
        building_id = BuildingId()
        address = Address.from_string("123 Test St, Test City, TS 12345")
        building = Building(
            id=building_id,
            name="Test Building",
            address=address,
            status=BuildingStatus.PLANNED,
        )

        self.mock_repository.get_by_id.return_value = building

        # Act
        response = self.get_use_case.execute(str(building_id))

        # Assert
        assert response.success is True
        assert response.building is not None
        assert response.building["id"] == str(building_id)
        assert response.building["name"] == "Test Building"
        assert response.building["status"] == "planned"

    def test_get_building_use_case_not_found(self):
        """Test building retrieval when building not found."""
        # Arrange
        building_id = BuildingId()
        self.mock_repository.get_by_id.return_value = None

        # Act
        response = self.get_use_case.execute(str(building_id))

        # Assert
        assert response.success is False
        assert response.error_message == "Building not found"

    def test_list_buildings_use_case_success(self):
        """Test successful building listing."""
        # Arrange
        buildings = []
        for i in range(3):
            building_id = BuildingId()
            address = Address.from_string(f"{i} Test St, Test City, TS 12345")
            building = Building(
                id=building_id,
                name=f"Test Building {i}",
                address=address,
                status=BuildingStatus.PLANNED,
            )
            buildings.append(building)

        self.mock_repository.get_all.return_value = buildings

        # Act
        response = self.list_use_case.execute(page=1, page_size=10)

        # Assert
        assert response.success is True
        assert len(response.buildings) == 3
        assert response.total_count == 3
        assert response.page == 1
        assert response.page_size == 10

    def test_delete_building_use_case_success(self):
        """Test successful building deletion."""
        # Arrange
        building_id = BuildingId()
        address = Address.from_string("123 Test St, Test City, TS 12345")
        building = Building(
            id=building_id,
            name="Test Building",
            address=address,
            status=BuildingStatus.PLANNED,
        )

        self.mock_repository.get_by_id.return_value = building

        # Act
        response = self.delete_use_case.execute(str(building_id))

        # Assert
        assert response.success is True
        assert response.building_id == str(building_id)
        assert response.message == "Building deleted successfully"
        assert response.deleted_at is not None
        self.mock_repository.delete.assert_called_once_with(building_id)


class TestBuildingApplicationService:
    """Test building application service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_repository = Mock(spec=BuildingRepository)
        self.service = BuildingApplicationService(self.mock_repository)

    def test_create_building_service(self):
        """Test building creation through application service."""
        # Arrange
        name = "Test Building"
        address = "123 Test St, Test City, TS 12345"
        description = "A test building"
        created_by = "test_user"

        # Mock the use case response
        mock_response = CreateBuildingResponse(
            success=True,
            building_id="test-id",
            message="Building created successfully",
            created_at=datetime.utcnow(),
        )

        # Mock the use case
        self.service.create_building_use_case.execute = Mock(return_value=mock_response)

        # Act
        response = self.service.create_building(
            name=name, address=address, description=description, created_by=created_by
        )

        # Assert
        assert response.success is True
        assert response.building_id == "test-id"
        assert response.message == "Building created successfully"

    def test_get_building_statistics(self):
        """Test building statistics calculation."""
        # Arrange
        buildings = []
        for i in range(3):
            building_id = BuildingId()
            address = Address.from_string(f"{i} Test St, Test City, TS 12345")
            building = Building(
                id=building_id,
                name=f"Test Building {i}",
                address=address,
                status=BuildingStatus.PLANNED,
            )
            # Add floors to the building to set floor_count
            for j in range(2):
                floor_id = FloorId()
                floor = Floor(
                    id=floor_id,
                    building_id=building_id,
                    floor_number=j,
                    name=f"Floor {j}",
                )
                building.add_floor(floor)
            buildings.append(building)

        self.mock_repository.get_all.return_value = buildings

        # Act
        stats = self.service.get_building_statistics()

        # Assert
        assert stats["total_buildings"] == 3
        assert stats["total_floors"] == 6
        assert stats["total_rooms"] == 0  # No rooms added to floors
        assert stats["total_devices"] == 0  # No devices added to rooms
        assert stats["average_floors_per_building"] == 2.0
        assert stats["average_rooms_per_building"] == 0.0  # No rooms
        assert stats["average_devices_per_building"] == 0.0  # No devices
        assert "planned" in stats["status_distribution"]
        assert stats["status_distribution"]["planned"] == 3

    def test_search_buildings(self):
        """Test building search functionality."""
        # Arrange
        buildings = []
        for i in range(3):
            building_id = BuildingId()
            address = Address.from_string(f"{i} Test St, Test City, TS 12345")
            building = Building(
                id=building_id,
                name=f"Office Building {i}",
                address=address,
                status=BuildingStatus.PLANNED,
            )
            buildings.append(building)

        self.mock_repository.get_all.return_value = buildings

        # Act
        response = self.service.search_buildings("Office")

        # Assert
        assert response.success is True
        assert len(response.buildings) == 3
        assert response.total_count == 3
        assert all("Office" in building["name"] for building in response.buildings)
