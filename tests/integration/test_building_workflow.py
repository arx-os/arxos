"""
Integration tests for Building Management Workflows.

Tests complete workflows from API layer through application services
to repository layer, ensuring all components work together correctly.
"""

import pytest
from typing import Dict, Any, List
from datetime import datetime

from tests.framework.test_base import IntegrationTestCase
from application.services.building_service import BuildingApplicationService
from application.dto.building_dto import (
    CreateBuildingRequest, UpdateBuildingRequest,
    GetBuildingResponse, ListBuildingsResponse
)
from domain.entities import Building
from domain.value_objects import BuildingStatus
from domain.exceptions import BuildingNotFoundError
from application.exceptions import ApplicationError
from infrastructure.services.cache_service import RedisCacheService
from infrastructure.logging.structured_logging import get_logger

logger = get_logger(__name__)


class TestBuildingWorkflowIntegration(IntegrationTestCase):
    """Integration tests for complete building management workflows."""
    
    def setUp(self) -> None:
        """Set up integration test with real services."""
        super().setUp()
        
        # Create real application service with test database
        self.cache_service = RedisCacheService() if self.config.cache_enabled else None
        self.building_service = BuildingApplicationService(
            unit_of_work=self.unit_of_work,
            cache_service=self.cache_service
        )
    
    def test_complete_building_lifecycle_workflow(self) -> None:
        """Test complete building lifecycle from creation to deletion."""
        # Phase 1: Create Building
        create_response = self.building_service.create_building(
            name="Lifecycle Test Building",
            address={
                "street": "123 Integration Test St",
                "city": "Test City",
                "state": "TS",
                "postal_code": "12345"
            },
            description="Building for lifecycle testing",
            created_by="test_integration_user"
        )
        
        self.assertTrue(create_response.success)
        self.assertIsNotNone(create_response.building_id)
        building_id = create_response.building_id
        
        # Phase 2: Retrieve Created Building
        get_response = self.building_service.get_building(building_id)
        self.assertTrue(get_response.success)
        self.assertIsNotNone(get_response.building)
        self.assertEqual(get_response.building["name"], "Lifecycle Test Building")
        self.assertEqual(get_response.building["status"], BuildingStatus.PLANNED.value)
        
        # Phase 3: Update Building Name
        update_response = self.building_service.update_building_name(
            building_id=building_id,
            new_name="Updated Lifecycle Building",
            updated_by="test_integration_user"
        )
        self.assertTrue(update_response.success)
        
        # Verify update
        updated_get_response = self.building_service.get_building(building_id)
        self.assertEqual(updated_get_response.building["name"], "Updated Lifecycle Building")
        
        # Phase 4: Update Building Status
        status_update_response = self.building_service.update_building_status(
            building_id=building_id,
            new_status=BuildingStatus.UNDER_CONSTRUCTION,
            updated_by="test_integration_user"
        )
        self.assertTrue(status_update_response.success)
        
        # Verify status update
        status_get_response = self.building_service.get_building(building_id)
        self.assertEqual(
            status_get_response.building["status"], 
            BuildingStatus.UNDER_CONSTRUCTION.value
        )
        
        # Phase 5: List Buildings (should include our building)
        list_response = self.building_service.list_buildings()
        self.assertTrue(list_response.success)
        self.assertGreaterEqual(len(list_response.buildings), 1)
        
        building_names = [b["name"] for b in list_response.buildings]
        self.assertIn("Updated Lifecycle Building", building_names)
        
        # Phase 6: Delete Building
        delete_response = self.building_service.delete_building(building_id)
        self.assertTrue(delete_response.success)
        
        # Verify deletion
        deleted_get_response = self.building_service.get_building(building_id)
        self.assertFalse(deleted_get_response.success)
        self.assertIn("not found", deleted_get_response.message)
    
    def test_building_hierarchy_workflow(self) -> None:
        """Test creating and managing a complete building hierarchy."""
        # Create test hierarchy using framework method
        hierarchy = self.create_test_building_hierarchy()
        building = hierarchy["building"]
        floor = hierarchy["floor"]
        rooms = hierarchy["rooms"]
        
        # Verify building exists and has correct associations
        get_response = self.building_service.get_building(str(building.id))
        self.assertTrue(get_response.success)
        
        # Verify we can retrieve building with its relationships
        building_data = get_response.building
        self.assertEqual(building_data["id"], str(building.id))
        self.assertEqual(building_data["name"], building.name)
        
        # Test querying buildings by status
        status_response = self.building_service.get_buildings_by_status(
            BuildingStatus.PLANNED.value
        )
        self.assertTrue(status_response.success)
        self.assertGreaterEqual(len(status_response.buildings), 1)
        
        # Verify our building is in the status query results
        building_ids = [b["id"] for b in status_response.buildings]
        self.assertIn(str(building.id), building_ids)
    
    def test_concurrent_building_operations(self) -> None:
        """Test concurrent building operations for data consistency."""
        import threading
        import time
        
        # Create base building
        create_response = self.building_service.create_building(
            name="Concurrent Test Building",
            address=self.test_data.create_test_address().__dict__,
            created_by="concurrent_test_user"
        )
        building_id = create_response.building_id
        
        # Results storage for threads
        thread_results = []
        
        def concurrent_update(thread_id: int, new_name: str):
            """Function to run concurrent updates."""
            try:
                response = self.building_service.update_building_name(
                    building_id=building_id,
                    new_name=new_name,
                    updated_by=f"thread_{thread_id}"
                )
                thread_results.append({
                    "thread_id": thread_id,
                    "success": response.success,
                    "name": new_name
                })
            except Exception as e:
                thread_results.append({
                    "thread_id": thread_id,
                    "success": False,
                    "error": str(e)
                })
        
        # Start concurrent update threads
        threads = []
        for i in range(3):
            thread = threading.Thread(
                target=concurrent_update, 
                args=(i, f"Concurrent Building {i}")
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify at least one update succeeded
        successful_updates = [r for r in thread_results if r["success"]]
        self.assertGreater(len(successful_updates), 0)
        
        # Verify final building state is consistent
        final_response = self.building_service.get_building(building_id)
        self.assertTrue(final_response.success)
        self.assertIn("Concurrent Building", final_response.building["name"])
    
    def test_bulk_building_operations_workflow(self) -> None:
        """Test bulk operations workflow with transaction integrity."""
        # Prepare bulk building data
        bulk_buildings = []
        for i in range(10):
            building_data = {
                "name": f"Bulk Building {i:02d}",
                "address": {
                    "street": f"{i*100} Bulk Street",
                    "city": "Bulk City",
                    "state": "BK",
                    "postal_code": f"{i:05d}"
                },
                "description": f"Bulk building number {i}",
                "created_by": "bulk_test_user"
            }
            bulk_buildings.append(building_data)
        
        # Create buildings one by one (simulating bulk operation)
        created_building_ids = []
        for building_data in bulk_buildings:
            response = self.building_service.create_building(**building_data)
            if response.success:
                created_building_ids.append(response.building_id)
        
        # Verify all buildings were created
        self.assertEqual(len(created_building_ids), 10)
        
        # Test bulk status update workflow
        for building_id in created_building_ids[:5]:  # Update first 5
            self.building_service.update_building_status(
                building_id=building_id,
                new_status=BuildingStatus.UNDER_CONSTRUCTION,
                updated_by="bulk_status_updater"
            )
        
        # Verify status updates
        construction_buildings = self.building_service.get_buildings_by_status(
            BuildingStatus.UNDER_CONSTRUCTION.value
        )
        self.assertGreaterEqual(len(construction_buildings.buildings), 5)
        
        # Test bulk cleanup
        for building_id in created_building_ids:
            delete_response = self.building_service.delete_building(building_id)
            self.assertTrue(delete_response.success)
    
    def test_error_handling_and_rollback_workflow(self) -> None:
        """Test error handling and transaction rollback in workflows."""
        # Test creation with invalid data
        invalid_response = self.building_service.create_building(
            name="",  # Invalid empty name
            address=self.test_data.create_test_address().__dict__,
            created_by="error_test_user"
        )
        self.assertFalse(invalid_response.success)
        self.assertIn("name cannot be empty", invalid_response.message)
        
        # Test operations on non-existent building
        non_existent_id = "non-existent-building-id"
        
        get_response = self.building_service.get_building(non_existent_id)
        self.assertFalse(get_response.success)
        self.assertIn("not found", get_response.message)
        
        update_response = self.building_service.update_building_name(
            building_id=non_existent_id,
            new_name="New Name",
            updated_by="error_test_user"
        )
        self.assertFalse(update_response.success)
        self.assertIn("not found", update_response.message)
        
        delete_response = self.building_service.delete_building(non_existent_id)
        self.assertFalse(delete_response.success)
        self.assertIn("not found", delete_response.message)
    
    def test_caching_integration_workflow(self) -> None:
        """Test caching behavior in complete workflows."""
        if not self.cache_service:
            self.skipTest("Cache service not available for testing")
        
        # Create building
        create_response = self.building_service.create_building(
            name="Cache Test Building",
            address=self.test_data.create_test_address().__dict__,
            created_by="cache_test_user"
        )
        building_id = create_response.building_id
        
        # First retrieval (cache miss)
        first_get = self.building_service.get_building(building_id)
        self.assertTrue(first_get.success)
        
        # Second retrieval (should be cache hit)
        second_get = self.building_service.get_building(building_id)
        self.assertTrue(second_get.success)
        self.assertEqual(first_get.building, second_get.building)
        
        # Update building (should invalidate cache)
        update_response = self.building_service.update_building_name(
            building_id=building_id,
            new_name="Updated Cache Building",
            updated_by="cache_test_user"
        )
        self.assertTrue(update_response.success)
        
        # Retrieve after update (cache should be fresh)
        updated_get = self.building_service.get_building(building_id)
        self.assertTrue(updated_get.success)
        self.assertEqual(updated_get.building["name"], "Updated Cache Building")
        self.assertNotEqual(updated_get.building["name"], first_get.building["name"])
    
    def test_search_and_filtering_workflow(self) -> None:
        """Test search and filtering workflows."""
        # Create buildings with different addresses
        test_buildings = [
            {
                "name": "Downtown Office",
                "address": {
                    "street": "123 Main Street",
                    "city": "Downtown",
                    "state": "DT",
                    "postal_code": "12345"
                }
            },
            {
                "name": "Suburban Store",
                "address": {
                    "street": "456 Oak Avenue",
                    "city": "Suburbia",
                    "state": "SB", 
                    "postal_code": "67890"
                }
            },
            {
                "name": "Industrial Warehouse",
                "address": {
                    "street": "789 Industrial Blvd",
                    "city": "Industrial Park",
                    "state": "IP",
                    "postal_code": "11111"
                }
            }
        ]
        
        # Create all test buildings
        created_ids = []
        for building_data in test_buildings:
            response = self.building_service.create_building(
                created_by="search_test_user",
                **building_data
            )
            self.assertTrue(response.success)
            created_ids.append(response.building_id)
        
        # Test address-based search
        main_street_results = self.building_service.search_buildings_by_address("Main Street")
        self.assertTrue(main_street_results.success)
        self.assertGreater(len(main_street_results.buildings), 0)
        
        downtown_names = [b["name"] for b in main_street_results.buildings]
        self.assertIn("Downtown Office", downtown_names)
        
        # Test status filtering (all should be PLANNED initially)
        planned_buildings = self.building_service.get_buildings_by_status(
            BuildingStatus.PLANNED.value
        )
        self.assertTrue(planned_buildings.success)
        self.assertGreaterEqual(len(planned_buildings.buildings), 3)
        
        # Update one building status and test filtering
        self.building_service.update_building_status(
            building_id=created_ids[0],
            new_status=BuildingStatus.UNDER_CONSTRUCTION,
            updated_by="search_test_user"
        )
        
        construction_buildings = self.building_service.get_buildings_by_status(
            BuildingStatus.UNDER_CONSTRUCTION.value
        )
        self.assertTrue(construction_buildings.success)
        self.assertGreaterEqual(len(construction_buildings.buildings), 1)
    
    def test_pagination_workflow(self) -> None:
        """Test pagination in list operations."""
        # Create multiple buildings for pagination testing
        building_count = 15
        created_ids = []
        
        for i in range(building_count):
            response = self.building_service.create_building(
                name=f"Pagination Building {i:02d}",
                address={
                    "street": f"{i} Pagination St",
                    "city": "Page City",
                    "state": "PG",
                    "postal_code": f"{i:05d}"
                },
                created_by="pagination_test_user"
            )
            self.assertTrue(response.success)
            created_ids.append(response.building_id)
        
        # Test first page
        first_page = self.building_service.list_buildings(page=1, page_size=5)
        self.assertTrue(first_page.success)
        self.assertEqual(len(first_page.buildings), 5)
        self.assertEqual(first_page.page, 1)
        self.assertEqual(first_page.page_size, 5)
        self.assertTrue(first_page.has_next)
        self.assertFalse(first_page.has_prev)
        
        # Test second page
        second_page = self.building_service.list_buildings(page=2, page_size=5)
        self.assertTrue(second_page.success)
        self.assertEqual(len(second_page.buildings), 5)
        self.assertEqual(second_page.page, 2)
        self.assertTrue(second_page.has_next)
        self.assertTrue(second_page.has_prev)
        
        # Test last page
        last_page = self.building_service.list_buildings(page=3, page_size=5)
        self.assertTrue(last_page.success)
        self.assertGreaterEqual(len(last_page.buildings), 5)  # At least our 15 buildings
        self.assertEqual(last_page.page, 3)
        # has_next depends on total buildings in database
        self.assertTrue(last_page.has_prev)
        
        # Verify no duplicate buildings across pages
        first_page_ids = {b["id"] for b in first_page.buildings}
        second_page_ids = {b["id"] for b in second_page.buildings}
        self.assertEqual(len(first_page_ids.intersection(second_page_ids)), 0)


if __name__ == '__main__':
    import unittest
    unittest.main()