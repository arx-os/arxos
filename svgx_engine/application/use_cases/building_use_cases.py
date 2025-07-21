"""
Building Use Cases

Use cases for building operations that orchestrate the domain layer
to achieve specific business goals.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...domain.aggregates.building_aggregate import BuildingAggregate
from ...domain.repositories.building_repository import BuildingRepository
from ...domain.value_objects.address import Address
from ...domain.value_objects.coordinates import Coordinates
from ...domain.value_objects.dimensions import Dimensions
from ...domain.value_objects.status import Status
from ...domain.value_objects.identifier import Identifier
from ..dto.building_dto import (
    BuildingDTO,
    CreateBuildingRequest,
    UpdateBuildingRequest,
    BuildingListResponse,
    BuildingSearchRequest
)


class CreateBuildingUseCase:
    """
    Use case for creating a new building.
    """
    
    def __init__(self, building_repository: BuildingRepository):
        """
        Initialize use case.
        
        Args:
            building_repository: Repository for building operations
        """
        self.building_repository = building_repository
    
    def execute(self, request: CreateBuildingRequest) -> BuildingDTO:
        """
        Execute the create building use case.
        
        Args:
            request: Create building request
            
        Returns:
            Created building DTO
            
        Raises:
            ValueError: If request validation fails
        """
        # Validate request
        errors = request.validate()
        if errors:
            raise ValueError(f"Invalid request: {'; '.join(errors)}")
        
        # Convert DTO to domain objects
        address = Address(
            street=request.address['street'],
            city=request.address['city'],
            state=request.address['state'],
            postal_code=request.address['postal_code'],
            country=request.address['country'],
            unit=request.address.get('unit')
        )
        
        coordinates = Coordinates(
            latitude=request.coordinates['latitude'],
            longitude=request.coordinates['longitude']
        )
        
        dimensions = Dimensions(
            length=request.dimensions['length'],
            width=request.dimensions['width'],
            height=request.dimensions.get('height')
        )
        
        status = None
        if request.status:
            status = Status.from_enum(Status.StatusType(request.status))
        
        # Create building aggregate
        building_aggregate = BuildingAggregate.create(
            name=request.name,
            address=address,
            coordinates=coordinates,
            dimensions=dimensions,
            building_type=request.building_type,
            status=status
        )
        
        # Save to repository
        saved_aggregate = self.building_repository.save(building_aggregate)
        
        # Return DTO
        return BuildingDTO.from_domain_aggregate(saved_aggregate)


class UpdateBuildingUseCase:
    """
    Use case for updating an existing building.
    """
    
    def __init__(self, building_repository: BuildingRepository):
        """
        Initialize use case.
        
        Args:
            building_repository: Repository for building operations
        """
        self.building_repository = building_repository
    
    def execute(self, building_id: str, request: UpdateBuildingRequest) -> BuildingDTO:
        """
        Execute the update building use case.
        
        Args:
            building_id: ID of building to update
            request: Update building request
            
        Returns:
            Updated building DTO
            
        Raises:
            ValueError: If request validation fails
            KeyError: If building not found
        """
        # Validate request
        errors = request.validate()
        if errors:
            raise ValueError(f"Invalid request: {'; '.join(errors)}")
        
        # Get existing building
        building_id_obj = Identifier(building_id)
        building_aggregate = self.building_repository.find_by_id(building_id_obj)
        
        if not building_aggregate:
            raise KeyError(f"Building with ID {building_id} not found")
        
        # Update building properties
        if request.name is not None:
            building_aggregate.update_name(request.name)
        
        if request.address is not None:
            address = Address(
                street=request.address['street'],
                city=request.address['city'],
                state=request.address['state'],
                postal_code=request.address['postal_code'],
                country=request.address['country'],
                unit=request.address.get('unit')
            )
            building_aggregate.update_address(address)
        
        if request.coordinates is not None:
            coordinates = Coordinates(
                latitude=request.coordinates['latitude'],
                longitude=request.coordinates['longitude']
            )
            building_aggregate.update_coordinates(coordinates)
        
        if request.dimensions is not None:
            dimensions = Dimensions(
                length=request.dimensions['length'],
                width=request.dimensions['width'],
                height=request.dimensions.get('height')
            )
            building_aggregate.update_dimensions(dimensions)
        
        if request.building_type is not None:
            building_aggregate.building.update_building_type(request.building_type)
        
        if request.status is not None:
            status = Status.from_enum(Status.StatusType(request.status))
            building_aggregate.change_status(status)
        
        if request.metadata is not None:
            building_aggregate.building.update_metadata(request.metadata)
        
        # Save to repository
        saved_aggregate = self.building_repository.save(building_aggregate)
        
        # Return DTO
        return BuildingDTO.from_domain_aggregate(saved_aggregate)


class GetBuildingUseCase:
    """
    Use case for retrieving a building by ID.
    """
    
    def __init__(self, building_repository: BuildingRepository):
        """
        Initialize use case.
        
        Args:
            building_repository: Repository for building operations
        """
        self.building_repository = building_repository
    
    def execute(self, building_id: str) -> Optional[BuildingDTO]:
        """
        Execute the get building use case.
        
        Args:
            building_id: ID of building to retrieve
            
        Returns:
            Building DTO if found, None otherwise
        """
        building_id_obj = Identifier(building_id)
        building_aggregate = self.building_repository.find_by_id(building_id_obj)
        
        if not building_aggregate:
            return None
        
        return BuildingDTO.from_domain_aggregate(building_aggregate)


class ListBuildingsUseCase:
    """
    Use case for listing buildings with search and pagination.
    """
    
    def __init__(self, building_repository: BuildingRepository):
        """
        Initialize use case.
        
        Args:
            building_repository: Repository for building operations
        """
        self.building_repository = building_repository
    
    def execute(self, request: BuildingSearchRequest) -> BuildingListResponse:
        """
        Execute the list buildings use case.
        
        Args:
            request: Search request with filters and pagination
            
        Returns:
            Building list response with pagination
            
        Raises:
            ValueError: If request validation fails
        """
        # Validate request
        errors = request.validate()
        if errors:
            raise ValueError(f"Invalid request: {'; '.join(errors)}")
        
        # Build search criteria
        buildings = []
        
        if request.coordinates and request.radius_km:
            coordinates = Coordinates(
                latitude=request.coordinates['latitude'],
                longitude=request.coordinates['longitude']
            )
            buildings = self.building_repository.find_by_coordinates(
                coordinates, radius_km=request.radius_km
            )
        elif request.building_type:
            buildings = self.building_repository.find_by_building_type(request.building_type)
        elif request.status:
            status = Status.from_enum(Status.StatusType(request.status))
            buildings = self.building_repository.find_by_status(status)
        elif request.min_area is not None and request.max_area is not None:
            buildings = self.building_repository.find_by_area_range(
                request.min_area, request.max_area
            )
        else:
            # Get all buildings with pagination
            offset = (request.page - 1) * request.page_size
            buildings = self.building_repository.find_all(
                limit=request.page_size,
                offset=offset
            )
        
        # Apply additional filtering
        if request.query:
            buildings = [b for b in buildings if request.query.lower() in b.name.lower()]
        
        # Convert to DTOs
        building_dtos = [BuildingDTO.from_domain_aggregate(b) for b in buildings]
        
        # Calculate pagination
        total_count = len(building_dtos)
        total_pages = (total_count + request.page_size - 1) // request.page_size
        
        # Apply pagination
        start_idx = (request.page - 1) * request.page_size
        end_idx = start_idx + request.page_size
        paginated_dtos = building_dtos[start_idx:end_idx]
        
        return BuildingListResponse(
            buildings=paginated_dtos,
            total_count=total_count,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages
        )


class DeleteBuildingUseCase:
    """
    Use case for deleting a building.
    """
    
    def __init__(self, building_repository: BuildingRepository):
        """
        Initialize use case.
        
        Args:
            building_repository: Repository for building operations
        """
        self.building_repository = building_repository
    
    def execute(self, building_id: str) -> bool:
        """
        Execute the delete building use case.
        
        Args:
            building_id: ID of building to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        building_id_obj = Identifier(building_id)
        
        # Check if building exists
        building_aggregate = self.building_repository.find_by_id(building_id_obj)
        if not building_aggregate:
            return False
        
        # Delete from repository
        return self.building_repository.delete(building_id_obj) 