"""
Building Repository Interface

Defines the contract for building data access and persistence.
This interface follows the Repository pattern for clean separation of concerns.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.building import Building
from ..aggregates.building_aggregate import BuildingAggregate
from ..value_objects.identifier import Identifier
from ..value_objects.address import Address
from ..value_objects.coordinates import Coordinates
from ..value_objects.status import Status


class BuildingRepository(ABC):
    """
    Repository interface for building entities and aggregates.
    
    This interface defines the contract for building data access and persistence,
    following the Repository pattern to abstract data access details from the domain.
    """
    
    @abstractmethod
    def save(self, building_aggregate: BuildingAggregate) -> BuildingAggregate:
        """
        Save a building aggregate.
        
        Args:
            building_aggregate: Building aggregate to save
            
        Returns:
            Saved building aggregate
        """
        pass
    
    @abstractmethod
    def find_by_id(self, building_id: Identifier) -> Optional[BuildingAggregate]:
        """
        Find building aggregate by ID.
        
        Args:
            building_id: Building identifier
            
        Returns:
            Building aggregate if found, None otherwise
        """
        pass
    
    @abstractmethod
    def find_by_name(self, name: str) -> Optional[BuildingAggregate]:
        """
        Find building aggregate by name.
        
        Args:
            name: Building name
            
        Returns:
            Building aggregate if found, None otherwise
        """
        pass
    
    @abstractmethod
    def find_by_address(self, address: Address) -> List[BuildingAggregate]:
        """
        Find building aggregates by address.
        
        Args:
            address: Building address
            
        Returns:
            List of building aggregates matching the address
        """
        pass
    
    @abstractmethod
    def find_by_coordinates(self, coordinates: Coordinates, radius_km: float = 1.0) -> List[BuildingAggregate]:
        """
        Find building aggregates within radius of coordinates.
        
        Args:
            coordinates: Center coordinates
            radius_km: Search radius in kilometers
            
        Returns:
            List of building aggregates within the radius
        """
        pass
    
    @abstractmethod
    def find_by_status(self, status: Status) -> List[BuildingAggregate]:
        """
        Find building aggregates by status.
        
        Args:
            status: Building status
            
        Returns:
            List of building aggregates with the specified status
        """
        pass
    
    @abstractmethod
    def find_by_building_type(self, building_type: str) -> List[BuildingAggregate]:
        """
        Find building aggregates by building type.
        
        Args:
            building_type: Type of building
            
        Returns:
            List of building aggregates of the specified type
        """
        pass
    
    @abstractmethod
    def find_active_buildings(self) -> List[BuildingAggregate]:
        """
        Find all active building aggregates.
        
        Returns:
            List of active building aggregates
        """
        pass
    
    @abstractmethod
    def find_available_buildings(self) -> List[BuildingAggregate]:
        """
        Find all available building aggregates.
        
        Returns:
            List of available building aggregates
        """
        pass
    
    @abstractmethod
    def find_by_area_range(self, min_area: float, max_area: float) -> List[BuildingAggregate]:
        """
        Find building aggregates by area range.
        
        Args:
            min_area: Minimum area in square meters
            max_area: Maximum area in square meters
            
        Returns:
            List of building aggregates within the area range
        """
        pass
    
    @abstractmethod
    def find_by_volume_range(self, min_volume: float, max_volume: float) -> List[BuildingAggregate]:
        """
        Find building aggregates by volume range.
        
        Args:
            min_volume: Minimum volume in cubic meters
            max_volume: Maximum volume in cubic meters
            
        Returns:
            List of building aggregates within the volume range
        """
        pass
    
    @abstractmethod
    def find_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[BuildingAggregate]:
        """
        Find all building aggregates with optional pagination.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of building aggregates
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """
        Get total count of building aggregates.
        
        Returns:
            Total count of building aggregates
        """
        pass
    
    @abstractmethod
    def count_by_status(self, status: Status) -> int:
        """
        Get count of building aggregates by status.
        
        Args:
            status: Building status
            
        Returns:
            Count of building aggregates with the specified status
        """
        pass
    
    @abstractmethod
    def exists(self, building_id: Identifier) -> bool:
        """
        Check if building aggregate exists.
        
        Args:
            building_id: Building identifier
            
        Returns:
            True if building aggregate exists, False otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, building_id: Identifier) -> bool:
        """
        Delete building aggregate by ID.
        
        Args:
            building_id: Building identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def delete_by_status(self, status: Status) -> int:
        """
        Delete building aggregates by status.
        
        Args:
            status: Building status
            
        Returns:
            Number of building aggregates deleted
        """
        pass
    
    @abstractmethod
    def update_status(self, building_id: Identifier, new_status: Status) -> bool:
        """
        Update building status.
        
        Args:
            building_id: Building identifier
            new_status: New building status
            
        Returns:
            True if updated successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get building statistics.
        
        Returns:
            Dictionary containing building statistics
        """
        pass 