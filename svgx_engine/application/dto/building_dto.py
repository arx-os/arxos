"""
Building DTOs - Data Transfer Objects for Application Layer
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

from svgx_engine.domain.value_objects.address import Address
from svgx_engine.domain.value_objects.coordinates import Coordinates
from svgx_engine.domain.value_objects.dimensions import Dimensions
from svgx_engine.domain.value_objects.status import Status
from svgx_engine.domain.value_objects.money import Money

# Pydantic Models for API Requests/Responses

class AddressDTO(BaseModel):
    """Address data transfer object."""
    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State or province")
    postal_code: str = Field(..., description="Postal code")
    country: str = Field(default="US", description="Country")
    coordinates: Optional[Dict[str, float]] = Field(None, description="Latitude and longitude")

class CoordinatesDTO(BaseModel):
    """Coordinates data transfer object."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")

class DimensionsDTO(BaseModel):
    """Dimensions data transfer object."""
    length: float = Field(..., gt=0, description="Length in meters")
    width: float = Field(..., gt=0, description="Width in meters")
    height: float = Field(..., gt=0, description="Height in meters")
    area: Optional[float] = Field(None, description="Calculated area in square meters")
    volume: Optional[float] = Field(None, description="Calculated volume in cubic meters")

class StatusDTO(BaseModel):
    """Status data transfer object."""
    value: str = Field(..., description="Status value")
    description: Optional[str] = Field(None, description="Status description")

class MoneyDTO(BaseModel):
    """Money data transfer object."""
    amount: float = Field(..., description="Amount")
    currency: str = Field(default="USD", description="Currency code")

class BuildingResponseDTO(BaseModel):
    """Building response data transfer object."""
    id: str = Field(..., description="Building ID")
    name: str = Field(..., description="Building name")
    address: AddressDTO = Field(..., description="Building address")
    dimensions: DimensionsDTO = Field(..., description="Building dimensions")
    status: StatusDTO = Field(..., description="Building status")
    cost: MoneyDTO = Field(..., description="Building cost")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class CreateBuildingRequestDTO(BaseModel):
    """Create building request data transfer object."""
    name: str = Field(..., min_length=1, max_length=255, description="Building name")
    address: AddressDTO = Field(..., description="Building address")
    dimensions: DimensionsDTO = Field(..., description="Building dimensions")
    status: Optional[StatusDTO] = Field(None, description="Building status")
    cost: MoneyDTO = Field(..., description="Building cost")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

class UpdateBuildingRequestDTO(BaseModel):
    """Update building request data transfer object."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Building name")
    address: Optional[AddressDTO] = Field(None, description="Building address")
    dimensions: Optional[DimensionsDTO] = Field(None, description="Building dimensions")
    status: Optional[StatusDTO] = Field(None, description="Building status")
    cost: Optional[MoneyDTO] = Field(None, description="Building cost")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class BuildingListResponseDTO(BaseModel):
    """Building list response data transfer object."""
    buildings: List[BuildingResponseDTO] = Field(..., description="List of buildings")
    total_count: int = Field(..., description="Total number of buildings")
    page: Optional[int] = Field(None, description="Current page number")
    page_size: Optional[int] = Field(None, description="Page size")
    total_pages: Optional[int] = Field(None, description="Total number of pages")

class BuildingSearchRequestDTO(BaseModel):
    """Building search request data transfer object."""
    name: Optional[str] = Field(None, description="Search by building name")
    status: Optional[str] = Field(None, description="Filter by status")
    coordinates: Optional[CoordinatesDTO] = Field(None, description="Search by coordinates")
    radius: Optional[float] = Field(None, gt=0, description="Search radius in kilometers")
    min_area: Optional[float] = Field(None, gt=0, description="Minimum area filter")
    max_area: Optional[float] = Field(None, gt=0, description="Maximum area filter")
    min_cost: Optional[float] = Field(None, ge=0, description="Minimum cost filter")
    max_cost: Optional[float] = Field(None, ge=0, description="Maximum cost filter")
    page: Optional[int] = Field(1, ge=1, description="Page number")
    page_size: Optional[int] = Field(10, ge=1, le=100, description="Page size")

# Dataclass Models for Internal Use

@dataclass
class CreateBuildingRequest:
    """Create building request for internal use."""
    name: str
    address: Address
    dimensions: Dimensions
    status: Optional[Status] = None
    cost: Money
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UpdateBuildingRequest:
    """Update building request for internal use."""
    building_id: str
    name: Optional[str] = None
    address: Optional[Address] = None
    dimensions: Optional[Dimensions] = None
    status: Optional[Status] = None
    cost: Optional[Money] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class BuildingResponse:
    """Building response for internal use."""
    id: str
    name: str
    address: Address
    dimensions: Dimensions
    status: Status
    cost: Money
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BuildingSearchRequest:
    """Building search request for internal use."""
    name: Optional[str] = None
    status: Optional[Status] = None
    coordinates: Optional[Coordinates] = None
    radius: Optional[float] = None
    min_area: Optional[float] = None
    max_area: Optional[float] = None
    min_cost: Optional[float] = None
    max_cost: Optional[float] = None
    page: int = 1
    page_size: int = 10

@dataclass
class BuildingListResponse:
    """Building list response for internal use."""
    buildings: List[BuildingResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int

# Conversion Functions

def address_to_dto(address: Address) -> AddressDTO:
    """Convert Address value object to DTO."""
    return AddressDTO(
        street=address.street,
        city=address.city,
        state=address.state,
        postal_code=address.postal_code,
        country=address.country,
        coordinates={
            "latitude": address.coordinates.latitude,
            "longitude": address.coordinates.longitude
        } if address.coordinates else None
    )

def coordinates_to_dto(coordinates: Coordinates) -> CoordinatesDTO:
    """Convert Coordinates value object to DTO."""
    return CoordinatesDTO(
        latitude=coordinates.latitude,
        longitude=coordinates.longitude
    )

def dimensions_to_dto(dimensions: Dimensions) -> DimensionsDTO:
    """Convert Dimensions value object to DTO."""
    return DimensionsDTO(
        length=dimensions.length,
        width=dimensions.width,
        height=dimensions.height,
        area=dimensions.area,
        volume=dimensions.volume
    )

def status_to_dto(status: Status) -> StatusDTO:
    """Convert Status value object to DTO."""
    return StatusDTO(
        value=status.value,
        description=status.description
    )

def money_to_dto(money: Money) -> MoneyDTO:
    """Convert Money value object to DTO."""
    return MoneyDTO(
        amount=money.amount,
        currency=money.currency
    )

def building_to_response_dto(building_response: BuildingResponse) -> BuildingResponseDTO:
    """Convert BuildingResponse to BuildingResponseDTO."""
    return BuildingResponseDTO(
        id=building_response.id,
        name=building_response.name,
        address=address_to_dto(building_response.address),
        dimensions=dimensions_to_dto(building_response.dimensions),
        status=status_to_dto(building_response.status),
        cost=money_to_dto(building_response.cost),
        created_at=building_response.created_at,
        updated_at=building_response.updated_at,
        metadata=building_response.metadata
    )

def create_request_dto_to_internal(dto: CreateBuildingRequestDTO) -> CreateBuildingRequest:
    """Convert CreateBuildingRequestDTO to CreateBuildingRequest."""
    return CreateBuildingRequest(
        name=dto.name,
        address=Address(
            street=dto.address.street,
            city=dto.address.city,
            state=dto.address.state,
            postal_code=dto.address.postal_code,
            country=dto.address.country,
            coordinates=Coordinates(
                latitude=dto.address.coordinates["latitude"],
                longitude=dto.address.coordinates["longitude"]
            ) if dto.address.coordinates else None
        ),
        dimensions=Dimensions(
            length=dto.dimensions.length,
            width=dto.dimensions.width,
            height=dto.dimensions.height
        ),
        status=Status(dto.status.value) if dto.status else None,
        cost=Money(
            amount=dto.cost.amount,
            currency=dto.cost.currency
        ),
        metadata=dto.metadata
    ) 