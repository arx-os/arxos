"""
Room Database Model

This module contains the SQLAlchemy model for the Room entity,
mapping domain room objects to database tables.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, Enum, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseModel
from domain.value_objects import RoomStatus


class RoomModel(BaseModel):
    """Room database model."""

    __tablename__ = 'rooms'

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True)

    # Foreign key to floor
    floor_id = Column(UUID(as_uuid=True), ForeignKey('floors.id'), nullable=False, index=True)

    # Basic information
    name = Column(String(255), nullable=False)
    room_number = Column(String(50), nullable=False, index=True)
    room_type = Column(String(100), nullable=False, default="general")
    description = Column(Text, nullable=True)

    # Status
    status = Column(Enum(RoomStatus), nullable=False, default=RoomStatus.PLANNED, index=True)

    # Dimensions
    width = Column(Float, nullable=True)
    length = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    dimensions_unit = Column(String(20), nullable=True, default="meters")

    # Relationships
    floor = relationship("FloorModel", back_populates="rooms")
    devices = relationship("DeviceModel", back_populates="room", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation of the room model."""
        return f"<RoomModel(id={self.id}, name='{self.name}', room_number='{self.room_number}')>"

    @property
def full_name(self) -> str:
        """Get the full room name."""
        return f"{self.name} ({self.room_number})
    @property
def device_count(self) -> int:
        """Get the number of devices in this room."""
        return len([d for d in self.devices if not d.is_deleted])

    @property
def dimensions_dict(self) -> Optional[dict]:
        """Get dimensions as dictionary."""
        if self.width is not None and self.length is not None:
            dims = {
                'width': self.width,
                'length': self.length,
                'unit': self.dimensions_unit or 'meters'
            }
            if self.height is not None:
                dims['height'] = self.height
            return dims
        return None

    def update_status(self, new_status: RoomStatus, updated_by: Optional[str] = None) -> None:
        """Update room status."""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by

    def update_name(self, new_name: str, updated_by: Optional[str] = None) -> None:
        """Update room name."""
        self.name = new_name
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by

    def update_dimensions(self, width: float, length: float,
                         height: Optional[float] = None, unit: str = "meters",
                         updated_by: Optional[str] = None) -> None:
        """Update room dimensions."""
        self.width = width
        self.length = length
        self.height = height
        self.dimensions_unit = unit
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
