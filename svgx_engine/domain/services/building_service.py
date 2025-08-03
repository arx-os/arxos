"""
Building Service - Domain Service for Building Operations
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from svgx_engine.domain.aggregates.building_aggregate import BuildingAggregate
from svgx_engine.domain.repositories.building_repository import BuildingRepository
from svgx_engine.domain.value_objects.address import Address
from svgx_engine.domain.value_objects.coordinates import Coordinates
from svgx_engine.domain.value_objects.dimensions import Dimensions
from svgx_engine.domain.value_objects.status import Status
from svgx_engine.domain.value_objects.money import Money

logger = logging.getLogger(__name__)

class BuildingService:
    """
    Domain service for building operations and business logic.
    """
    
    def __init__(self, building_repository: BuildingRepository):
    """
    Perform __init__ operation

Args:
        building_repository: Description of building_repository

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.building_repository = building_repository
    
    def create_building(
        self,
        name: str,
        address: Address,
        coordinates: Coordinates,
        dimensions: Dimensions,
        status: Status,
        cost: Money
    ) -> BuildingAggregate:
        """
        Create a new building with validation and business rules.
        """
        # Business logic validation
        if not name or len(name.strip()) == 0:
            raise ValueError("Building name cannot be empty")
        
        if cost.amount < 0:
            raise ValueError("Building cost cannot be negative")
        
        # Create building aggregate
        building_aggregate = BuildingAggregate.create(
            name=name,
            address=address,
            coordinates=coordinates,
            dimensions=dimensions,
            status=status,
            cost=cost
        )
        
        # Save to repository
        self.building_repository.save(building_aggregate)
        
        logger.info(f"Created building: {building_aggregate.id}")
        return building_aggregate
    
    def update_building(
        self,
        building_id: str,
        updates: Dict[str, Any]
    ) -> BuildingAggregate:
        """
        Update building with validation and business rules.
        """
        building = self.building_repository.get_by_id(building_id)
        if not building:
            raise ValueError(f"Building with id {building_id} not found")
        
        # Apply updates with validation
        building.update(updates)
        
        # Save to repository
        self.building_repository.save(building)
        
        logger.info(f"Updated building: {building_id}")
        return building
    
    def get_building(self, building_id: str) -> Optional[BuildingAggregate]:
        """
        Get building by ID.
        """
        return self.building_repository.get_by_id(building_id)
    
    def get_all_buildings(self) -> List[BuildingAggregate]:
        """
        Get all buildings.
        """
        return self.building_repository.get_all()
    
    def delete_building(self, building_id: str) -> bool:
        """
        Delete building with validation.
        """
        building = self.building_repository.get_by_id(building_id)
        if not building:
            return False
        
        # Business logic validation
        if building.status.value == "ACTIVE":
            raise ValueError("Cannot delete active building")
        
        self.building_repository.delete(building_id)
        logger.info(f"Deleted building: {building_id}")
        return True
    
    def get_buildings_by_status(self, status: Status) -> List[BuildingAggregate]:
        """
        Get buildings filtered by status.
        """
        return self.building_repository.get_by_status(status)
    
    def get_buildings_by_location(
        self,
        coordinates: Coordinates,
        radius: float
    ) -> List[BuildingAggregate]:
        """
        Get buildings within specified radius of coordinates.
        """
        return self.building_repository.get_by_location(coordinates, radius) 