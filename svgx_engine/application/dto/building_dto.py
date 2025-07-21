"""
Building DTOs

Data Transfer Objects for building operations in the application layer.
These DTOs define the structure of data exchanged between the application
layer and external systems (APIs, UI, etc.).
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...domain.value_objects.address import Address
from ...domain.value_objects.coordinates import Coordinates
from ...domain.value_objects.dimensions import Dimensions
from ...domain.value_objects.status import Status
from ...domain.value_objects.money import Money


@dataclass
class BuildingDTO:
    """
    Data Transfer Object for building information.
    
    This DTO represents building data as it should be exposed to external systems,
    providing a clean interface that hides internal domain complexity.
    """
    
    id: str
    name: str
    address: Dict[str, str]
    coordinates: Dict[str, float]
    dimensions: Dict[str, float]
    building_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_domain_aggregate(cls, building_aggregate) -> 'BuildingDTO':
        """
        Create BuildingDTO from domain aggregate.
        
        Args:
            building_aggregate: BuildingAggregate instance
            
        Returns:
            BuildingDTO instance
        """
        building = building_aggregate.building
        
        return cls(
            id=str(building.id),
            name=building.name,
            address={
                'street': building.address.street,
                'city': building.address.city,
                'state': building.address.state,
                'postal_code': building.address.postal_code,
                'country': building.address.country,
                'unit': building.address.unit,
                'full_address': building.address.full_address
            },
            coordinates={
                'latitude': building.coordinates.latitude,
                'longitude': building.coordinates.longitude
            },
            dimensions={
                'length': building.dimensions.length,
                'width': building.dimensions.width,
                'height': building.dimensions.height,
                'area': building.dimensions.area,
                'volume': building.dimensions.volume,
                'perimeter': building.dimensions.perimeter,
                'surface_area': building.dimensions.surface_area
            },
            building_type=building.building_type,
            status=building.status.value,
            created_at=building.created_at,
            updated_at=building.updated_at,
            metadata=building.metadata
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'coordinates': self.coordinates,
            'dimensions': self.dimensions,
            'building_type': self.building_type,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class CreateBuildingRequest:
    """
    Request DTO for creating a new building.
    """
    
    name: str
    address: Dict[str, str]
    coordinates: Dict[str, float]
    dimensions: Dict[str, float]
    building_type: str
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def validate(self) -> List[str]:
        """
        Validate the request data.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append("Building name is required")
        
        if not self.address:
            errors.append("Building address is required")
        else:
            required_address_fields = ['street', 'city', 'state', 'postal_code', 'country']
            for field in required_address_fields:
                if field not in self.address or not self.address[field]:
                    errors.append(f"Address {field} is required")
        
        if not self.coordinates:
            errors.append("Building coordinates are required")
        else:
            required_coord_fields = ['latitude', 'longitude']
            for field in required_coord_fields:
                if field not in self.coordinates:
                    errors.append(f"Coordinate {field} is required")
                else:
                    coord_value = self.coordinates[field]
                    if not isinstance(coord_value, (int, float)):
                        errors.append(f"Coordinate {field} must be a number")
        
        if not self.dimensions:
            errors.append("Building dimensions are required")
        else:
            required_dim_fields = ['length', 'width']
            for field in required_dim_fields:
                if field not in self.dimensions:
                    errors.append(f"Dimension {field} is required")
                else:
                    dim_value = self.dimensions[field]
                    if not isinstance(dim_value, (int, float)) or dim_value <= 0:
                        errors.append(f"Dimension {field} must be a positive number")
        
        if not self.building_type or not self.building_type.strip():
            errors.append("Building type is required")
        
        return errors


@dataclass
class UpdateBuildingRequest:
    """
    Request DTO for updating an existing building.
    """
    
    name: Optional[str] = None
    address: Optional[Dict[str, str]] = None
    coordinates: Optional[Dict[str, float]] = None
    dimensions: Optional[Dict[str, float]] = None
    building_type: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def validate(self) -> List[str]:
        """
        Validate the request data.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        if self.name is not None and not self.name.strip():
            errors.append("Building name cannot be empty")
        
        if self.address is not None:
            required_address_fields = ['street', 'city', 'state', 'postal_code', 'country']
            for field in required_address_fields:
                if field not in self.address or not self.address[field]:
                    errors.append(f"Address {field} is required")
        
        if self.coordinates is not None:
            required_coord_fields = ['latitude', 'longitude']
            for field in required_coord_fields:
                if field not in self.coordinates:
                    errors.append(f"Coordinate {field} is required")
                else:
                    coord_value = self.coordinates[field]
                    if not isinstance(coord_value, (int, float)):
                        errors.append(f"Coordinate {field} must be a number")
        
        if self.dimensions is not None:
            required_dim_fields = ['length', 'width']
            for field in required_dim_fields:
                if field not in self.dimensions:
                    errors.append(f"Dimension {field} is required")
                else:
                    dim_value = self.dimensions[field]
                    if not isinstance(dim_value, (int, float)) or dim_value <= 0:
                        errors.append(f"Dimension {field} must be a positive number")
        
        if self.building_type is not None and not self.building_type.strip():
            errors.append("Building type cannot be empty")
        
        return errors


@dataclass
class BuildingListResponse:
    """
    Response DTO for building list operations.
    """
    
    buildings: List[BuildingDTO]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            'buildings': [building.to_dict() for building in self.buildings],
            'total_count': self.total_count,
            'page': self.page,
            'page_size': self.page_size,
            'total_pages': self.total_pages
        }


@dataclass
class BuildingSearchRequest:
    """
    Request DTO for building search operations.
    """
    
    query: Optional[str] = None
    building_type: Optional[str] = None
    status: Optional[str] = None
    min_area: Optional[float] = None
    max_area: Optional[float] = None
    coordinates: Optional[Dict[str, float]] = None
    radius_km: Optional[float] = None
    page: int = 1
    page_size: int = 20
    sort_by: Optional[str] = None
    sort_order: str = 'asc'
    
    def validate(self) -> List[str]:
        """
        Validate the search request.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        if self.page < 1:
            errors.append("Page number must be at least 1")
        
        if self.page_size < 1 or self.page_size > 100:
            errors.append("Page size must be between 1 and 100")
        
        if self.sort_order not in ['asc', 'desc']:
            errors.append("Sort order must be 'asc' or 'desc'")
        
        if self.min_area is not None and self.max_area is not None:
            if self.min_area > self.max_area:
                errors.append("Minimum area cannot be greater than maximum area")
        
        if self.radius_km is not None and self.radius_km <= 0:
            errors.append("Radius must be a positive number")
        
        if self.coordinates is not None and self.radius_km is not None:
            required_coord_fields = ['latitude', 'longitude']
            for field in required_coord_fields:
                if field not in self.coordinates:
                    errors.append(f"Coordinate {field} is required when using radius search")
        
        return errors 