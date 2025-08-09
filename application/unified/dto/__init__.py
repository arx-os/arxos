"""
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
