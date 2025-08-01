"""
Device Database Model

This module contains the SQLAlchemy model for the Device entity,
mapping domain device objects to database tables.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseModel
from domain.value_objects import DeviceStatus


class DeviceModel(BaseModel):
    """Device database model."""
    
    __tablename__ = 'devices'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True)
    
    # Foreign key to room
    room_id = Column(UUID(as_uuid=True), ForeignKey('rooms.id'), nullable=False, index=True)
    
    # Basic information
    device_id = Column(String(255), nullable=False, unique=True, index=True)  # External device ID
    name = Column(String(255), nullable=False)
    device_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Status
    status = Column(Enum(DeviceStatus), nullable=False, default=DeviceStatus.INSTALLED, index=True)
    
    # Device details
    manufacturer = Column(String(255), nullable=True)
    model = Column(String(255), nullable=True)
    serial_number = Column(String(255), nullable=True)
    
    # Relationships
    room = relationship("RoomModel", back_populates="devices")
    
    def __repr__(self) -> str:
        """String representation of the device model."""
        return f"<DeviceModel(id={self.id}, name='{self.name}', device_type='{self.device_type}')>"
    
    @property
    def full_name(self) -> str:
        """Get the full device name."""
        return f"{self.name} ({self.device_type})"
    
    def update_status(self, new_status: DeviceStatus, updated_by: Optional[str] = None) -> None:
        """Update device status."""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
    
    def update_name(self, new_name: str, updated_by: Optional[str] = None) -> None:
        """Update device name."""
        self.name = new_name
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by 