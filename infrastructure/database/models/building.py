"""
Building Database Model

This module contains the SQLAlchemy model for the Building entity,
mapping domain building objects to database tables.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, Enum, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import BaseModel
from domain.unified.value_objects import BuildingStatus


class BuildingModel(BaseModel):
    """Building database model."""

    __tablename__ = 'buildings'

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True)

    # Basic information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Status
    status = Column(Enum(BuildingStatus), nullable=False, default=BuildingStatus.PLANNED, index=True)

    # Address information (stored as JSON for flexibility)
    address_street = Column(String(500), nullable=False)
    address_city = Column(String(100), nullable=False)
    address_state = Column(String(100), nullable=False)
    address_postal_code = Column(String(20), nullable=False)
    address_country = Column(String(100), nullable=False, default="USA")
    address_unit = Column(String(50), nullable=True)

    # Coordinates (spatial data)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    elevation = Column(Float, nullable=True)

    # Dimensions
    width = Column(Float, nullable=True)
    length = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    dimensions_unit = Column(String(20), nullable=True, default="meters")

    # Relationships
    floors = relationship("FloorModel", back_populates="building", cascade="all, delete-orphan")
    projects = relationship("ProjectModel", back_populates="building", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation of the building model."""
        return f"<BuildingModel(id={self.id}, name='{self.name}', status={self.status})>"

    @property
    def full_address(self) -> str:
        """Get the complete address string."""
        address_parts = [self.address_street]
        if self.address_unit:
            address_parts.append(f"Unit {self.address_unit}")
        address_parts.extend([
            self.address_city,
            self.address_state,
            self.address_postal_code
        ])
        if self.address_country != "USA":
            address_parts.append(self.address_country)
        return ", ".join(address_parts)

    @property
    def coordinates_dict(self) -> Optional[dict]:
        """Get coordinates as dictionary."""
        if self.latitude is not None and self.longitude is not None:
            coords = {
                'latitude': self.latitude,
                'longitude': self.longitude
            }
            if self.elevation is not None:
                coords['elevation'] = self.elevation
            return coords
        return None

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

    @property
    def floor_count(self) -> int:
        """Get the number of floors."""
        return len([f for f in self.floors if not f.is_deleted])

    @property
    def room_count(self) -> int:
        """Get the total number of rooms."""
        count = 0
        for floor in self.floors:
            if not floor.is_deleted:
                count += floor.room_count
        return count

    @property
    def device_count(self) -> int:
        """Get the total number of devices."""
        count = 0
        for floor in self.floors:
            if not floor.is_deleted:
                count += floor.device_count
        return count

    def update_status(self, new_status: BuildingStatus, updated_by: Optional[str] = None) -> None:
        """Update building status."""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by

    def update_address(self, street: str, city: str, state: str, postal_code: str,
                      country: str = "USA", unit: Optional[str] = None,
                      updated_by: Optional[str] = None) -> None:
        """Update building address."""
        self.address_street = street
        self.address_city = city
        self.address_state = state
        self.address_postal_code = postal_code
        self.address_country = country
        self.address_unit = unit
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by

    def update_coordinates(self, latitude: float, longitude: float,
                          elevation: Optional[float] = None,
                          updated_by: Optional[str] = None) -> None:
        """Update building coordinates."""
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by

    def update_dimensions(self, width: float, length: float,
                         height: Optional[float] = None, unit: str = "meters",
                         updated_by: Optional[str] = None) -> None:
        """Update building dimensions."""
        self.width = width
        self.length = length
        self.height = height
        self.dimensions_unit = unit
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
