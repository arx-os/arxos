"""
Unified Room Entity
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

from ..value_objects import RoomId, FloorId, Dimensions
from domain.exceptions import InvalidRoomError


@dataclass
class Room:
    id: RoomId
    floor_id: FloorId
    room_number: str
    name: str
    room_type: str = "general"
    dimensions: Optional[Dimensions] = None
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise InvalidRoomError("Room name cannot be empty")
        if not self.room_number or not self.room_number.strip():
            raise InvalidRoomError("Room number cannot be empty")

    @classmethod
    def create(
        cls,
        floor_id: FloorId,
        room_number: str,
        name: str,
        room_type: str = "general",
        dimensions: Optional[Dimensions] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> "Room":
        return cls(
            id=RoomId(),
            floor_id=floor_id,
            room_number=room_number,
            name=name,
            room_type=room_type,
            dimensions=dimensions,
            description=description,
            created_by=created_by,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "floor_id": str(self.floor_id),
            "room_number": self.room_number,
            "name": self.name,
            "room_type": self.room_type,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
