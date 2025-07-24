"""
In-Memory Building Repository Implementation
"""

from typing import List, Optional, Dict, Any
import logging

from svgx_engine.domain.repositories.building_repository import BuildingRepository
from svgx_engine.domain.aggregates.building_aggregate import BuildingAggregate
from svgx_engine.domain.value_objects.identifier import Identifier
from svgx_engine.domain.value_objects.address import Address
from svgx_engine.domain.value_objects.coordinates import Coordinates
from svgx_engine.domain.value_objects.status import Status

logger = logging.getLogger(__name__)

class InMemoryBuildingRepository(BuildingRepository):
    """
    In-memory implementation of the building repository.
    
    This implementation stores building aggregates in memory and is suitable
    for testing, development, and small-scale applications.
    """
    
    def __init__(self):
        self._buildings: Dict[str, BuildingAggregate] = {}
        self._next_id = 1
        logger.info("InMemoryBuildingRepository initialized")
    
    def save(self, building: BuildingAggregate) -> None:
        """
        Save a building aggregate to the repository.
        
        Args:
            building: The building aggregate to save
        """
        if not building:
            raise ValueError("Building aggregate cannot be None")
        
        building_id = str(building.id)
        self._buildings[building_id] = building
        logger.debug(f"Saved building: {building_id}")
    
    def get_by_id(self, building_id: str) -> Optional[BuildingAggregate]:
        """
        Get a building aggregate by its ID.
        
        Args:
            building_id: The ID of the building to retrieve
            
        Returns:
            The building aggregate if found, None otherwise
        """
        if not building_id:
            return None
        
        building = self._buildings.get(building_id)
        if building:
            logger.debug(f"Retrieved building: {building_id}")
        else:
            logger.debug(f"Building not found: {building_id}")
        
        return building
    
    def get_all(self) -> List[BuildingAggregate]:
        """
        Get all building aggregates from the repository.
        
        Returns:
            List of all building aggregates
        """
        buildings = list(self._buildings.values())
        logger.debug(f"Retrieved {len(buildings)} buildings")
        return buildings
    
    def delete(self, building_id: str) -> bool:
        """
        Delete a building aggregate by its ID.
        
        Args:
            building_id: The ID of the building to delete
            
        Returns:
            True if the building was deleted, False if not found
        """
        if not building_id:
            return False
        
        if building_id in self._buildings:
            del self._buildings[building_id]
            logger.debug(f"Deleted building: {building_id}")
            return True
        else:
            logger.debug(f"Building not found for deletion: {building_id}")
            return False
    
    def get_by_status(self, status: Status) -> List[BuildingAggregate]:
        """
        Get building aggregates filtered by status.
        
        Args:
            status: The status to filter by
            
        Returns:
            List of building aggregates with the specified status
        """
        if not status:
            return []
        
        buildings = [
            building for building in self._buildings.values()
            if building.status and building.status.value == status.value
        ]
        
        logger.debug(f"Retrieved {len(buildings)} buildings with status: {status.value}")
        return buildings
    
    def get_by_location(
        self,
        coordinates: Coordinates,
        radius: float
    ) -> List[BuildingAggregate]:
        """
        Get building aggregates within a specified radius of coordinates.
        
        Args:
            coordinates: The center coordinates for the search
            radius: The radius in kilometers for the search
            
        Returns:
            List of building aggregates within the specified radius
        """
        if not coordinates or radius <= 0:
            return []
        
        buildings = []
        for building in self._buildings.values():
            if building.address and building.address.coordinates:
                distance = self._calculate_distance(
                    coordinates,
                    building.address.coordinates
                )
                if distance <= radius:
                    buildings.append(building)
        
        logger.debug(f"Retrieved {len(buildings)} buildings within {radius}km of {coordinates}")
        return buildings
    
    def get_by_address(self, address: Address) -> List[BuildingAggregate]:
        """
        Get building aggregates by address.
        
        Args:
            address: The address to search for
            
        Returns:
            List of building aggregates with the specified address
        """
        if not address:
            return []
        
        buildings = [
            building for building in self._buildings.values()
            if building.address and self._addresses_match(building.address, address)
        ]
        
        logger.debug(f"Retrieved {len(buildings)} buildings with address: {address}")
        return buildings
    
    def count(self) -> int:
        """
        Get the total count of building aggregates in the repository.
        
        Returns:
            The total count of building aggregates
        """
        count = len(self._buildings)
        logger.debug(f"Repository contains {count} buildings")
        return count
    
    def exists(self, building_id: str) -> bool:
        """
        Check if a building aggregate exists by its ID.
        
        Args:
            building_id: The ID of the building to check
            
        Returns:
            True if the building exists, False otherwise
        """
        exists = building_id in self._buildings
        logger.debug(f"Building {building_id} exists: {exists}")
        return exists
    
    def clear(self) -> None:
        """
        Clear all building aggregates from the repository.
        """
        self._buildings.clear()
        logger.info("Repository cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get repository statistics.
        
        Returns:
            Dictionary containing repository statistics
        """
        total_buildings = len(self._buildings)
        status_counts = {}
        
        for building in self._buildings.values():
            if building.status:
                status = building.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
        
        stats = {
            "total_buildings": total_buildings,
            "status_counts": status_counts,
            "repository_type": "in_memory"
        }
        
        logger.debug(f"Repository statistics: {stats}")
        return stats
    
    def _calculate_distance(self, coord1: Coordinates, coord2: Coordinates) -> float:
        """
        Calculate distance between two coordinates using Haversine formula.
        
        Args:
            coord1: First coordinates
            coord2: Second coordinates
            
        Returns:
            Distance in kilometers
        """
        import math
        
        lat1, lon1 = coord1.latitude, coord1.longitude
        lat2, lon2 = coord2.latitude, coord2.longitude
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        r = 6371
        
        return c * r
    
    def _addresses_match(self, addr1: Address, addr2: Address) -> bool:
        """
        Check if two addresses match.
        
        Args:
            addr1: First address
            addr2: Second address
            
        Returns:
            True if addresses match, False otherwise
        """
        # Simple string comparison for now
        # In a real implementation, this would be more sophisticated
        return str(addr1).lower() == str(addr2).lower() 