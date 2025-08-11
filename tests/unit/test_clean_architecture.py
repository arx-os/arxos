"""
Clean Architecture Test Suite

Comprehensive tests for the Clean Architecture implementation including
domain layer, application layer, and infrastructure layer components.
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime

# Domain Layer Imports - Updated to use Unified Domain
from domain.unified.value_objects import (
    Address, Coordinates, Dimensions, BuildingStatus, 
    BuildingId, Money
)
from domain.unified.entities.building import Building
from domain.unified.repositories.building_repository import BuildingRepository

# Application Layer Imports
from svgx_engine.application.dto.building_dto import (
    BuildingDTO,
    CreateBuildingRequest,
    UpdateBuildingRequest,
    BuildingSearchRequest
)
from svgx_engine.application.use_cases.building_use_cases import (
    CreateBuildingUseCase,
    UpdateBuildingUseCase,
    GetBuildingUseCase,
    ListBuildingsUseCase,
    DeleteBuildingUseCase
)

# Infrastructure Layer Imports
from svgx_engine.infrastructure.repositories.in_memory_building_repository import InMemoryBuildingRepository


class TestValueObjects(unittest.TestCase):
    """Test value objects functionality."""

    def test_address_creation(self):
        """Test Address value object creation and validation."""
        address = Address(
            street="123 Main St",
            city="New York",
            state="NY",
            postal_code="10001",
            country="USA"
        )

        self.assertEqual(address.street, "123 Main St")
        self.assertEqual(address.city, "New York")
        self.assertEqual(address.full_address, "123 Main St, New York, NY 10001, USA")

    def test_address_validation(self):
        """Test Address validation."""
        with self.assertRaises(ValueError):
            Address(
                street="",  # Empty street
                city="New York",
                state="NY",
                postal_code="10001",
                country="USA"
            )

    def test_coordinates_creation(self):
        """Test Coordinates value object creation."""
        coords = Coordinates(latitude=40.7128, longitude=-74.0060)

        self.assertEqual(coords.latitude, 40.7128)
        self.assertEqual(coords.longitude, -74.0060)
        self.assertTrue(coords.is_valid)

    def test_coordinates_validation(self):
        """Test Coordinates validation."""
        with self.assertRaises(ValueError):
            Coordinates(latitude=100, longitude=-74.0060)  # Invalid latitude

    def test_dimensions_creation(self):
        """Test Dimensions value object creation."""
        dims = Dimensions(length=10.0, width=5.0, height=3.0)

        self.assertEqual(dims.length, 10.0)
        self.assertEqual(dims.width, 5.0)
        self.assertEqual(dims.height, 3.0)
        self.assertEqual(dims.area, 50.0)
        self.assertEqual(dims.volume, 150.0)

    def test_status_creation(self):
        """Test Status value object creation."""
        status = Status.active("Building is active")

        self.assertEqual(status.value, "active")
        self.assertTrue(status.is_active)
        self.assertFalse(status.is_final)

    def test_money_creation(self):
        """Test Money value object creation."""
        money = Money.from_float(100.50, "USD")

        self.assertEqual(money.amount, 100.50)
        self.assertEqual(money.currency, "USD")
        self.assertTrue(money.is_positive)

    def test_identifier_creation(self):
        """Test Identifier value object creation."""
        identifier = Identifier.generate_uuid("BLD")

        self.assertIsNotNone(identifier.value)
        self.assertEqual(identifier.prefix, "BLD")
        self.assertTrue(identifier.is_uuid)


class TestDomainAggregates(unittest.TestCase):
    """Test domain aggregates functionality."""

    def setUp(self):
        """Set up test data."""
        self.address = Address(
            street="123 Main St",
            city="New York",
            state="NY",
            postal_code="10001",
            country="USA"
        )
        self.coordinates = Coordinates(latitude=40.7128, longitude=-74.0060)
        self.dimensions = Dimensions(length=10.0, width=5.0, height=3.0)

    def test_building_aggregate_creation(self):
        """Test BuildingAggregate creation."""
        aggregate = BuildingAggregate.create(
            name="Test Building",
            address=self.address,
            coordinates=self.coordinates,
            dimensions=self.dimensions,
            building_type="Office"
        )

        self.assertIsNotNone(aggregate.id)
        self.assertEqual(aggregate.name, "Test Building")
        self.assertEqual(aggregate.building_type, "Office")
        self.assertTrue(aggregate.is_active())

    def test_building_aggregate_update(self):
        """Test BuildingAggregate update operations."""
        aggregate = BuildingAggregate.create(
            name="Test Building",
            address=self.address,
            coordinates=self.coordinates,
            dimensions=self.dimensions,
            building_type="Office"
        )

        # Test name update
        aggregate.update_name("Updated Building")
        self.assertEqual(aggregate.name, "Updated Building")

        # Test status change
        new_status = Status.inactive("Building is inactive")
        aggregate.change_status(new_status)
        self.assertEqual(aggregate.status.value, "inactive")

    def test_domain_events(self):
        """Test domain events generation."""
        aggregate = BuildingAggregate.create(
            name="Test Building",
            address=self.address,
            coordinates=self.coordinates,
            dimensions=self.dimensions,
            building_type="Office"
        )

        # Should have creation event
        self.assertEqual(len(aggregate.domain_events), 1)
        self.assertEqual(aggregate.domain_events[0].event_type, "building.created")

        # Update should generate update event
        aggregate.update_name("Updated Building")
        self.assertEqual(len(aggregate.domain_events), 2)
        self.assertEqual(aggregate.domain_events[1].event_type, "building.updated")


class TestApplicationLayer(unittest.TestCase):
    """Test application layer functionality."""

    def setUp(self):
        """Set up test data."""
        self.repository = InMemoryBuildingRepository()
        self.create_use_case = CreateBuildingUseCase(self.repository)
        self.get_use_case = GetBuildingUseCase(self.repository)
        self.update_use_case = UpdateBuildingUseCase(self.repository)
        self.list_use_case = ListBuildingsUseCase(self.repository)
        self.delete_use_case = DeleteBuildingUseCase(self.repository)

    def test_create_building_use_case(self):
        """Test CreateBuildingUseCase."""
        request = CreateBuildingRequest(
            name="Test Building",
            address={
                'street': '123 Main St',
                'city': 'New York',
                'state': 'NY',
                'postal_code': '10001',
                'country': 'USA'
            },
            coordinates={
                'latitude': 40.7128,
                'longitude': -74.0060
            },
            dimensions={
                'length': 10.0,
                'width': 5.0,
                'height': 3.0
            },
            building_type="Office"
        )

        result = self.create_use_case.execute(request)

        self.assertIsInstance(result, BuildingDTO)
        self.assertEqual(result.name, "Test Building")
        self.assertEqual(result.building_type, "Office")

    def test_get_building_use_case(self):
        """Test GetBuildingUseCase."""
        # First create a building
        request = CreateBuildingRequest(
            name="Test Building",
            address={
                'street': '123 Main St',
                'city': 'New York',
                'state': 'NY',
                'postal_code': '10001',
                'country': 'USA'
            },
            coordinates={
                'latitude': 40.7128,
                'longitude': -74.0060
            },
            dimensions={
                'length': 10.0,
                'width': 5.0,
                'height': 3.0
            },
            building_type="Office"
        )

        created = self.create_use_case.execute(request)

        # Then retrieve it
        retrieved = self.get_use_case.execute(created.id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Building")

    def test_update_building_use_case(self):
        """Test UpdateBuildingUseCase."""
        # First create a building
        create_request = CreateBuildingRequest(
            name="Test Building",
            address={
                'street': '123 Main St',
                'city': 'New York',
                'state': 'NY',
                'postal_code': '10001',
                'country': 'USA'
            },
            coordinates={
                'latitude': 40.7128,
                'longitude': -74.0060
            },
            dimensions={
                'length': 10.0,
                'width': 5.0,
                'height': 3.0
            },
            building_type="Office"
        )

        created = self.create_use_case.execute(create_request)

        # Then update it
        update_request = UpdateBuildingRequest(
            name="Updated Building",
            building_type="Residential"
        )

        updated = self.update_use_case.execute(created.id, update_request)

        self.assertEqual(updated.name, "Updated Building")
        self.assertEqual(updated.building_type, "Residential")

    def test_list_buildings_use_case(self):
        """Test ListBuildingsUseCase."""
        # Create multiple buildings
        for i in range(3):
            request = CreateBuildingRequest(
                name=f"Test Building {i}",
                address={
                    'street': f'{123 + i} Main St',
                    'city': 'New York',
                    'state': 'NY',
                    'postal_code': '10001',
                    'country': 'USA'
                },
                coordinates={
                    'latitude': 40.7128,
                    'longitude': -74.0060
                },
                dimensions={
                    'length': 10.0,
                    'width': 5.0,
                    'height': 3.0
                },
                building_type="Office"
            )
            self.create_use_case.execute(request)

        # List buildings
        search_request = BuildingSearchRequest(page=1, page_size=10)
        result = self.list_use_case.execute(search_request)

        self.assertEqual(result.total_count, 3)
        self.assertEqual(len(result.buildings), 3)

    def test_delete_building_use_case(self):
        """Test DeleteBuildingUseCase."""
        # First create a building
        request = CreateBuildingRequest(
            name="Test Building",
            address={
                'street': '123 Main St',
                'city': 'New York',
                'state': 'NY',
                'postal_code': '10001',
                'country': 'USA'
            },
            coordinates={
                'latitude': 40.7128,
                'longitude': -74.0060
            },
            dimensions={
                'length': 10.0,
                'width': 5.0,
                'height': 3.0
            },
            building_type="Office"
        )

        created = self.create_use_case.execute(request)

        # Then delete it
        deleted = self.delete_use_case.execute(created.id)

        self.assertTrue(deleted)

        # Verify it's gone'
        retrieved = self.get_use_case.execute(created.id)
        self.assertIsNone(retrieved)


class TestInfrastructureLayer(unittest.TestCase):
    """Test infrastructure layer functionality."""

    def setUp(self):
        """Set up test data."""
        self.repository = InMemoryBuildingRepository()
        self.address = Address(
            street="123 Main St",
            city="New York",
            state="NY",
            postal_code="10001",
            country="USA"
        )
        self.coordinates = Coordinates(latitude=40.7128, longitude=-74.0060)
        self.dimensions = Dimensions(length=10.0, width=5.0, height=3.0)

    def test_repository_save_and_find(self):
        """Test repository save and find operations."""
        aggregate = BuildingAggregate.create(
            name="Test Building",
            address=self.address,
            coordinates=self.coordinates,
            dimensions=self.dimensions,
            building_type="Office"
        )

        # Save
        saved = self.repository.save(aggregate)
        self.assertIsNotNone(saved.id)

        # Find by ID
        found = self.repository.find_by_id(saved.id)
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "Test Building")

    def test_repository_search_operations(self):
        """Test repository search operations."""
        # Create buildings
        for i in range(3):
            aggregate = BuildingAggregate.create(
                name=f"Test Building {i}",
                address=self.address,
                coordinates=self.coordinates,
                dimensions=self.dimensions,
                building_type="Office"
            )
            self.repository.save(aggregate)

        # Test find all
        all_buildings = self.repository.find_all()
        self.assertEqual(len(all_buildings), 3)

        # Test find by status
        active_buildings = self.repository.find_active_buildings()
        self.assertEqual(len(active_buildings), 3)

        # Test count
        count = self.repository.count()
        self.assertEqual(count, 3)

    def test_repository_statistics(self):
        """Test repository statistics."""
        # Create buildings
        for i in range(3):
            aggregate = BuildingAggregate.create(
                name=f"Test Building {i}",
                address=self.address,
                coordinates=self.coordinates,
                dimensions=self.dimensions,
                building_type="Office"
            )
            self.repository.save(aggregate)

        # Get statistics
        stats = self.repository.get_statistics()

        self.assertEqual(stats['total_buildings'], 3)
        self.assertEqual(stats['total_area'], 150.0)  # 3 * 50.0
        self.assertEqual(stats['average_area'], 50.0)


class TestCleanArchitectureIntegration(unittest.TestCase):
    """Test Clean Architecture integration."""

    def setUp(self):
        """Set up test data."""
        self.repository = InMemoryBuildingRepository()
        self.create_use_case = CreateBuildingUseCase(self.repository)
        self.get_use_case = GetBuildingUseCase(self.repository)

    def test_full_workflow(self):
        """Test complete workflow from application to infrastructure."""
        # Application layer: Create building
        request = CreateBuildingRequest(
            name="Integration Test Building",
            address={
                'street': '123 Main St',
                'city': 'New York',
                'state': 'NY',
                'postal_code': '10001',
                'country': 'USA'
            },
            coordinates={
                'latitude': 40.7128,
                'longitude': -74.0060
            },
            dimensions={
                'length': 10.0,
                'width': 5.0,
                'height': 3.0
            },
            building_type="Office"
        )

        # Execute use case
        building_dto = self.create_use_case.execute(request)

        # Verify DTO
        self.assertIsInstance(building_dto, BuildingDTO)
        self.assertEqual(building_dto.name, "Integration Test Building")
        self.assertEqual(building_dto.building_type, "Office")

        # Verify domain events were generated
        building_aggregate = self.repository.find_by_id(Identifier(building_dto.id))
        self.assertEqual(len(building_aggregate.domain_events), 1)
        self.assertEqual(building_aggregate.domain_events[0].event_type, "building.created")

        # Test retrieval
        retrieved_dto = self.get_use_case.execute(building_dto.id)
        self.assertEqual(retrieved_dto.name, "Integration Test Building")


if __name__ == '__main__':
    unittest.main()
