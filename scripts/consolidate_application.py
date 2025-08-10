#!/usr/bin/env python3
"""
Script to consolidate application layer and eliminate service layer chaos.
This script will create unified services and use cases with proper abstractions.
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any

def create_unified_application_structure():
    """Create a unified application structure."""

    # Create unified application directory
    unified_app = Path("application/unified")
    unified_app.mkdir(exist_ok=True)

    # Create subdirectories
    (unified_app / "services").mkdir(exist_ok=True)
    (unified_app / "use_cases").mkdir(exist_ok=True)
    (unified_app / "dto").mkdir(exist_ok=True)
    (unified_app / "validators").mkdir(exist_ok=True)

    return unified_app

def create_unified_building_service():
    """Create a unified building service."""

    content = '''""
Unified Building Service

This service provides a unified interface for building operations,
eliminating duplication between different service implementations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from domain.unified.entities import Building
from domain.unified.repositories import BuildingRepository
from domain.unified.value_objects import BuildingId, Address, Dimensions, BuildingStatus
from domain.unified.exceptions import InvalidBuildingError, BuildingNotFoundError

class UnifiedBuildingService:
    """
    Unified building service that provides a single interface for building operations.

    This service combines the best features from different service implementations
    and provides a clean, consistent interface for building management.
    """

    def __init__(self, building_repository: BuildingRepository):
        """Initialize the unified building service."""
        self.building_repository = building_repository
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_building(
        self,
        name: str,
        address: Address,
        status: BuildingStatus = BuildingStatus.PLANNED,
        dimensions: Optional[Dimensions] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Building:
        """
        Create a new building.

        Args:
            name: Building name
            address: Building address
            status: Building status
            dimensions: Building dimensions
            description: Building description
            created_by: User who created the building
            metadata: Additional metadata

        Returns:
            Created building entity

        Raises:
            InvalidBuildingError: If building data is invalid
        """
        try:
            building = Building.create(
                name=name,
                address=address,
                status=status,
                dimensions=dimensions,
                description=description,
                created_by=created_by,
                metadata=metadata or {}
            )

            saved_building = self.building_repository.save(building)
            self.logger.info(f"Created building {saved_building.id} with name '{name}'")

            return saved_building

        except Exception as e:
            self.logger.error(f"Error creating building '{name}': {e}")
            raise InvalidBuildingError(f"Failed to create building: {e}")

    def get_building(self, building_id: str) -> Building:
        """
        Get a building by ID.

        Args:
            building_id: Building ID

        Returns:
            Building entity

        Raises:
            BuildingNotFoundError: If building is not found
        """
        building = self.building_repository.get_by_id(building_id)
        if not building:
            raise BuildingNotFoundError(f"Building with ID {building_id} not found")

        return building

    def get_all_buildings(self) -> List[Building]:
        """
        Get all buildings.

        Returns:
            List of building entities
        """
        return self.building_repository.get_all()

    def get_buildings_by_status(self, status: str) -> List[Building]:
        """
        Get buildings by status.

        Args:
            status: Building status

        Returns:
            List of buildings with the specified status
        """
        return self.building_repository.get_by_status(status)

    def get_buildings_by_address(self, address: str) -> List[Building]:
        """
        Get buildings by address.

        Args:
            address: Address to search for

        Returns:
            List of buildings matching the address
        """
        return self.building_repository.get_by_address(address)

    def update_building_name(self, building_id: str, new_name: str, updated_by: str) -> Building:
        """
        Update building name.

        Args:
            building_id: Building ID
            new_name: New building name
            updated_by: User who updated the building

        Returns:
            Updated building entity

        Raises:
            BuildingNotFoundError: If building is not found
            InvalidBuildingError: If new name is invalid
        """
        building = self.get_building(building_id)
        building.update_name(new_name, updated_by)

        saved_building = self.building_repository.save(building)
        self.logger.info(f"Updated building {building_id} name to '{new_name}'")

        return saved_building

    def update_building_status(self, building_id: str, new_status: BuildingStatus, updated_by: str) -> Building:
        """
        Update building status.

        Args:
            building_id: Building ID
            new_status: New building status
            updated_by: User who updated the building

        Returns:
            Updated building entity

        Raises:
            BuildingNotFoundError: If building is not found
            InvalidStatusTransitionError: If status transition is invalid
        """
        building = self.get_building(building_id)
        building.update_status(new_status, updated_by)

        saved_building = self.building_repository.save(building)
        self.logger.info(f"Updated building {building_id} status to {new_status.value}")

        return saved_building

    def update_building_dimensions(self, building_id: str, dimensions: Dimensions, updated_by: str) -> Building:
        """
        Update building dimensions.

        Args:
            building_id: Building ID
            dimensions: New building dimensions
            updated_by: User who updated the building

        Returns:
            Updated building entity

        Raises:
            BuildingNotFoundError: If building is not found
            InvalidBuildingError: If dimensions are invalid
        """
        building = self.get_building(building_id)
        building.update_dimensions(dimensions, updated_by)

        saved_building = self.building_repository.save(building)
        self.logger.info(f"Updated building {building_id} dimensions")

        return saved_building

    def add_building_metadata(self, building_id: str, key: str, value: Any, updated_by: str) -> Building:
        """
        Add metadata to building.

        Args:
            building_id: Building ID
            key: Metadata key
            value: Metadata value
            updated_by: User who updated the building

        Returns:
            Updated building entity

        Raises:
            BuildingNotFoundError: If building is not found
        """
        building = self.get_building(building_id)
        building.add_metadata(key, value, updated_by)

        saved_building = self.building_repository.save(building)
        self.logger.info(f"Added metadata '{key}' to building {building_id}")

        return saved_building

    def remove_building_metadata(self, building_id: str, key: str, updated_by: str) -> Building:
        """
        Remove metadata from building.

        Args:
            building_id: Building ID
            key: Metadata key to remove
            updated_by: User who updated the building

        Returns:
            Updated building entity

        Raises:
            BuildingNotFoundError: If building is not found
        """
        building = self.get_building(building_id)
        building.remove_metadata(key, updated_by)

        saved_building = self.building_repository.save(building)
        self.logger.info(f"Removed metadata '{key}' from building {building_id}")

        return saved_building

    def delete_building(self, building_id: str) -> bool:
        """
        Delete a building.

        Args:
            building_id: Building ID

        Returns:
            True if building was deleted, False otherwise

        Raises:
            BuildingNotFoundError: If building is not found
        """
        building = self.get_building(building_id)

        success = self.building_repository.delete(building_id)
        if success:
            self.logger.info(f"Deleted building {building_id}")
        else:
            self.logger.error(f"Failed to delete building {building_id}")

        return success

    def get_building_statistics(self) -> Dict[str, Any]:
        """
        Get building statistics.

        Returns:
            Dictionary with building statistics
        """
        buildings = self.get_all_buildings()

        stats = {
            "total_buildings": len(buildings),
            "buildings_by_status": {},
            "total_floors": sum(b.floor_count for b in buildings),
            "total_rooms": sum(b.room_count for b in buildings),
            "total_devices": sum(b.device_count for b in buildings),
            "average_area": 0,
            "average_volume": 0
        }

        # Calculate status distribution
        for building in buildings:
            status = building.status.value
            stats["buildings_by_status"][status] = stats["buildings_by_status"].get(status, 0) + 1

        # Calculate averages
        buildings_with_area = [b for b in buildings if b.area is not None]
        buildings_with_volume = [b for b in buildings if b.volume is not None]

        if buildings_with_area:
            stats["average_area"] = sum(b.area for b in buildings_with_area) / len(buildings_with_area)

        if buildings_with_volume:
            stats["average_volume"] = sum(b.volume for b in buildings_with_volume) / len(buildings_with_volume)

        return stats
'''

    return content

def create_unified_use_case():
    """Create a unified use case implementation."""

    content = '''""
Unified Use Case Implementation

This module provides unified use cases that eliminate duplication
and provide consistent business logic across the application.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from domain.unified.entities import Building, Floor, Room, Device, User, Project
from domain.unified.repositories import (
    BuildingRepository, FloorRepository, RoomRepository,
    DeviceRepository, UserRepository, ProjectRepository
)
from domain.unified.value_objects import (
    BuildingId, FloorId, RoomId, DeviceId, UserId, ProjectId,
    Address, Dimensions, BuildingStatus, FloorStatus, RoomStatus,
    DeviceStatus, UserRole, ProjectStatus
)
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
            floor = Floor.create(
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
            rooms = self.room_repository.get_by_floor_id(str(floor.id)
            floor_data = floor.to_dict()
            floor_data["rooms"] = []

            for room in rooms:
                devices = self.device_repository.get_by_room_id(str(room.id)
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
    ) -> Floor:
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

        floor = Floor.create(
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
    ) -> Room:
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

        room = Room.create(
            floor_id=FloorId(floor_id),
            room_number=room_number,
            name=name,
            room_type=room_type,
            dimensions=dimensions,
            description=description,
            created_by=created_by
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
    ) -> Device:
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

        device = Device.create(
            room_id=RoomId(room_id),
            device_id=device_id,
            device_type=device_type,
            name=name,
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
            description=description,
            created_by=created_by
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
            rooms = self.room_repository.get_by_floor_id(str(floor.id)
            floor_stats = {
                "floor": floor.to_dict(),
                "room_count": len(rooms),
                "device_count": 0,
                "rooms": []
            }

            for room in rooms:
                devices = self.device_repository.get_by_room_id(str(room.id)
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
'''

    return content

def create_unified_dto():
    """Create unified DTOs."""

    content = '''""
Unified Data Transfer Objects (DTOs)

This module provides unified DTOs for data transfer between layers,
eliminating duplication and ensuring consistent data structures.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class BuildingDTO:
    """Data transfer object for building entities."""

    id: str
    name: str
    address: Dict[str, Any]
    status: str
    dimensions: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    created_at: str = None
    updated_at: str = None
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = None
    floor_count: int = 0
    room_count: int = 0
    device_count: int = 0
    area: Optional[float] = None
    volume: Optional[float] = None

    @classmethod
def from_entity(cls, building) -> "BuildingDTO":
        """Create DTO from building entity."""
        return cls(
            id=str(building.id),
            name=building.name,
            address=building.address.to_dict(),
            status=building.status.value,
            dimensions=building.dimensions.to_dict() if building.dimensions else None,
            description=building.description,
            created_at=building.created_at.isoformat(),
            updated_at=building.updated_at.isoformat(),
            created_by=building.created_by,
            metadata=building.metadata,
            floor_count=building.floor_count,
            room_count=building.room_count,
            device_count=building.device_count,
            area=building.area,
            volume=building.volume
        )

@dataclass
class FloorDTO:
    """Data transfer object for floor entities."""

    id: str
    building_id: str
    floor_number: int
    name: str
    status: str
    description: Optional[str] = None
    created_at: str = None
    updated_at: str = None
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = None
    room_count: int = 0
    device_count: int = 0

    @classmethod
def from_entity(cls, floor) -> "FloorDTO":
        """Create DTO from floor entity."""
        return cls(
            id=str(floor.id),
            building_id=str(floor.building_id),
            floor_number=floor.floor_number,
            name=floor.name,
            status=floor.status.value,
            description=floor.description,
            created_at=floor.created_at.isoformat(),
            updated_at=floor.updated_at.isoformat(),
            created_by=floor.created_by,
            metadata=floor.metadata,
            room_count=floor.room_count,
            device_count=floor.device_count
        )

@dataclass
class RoomDTO:
    """Data transfer object for room entities."""

    id: str
    floor_id: str
    room_number: str
    name: str
    status: str
    room_type: str
    dimensions: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    created_at: str = None
    updated_at: str = None
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = None
    device_count: int = 0
    area: Optional[float] = None
    volume: Optional[float] = None

    @classmethod
def from_entity(cls, room) -> "RoomDTO":
        """Create DTO from room entity."""
        return cls(
            id=str(room.id),
            floor_id=str(room.floor_id),
            room_number=room.room_number,
            name=room.name,
            status=room.status.value,
            room_type=room.room_type,
            dimensions=room.dimensions.to_dict() if room.dimensions else None,
            description=room.description,
            created_at=room.created_at.isoformat(),
            updated_at=room.updated_at.isoformat(),
            created_by=room.created_by,
            metadata=room.metadata,
            device_count=room.device_count,
            area=room.area,
            volume=room.volume
        )

@dataclass
class DeviceDTO:
    """Data transfer object for device entities."""

    id: str
    room_id: str
    device_id: str
    device_type: str
    name: str
    status: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    description: Optional[str] = None
    created_at: str = None
    updated_at: str = None
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = None

    @classmethod
def from_entity(cls, device) -> "DeviceDTO":
        """Create DTO from device entity."""
        return cls(
            id=str(device.id),
            room_id=str(device.room_id),
            device_id=device.device_id,
            device_type=device.device_type,
            name=device.name,
            status=device.status.value,
            manufacturer=device.manufacturer,
            model=device.model,
            serial_number=device.serial_number,
            description=device.description,
            created_at=device.created_at.isoformat(),
            updated_at=device.updated_at.isoformat(),
            created_by=device.created_by,
            metadata=device.metadata
        )

@dataclass
class BuildingHierarchyDTO:
    """Data transfer object for building hierarchy."""

    building: BuildingDTO
    floors: List[FloorDTO]
    total_rooms: int
    total_devices: int

    @classmethod
def from_hierarchy(cls, hierarchy: Dict[str, Any]) -> "BuildingHierarchyDTO":
        """Create DTO from building hierarchy."""
        building_dto = BuildingDTO.from_entity(hierarchy["building"])
        floor_dtos = [FloorDTO.from_entity(floor) for floor in hierarchy["floors"]]

        total_rooms = sum(floor.room_count for floor in floor_dtos)
        total_devices = sum(floor.device_count for floor in floor_dtos)

        return cls(
            building=building_dto,
            floors=floor_dtos,
            total_rooms=total_rooms,
            total_devices=total_devices
        )
'''

    return content

def main():
    """Main consolidation function."""
    print("🔄 Starting Application Layer Consolidation")

    # Create unified application structure
    unified_app = create_unified_application_structure()
    print(f"✅ Created unified application structure at {unified_app}")

    # Create unified building service
    building_service_path = unified_app / "services" / "building_service.py"
    with open(building_service_path, 'w') as f:
        f.write(create_unified_building_service()
    print(f"✅ Created unified building service at {building_service_path}")

    # Create unified use case
    use_case_path = unified_app / "use_cases" / "building_use_case.py"
    with open(use_case_path, 'w') as f:
        f.write(create_unified_use_case()
    print(f"✅ Created unified use case at {use_case_path}")

    # Create unified DTOs
    dto_path = unified_app / "dto" / "__init__.py"
    with open(dto_path, 'w') as f:
        f.write(create_unified_dto()
    print(f"✅ Created unified DTOs at {dto_path}")

    print("🎯 Application layer consolidation completed successfully!")
    print("📋 Application consolidation benefits:")
    print("   ✅ Eliminated service layer chaos")
    print("   ✅ Unified service interfaces")
    print("   ✅ Consistent business logic")
    print("   ✅ Clean use case implementations")
    print("   ✅ Standardized DTOs")

if __name__ == "__main__":
    main()
