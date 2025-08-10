"""
Unified Device Entity
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

from ..value_objects import DeviceId, RoomId
from domain.value_objects import DeviceStatus
from domain.exceptions import InvalidDeviceError


@dataclass
class Device:
    id: DeviceId
    room_id: RoomId
    device_id: str
    device_type: str
    name: str
    status: DeviceStatus = DeviceStatus.INSTALLED
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise InvalidDeviceError("Device name cannot be empty")
        if not self.device_id or not self.device_id.strip():
            raise InvalidDeviceError("Device ID cannot be empty")
        if not self.device_type or not self.device_type.strip():
            raise InvalidDeviceError("Device type cannot be empty")

    @classmethod
    def create(
        cls,
        room_id: RoomId,
        device_id: str,
        device_type: str,
        name: str,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        serial_number: Optional[str] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> "Device":
        return cls(
            id=DeviceId(),
            room_id=room_id,
            device_id=device_id,
            device_type=device_type,
            name=name,
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
            description=description,
            created_by=created_by,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "room_id": str(self.room_id),
            "device_id": self.device_id,
            "device_type": self.device_type,
            "name": self.name,
            "status": self.status.value,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "serial_number": self.serial_number,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
