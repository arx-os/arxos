"""
Infrastructure Layer Tests

This module contains tests for the infrastructure layer components,
including database models and repository implementations.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from infrastructure.database.config import DatabaseConfig
from infrastructure.database.models.building import BuildingModel
from infrastructure.database.models.floor import FloorModel
from infrastructure.repositories.building_repository import SQLAlchemyBuildingRepository
from domain.entities import Building
from domain.value_objects import (
    BuildingId,
    Address,
    BuildingStatus,
    Coordinates,
    Dimensions,
)


class TestDatabaseConfig:
    """Test database configuration."""

    def test_database_config_creation(self):
        """Test creating database configuration."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass",
        )

        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "test_db"
        assert config.username == "test_user"
        assert config.password == "test_pass"

    def test_database_config_connection_string(self):
        """Test database connection string generation."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass",
        )

        expected = "postgresql://test_user:test_pass@localhost:5432/test_db"
        assert config.connection_string == expected

    def test_database_config_validation(self):
        """Test database configuration validation."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass",
        )

        # Should not raise an exception
        config.validate()


class TestBuildingModel:
    """Test building database model."""

    def test_building_model_creation(self):
        """Test creating building model."""
        model = BuildingModel(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Test Building",
            description="A test building",
            status=BuildingStatus.PLANNED,
            address_street="123 Test St",
            address_city="Test City",
            address_state="TS",
            address_postal_code="12345",
            address_country="USA",
        )

        assert model.name == "Test Building"
        assert model.description == "A test building"
        assert model.status == BuildingStatus.PLANNED
        assert model.address_street == "123 Test St"
        assert model.address_city == "Test City"
        assert model.address_state == "TS"
        assert model.address_postal_code == "12345"
        assert model.address_country == "USA"

    def test_building_model_full_address(self):
        """Test building model full address property."""
        model = BuildingModel(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Test Building",
            address_street="123 Test St",
            address_city="Test City",
            address_state="TS",
            address_postal_code="12345",
            address_country="USA",
        )

        expected = "123 Test St, Test City, TS, 12345"
        assert model.full_address == expected

    def test_building_model_coordinates_dict(self):
        """Test building model coordinates dictionary."""
        model = BuildingModel(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Test Building",
            latitude=40.7128,
            longitude=-74.0060,
            elevation=10.5,
        )

        coords = model.coordinates_dict
        assert coords["latitude"] == 40.7128
        assert coords["longitude"] == -74.0060
        assert coords["elevation"] == 10.5

    def test_building_model_dimensions_dict(self):
        """Test building model dimensions dictionary."""
        model = BuildingModel(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Test Building",
            width=100.0,
            length=200.0,
            height=50.0,
            dimensions_unit="meters",
        )

        dims = model.dimensions_dict
        assert dims["width"] == 100.0
        assert dims["length"] == 200.0
        assert dims["height"] == 50.0
        assert dims["unit"] == "meters"


class TestBuildingRepository:
    """Test building repository implementation."""

    def test_building_repository_creation(self):
        """Test creating building repository."""
        mock_session = Mock()
        repo = SQLAlchemyBuildingRepository(mock_session)

        assert repo.session == mock_session
        assert repo.entity_class == Building
        assert repo.model_class == BuildingModel

    def test_building_repository_entity_to_model(self):
        """Test converting building entity to model."""
        mock_session = Mock()
        repo = SQLAlchemyBuildingRepository(mock_session)

        # Create a building entity
        building_id = BuildingId()
        address = Address.from_string("123 Test St, Test City, TS 12345")
        building = Building(
            id=building_id,
            name="Test Building",
            address=address,
            status=BuildingStatus.PLANNED,
            description="A test building",
            created_by="test_user",
        )

        model = repo._entity_to_model(building)

        assert model.id == building_id.value
        assert model.name == "Test Building"
        assert model.description == "A test building"
        assert model.status == BuildingStatus.PLANNED
        assert model.address_street == "123 Test St"
        assert model.address_city == "Test City"
        assert model.address_state == "TS"
        assert model.address_postal_code == "12345"
        assert model.created_by == "test_user"

    def test_building_repository_model_to_entity(self):
        """Test converting building model to entity."""
        mock_session = Mock()
        repo = SQLAlchemyBuildingRepository(mock_session)

        # Create a building model
        model = BuildingModel(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Test Building",
            description="A test building",
            status=BuildingStatus.PLANNED,
            address_street="123 Test St",
            address_city="Test City",
            address_state="TS",
            address_postal_code="12345",
            address_country="USA",
            created_by="test_user",
        )

        entity = repo._model_to_entity(model)

        assert entity.id.value == "550e8400-e29b-41d4-a716-446655440000"
        assert entity.name == "Test Building"
        assert entity.description == "A test building"
        assert entity.status == BuildingStatus.PLANNED
        assert entity.address.street == "123 Test St"
        assert entity.address.city == "Test City"
        assert entity.address.state == "TS"
        assert entity.address.postal_code == "12345"
        assert entity.address.country == "USA"
        assert entity.created_by == "test_user"


class TestFloorModel:
    """Test floor database model."""

    def test_floor_model_creation(self):
        """Test creating floor model."""
        model = FloorModel(
            id="550e8400-e29b-41d4-a716-446655440001",
            building_id="550e8400-e29b-41d4-a716-446655440000",
            name="Ground Floor",
            floor_number=1,
            description="The ground floor",
            status=BuildingStatus.PLANNED,
        )

        assert model.name == "Ground Floor"
        assert model.floor_number == 1
        assert model.description == "The ground floor"
        assert model.status == BuildingStatus.PLANNED

    def test_floor_model_full_name(self):
        """Test floor model full name property."""
        model = FloorModel(
            id="550e8400-e29b-41d4-a716-446655440001",
            building_id="550e8400-e29b-41d4-a716-446655440000",
            name="Ground Floor",
            floor_number=1,
        )

        expected = "Ground Floor (Floor 1)"
        assert model.full_name == expected
