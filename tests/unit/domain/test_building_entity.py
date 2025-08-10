"""
Comprehensive unit tests for Building domain entity.

Tests domain logic, business rules, validation, and domain events
for the Building aggregate root.
"""

import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from tests.framework.test_base import BaseTestCase, TestDataFactory
from domain.entities import Building
from domain.value_objects import BuildingId, Address, Coordinates, Dimensions, BuildingStatus
from domain.exceptions import InvalidBuildingError, BusinessRuleViolationError
from domain.events import BuildingCreated, BuildingUpdated, BuildingStatusChanged


class TestBuildingEntity(BaseTestCase):
    """Test cases for Building entity domain logic."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        super().setUp()
        self.test_address = self.test_data.create_test_address()
        self.test_coordinates = self.test_data.create_test_coordinates()
        self.test_dimensions = self.test_data.create_test_dimensions()
    
    def test_building_creation_with_valid_data(self) -> None:
        """Test successful building creation with valid data."""
        # Act
        building = Building(
            id=BuildingId(),
            name="Test Building",
            address=self.test_address,
            description="A test building",
            coordinates=self.test_coordinates,
            dimensions=self.test_dimensions,
            created_by="test_user"
        )
        
        # Assert
        self.assertIsNotNone(building.id)
        self.assertEqual(building.name, "Test Building")
        self.assertEqual(building.address, self.test_address)
        self.assertEqual(building.description, "A test building")
        self.assertEqual(building.coordinates, self.test_coordinates)
        self.assertEqual(building.dimensions, self.test_dimensions)
        self.assertEqual(building.created_by, "test_user")
        self.assertEqual(building.status, BuildingStatus.PLANNED)
        self.assertIsNotNone(building.created_at)
        
        # Assert domain event was created
        self.assertDomainEvent(building, BuildingCreated,
                              building_id=str(building.id),
                              building_name=building.name,
                              created_by="test_user")
    
    def test_building_creation_fails_with_empty_name(self) -> None:
        """Test that building creation fails with empty name."""
        with self.assertRaisesWithMessage(InvalidBuildingError, "Building name cannot be empty"):
            Building(
                id=BuildingId(),
                name="",  # Empty name should fail
                address=self.test_address,
                created_by="test_user"
            )
    
    def test_building_creation_fails_with_whitespace_name(self) -> None:
        """Test that building creation fails with whitespace-only name."""
        with self.assertRaisesWithMessage(InvalidBuildingError, "Building name cannot be empty"):
            Building(
                id=BuildingId(),
                name="   ",  # Whitespace-only name should fail
                address=self.test_address,
                created_by="test_user"
            )
    
    def test_building_creation_fails_with_no_address(self) -> None:
        """Test that building creation fails without address."""
        with self.assertRaisesWithMessage(InvalidBuildingError, "Building address is required"):
            Building(
                id=BuildingId(),
                name="Test Building",
                address=None,  # No address should fail
                created_by="test_user"
            )
    
    def test_building_creation_fails_with_invalid_address(self) -> None:
        """Test that building creation fails with invalid address."""
        invalid_address = Address(
            street="",  # Empty street should make address invalid
            city="Test City",
            state="TS",
            postal_code="12345"
        )
        
        # Note: This should fail during address creation, not building creation
        with self.assertRaises(ValueError):
            Building(
                id=BuildingId(),
                name="Test Building", 
                address=invalid_address,
                created_by="test_user"
            )
    
    def test_update_building_name_success(self) -> None:
        """Test successful building name update."""
        # Arrange
        building = self.test_data.create_test_building()
        original_name = building.name
        new_name = "Updated Building Name"
        updated_by = "test_updater"
        
        # Act
        building.update_name(new_name, updated_by)
        
        # Assert
        self.assertEqual(building.name, new_name)
        self.assertNotEqual(building.name, original_name)
        self.assertIsNotNone(building.updated_at)
        
        # Assert domain event was created
        self.assertDomainEvent(building, BuildingUpdated,
                              building_id=str(building.id),
                              updated_fields=["name"],
                              updated_by=updated_by)
    
    def test_update_building_name_fails_with_empty_name(self) -> None:
        """Test that name update fails with empty name.""" 
        building = self.test_data.create_test_building()
        
        with self.assertRaisesWithMessage(InvalidBuildingError, "Building name cannot be empty"):
            building.update_name("", "test_updater")
    
    def test_update_building_name_no_change_if_same(self) -> None:
        """Test that name update is skipped if name is the same."""
        building = self.test_data.create_test_building()
        original_name = building.name
        original_events_count = len(building.get_domain_events())
        
        # Act - update with same name
        building.update_name(original_name, "test_updater")
        
        # Assert - no change should occur
        self.assertEqual(building.name, original_name)
        self.assertEqual(len(building.get_domain_events()), original_events_count)
    
    def test_update_building_status_success(self) -> None:
        """Test successful building status update."""
        # Arrange
        building = self.test_data.create_test_building()
        original_status = building.status
        new_status = BuildingStatus.UNDER_CONSTRUCTION
        updated_by = "test_updater"
        
        # Act
        building.update_status(new_status, updated_by)
        
        # Assert
        self.assertEqual(building.status, new_status)
        self.assertNotEqual(building.status, original_status)
        self.assertIsNotNone(building.updated_at)
        
        # Assert domain event was created
        self.assertDomainEvent(building, BuildingStatusChanged,
                              building_id=str(building.id),
                              old_status=original_status.value,
                              new_status=new_status.value,
                              changed_by=updated_by)
    
    def test_update_building_status_no_change_if_same(self) -> None:
        """Test that status update is skipped if status is the same."""
        building = self.test_data.create_test_building()
        original_status = building.status
        original_events_count = len(building.get_domain_events())
        
        # Act - update with same status
        building.update_status(original_status, "test_updater")
        
        # Assert - no change should occur
        self.assertEqual(building.status, original_status)
        self.assertEqual(len(building.get_domain_events()), original_events_count)
    
    def test_building_status_transition_validation(self) -> None:
        """Test building status transition validation rules."""
        building = self.test_data.create_test_building()
        
        # Valid transitions
        building.update_status(BuildingStatus.UNDER_CONSTRUCTION, "test_user")
        building.update_status(BuildingStatus.COMPLETED, "test_user")
        building.update_status(BuildingStatus.OPERATIONAL, "test_user")
        building.update_status(BuildingStatus.MAINTENANCE, "test_user")
        
        # Should be able to go back to operational from maintenance
        building.update_status(BuildingStatus.OPERATIONAL, "test_user")
        
        # Final decommission
        building.update_status(BuildingStatus.DECOMMISSIONED, "test_user")
        
        # Cannot go from decommissioned back to any other status
        with self.assertRaisesWithMessage(BusinessRuleViolationError, 
                                         "Cannot change status of decommissioned building"):
            building.update_status(BuildingStatus.OPERATIONAL, "test_user")
    
    def test_add_floor_to_building(self) -> None:
        """Test adding a floor to a building."""
        building = self.test_data.create_test_building()
        floor = self.test_data.create_test_floor(building_id=building.id)
        
        # Act
        building.add_floor(floor)
        
        # Assert
        self.assertIn(floor, building.floors)
        self.assertEqual(len(building.floors), 1)
    
    def test_remove_floor_from_building(self) -> None:
        """Test removing a floor from a building."""
        building = self.test_data.create_test_building()
        floor = self.test_data.create_test_floor(building_id=building.id)
        building.add_floor(floor)
        
        # Act
        building.remove_floor(floor.id)
        
        # Assert
        self.assertNotIn(floor, building.floors)
        self.assertEqual(len(building.floors), 0)
    
    def test_get_floor_by_number(self) -> None:
        """Test retrieving a floor by its number."""
        building = self.test_data.create_test_building()
        floor1 = self.test_data.create_test_floor(building_id=building.id, floor_number=1)
        floor2 = self.test_data.create_test_floor(building_id=building.id, floor_number=2)
        building.add_floor(floor1)
        building.add_floor(floor2)
        
        # Act & Assert
        found_floor = building.get_floor_by_number(2)
        self.assertEqual(found_floor, floor2)
        
        # Test non-existent floor
        non_existent = building.get_floor_by_number(99)
        self.assertIsNone(non_existent)
    
    def test_building_area_calculation(self) -> None:
        """Test building area calculation based on dimensions."""
        building = self.test_data.create_test_building(
            dimensions=Dimensions(width=20.0, length=30.0, height=3.0)
        )
        
        expected_area = 20.0 * 30.0  # width * length
        self.assertEqual(building.area, expected_area)
    
    def test_building_volume_calculation(self) -> None:
        """Test building volume calculation based on dimensions."""
        building = self.test_data.create_test_building(
            dimensions=Dimensions(width=20.0, length=30.0, height=3.0)
        )
        
        expected_volume = 20.0 * 30.0 * 3.0  # width * length * height
        self.assertEqual(building.volume, expected_volume)
    
    def test_building_without_dimensions(self) -> None:
        """Test building behavior without dimensions."""
        building = Building(
            id=BuildingId(),
            name="Test Building",
            address=self.test_address,
            coordinates=self.test_coordinates,
            dimensions=None,  # No dimensions
            created_by="test_user"
        )
        
        # Area and volume should be None
        self.assertIsNone(building.area)
        self.assertIsNone(building.volume)
    
    def test_building_metadata_management(self) -> None:
        """Test building metadata add/remove operations."""
        building = self.test_data.create_test_building()
        
        # Add metadata
        building.add_metadata("test_key", "test_value", "test_user")
        self.assertEqual(building.metadata["test_key"], "test_value")
        
        # Update metadata
        building.add_metadata("test_key", "updated_value", "test_user")
        self.assertEqual(building.metadata["test_key"], "updated_value")
        
        # Remove metadata
        building.remove_metadata("test_key", "test_user")
        self.assertNotIn("test_key", building.metadata)
    
    def test_building_domain_events_collection(self) -> None:
        """Test that domain events are properly collected."""
        building = self.test_data.create_test_building()
        initial_events = building.get_domain_events()
        
        # Should have BuildingCreated event
        self.assertEqual(len(initial_events), 1)
        self.assertIsInstance(initial_events[0], BuildingCreated)
        
        # Update name - should add BuildingUpdated event
        building.update_name("New Name", "test_user")
        all_events = building.get_domain_events()
        self.assertEqual(len(all_events), 2)
        self.assertIsInstance(all_events[1], BuildingUpdated)
        
        # Clear events
        building.clear_domain_events()
        self.assertEqual(len(building.get_domain_events()), 0)
    
    def test_building_string_representation(self) -> None:
        """Test building string representation."""
        building = self.test_data.create_test_building(name="Test Building")
        
        str_repr = str(building)
        self.assertIn("Test Building", str_repr)
        self.assertIn(str(building.id), str_repr)
    
    def test_building_equality(self) -> None:
        """Test building equality based on ID."""
        building_id = BuildingId()
        building1 = Building(
            id=building_id,
            name="Building 1",
            address=self.test_address,
            created_by="test_user"
        )
        building2 = Building(
            id=building_id,  # Same ID
            name="Building 2",  # Different name
            address=self.test_address,
            created_by="test_user"
        )
        building3 = Building(
            id=BuildingId(),  # Different ID
            name="Building 1",  # Same name as building1
            address=self.test_address,
            created_by="test_user"
        )
        
        # Buildings with same ID should be equal
        self.assertEqual(building1, building2)
        
        # Buildings with different IDs should not be equal
        self.assertNotEqual(building1, building3)
    
    def test_building_hash(self) -> None:
        """Test building hash based on ID."""
        building_id = BuildingId()
        building1 = Building(
            id=building_id,
            name="Building 1",
            address=self.test_address,
            created_by="test_user"
        )
        building2 = Building(
            id=building_id,  # Same ID
            name="Building 2",  # Different name
            address=self.test_address,
            created_by="test_user"
        )
        
        # Buildings with same ID should have same hash
        self.assertEqual(hash(building1), hash(building2))
        
        # Should be usable in sets and dictionaries
        building_set = {building1, building2}
        self.assertEqual(len(building_set), 1)  # Should contain only one building


if __name__ == '__main__':
    unittest.main()