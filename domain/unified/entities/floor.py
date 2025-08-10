"""
Unified Floor Entity
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

from ..value_objects import FloorId, BuildingId, Dimensions, FloorStatus
from domain.exceptions import InvalidFloorError


@dataclass
class Floor:
    id: FloorId
    building_id: BuildingId
    floor_number: int
    name: str
    status: FloorStatus = FloorStatus.PLANNED
    description: Optional[str] = None
    dimensions: Optional[Dimensions] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Relationships
    rooms: List[Any] = field(default_factory=list)

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise InvalidFloorError("Floor name cannot be empty")
        if self.floor_number < 0:
            raise InvalidFloorError("Floor number must be non-negative")

    @classmethod
    def create(
        cls,
        building_id: BuildingId,
        floor_number: int,
        name: str,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Floor":
        return cls(
            id=FloorId(),
            building_id=building_id,
            floor_number=floor_number,
            name=name,
            description=description,
            created_by=created_by,
            metadata=metadata or {},
        )

    def update_name(self, new_name: str, updated_by: str) -> None:
        if not new_name or not new_name.strip():
            raise InvalidFloorError("Floor name cannot be empty")
        self.name = new_name.strip()
        self.updated_at = datetime.utcnow()

    def add_room(self, room: Any) -> None:
        self.rooms.append(room)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "building_id": str(self.building_id),
            "floor_number": self.floor_number,
            "name": self.name,
            "status": self.status.value,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }
