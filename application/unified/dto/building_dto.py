"""
Unified Building DTOs

Defines DTOs used by unified controllers and schemas for building endpoints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class AddressDTO:
    street: str
    city: str
    state: str
    postal_code: str
    country: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
        }


@dataclass
class CoordinatesDTO:
    latitude: float
    longitude: float
    elevation: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "elevation": self.elevation,
        }


@dataclass
class DimensionsDTO:
    length: float
    width: float
    height: float
    area: Optional[float] = None
    volume: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "length": self.length,
            "width": self.width,
            "height": self.height,
            "area": self.area,
            "volume": self.volume,
        }


@dataclass
class BuildingDTO:
    id: str
    name: str
    building_type: str
    status: str
    address: Optional[AddressDTO] = None
    coordinates: Optional[CoordinatesDTO] = None
    dimensions: Optional[DimensionsDTO] = None
    description: Optional[str] = None
    year_built: Optional[int] = None
    total_floors: Optional[int] = None
    owner_id: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "building_type": self.building_type,
            "status": self.status,
            "address": self.address.to_dict() if self.address else None,
            "coordinates": self.coordinates.to_dict() if self.coordinates else None,
            "dimensions": self.dimensions.to_dict() if self.dimensions else None,
            "description": self.description,
            "year_built": self.year_built,
            "total_floors": self.total_floors,
            "owner_id": self.owner_id,
            "tags": self.tags or [],
            "metadata": self.metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
