"""
Building Use Cases - Application Layer Use Cases
"""

from typing import List, Optional, Dict, Any
import logging

from svgx_engine.domain.aggregates.building_aggregate import BuildingAggregate
from svgx_engine.domain.repositories.building_repository import BuildingRepository
from svgx_engine.domain.value_objects.address import Address
from svgx_engine.domain.value_objects.coordinates import Coordinates
from svgx_engine.domain.value_objects.dimensions import Dimensions
from svgx_engine.domain.value_objects.status import Status
from svgx_engine.domain.value_objects.identifier import Identifier
from svgx_engine.application.dto.building_dto import (
    CreateBuildingRequest,
    UpdateBuildingRequest,
    BuildingResponse,
    BuildingSearchRequest,
    BuildingListResponse
)

logger = logging.getLogger(__name__)

class CreateBuildingUseCase:
    """
    Use case for creating a new building.
    """
    
    def __init__(self, building_service):
    """
    Perform __init__ operation

Args:
        building_service: Description of building_service

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.building_service = building_service
    
    def execute(self, request: CreateBuildingRequest) -> BuildingResponse:
        """
        Execute the create building use case.
        
        Args:
            request: Create building request
            
        Returns:
            Building response with created building details
            
        Raises:
            ValueError: If request validation fails
        """
        logger.info(f"Creating building: {request.name}")
        
        try:
            # Create building aggregate
            building_aggregate = self.building_service.create_building(
                name=request.name,
                address=request.address,
                coordinates=request.address.coordinates,
                dimensions=request.dimensions,
                status=request.status or Status("ACTIVE"),
                cost=request.cost
            )
            
            # Convert to response
            response = BuildingResponse(
                id=str(building_aggregate.id),
                name=building_aggregate.building.name,
                address=building_aggregate.building.address,
                dimensions=building_aggregate.building.dimensions,
                status=building_aggregate.status,
                cost=building_aggregate.cost,
                created_at=building_aggregate.building.created_at,
                updated_at=building_aggregate.building.updated_at,
                metadata=building_aggregate.building.metadata
            )
            
            logger.info(f"Building created successfully: {response.id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to create building: {e}")
            raise

class UpdateBuildingUseCase:
    """
    Use case for updating an existing building.
    """
    
    def __init__(self, building_service):
        self.building_service = building_service
    
    def execute(self, request: UpdateBuildingRequest) -> BuildingResponse:
        """
        Execute the update building use case.
        
        Args:
            request: Update building request
            
        Returns:
            Building response with updated building details
            
        Raises:
            ValueError: If building not found or validation fails
        """
        logger.info(f"Updating building: {request.building_id}")
        
        try:
            # Prepare updates dictionary
            updates = {}
            if request.name is not None:
                updates["name"] = request.name
            if request.address is not None:
                updates["address"] = request.address
            if request.dimensions is not None:
                updates["dimensions"] = request.dimensions
            if request.status is not None:
                updates["status"] = request.status
            if request.cost is not None:
                updates["cost"] = request.cost
            if request.metadata is not None:
                updates["metadata"] = request.metadata
            
            # Update building
            building_aggregate = self.building_service.update_building(
                building_id=request.building_id,
                updates=updates
            )
            
            # Convert to response
            response = BuildingResponse(
                id=str(building_aggregate.id),
                name=building_aggregate.building.name,
                address=building_aggregate.building.address,
                dimensions=building_aggregate.building.dimensions,
                status=building_aggregate.status,
                cost=building_aggregate.cost,
                created_at=building_aggregate.building.created_at,
                updated_at=building_aggregate.building.updated_at,
                metadata=building_aggregate.building.metadata
            )
            
            logger.info(f"Building updated successfully: {response.id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to update building: {e}")
            raise

class GetBuildingUseCase:
    """
    Use case for retrieving a building by ID.
    """
    
    def __init__(self, building_service):
        self.building_service = building_service
    
    def execute(self, building_id: str) -> Optional[BuildingResponse]:
        """
        Execute the get building use case.
        
        Args:
            building_id: ID of the building to retrieve
            
        Returns:
            Building response if found, None otherwise
        """
        logger.info(f"Getting building: {building_id}")
        
        try:
            building_aggregate = self.building_service.get_building(building_id)
            
            if not building_aggregate:
                logger.warning(f"Building not found: {building_id}")
                return None
            
            # Convert to response
            response = BuildingResponse(
                id=str(building_aggregate.id),
                name=building_aggregate.building.name,
                address=building_aggregate.building.address,
                dimensions=building_aggregate.building.dimensions,
                status=building_aggregate.status,
                cost=building_aggregate.cost,
                created_at=building_aggregate.building.created_at,
                updated_at=building_aggregate.building.updated_at,
                metadata=building_aggregate.building.metadata
            )
            
            logger.info(f"Building retrieved successfully: {response.id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to get building: {e}")
            raise

class DeleteBuildingUseCase:
    """
    Use case for deleting a building.
    """
    
    def __init__(self, building_service):
        self.building_service = building_service
    
    def execute(self, building_id: str) -> bool:
        """
        Execute the delete building use case.
        
        Args:
            building_id: ID of the building to delete
            
        Returns:
            True if building was deleted, False if not found
        """
        logger.info(f"Deleting building: {building_id}")
        
        try:
            success = self.building_service.delete_building(building_id)
            
            if success:
                logger.info(f"Building deleted successfully: {building_id}")
            else:
                logger.warning(f"Building not found for deletion: {building_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete building: {e}")
            raise

class ListBuildingsUseCase:
    """
    Use case for listing buildings with optional filtering.
    """
    
    def __init__(self, building_service):
        self.building_service = building_service
    
    def execute(self, request: Optional[BuildingSearchRequest] = None) -> BuildingListResponse:
        """
        Execute the list buildings use case.
        
        Args:
            request: Optional search request with filters
            
        Returns:
            Building list response with pagination
        """
        logger.info("Listing buildings")
        
        try:
            # Get all buildings
            buildings = self.building_service.get_all_buildings()
            
            # Apply filters if provided
            if request:
                buildings = self._apply_filters(buildings, request)
            
            # Apply pagination
            total_count = len(buildings)
            page = request.page if request else 1
            page_size = request.page_size if request else 10
            
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_buildings = buildings[start_index:end_index]
            
            # Convert to responses
            building_responses = []
            for building_aggregate in paginated_buildings:
                response = BuildingResponse(
                    id=str(building_aggregate.id),
                    name=building_aggregate.building.name,
                    address=building_aggregate.building.address,
                    dimensions=building_aggregate.building.dimensions,
                    status=building_aggregate.status,
                    cost=building_aggregate.cost,
                    created_at=building_aggregate.building.created_at,
                    updated_at=building_aggregate.building.updated_at,
                    metadata=building_aggregate.building.metadata
                )
                building_responses.append(response)
            
            # Calculate total pages
            total_pages = (total_count + page_size - 1) // page_size
            
            result = BuildingListResponse(
                buildings=building_responses,
                total_count=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
            logger.info(f"Listed {len(building_responses)} buildings out of {total_count}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to list buildings: {e}")
            raise
    
    def _apply_filters(self, buildings: List[BuildingAggregate], request: BuildingSearchRequest) -> List[BuildingAggregate]:
        """
        Apply filters to building list.
        
        Args:
            buildings: List of building aggregates
            request: Search request with filters
            
        Returns:
            Filtered list of building aggregates
        """
        filtered_buildings = buildings
        
        # Filter by name
        if request.name:
            filtered_buildings = [
                b for b in filtered_buildings
                if request.name.lower() in b.building.name.lower()
            ]
        
        # Filter by status
        if request.status:
            filtered_buildings = [
                b for b in filtered_buildings
                if b.status and b.status.value == request.status.value
            ]
        
        # Filter by location
        if request.coordinates and request.radius:
            filtered_buildings = self.building_service.get_buildings_by_location(
                request.coordinates, request.radius
            )
        
        # Filter by area
        if request.min_area or request.max_area:
            filtered_buildings = [
                b for b in filtered_buildings
                if self._area_in_range(b.building.dimensions.area, request.min_area, request.max_area)
            ]
        
        # Filter by cost
        if request.min_cost or request.max_cost:
            filtered_buildings = [
                b for b in filtered_buildings
                if self._cost_in_range(b.cost.amount, request.min_cost, request.max_cost)
            ]
        
        return filtered_buildings
    
    def _area_in_range(self, area: float, min_area: Optional[float], max_area: Optional[float]) -> bool:
        """Check if area is within specified range."""
        if min_area and area < min_area:
            return False
        if max_area and area > max_area:
            return False
        return True
    
    def _cost_in_range(self, cost: float, min_cost: Optional[float], max_cost: Optional[float]) -> bool:
        """Check if cost is within specified range."""
        if min_cost and cost < min_cost:
            return False
        if max_cost and cost > max_cost:
            return False
        return True 