"""
Floor Database Model

This module contains the SQLAlchemy model for the Floor entity,
mapping domain floor objects to database tables.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, Enum, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseModel
from domain.value_objects import FloorStatus


class FloorModel(BaseModel):
    """Floor database model."""
    
    __tablename__ = 'floors'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True)
    
    # Foreign key to building
    building_id = Column(UUID(as_uuid=True), ForeignKey('buildings.id'), nullable=False, index=True)
    
    # Basic information
    name = Column(String(255), nullable=False)
    floor_number = Column(Integer, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Status
    status = Column(Enum(FloorStatus), nullable=False, default=FloorStatus.PLANNED, index=True)
    
    # Relationships
    building = relationship("BuildingModel", back_populates="floors")
    rooms = relationship("RoomModel", back_populates="floor", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        """String representation of the floor model."""
        return f"<FloorModel(id={self.id}, name='{self.name}', floor_number={self.floor_number})>"
    
    @property
    def full_name(self) -> str:
        """Get the full floor name."""
        return f"{self.name} (Floor {self.floor_number})"
    
    @property
    def room_count(self) -> int:
        """Get the number of rooms on this floor."""
        return len([r for r in self.rooms if not r.is_deleted])
    
    @property
    def device_count(self) -> int:
        """Get the total number of devices on this floor."""
        count = 0
        for room in self.rooms:
            if not room.is_deleted:
                count += room.device_count
        return count
    
    def update_status(self, new_status: FloorStatus, updated_by: Optional[str] = None) -> None:
        """Update floor status."""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
    
    def update_name(self, new_name: str, updated_by: Optional[str] = None) -> None:
        """Update floor name."""
        self.name = new_name
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
    
    def update_floor_number(self, new_floor_number: int, updated_by: Optional[str] = None) -> None:
        """Update floor number."""
        self.floor_number = new_floor_number
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by 