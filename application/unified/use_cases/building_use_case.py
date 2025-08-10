"""
Unified Use Case Implementation

This module provides unified use cases that eliminate duplication
and provide consistent business logic across the application.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from domain.unified.entities import Building  # Using Building for create path
from domain.unified.repositories import (
    BuildingRepository, FloorRepository, RoomRepository,
    DeviceRepository, UserRepository, ProjectRepository
)
from domain.unified.value_objects import (
    BuildingId, Address, Dimensions, BuildingStatus, FloorId, RoomId
)
from domain.unified.entities import Floor as UnifiedFloor, Room as UnifiedRoom, Device as UnifiedDevice
from domain.unified.exceptions import (
    InvalidBuildingError, BuildingNotFoundError,
    InvalidFloorError, FloorNotFoundError,
    InvalidRoomError, RoomNotFoundError,
    InvalidDeviceError, DeviceNotFoundError,
    InvalidUserError, UserNotFoundError,
    InvalidProjectError, ProjectNotFoundError
)

class UnifiedBuildingUseCase:
    """
    Unified use case for building operations.

    This use case provides a clean interface for building-related
    business operations, eliminating duplication and ensuring
    consistent business logic.
    """

    def __init__(
        self,
        building_repository: BuildingRepository,
        floor_repository: FloorRepository,
        room_repository: RoomRepository,
        device_repository: DeviceRepository,
        project_repository: ProjectRepository
    ):
        """Initialize the unified building use case."""
        self.building_repository = building_repository
        self.floor_repository = floor_repository
        self.room_repository = room_repository
        self.device_repository = device_repository
        self.project_repository = project_repository
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_building_with_floors(
        self,
        name: str,
        address: Address,
        floor_data: List[Dict[str, Any]],
        status: BuildingStatus = BuildingStatus.PLANNED,
        dimensions: Optional[Dimensions] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Building:
        """
        Create a building with floors.

        Args:
            name: Building name
            address: Building address
            floor_data: List of floor data dictionaries
            status: Building status
            dimensions: Building dimensions
            description: Building description
            created_by: User who created the building
            metadata: Additional metadata

        Returns:
            Created building with floors
        """
        # Create building
        building = Building.create(
            name=name,
            address=address,
            status=status,
            dimensions=dimensions,
            description=description,
            created_by=created_by,
            metadata=metadata or {}
        )

        # Save building
        saved_building = self.building_repository.save(building)

        # Create floors
        for floor_info in floor_data:
            floor = UnifiedFloor.create(
                building_id=saved_building.id,
                floor_number=floor_info["floor_number"],
                name=floor_info["name"],
                description=floor_info.get("description"),
                created_by=created_by
            )

            saved_floor = self.floor_repository.save(floor)
            saved_building.add_floor(saved_floor)

        # Update building with floors
        final_building = self.building_repository.save(saved_building)

        self.logger.info(f"Created building {final_building.id} with {len(floor_data)} floors")
        return final_building

    def get_building_hierarchy(self, building_id: str) -> Dict[str, Any]:
        """
        Get complete building hierarchy.

        Args:
            building_id: Building ID

        Returns:
            Dictionary with building hierarchy
        """
        building = self.building_repository.get_by_id(building_id)
        if not building:
            raise BuildingNotFoundError(f"Building with ID {building_id} not found")

        floors = self.floor_repository.get_by_building_id(building_id)

        hierarchy = {
            "building": building.to_dict(),
            "floors": []
        }

        for floor in floors:
            rooms = self.room_repository.get_by_floor_id(str(floor.id))

            floor_data = floor.to_dict()
            floor_data["rooms"] = []

            for room in rooms:
                devices = self.device_repository.get_by_room_id(str(room.id))

                room_data = room.to_dict()
                room_data["devices"] = [device.to_dict() for device in devices]

                floor_data["rooms"].append(room_data)

            hierarchy["floors"].append(floor_data)

        return hierarchy

    def add_floor_to_building(
        self,
        building_id: str,
        floor_number: int,
        name: str,
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> UnifiedFloor:
        """
        Add a floor to a building.

        Args:
            building_id: Building ID
            floor_number: Floor number
            name: Floor name
            description: Floor description
            created_by: User who created the floor

        Returns:
            Created floor
        """
        building = self.building_repository.get_by_id(building_id)
        if not building:
            raise BuildingNotFoundError(f"Building with ID {building_id} not found")

        # Check if floor number already exists
        existing_floor = self.floor_repository.get_by_floor_number(building_id, floor_number)
        if existing_floor:
            raise InvalidFloorError(f"Floor {floor_number} already exists in building {building_id}")

        floor = UnifiedFloor.create(
            building_id=BuildingId.from_string(building_id),
            floor_number=floor_number,
            name=name,
            description=description,
            created_by=created_by
        )

        saved_floor = self.floor_repository.save(floor)
        building.add_floor(saved_floor)

        self.building_repository.save(building)

        self.logger.info(f"Added floor {floor_number} to building {building_id}")
        return saved_floor

    def add_room_to_floor(
        self,
        floor_id: str,
        room_number: str,
        name: str,
        room_type: str = "general",
        dimensions: Optional[Dimensions] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> UnifiedRoom:
        """
        Add a room to a floor.

        Args:
            floor_id: Floor ID
            room_number: Room number
            name: Room name
            room_type: Room type
            dimensions: Room dimensions
            description: Room description
            created_by: User who created the room

        Returns:
            Created room
        """
        floor = self.floor_repository.get_by_id(floor_id)
        if not floor:
            raise FloorNotFoundError(f"Floor with ID {floor_id} not found")

        # Check if room number already exists
        existing_room = self.room_repository.get_by_room_number(floor_id, room_number)
        if existing_room:
            raise InvalidRoomError(f"Room {room_number} already exists on floor {floor_id}")

        room = UnifiedRoom.create(
            floor_id=FloorId(floor_id),
            room_number=room_number,
            name=name,
            room_type=room_type,
            dimensions=dimensions,
            description=description,
            created_by=created_by,
        )

        saved_room = self.room_repository.save(room)
        floor.add_room(saved_room)

        self.floor_repository.save(floor)

        self.logger.info(f"Added room {room_number} to floor {floor_id}")
        return saved_room

    def add_device_to_room(
        self,
        room_id: str,
        device_id: str,
        device_type: str,
        name: str,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        serial_number: Optional[str] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> UnifiedDevice:
        """
        Add a device to a room.

        Args:
            room_id: Room ID
            device_id: External device ID
            device_type: Device type
            name: Device name
            manufacturer: Device manufacturer
            model: Device model
            serial_number: Device serial number
            description: Device description
            created_by: User who created the device

        Returns:
            Created device
        """
        room = self.room_repository.get_by_id(room_id)
        if not room:
            raise RoomNotFoundError(f"Room with ID {room_id} not found")

        device = UnifiedDevice.create(
            room_id=RoomId(room_id),
            device_id=device_id,
            device_type=device_type,
            name=name,
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
            description=description,
            created_by=created_by,
        )

        saved_device = self.device_repository.save(device)
        room.add_device(saved_device)

        self.room_repository.save(room)

        self.logger.info(f"Added device {device_id} to room {room_id}")
        return saved_device

    def get_building_statistics(self, building_id: str) -> Dict[str, Any]:
        """
        Get detailed statistics for a building.

        Args:
            building_id: Building ID

        Returns:
            Dictionary with building statistics
        """
        building = self.building_repository.get_by_id(building_id)
        if not building:
            raise BuildingNotFoundError(f"Building with ID {building_id} not found")

        floors = self.floor_repository.get_by_building_id(building_id)

        stats = {
            "building": building.to_dict(),
            "floor_count": len(floors),
            "room_count": 0,
            "device_count": 0,
            "device_types": {},
            "room_types": {},
            "floors": []
        }

        for floor in floors:
            rooms = self.room_repository.get_by_floor_id(str(floor.id))

            floor_stats = {
                "floor": floor.to_dict(),
                "room_count": len(rooms),
                "device_count": 0,
                "rooms": []
            }

            for room in rooms:
                devices = self.device_repository.get_by_room_id(str(room.id))

                room_stats = {
                    "room": room.to_dict(),
                    "device_count": len(devices),
                    "devices": [device.to_dict() for device in devices]
                }

                floor_stats["rooms"].append(room_stats)
                floor_stats["device_count"] += len(devices)
                stats["room_count"] += 1
                stats["device_count"] += len(devices)

                # Count room types
                room_type = room.room_type
                stats["room_types"][room_type] = stats["room_types"].get(room_type, 0) + 1

                # Count device types
                for device in devices:
                    device_type = device.device_type
                    stats["device_types"][device_type] = stats["device_types"].get(device_type, 0) + 1

            stats["floors"].append(floor_stats)

        return stats
