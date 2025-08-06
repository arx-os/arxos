"""
Test Domain Layer Implementation

This module tests the domain layer components to ensure they are working
correctly and following Clean Architecture principles.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from domain.value_objects import (
    BuildingId,
    FloorId,
    RoomId,
    DeviceId,
    UserId,
    ProjectId,
    Address,
    Coordinates,
    Dimensions,
    Email,
    PhoneNumber,
    BuildingStatus,
    FloorStatus,
    RoomStatus,
    DeviceStatus,
    UserRole,
    ProjectStatus,
)
from domain.entities import Building, Floor, Room, Device, User, Project
from domain.events import (
    BuildingCreated,
    BuildingUpdated,
    BuildingStatusChanged,
    FloorAdded,
    FloorUpdated,
    FloorStatusChanged,
    RoomAdded,
    RoomUpdated,
    RoomStatusChanged,
    DeviceAdded,
    DeviceUpdated,
    DeviceStatusChanged,
    UserCreated,
    UserUpdated,
    UserRoleChanged,
    ProjectCreated,
    ProjectUpdated,
    ProjectStatusChanged,
    EventBus,
    EventHandler,
)
from domain.exceptions import (
    InvalidBuildingError,
    InvalidFloorError,
    InvalidRoomError,
    InvalidDeviceError,
    InvalidUserError,
    InvalidProjectError,
    DuplicateFloorError,
    DuplicateRoomError,
    DuplicateDeviceError,
    InvalidStatusTransitionError,
)
from domain.services import (
    BuildingDomainService,
    FloorDomainService,
    RoomDomainService,
    DeviceDomainService,
    UserDomainService,
    ProjectDomainService,
)


class TestValueObjects:
    """Test value objects functionality."""

    def test_building_id_creation(self):
        """Test building ID creation and validation."""
        building_id = BuildingId()
        assert isinstance(building_id.value, str)
        assert len(building_id.value) > 0

        # Test string representation
        assert str(building_id) == building_id.value

    def test_address_creation(self):
        """Test address creation and validation."""
        address = Address(
            street="123 Main St", city="New York", state="NY", postal_code="10001"
        )

        assert address.street == "123 Main St"
        assert address.city == "New York"
        assert address.state == "NY"
        assert address.postal_code == "10001"
        assert address.is_valid() is True
        assert "123 Main St" in address.full_address

    def test_address_validation(self):
        """Test address validation."""
        with pytest.raises(ValueError):
            Address(
                street="",  # Empty street
                city="New York",
                state="NY",
                postal_code="10001",
            )

    def test_coordinates_creation(self):
        """Test coordinates creation and validation."""
        coords = Coordinates(latitude=40.7128, longitude=-74.0060)

        assert coords.latitude == 40.7128
        assert coords.longitude == -74.0060
        assert coords.elevation is None

    def test_coordinates_validation(self):
        """Test coordinates validation."""
        with pytest.raises(ValueError):
            Coordinates(latitude=100, longitude=0)  # Invalid latitude

        with pytest.raises(ValueError):
            Coordinates(latitude=0, longitude=200)  # Invalid longitude

    def test_dimensions_creation(self):
        """Test dimensions creation and validation."""
        dims = Dimensions(width=10.0, length=20.0, height=3.0)

        assert dims.width == 10.0
        assert dims.length == 20.0
        assert dims.height == 3.0
        assert dims.area == 200.0  # 10 * 20
        assert dims.volume == 600.0  # 10 * 20 * 3

    def test_email_creation(self):
        """Test email creation and validation."""
        email = Email("test@example.com")
        assert str(email) == "test@example.com"
        assert email.domain == "example.com"
        assert email.local_part == "test"

    def test_email_validation(self):
        """Test email validation."""
        with pytest.raises(ValueError):
            Email("invalid-email")  # Invalid email format


class TestEntities:
    """Test domain entities functionality."""

    def test_building_creation(self):
        """Test building entity creation."""
        address = Address(
            street="123 Main St", city="New York", state="NY", postal_code="10001"
        )

        building = Building(
            id=BuildingId(),
            name="Test Building",
            address=address,
            created_by="test_user",
        )

        assert building.name == "Test Building"
        assert building.address == address
        assert building.status == BuildingStatus.PLANNED
        assert building.created_by == "test_user"
        assert building.floor_count == 0
        assert building.room_count == 0
        assert building.device_count == 0

    def test_building_validation(self):
        """Test building validation."""
        address = Address(
            street="123 Main St", city="New York", state="NY", postal_code="10001"
        )

        with pytest.raises(InvalidBuildingError):
            Building(
                id=BuildingId(),
                name="",  # Empty name
                address=address,
                created_by="test_user",
            )

    def test_building_status_transition(self):
        """Test building status transitions."""
        address = Address(
            street="123 Main St", city="New York", state="NY", postal_code="10001"
        )

        building = Building(
            id=BuildingId(),
            name="Test Building",
            address=address,
            created_by="test_user",
        )

        # Valid transition
        building.update_status(BuildingStatus.UNDER_CONSTRUCTION, "test_user")
        assert building.status == BuildingStatus.UNDER_CONSTRUCTION

        # Invalid transition
        with pytest.raises(InvalidStatusTransitionError):
            building.update_status(BuildingStatus.DECOMMISSIONED, "test_user")

    def test_floor_creation(self):
        """Test floor entity creation."""
        floor = Floor(
            id=FloorId(),
            building_id=BuildingId(),
            floor_number=1,
            name="Ground Floor",
            created_by="test_user",
        )

        assert floor.floor_number == 1
        assert floor.name == "Ground Floor"
        assert floor.status == FloorStatus.PLANNED
        assert floor.room_count == 0
        assert floor.device_count == 0

    def test_room_creation(self):
        """Test room entity creation."""
        room = Room(
            id=RoomId(),
            floor_id=FloorId(),
            room_number="101",
            name="Conference Room",
            room_type="meeting",
            created_by="test_user",
        )

        assert room.room_number == "101"
        assert room.name == "Conference Room"
        assert room.room_type == "meeting"
        assert room.status == RoomStatus.PLANNED
        assert room.device_count == 0

    def test_device_creation(self):
        """Test device entity creation."""
        device = Device(
            id=DeviceId(),
            room_id=RoomId(),
            device_id="DEV001",
            device_type="sensor",
            name="Temperature Sensor",
            created_by="test_user",
        )

        assert device.device_id == "DEV001"
        assert device.device_type == "sensor"
        assert device.name == "Temperature Sensor"
        assert device.status == DeviceStatus.INSTALLED

    def test_user_creation(self):
        """Test user entity creation."""
        user = User(
            id=UserId(),
            email=Email("user@example.com"),
            username="testuser",
            role=UserRole.VIEWER,
            created_by="admin",
        )

        assert user.email.value == "user@example.com"
        assert user.username == "testuser"
        assert user.role == UserRole.VIEWER
        assert user.is_active is True

    def test_project_creation(self):
        """Test project entity creation."""
        project = Project(
            id=ProjectId(),
            name="Test Project",
            building_id=BuildingId(),
            created_by="test_user",
        )

        assert project.name == "Test Project"
        assert project.status == ProjectStatus.DRAFT
        assert project.created_by == "test_user"


class TestDomainEvents:
    """Test domain events functionality."""

    def test_building_created_event(self):
        """Test building created event."""
        event = BuildingCreated(
            building_id="test-building-id",
            building_name="Test Building",
            address="123 Main St, New York, NY 10001",
            created_by="test_user",
        )

        assert event.building_id == "test-building-id"
        assert event.building_name == "Test Building"
        assert event.event_type.value == "building_created"
        assert event.get_aggregate_id() == "test-building-id"

    def test_event_bus(self):
        """Test event bus functionality."""
        event_bus = EventBus()

        # Create a mock handler
        mock_handler = Mock()

        # Subscribe to building created events
        event_bus.subscribe(BuildingCreated.event_type, mock_handler)

        # Create and publish an event
        event = BuildingCreated(
            building_id="test-id",
            building_name="Test Building",
            address="123 Main St",
            created_by="test_user",
        )

        event_bus.publish(event)

        # Verify handler was called
        mock_handler.handle.assert_called_once_with(event)

    def test_event_aggregation(self):
        """Test event aggregation by aggregate ID."""
        event_bus = EventBus()

        # Create multiple events for the same building
        event1 = BuildingCreated(
            building_id="building-1",
            building_name="Building 1",
            address="123 Main St",
            created_by="user1",
        )

        event2 = BuildingUpdated(
            building_id="building-1", updated_fields=["name"], updated_by="user2"
        )

        event_bus.publish(event1)
        event_bus.publish(event2)

        # Get events for the building
        building_events = event_bus.get_events_by_aggregate_id("building-1")
        assert len(building_events) == 2


class TestDomainServices:
    """Test domain services functionality."""

    def test_building_domain_service_creation(self):
        """Test building domain service creation."""
        mock_repository = Mock()
        service = BuildingDomainService(mock_repository)

        assert service.building_repository == mock_repository

    def test_floor_domain_service_creation(self):
        """Test floor domain service creation."""
        mock_repository = Mock()
        service = FloorDomainService(mock_repository)

        assert service.floor_repository == mock_repository

    def test_room_domain_service_creation(self):
        """Test room domain service creation."""
        mock_repository = Mock()
        service = RoomDomainService(mock_repository)

        assert service.room_repository == mock_repository

    def test_device_domain_service_creation(self):
        """Test device domain service creation."""
        mock_repository = Mock()
        service = DeviceDomainService(mock_repository)

        assert service.device_repository == mock_repository

    def test_user_domain_service_creation(self):
        """Test user domain service creation."""
        mock_repository = Mock()
        service = UserDomainService(mock_repository)

        assert service.user_repository == mock_repository

    def test_project_domain_service_creation(self):
        """Test project domain service creation."""
        mock_repository = Mock()
        service = ProjectDomainService(mock_repository)

        assert service.project_repository == mock_repository


class TestDomainExceptions:
    """Test domain exceptions functionality."""

    def test_domain_exception_creation(self):
        """Test domain exception creation."""
        exception = InvalidBuildingError("Test error message")
        assert str(exception) == "Test error message"

    def test_exception_inheritance(self):
        """Test exception inheritance hierarchy."""
        assert issubclass(InvalidBuildingError, Exception)
        assert issubclass(InvalidFloorError, Exception)
        assert issubclass(InvalidRoomError, Exception)
        assert issubclass(InvalidDeviceError, Exception)
        assert issubclass(InvalidUserError, Exception)
        assert issubclass(InvalidProjectError, Exception)


if __name__ == "__main__":
    pytest.main([__file__])
