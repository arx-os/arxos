"""
Building Schemas - Unified Building API Schemas

This module provides unified Pydantic schemas for building API endpoints,
ensuring consistent request/response validation and documentation.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum
from decimal import Decimal

from application.unified.dto.building_dto import BuildingDTO


class BuildingStatus(str, Enum):
    """Building status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    CONSTRUCTION = "construction"
    DEMOLISHED = "demolished"


class BuildingType(str, Enum):
    """Building type enumeration."""
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    EDUCATIONAL = "educational"
    HEALTHCARE = "healthcare"
    GOVERNMENT = "government"
    MIXED_USE = "mixed_use"
    OTHER = "other"


class AddressSchema(BaseModel):
    """Address schema for building location."""
    street: str = Field(..., min_length=1, max_length=255, description="Street address")
    city: str = Field(..., min_length=1, max_length=100, description="City name")
    state: str = Field(..., min_length=1, max_length=100, description="State or province")
    postal_code: str = Field(..., min_length=1, max_length=20, description="Postal code")
    country: str = Field(..., min_length=1, max_length=100, description="Country name")

    class Config:
        schema_extra = {
            "example": {
                "street": "123 Main Street",
                "city": "New York",
                "state": "NY",
                "postal_code": "10001",
                "country": "United States"
            }
        }


class CoordinatesSchema(BaseModel):
    """Coordinates schema for building location."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    elevation: Optional[float] = Field(None, description="Elevation in meters")

    class Config:
        schema_extra = {
            "example": {
                "latitude": 40.7128,
                "longitude": -74.0060,
                "elevation": 10.5
            }
        }


class DimensionsSchema(BaseModel):
    """Dimensions schema for building measurements."""
    length: float = Field(..., gt=0, description="Length in meters")
    width: float = Field(..., gt=0, description="Width in meters")
    height: float = Field(..., gt=0, description="Height in meters")
    area: Optional[float] = Field(None, gt=0, description="Total area in square meters")
    volume: Optional[float] = Field(None, gt=0, description="Total volume in cubic meters")

    @field_validator('area', mode='before')
    @classmethod
    def calculate_area(cls, v, values):
        """Calculate area if not provided."""
        if v is None and 'length' in values and 'width' in values:
            return values['length'] * values['width']
        return v

    @field_validator('volume', mode='before')
    @classmethod
    def calculate_volume(cls, v, values):
        """Calculate volume if not provided."""
        if v is None and 'length' in values and 'width' in values and 'height' in values:
            return values['length'] * values['width'] * values['height']
        return v

    class Config:
        schema_extra = {
            "example": {
                "length": 50.0,
                "width": 30.0,
                "height": 20.0,
                "area": 1500.0,
                "volume": 30000.0
            }
        }


class CreateBuildingRequest(BaseModel):
    """Request schema for creating a building."""
    name: str = Field(..., min_length=1, max_length=255, description="Building name")
    description: Optional[str] = Field(None, max_length=1000, description="Building description")
    building_type: BuildingType = Field(..., description="Type of building")
    status: BuildingStatus = Field(default=BuildingStatus.ACTIVE, description="Building status")
    address: AddressSchema = Field(..., description="Building address")
    coordinates: Optional[CoordinatesSchema] = Field(None, description="Building coordinates")
    dimensions: Optional[DimensionsSchema] = Field(None, description="Building dimensions")
    year_built: Optional[int] = Field(None, ge=1800, le=2100, description="Year building was built")
    total_floors: Optional[int] = Field(None, ge=1, description="Total number of floors")
    owner_id: Optional[str] = Field(None, description="Building owner ID")
    tags: Optional[List[str]] = Field(default=[], description="Building tags")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")

    class Config:
        schema_extra = {
            "example": {
                "name": "Empire State Building",
                "description": "Iconic skyscraper in Manhattan",
                "building_type": "commercial",
                "status": "active",
                "address": {
                    "street": "350 5th Avenue",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10118",
                    "country": "United States"
                },
                "coordinates": {
                    "latitude": 40.7484,
                    "longitude": -73.9857,
                    "elevation": 10.0
                },
                "dimensions": {
                    "length": 129.0,
                    "width": 57.0,
                    "height": 443.0
                },
                "year_built": 1931,
                "total_floors": 102,
                "tags": ["landmark", "skyscraper", "art-deco"],
                "metadata": {
                    "architect": "Shreve, Lamb & Harmon",
                    "construction_cost": 40948900
                }
            }
        }


class UpdateBuildingRequest(BaseModel):
    """Request schema for updating a building."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Building name")
    description: Optional[str] = Field(None, max_length=1000, description="Building description")
    building_type: Optional[BuildingType] = Field(None, description="Type of building")
    status: Optional[BuildingStatus] = Field(None, description="Building status")
    address: Optional[AddressSchema] = Field(None, description="Building address")
    coordinates: Optional[CoordinatesSchema] = Field(None, description="Building coordinates")
    dimensions: Optional[DimensionsSchema] = Field(None, description="Building dimensions")
    year_built: Optional[int] = Field(None, ge=1800, le=2100, description="Year building was built")
    total_floors: Optional[int] = Field(None, ge=1, description="Total number of floors")
    owner_id: Optional[str] = Field(None, description="Building owner ID")
    tags: Optional[List[str]] = Field(None, description="Building tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        schema_extra = {
            "example": {
                "name": "Updated Building Name",
                "status": "maintenance",
                "total_floors": 105,
                "tags": ["updated", "maintenance"]
            }
        }


class BuildingResponse(BaseModel):
    """Response schema for building data."""
    id: str = Field(..., description="Building unique identifier")
    name: str = Field(..., description="Building name")
    description: Optional[str] = Field(None, description="Building description")
    building_type: BuildingType = Field(..., description="Type of building")
    status: BuildingStatus = Field(..., description="Building status")
    address: AddressSchema = Field(..., description="Building address")
    coordinates: Optional[CoordinatesSchema] = Field(None, description="Building coordinates")
    dimensions: Optional[DimensionsSchema] = Field(None, description="Building dimensions")
    year_built: Optional[int] = Field(None, description="Year building was built")
    total_floors: Optional[int] = Field(None, description="Total number of floors")
    owner_id: Optional[str] = Field(None, description="Building owner ID")
    tags: List[str] = Field(default=[], description="Building tags")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    @classmethod
    def from_dto(cls, dto: BuildingDTO) -> 'BuildingResponse':
        """Create response from DTO."""
        return cls(
            id=dto.id,
            name=dto.name,
            description=dto.description,
            building_type=dto.building_type,
            status=dto.status,
            address=AddressSchema(**dto.address.to_dict()) if dto.address else None,
            coordinates=CoordinatesSchema(**dto.coordinates.to_dict()) if dto.coordinates else None,
            dimensions=DimensionsSchema(**dto.dimensions.to_dict()) if dto.dimensions else None,
            year_built=dto.year_built,
            total_floors=dto.total_floors,
            owner_id=dto.owner_id,
            tags=dto.tags or [],
            metadata=dto.metadata or {},
            created_at=dto.created_at,
            updated_at=dto.updated_at
        )

    class Config:
        schema_extra = {
            "example": {
                "id": "building_123",
                "name": "Empire State Building",
                "description": "Iconic skyscraper in Manhattan",
                "building_type": "commercial",
                "status": "active",
                "address": {
                    "street": "350 5th Avenue",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10118",
                    "country": "United States"
                },
                "coordinates": {
                    "latitude": 40.7484,
                    "longitude": -73.9857,
                    "elevation": 10.0
                },
                "dimensions": {
                    "length": 129.0,
                    "width": 57.0,
                    "height": 443.0,
                    "area": 7353.0,
                    "volume": 3258171.0
                },
                "year_built": 1931,
                "total_floors": 102,
                "owner_id": "owner_456",
                "tags": ["landmark", "skyscraper", "art-deco"],
                "metadata": {
                    "architect": "Shreve, Lamb & Harmon",
                    "construction_cost": 40948900
                },
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class BuildingListResponse(BaseModel):
    """Response schema for building list."""
    buildings: List[BuildingResponse] = Field(..., description="List of buildings")
    total_count: int = Field(..., description="Total number of buildings")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")

    @classmethod
    def from_dtos(cls, dtos: List[BuildingDTO], total_count: int,
                  page: int, page_size: int) -> 'BuildingListResponse':
        """Create response from DTOs."""
        buildings = [BuildingResponse.from_dto(dto) for dto in dtos]
        total_pages = (total_count + page_size - 1) // page_size

        return cls(
            buildings=buildings,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    class Config:
        schema_extra = {
            "example": {
                "buildings": [
                    {
                        "id": "building_123",
                        "name": "Empire State Building",
                        "building_type": "commercial",
                        "status": "active"
                    }
                ],
                "total_count": 1,
                "page": 1,
                "page_size": 10,
                "total_pages": 1
            }
        }


class FloorSummarySchema(BaseModel):
    """Summary schema for a floor in a building."""
    id: str
    floor_number: int
    name: str
    status: Optional[str] = None
    room_count: Optional[int] = None


class DeviceSummarySchema(BaseModel):
    """Summary schema for a device associated with a room/building."""
    id: Optional[str] = None
    room_id: Optional[str] = None
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None


class BuildingFilterSchema(BaseModel):
    """Schema for building filter parameters."""
    name: Optional[str] = Field(None, description="Filter by building name")
    building_type: Optional[BuildingType] = Field(None, description="Filter by building type")
    status: Optional[BuildingStatus] = Field(None, description="Filter by building status")
    city: Optional[str] = Field(None, description="Filter by city")
    state: Optional[str] = Field(None, description="Filter by state")
    country: Optional[str] = Field(None, description="Filter by country")
    year_built_min: Optional[int] = Field(None, ge=1800, description="Minimum year built")
    year_built_max: Optional[int] = Field(None, le=2100, description="Maximum year built")
    total_floors_min: Optional[int] = Field(None, ge=1, description="Minimum number of floors")
    total_floors_max: Optional[int] = Field(None, description="Maximum number of floors")
    owner_id: Optional[str] = Field(None, description="Filter by owner ID")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")

    class Config:
        schema_extra = {
            "example": {
                "building_type": "commercial",
                "status": "active",
                "city": "New York",
                "year_built_min": 1900,
                "total_floors_min": 10
            }
        }


class BuildingPaginationSchema(BaseModel):
    """Schema for building pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=10, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(default="name", description="Sort field")
    sort_order: Optional[str] = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")

    class Config:
        schema_extra = {
            "example": {
                "page": 1,
                "page_size": 20,
                "sort_by": "name",
                "sort_order": "asc"
            }
        }
