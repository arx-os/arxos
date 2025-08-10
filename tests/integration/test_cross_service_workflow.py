"""
Integration tests for Cross-Service Workflows.

Tests workflows that span multiple application services and domain boundaries,
ensuring proper coordination and data consistency across services.
"""

import pytest
from typing import Dict, Any, List
from datetime import datetime, timedelta

from tests.framework.test_base import IntegrationTestCase
from application.services.building_service import BuildingApplicationService
from application.services.floor_service import FloorApplicationService
from application.services.room_service import RoomApplicationService
from application.services.device_service import DeviceApplicationService
from application.services.user_service import UserApplicationService
from domain.value_objects import BuildingStatus, FloorStatus, RoomStatus, DeviceStatus
from domain.exceptions import BusinessRuleViolationError
from infrastructure.logging.structured_logging import get_logger, log_context

logger = get_logger(__name__)


class TestCrossServiceWorkflowIntegration(IntegrationTestCase):
    """Integration tests for workflows spanning multiple services."""
    
    def setUp(self) -> None:
        """Set up integration test with multiple real services."""
        super().setUp()
        
        # Create all application services with shared unit of work
        self.building_service = BuildingApplicationService(unit_of_work=self.unit_of_work)
        self.floor_service = FloorApplicationService(unit_of_work=self.unit_of_work)
        self.room_service = RoomApplicationService(unit_of_work=self.unit_of_work)
        self.device_service = DeviceApplicationService(unit_of_work=self.unit_of_work)
        self.user_service = UserApplicationService(unit_of_work=self.unit_of_work)
    
    def test_complete_building_setup_workflow(self) -> None:
        """Test complete building setup from creation to device installation."""
        with log_context(operation="complete_building_setup"):
            # Phase 1: Create User who will own the building
            user_response = self.user_service.create_user(
                username="building_owner",
                email="owner@example.com",
                first_name="Building",
                last_name="Owner",
                created_by="system_admin"
            )
            self.assertTrue(user_response.success)
            user_id = user_response.user_id
            
            # Phase 2: Create Building
            building_response = self.building_service.create_building(
                name="Complete Setup Building",
                address={
                    "street": "100 Setup Street",
                    "city": "Setup City",
                    "state": "SC",
                    "postal_code": "12345"
                },
                description="Building for complete setup workflow testing",
                created_by=user_id
            )
            self.assertTrue(building_response.success)
            building_id = building_response.building_id
            
            # Phase 3: Add Multiple Floors
            floor_ids = []
            for floor_num in [1, 2, 3]:
                floor_response = self.floor_service.create_floor(
                    building_id=building_id,
                    name=f"Floor {floor_num}",
                    floor_number=floor_num,
                    description=f"Floor {floor_num} for setup testing",
                    created_by=user_id
                )
                self.assertTrue(floor_response.success)
                floor_ids.append(floor_response.floor_id)
            
            # Phase 4: Add Rooms to Each Floor
            room_ids = []
            room_types = ["office", "conference", "storage", "restroom"]
            
            for floor_idx, floor_id in enumerate(floor_ids):
                for room_num in range(1, 5):  # 4 rooms per floor
                    room_response = self.room_service.create_room(
                        floor_id=floor_id,
                        name=f"Room {floor_idx+1}{room_num:02d}",
                        room_number=f"{floor_idx+1}{room_num:02d}",
                        room_type=room_types[room_num-1],
                        description=f"Room {room_num} on floor {floor_idx+1}",
                        area=25.0,  # 25 sq meters
                        created_by=user_id
                    )
                    self.assertTrue(room_response.success)
                    room_ids.append(room_response.room_id)
            
            # Phase 5: Install Devices in Rooms
            device_types = ["sensor", "camera", "access_control", "hvac"]
            device_ids = []
            
            for room_idx, room_id in enumerate(room_ids[:8]):  # Install in first 8 rooms
                device_response = self.device_service.create_device(
                    room_id=room_id,
                    name=f"Device-{room_idx+1:03d}",
                    device_id=f"DEV_{room_idx+1:03d}",
                    device_type=device_types[room_idx % len(device_types)],
                    manufacturer="SetupTech",
                    model=f"ST-{device_types[room_idx % len(device_types)].upper()}-v1",
                    created_by=user_id
                )
                self.assertTrue(device_response.success)
                device_ids.append(device_response.device_id)
            
            # Phase 6: Verify Complete Hierarchy
            # Verify building exists and has correct data
            building_check = self.building_service.get_building(building_id)
            self.assertTrue(building_check.success)
            self.assertEqual(building_check.building["name"], "Complete Setup Building")
            
            # Verify floors exist
            for floor_id in floor_ids:
                floor_check = self.floor_service.get_floor(floor_id)
                self.assertTrue(floor_check.success)
                self.assertEqual(floor_check.floor["building_id"], building_id)
            
            # Verify rooms exist and are properly associated
            for room_id in room_ids:
                room_check = self.room_service.get_room(room_id)
                self.assertTrue(room_check.success)
                self.assertIn(room_check.room["floor_id"], floor_ids)
            
            # Verify devices exist and are properly associated
            for device_id in device_ids:
                device_check = self.device_service.get_device(device_id)
                self.assertTrue(device_check.success)
                self.assertIn(device_check.device["room_id"], room_ids)
            
            # Phase 7: Test Cross-Service Queries
            # Get all floors for building
            building_floors = self.floor_service.get_floors_by_building(building_id)
            self.assertTrue(building_floors.success)
            self.assertEqual(len(building_floors.floors), 3)
            
            # Get all rooms for first floor
            floor_rooms = self.room_service.get_rooms_by_floor(floor_ids[0])
            self.assertTrue(floor_rooms.success)
            self.assertEqual(len(floor_rooms.rooms), 4)
            
            # Get all devices by type
            sensor_devices = self.device_service.get_devices_by_type("sensor")
            self.assertTrue(sensor_devices.success)
            self.assertGreaterEqual(len(sensor_devices.devices), 2)  # At least 2 sensors installed
    
    def test_building_status_propagation_workflow(self) -> None:
        """Test status changes propagating through building hierarchy."""
        # Create basic hierarchy
        hierarchy = self.create_test_building_hierarchy()
        building_id = str(hierarchy["building"].id)
        floor_id = str(hierarchy["floor"].id)
        room_ids = [str(room.id) for room in hierarchy["rooms"]]
        
        # Install devices in rooms
        device_ids = []
        for i, room_id in enumerate(room_ids):
            device_response = self.device_service.create_device(
                room_id=room_id,
                name=f"Status Test Device {i+1}",
                device_id=f"STATUS_DEV_{i+1:03d}",
                device_type="sensor",
                manufacturer="StatusTech",
                model="ST-SENSOR-v1",
                created_by="status_test_user"
            )
            self.assertTrue(device_response.success)
            device_ids.append(device_response.device_id)
        
        # Phase 1: Set building to Under Construction
        building_status_response = self.building_service.update_building_status(
            building_id=building_id,
            new_status=BuildingStatus.UNDER_CONSTRUCTION,
            updated_by="status_test_user"
        )
        self.assertTrue(building_status_response.success)
        
        # Phase 2: Update floor status to match
        floor_status_response = self.floor_service.update_floor_status(
            floor_id=floor_id,
            new_status=FloorStatus.UNDER_CONSTRUCTION,
            updated_by="status_test_user"
        )
        self.assertTrue(floor_status_response.success)
        
        # Phase 3: Update room statuses
        for room_id in room_ids:
            room_status_response = self.room_service.update_room_status(
                room_id=room_id,
                new_status=RoomStatus.UNDER_CONSTRUCTION,
                updated_by="status_test_user"
            )
            self.assertTrue(room_status_response.success)
        
        # Phase 4: Set devices to maintenance during construction
        for device_id in device_ids:
            device_status_response = self.device_service.update_device_status(
                device_id=device_id,
                new_status=DeviceStatus.MAINTENANCE,
                updated_by="status_test_user"
            )
            self.assertTrue(device_status_response.success)
        
        # Phase 5: Complete construction workflow
        # Building completed
        self.building_service.update_building_status(
            building_id=building_id,
            new_status=BuildingStatus.COMPLETED,
            updated_by="status_test_user"
        )
        
        # Floor completed
        self.floor_service.update_floor_status(
            floor_id=floor_id,
            new_status=FloorStatus.OPERATIONAL,
            updated_by="status_test_user"
        )
        
        # Rooms operational
        for room_id in room_ids:
            self.room_service.update_room_status(
                room_id=room_id,
                new_status=RoomStatus.OPERATIONAL,
                updated_by="status_test_user"
            )
        
        # Devices operational
        for device_id in device_ids:
            self.device_service.update_device_status(
                device_id=device_id,
                new_status=DeviceStatus.OPERATIONAL,
                updated_by="status_test_user"
            )
        
        # Verify final status consistency
        final_building = self.building_service.get_building(building_id)
        final_floor = self.floor_service.get_floor(floor_id)
        
        self.assertEqual(final_building.building["status"], BuildingStatus.COMPLETED.value)
        self.assertEqual(final_floor.floor["status"], FloorStatus.OPERATIONAL.value)
        
        for room_id in room_ids:
            room_check = self.room_service.get_room(room_id)
            self.assertEqual(room_check.room["status"], RoomStatus.OPERATIONAL.value)
        
        for device_id in device_ids:
            device_check = self.device_service.get_device(device_id)
            self.assertEqual(device_check.device["status"], DeviceStatus.OPERATIONAL.value)
    
    def test_user_permission_workflow(self) -> None:
        """Test user permissions across different services."""
        # Create users with different roles
        admin_response = self.user_service.create_user(
            username="admin_user",
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            role="admin",
            created_by="system"
        )
        self.assertTrue(admin_response.success)
        admin_id = admin_response.user_id
        
        manager_response = self.user_service.create_user(
            username="manager_user",
            email="manager@example.com",
            first_name="Manager",
            last_name="User",
            role="manager",
            created_by=admin_id
        )
        self.assertTrue(manager_response.success)
        manager_id = manager_response.user_id
        
        operator_response = self.user_service.create_user(
            username="operator_user",
            email="operator@example.com",
            first_name="Operator",
            last_name="User",
            role="operator",
            created_by=admin_id
        )
        self.assertTrue(operator_response.success)
        operator_id = operator_response.user_id
        
        # Admin creates building
        building_response = self.building_service.create_building(
            name="Permission Test Building",
            address=self.test_data.create_test_address().__dict__,
            created_by=admin_id
        )
        self.assertTrue(building_response.success)
        building_id = building_response.building_id
        
        # Manager adds floor
        floor_response = self.floor_service.create_floor(
            building_id=building_id,
            name="Permission Test Floor",
            floor_number=1,
            created_by=manager_id
        )
        self.assertTrue(floor_response.success)
        floor_id = floor_response.floor_id
        
        # Operator adds room
        room_response = self.room_service.create_room(
            floor_id=floor_id,
            name="Permission Test Room",
            room_number="101",
            room_type="office",
            area=20.0,
            created_by=operator_id
        )
        self.assertTrue(room_response.success)
        room_id = room_response.room_id
        
        # Verify all users can view the hierarchy they created
        admin_building_check = self.building_service.get_building(building_id)
        manager_floor_check = self.floor_service.get_floor(floor_id)
        operator_room_check = self.room_service.get_room(room_id)
        
        self.assertTrue(admin_building_check.success)
        self.assertTrue(manager_floor_check.success)
        self.assertTrue(operator_room_check.success)
        
        # Verify creation audit trail
        self.assertEqual(admin_building_check.building["created_by"], admin_id)
        self.assertEqual(manager_floor_check.floor["created_by"], manager_id)
        self.assertEqual(operator_room_check.room["created_by"], operator_id)
    
    def test_data_consistency_across_services(self) -> None:
        """Test data consistency when operations span multiple services."""
        # Create base hierarchy
        hierarchy = self.create_test_building_hierarchy()
        building = hierarchy["building"]
        floor = hierarchy["floor"]
        rooms = hierarchy["rooms"]
        
        # Add devices to rooms
        device_ids = []
        for i, room in enumerate(rooms):
            device_response = self.device_service.create_device(
                room_id=str(room.id),
                name=f"Consistency Device {i+1}",
                device_id=f"CONS_DEV_{i+1:03d}",
                device_type="sensor",
                manufacturer="ConsistencyTech",
                model="CT-SENSOR-v1",
                created_by="consistency_test_user"
            )
            self.assertTrue(device_response.success)
            device_ids.append(device_response.device_id)
        
        # Test referential integrity
        # Try to delete floor that has rooms (should fail or handle gracefully)
        floor_delete_response = self.floor_service.delete_floor(str(floor.id))
        
        # Depending on implementation, this should either:
        # 1. Fail due to referential integrity constraints, or
        # 2. Succeed with cascade delete of dependent entities
        # We'll verify the building hierarchy remains consistent
        
        if not floor_delete_response.success:
            # If deletion failed, verify everything still exists
            floor_check = self.floor_service.get_floor(str(floor.id))
            self.assertTrue(floor_check.success)
            
            for room in rooms:
                room_check = self.room_service.get_room(str(room.id))
                self.assertTrue(room_check.success)
            
            for device_id in device_ids:
                device_check = self.device_service.get_device(device_id)
                self.assertTrue(device_check.success)
        else:
            # If deletion succeeded, verify cascade behavior
            floor_check = self.floor_service.get_floor(str(floor.id))
            self.assertFalse(floor_check.success)
            
            # Check if rooms were cascade deleted
            for room in rooms:
                room_check = self.room_service.get_room(str(room.id))
                # Should be deleted if cascade is implemented
                if not room_check.success:
                    # Verify devices were also cascade deleted
                    for device_id in device_ids:
                        device_check = self.device_service.get_device(device_id)
                        self.assertFalse(device_check.success)
    
    def test_cross_service_search_workflow(self) -> None:
        """Test search operations that span multiple services."""
        # Create searchable hierarchy
        building_response = self.building_service.create_building(
            name="Global Search Building",
            address={
                "street": "123 Search Street",
                "city": "Search City",
                "state": "SC",
                "postal_code": "12345"
            },
            description="Building for global search testing",
            created_by="search_test_user"
        )
        building_id = building_response.building_id
        
        # Add floor with searchable name
        floor_response = self.floor_service.create_floor(
            building_id=building_id,
            name="Executive Search Floor",
            floor_number=1,
            description="Executive offices floor",
            created_by="search_test_user"
        )
        floor_id = floor_response.floor_id
        
        # Add rooms with searchable names and types
        room_types = ["executive_office", "conference", "executive_lounge"]
        room_ids = []
        
        for i, room_type in enumerate(room_types):
            room_response = self.room_service.create_room(
                floor_id=floor_id,
                name=f"Executive {room_type.replace('_', ' ').title()} {i+1}",
                room_number=f"E{i+1:02d}",
                room_type=room_type,
                area=30.0,
                created_by="search_test_user"
            )
            room_ids.append(room_response.room_id)
        
        # Add devices with searchable properties
        device_manufacturers = ["SearchTech", "GlobalDevices", "SmartSystems"]
        device_ids = []
        
        for i, room_id in enumerate(room_ids):
            device_response = self.device_service.create_device(
                room_id=room_id,
                name=f"Executive Device {i+1}",
                device_id=f"EXEC_DEV_{i+1:03d}",
                device_type="smart_sensor",
                manufacturer=device_manufacturers[i],
                model=f"ES-{i+1:03d}",
                created_by="search_test_user"
            )
            device_ids.append(device_response.device_id)
        
        # Test cross-service search operations
        
        # Search buildings by address
        address_search = self.building_service.search_buildings_by_address("Search Street")
        self.assertTrue(address_search.success)
        search_names = [b["name"] for b in address_search.buildings]
        self.assertIn("Global Search Building", search_names)
        
        # Search rooms by type
        executive_rooms = self.room_service.get_rooms_by_type("executive_office")
        self.assertTrue(executive_rooms.success)
        self.assertGreaterEqual(len(executive_rooms.rooms), 1)
        
        # Search devices by manufacturer
        searchtech_devices = self.device_service.get_devices_by_manufacturer("SearchTech")
        self.assertTrue(searchtech_devices.success)
        self.assertGreaterEqual(len(searchtech_devices.devices), 1)
        
        # Search devices by type across all rooms
        smart_sensors = self.device_service.get_devices_by_type("smart_sensor")
        self.assertTrue(smart_sensors.success)
        self.assertGreaterEqual(len(smart_sensors.devices), 3)
    
    def test_performance_across_services(self) -> None:
        """Test performance when operations span multiple services."""
        import time
        
        start_time = time.time()
        
        # Create a moderately complex hierarchy quickly
        building_response = self.building_service.create_building(
            name="Performance Test Building",
            address=self.test_data.create_test_address().__dict__,
            created_by="performance_test_user"
        )
        building_id = building_response.building_id
        
        # Add 5 floors
        floor_ids = []
        for i in range(5):
            floor_response = self.floor_service.create_floor(
                building_id=building_id,
                name=f"Performance Floor {i+1}",
                floor_number=i+1,
                created_by="performance_test_user"
            )
            floor_ids.append(floor_response.floor_id)
        
        # Add 3 rooms per floor (15 total)
        room_ids = []
        for floor_id in floor_ids:
            for j in range(3):
                room_response = self.room_service.create_room(
                    floor_id=floor_id,
                    name=f"Performance Room {j+1}",
                    room_number=f"R{j+1:02d}",
                    room_type="office",
                    area=15.0,
                    created_by="performance_test_user"
                )
                room_ids.append(room_response.room_id)
        
        # Add 1 device per room (15 total)
        device_ids = []
        for i, room_id in enumerate(room_ids):
            device_response = self.device_service.create_device(
                room_id=room_id,
                name=f"Performance Device {i+1}",
                device_id=f"PERF_DEV_{i+1:03d}",
                device_type="sensor",
                manufacturer="PerformanceTech",
                model="PT-SENSOR-v1",
                created_by="performance_test_user"
            )
            device_ids.append(device_response.device_id)
        
        creation_time = time.time() - start_time
        
        # Test bulk retrieval performance
        retrieval_start = time.time()
        
        # Get all floors for building
        floors_response = self.floor_service.get_floors_by_building(building_id)
        self.assertTrue(floors_response.success)
        self.assertEqual(len(floors_response.floors), 5)
        
        # Get all rooms for all floors
        all_rooms = []
        for floor_id in floor_ids:
            rooms_response = self.room_service.get_rooms_by_floor(floor_id)
            all_rooms.extend(rooms_response.rooms)
        
        self.assertEqual(len(all_rooms), 15)
        
        # Get all devices by type
        sensor_devices = self.device_service.get_devices_by_type("sensor")
        self.assertGreaterEqual(len(sensor_devices.devices), 15)
        
        retrieval_time = time.time() - retrieval_start
        
        # Performance assertions (adjust thresholds based on requirements)
        self.assertLess(creation_time, 5.0, "Creation workflow too slow")
        self.assertLess(retrieval_time, 2.0, "Retrieval workflow too slow")
        
        logger.info("Cross-service performance test completed", extra={
            "creation_time_seconds": round(creation_time, 2),
            "retrieval_time_seconds": round(retrieval_time, 2),
            "entities_created": {
                "buildings": 1,
                "floors": 5,
                "rooms": 15,
                "devices": 15
            }
        })


if __name__ == '__main__':
    import unittest
    unittest.main()