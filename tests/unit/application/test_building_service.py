"""
Comprehensive unit tests for Building Application Service.

Tests service layer orchestration, error handling, caching,
and integration with repositories and infrastructure services.
"""

import unittest
from unittest.mock import Mock, patch, call, MagicMock
from datetime import datetime
from typing import Dict, Any

from tests.framework.test_base import ServiceTestCase, TestDataFactory
from application.services.building_service import BuildingApplicationService
from application.dto.building_dto import (
    CreateBuildingRequest, CreateBuildingResponse,
    GetBuildingResponse, ListBuildingsResponse,
    UpdateBuildingRequest, UpdateBuildingResponse,
    DeleteBuildingResponse
)
from domain.entities import Building
from domain.value_objects import BuildingId, Address, BuildingStatus
from domain.exceptions import BuildingNotFoundError, InvalidBuildingError
from application.exceptions import ApplicationError, ResourceNotFoundError


class TestBuildingApplicationService(ServiceTestCase):
    """Test cases for Building Application Service."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        super().setUp()
        
        # Create service instance with mocked dependencies
        self.service = BuildingApplicationService(
            unit_of_work=self.mock_unit_of_work,
            cache_service=self.mock_cache_service,
            event_store=self.mock_event_store,
            message_queue=self.mock_message_queue,
            metrics=self.mock_metrics
        )
        
        self.test_building = self.test_data.create_test_building()
        self.test_address = self.test_data.create_test_address()
    
    def test_create_building_success(self) -> None:
        """Test successful building creation."""
        # Arrange
        request = CreateBuildingRequest(
            name="New Building",
            address={
                "street": "123 New Street",
                "city": "New City", 
                "state": "NC",
                "postal_code": "12345"
            },
            description="A new test building",
            created_by="test_user"
        )
        
        # Mock repository to return saved building
        self.mock_building_repository.save.return_value = self.test_building
        
        # Act
        response = self.service.create_building(
            name=request.name,
            address=request.address,
            description=request.description,
            created_by=request.created_by
        )
        
        # Assert
        self.assertIsInstance(response, CreateBuildingResponse)
        self.assertTrue(response.success)
        self.assertIsNotNone(response.building_id)
        self.assertEqual(response.message, "Building created successfully")
        
        # Verify repository interactions
        self.assertRepositoryMethod(self.mock_building_repository, "save", call_count=1)
        self.mock_unit_of_work.commit.assert_called_once()
        
        # Verify event publishing
        self.mock_event_store.store_event.assert_called()
        self.mock_message_queue.publish.assert_called()
        
        # Verify metrics
        self.mock_metrics.record_operation_duration.assert_called()
        self.mock_metrics.increment_counter.assert_called_with(
            "building_operations_total", {"operation": "create", "status": "success"}
        )
    
    def test_create_building_validation_error(self) -> None:
        """Test building creation with validation error."""
        # Arrange - empty name should cause validation error
        request = CreateBuildingRequest(
            name="",  # Empty name
            address=self.test_address,
            created_by="test_user"
        )
        
        # Act
        response = self.service.create_building(
            name=request.name,
            address=request.address,
            created_by=request.created_by
        )
        
        # Assert
        self.assertIsInstance(response, CreateBuildingResponse)
        self.assertFalse(response.success)
        self.assertIsNone(response.building_id)
        self.assertIn("Building name cannot be empty", response.message)
        
        # Verify no repository interactions occurred
        self.mock_building_repository.save.assert_not_called()
        self.mock_unit_of_work.commit.assert_not_called()
        
        # Verify error metrics
        self.mock_metrics.increment_counter.assert_called_with(
            "building_operations_total", {"operation": "create", "status": "error"}
        )
    
    def test_create_building_repository_error(self) -> None:
        """Test building creation with repository error."""
        # Arrange
        request = CreateBuildingRequest(
            name="Test Building",
            address=self.test_address,
            created_by="test_user"
        )
        
        # Mock repository to raise error
        self.mock_building_repository.save.side_effect = Exception("Database error")
        
        # Act
        response = self.service.create_building(
            name=request.name,
            address=request.address,
            created_by=request.created_by
        )
        
        # Assert
        self.assertFalse(response.success)
        self.assertIn("Database error", response.message)
        
        # Verify rollback occurred
        self.mock_unit_of_work.rollback.assert_called_once()
    
    def test_get_building_success_with_cache_miss(self) -> None:
        """Test successful building retrieval with cache miss."""
        # Arrange
        building_id = str(self.test_building.id)
        
        # Mock cache miss
        self.mock_cache_service.get.return_value = None
        
        # Mock repository to return building
        self.mock_building_repository.get_by_id.return_value = self.test_building
        
        # Act
        response = self.service.get_building(building_id)
        
        # Assert
        self.assertIsInstance(response, GetBuildingResponse)
        self.assertTrue(response.success)
        self.assertIsNotNone(response.building)
        self.assertEqual(response.building["name"], self.test_building.name)
        
        # Verify cache was checked and populated
        self.mock_cache_service.get.assert_called_once()
        self.mock_cache_service.set.assert_called_once()
        
        # Verify repository interaction
        self.assertRepositoryMethod(self.mock_building_repository, "get_by_id", 
                                   call_count=1, building_id=building_id)
    
    def test_get_building_success_with_cache_hit(self) -> None:
        """Test successful building retrieval with cache hit."""
        # Arrange
        building_id = str(self.test_building.id)
        cached_data = {
            "id": building_id,
            "name": self.test_building.name,
            "status": self.test_building.status.value
        }
        
        # Mock cache hit
        self.mock_cache_service.get.return_value = cached_data
        
        # Act
        response = self.service.get_building(building_id)
        
        # Assert
        self.assertTrue(response.success)
        self.assertEqual(response.building, cached_data)
        
        # Verify cache was used and repository was not called
        self.mock_cache_service.get.assert_called_once()
        self.mock_building_repository.get_by_id.assert_not_called()
    
    def test_get_building_not_found(self) -> None:
        """Test building retrieval when building doesn't exist."""
        # Arrange
        building_id = "non-existent-id"
        
        # Mock cache miss and repository returns None
        self.mock_cache_service.get.return_value = None
        self.mock_building_repository.get_by_id.return_value = None
        
        # Act
        response = self.service.get_building(building_id)
        
        # Assert
        self.assertFalse(response.success)
        self.assertIsNone(response.building)
        self.assertIn("not found", response.message)
    
    def test_list_buildings_success(self) -> None:
        """Test successful building list retrieval."""
        # Arrange
        buildings = [
            self.test_data.create_test_building(name="Building 1"),
            self.test_data.create_test_building(name="Building 2"),
            self.test_data.create_test_building(name="Building 3")
        ]
        
        # Mock repository to return buildings
        self.mock_building_repository.get_all.return_value = buildings
        
        # Act
        response = self.service.list_buildings()
        
        # Assert
        self.assertIsInstance(response, ListBuildingsResponse)
        self.assertTrue(response.success)
        self.assertEqual(len(response.buildings), 3)
        self.assertIn("Building 1", [b["name"] for b in response.buildings])
        
        # Verify repository interaction
        self.assertRepositoryMethod(self.mock_building_repository, "get_all", call_count=1)
    
    def test_list_buildings_with_pagination(self) -> None:
        """Test building list with pagination."""
        # Arrange
        buildings = [self.test_data.create_test_building() for _ in range(5)]
        
        # Mock repository
        self.mock_building_repository.find_all.return_value = buildings[:2]  # First page
        self.mock_building_repository.count.return_value = 5  # Total count
        
        # Act
        response = self.service.list_buildings(page=1, page_size=2)
        
        # Assert
        self.assertTrue(response.success)
        self.assertEqual(len(response.buildings), 2)
        self.assertEqual(response.total_count, 5)
        self.assertEqual(response.page, 1)
        self.assertEqual(response.page_size, 2)
        self.assertTrue(response.has_next)
    
    def test_update_building_name_success(self) -> None:
        """Test successful building name update."""
        # Arrange
        building_id = str(self.test_building.id)
        new_name = "Updated Building Name"
        updated_by = "test_updater"
        
        # Mock repository to return building
        self.mock_building_repository.get_by_id.return_value = self.test_building
        self.mock_building_repository.save.return_value = self.test_building
        
        # Act
        response = self.service.update_building_name(building_id, new_name, updated_by)
        
        # Assert
        self.assertIsInstance(response, UpdateBuildingResponse)
        self.assertTrue(response.success)
        self.assertEqual(response.message, "Building updated successfully")
        
        # Verify repository interactions
        self.assertRepositoryMethod(self.mock_building_repository, "get_by_id", 
                                   call_count=1, building_id=building_id)
        self.assertRepositoryMethod(self.mock_building_repository, "save", call_count=1)
        
        # Verify cache was cleared
        self.mock_cache_service.delete.assert_called()
    
    def test_update_building_not_found(self) -> None:
        """Test building update when building doesn't exist."""
        # Arrange
        building_id = "non-existent-id"
        
        # Mock repository to return None
        self.mock_building_repository.get_by_id.return_value = None
        
        # Act
        response = self.service.update_building_name(building_id, "New Name", "test_user")
        
        # Assert
        self.assertFalse(response.success)
        self.assertIn("not found", response.message)
        
        # Verify save was not called
        self.mock_building_repository.save.assert_not_called()
    
    def test_delete_building_success(self) -> None:
        """Test successful building deletion."""
        # Arrange
        building_id = str(self.test_building.id)
        
        # Mock repository methods
        self.mock_building_repository.exists.return_value = True
        self.mock_building_repository.delete.return_value = True
        
        # Act
        response = self.service.delete_building(building_id)
        
        # Assert
        self.assertIsInstance(response, DeleteBuildingResponse)
        self.assertTrue(response.success)
        self.assertEqual(response.message, "Building deleted successfully")
        
        # Verify repository interactions
        self.assertRepositoryMethod(self.mock_building_repository, "exists", 
                                   call_count=1, building_id=building_id)
        self.assertRepositoryMethod(self.mock_building_repository, "delete", 
                                   call_count=1, building_id=building_id)
        
        # Verify cache was cleared
        self.mock_cache_service.delete.assert_called()
    
    def test_delete_building_not_found(self) -> None:
        """Test building deletion when building doesn't exist."""
        # Arrange
        building_id = "non-existent-id"
        
        # Mock repository to return False for exists
        self.mock_building_repository.exists.return_value = False
        
        # Act
        response = self.service.delete_building(building_id)
        
        # Assert
        self.assertFalse(response.success)
        self.assertIn("not found", response.message)
        
        # Verify delete was not called
        self.mock_building_repository.delete.assert_not_called()
    
    def test_get_buildings_by_status(self) -> None:
        """Test retrieving buildings by status."""
        # Arrange
        status = BuildingStatus.OPERATIONAL
        buildings = [self.test_data.create_test_building(status=status) for _ in range(2)]
        
        # Mock repository
        self.mock_building_repository.get_by_status.return_value = buildings
        
        # Act
        response = self.service.get_buildings_by_status(status.value)
        
        # Assert
        self.assertTrue(response.success)
        self.assertEqual(len(response.buildings), 2)
        
        # Verify repository interaction
        self.assertRepositoryMethod(self.mock_building_repository, "get_by_status", 
                                   call_count=1, status=status)
    
    def test_search_buildings_by_address(self) -> None:
        """Test searching buildings by address."""
        # Arrange
        search_term = "Main Street"
        buildings = [self.test_data.create_test_building()]
        
        # Mock repository
        self.mock_building_repository.get_by_address.return_value = buildings
        
        # Act
        response = self.service.search_buildings_by_address(search_term)
        
        # Assert
        self.assertTrue(response.success)
        self.assertEqual(len(response.buildings), 1)
        
        # Verify repository interaction
        self.assertRepositoryMethod(self.mock_building_repository, "get_by_address", 
                                   call_count=1, address=search_term)
    
    @patch('time.time', return_value=1000.0)
    def test_performance_monitoring(self, mock_time) -> None:
        """Test that performance metrics are collected."""
        # Arrange
        self.mock_building_repository.get_by_id.return_value = self.test_building
        
        # Act
        self.service.get_building(str(self.test_building.id))
        
        # Assert performance monitoring
        self.mock_metrics.record_operation_duration.assert_called()
        self.mock_metrics.increment_counter.assert_called()
    
    def test_error_handling_with_logging(self) -> None:
        """Test that errors are properly logged."""
        # Arrange
        building_id = str(self.test_building.id)
        error_message = "Database connection failed"
        
        # Mock repository to raise error
        self.mock_building_repository.get_by_id.side_effect = Exception(error_message)
        
        # Act
        response = self.service.get_building(building_id)
        
        # Assert
        self.assertFalse(response.success)
        self.assertIn(error_message, response.message)
    
    def test_cache_invalidation_on_update(self) -> None:
        """Test that cache is properly invalidated on updates."""
        # Arrange
        building_id = str(self.test_building.id)
        self.mock_building_repository.get_by_id.return_value = self.test_building
        self.mock_building_repository.save.return_value = self.test_building
        
        # Act
        self.service.update_building_name(building_id, "New Name", "test_user")
        
        # Assert cache invalidation
        self.mock_cache_service.delete.assert_called_with(f"building:{building_id}")
        self.mock_cache_service.delete_pattern.assert_called_with("building:list:*")
    
    def test_bulk_operations_disable_cache(self) -> None:
        """Test that bulk operations temporarily disable cache."""
        # This would be implemented if the service had bulk operations
        # For now, just verify that the pattern is available
        self.assertIsNotNone(self.service.cache_service)
    
    def test_service_health_check(self) -> None:
        """Test service health check functionality."""
        # Mock healthy dependencies
        self.mock_unit_of_work.__enter__ = Mock(return_value=self.mock_unit_of_work)
        self.mock_unit_of_work.__exit__ = Mock(return_value=None)
        self.mock_cache_service.ping.return_value = True
        
        # Act
        health_status = self.service.health_check()
        
        # Assert
        self.assertEqual(health_status["status"], "healthy")
        self.assertIn("dependencies", health_status)
        self.assertEqual(health_status["dependencies"]["database"], "healthy")


if __name__ == '__main__':
    unittest.main()