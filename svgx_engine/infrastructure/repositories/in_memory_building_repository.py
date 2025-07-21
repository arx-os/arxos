"""
In-Memory Building Repository Implementation

In-memory implementation of the BuildingRepository interface for testing
and development purposes.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from ...domain.repositories.building_repository import BuildingRepository
from ...domain.aggregates.building_aggregate import BuildingAggregate
from ...domain.value_objects.identifier import Identifier
from ...domain.value_objects.address import Address
from ...domain.value_objects.coordinates import Coordinates
from ...domain.value_objects.status import Status


class InMemoryBuildingRepository(BuildingRepository):
    """
    In-memory implementation of BuildingRepository for testing and development.
    
    This implementation stores building aggregates in memory and provides
    basic search and filtering capabilities.
    """
    
    def __init__(self):
        """Initialize the in-memory repository."""
        self._buildings: Dict[str, BuildingAggregate] = {}
        self._next_id = 1
    
    def save(self, building_aggregate: BuildingAggregate) -> BuildingAggregate:
        """
        Save a building aggregate.
        
        Args:
            building_aggregate: Building aggregate to save
            
        Returns:
            Saved building aggregate
        """
        if not building_aggregate.id:
            # Generate new ID for new buildings
            new_id = Identifier(str(self._next_id), prefix="BLD")
            building_aggregate.building.id = new_id
            self._next_id += 1
        
        # Store in memory
        building_id = str(building_aggregate.id)
        self._buildings[building_id] = building_aggregate
        
        return building_aggregate
    
    def find_by_id(self, building_id: Identifier) -> Optional[BuildingAggregate]:
        """
        Find building aggregate by ID.
        
        Args:
            building_id: Building identifier
            
        Returns:
            Building aggregate if found, None otherwise
        """
        return self._buildings.get(str(building_id))
    
    def find_by_name(self, name: str) -> Optional[BuildingAggregate]:
        """
        Find building aggregate by name.
        
        Args:
            name: Building name
            
        Returns:
            Building aggregate if found, None otherwise
        """
        for building in self._buildings.values():
            if building.building.name.lower() == name.lower():
                return building
        return None
    
    def find_by_address(self, address: Address) -> List[BuildingAggregate]:
        """
        Find building aggregates by address.
        
        Args:
            address: Building address
            
        Returns:
            List of building aggregates matching the address
        """
        matching_buildings = []
        for building in self._buildings.values():
            if building.building.address.full_address == address.full_address:
                matching_buildings.append(building)
        return matching_buildings
    
    def find_by_coordinates(self, coordinates: Coordinates, radius_km: float = 1.0) -> List[BuildingAggregate]:
        """
        Find building aggregates within radius of coordinates.
        
        Args:
            coordinates: Center coordinates
            radius_km: Search radius in kilometers
            
        Returns:
            List of building aggregates within the radius
        """
        matching_buildings = []
        for building in self._buildings.values():
            distance = building.building.coordinates.distance_to(coordinates)
            if distance <= radius_km:
                matching_buildings.append(building)
        return matching_buildings
    
    def find_by_status(self, status: Status) -> List[BuildingAggregate]:
        """
        Find building aggregates by status.
        
        Args:
            status: Building status
            
        Returns:
            List of building aggregates with the specified status
        """
        matching_buildings = []
        for building in self._buildings.values():
            if building.building.status.value == status.value:
                matching_buildings.append(building)
        return matching_buildings
    
    def find_by_building_type(self, building_type: str) -> List[BuildingAggregate]:
        """
        Find building aggregates by building type.
        
        Args:
            building_type: Type of building
            
        Returns:
            List of building aggregates of the specified type
        """
        matching_buildings = []
        for building in self._buildings.values():
            if building.building.building_type.lower() == building_type.lower():
                matching_buildings.append(building)
        return matching_buildings
    
    def find_active_buildings(self) -> List[BuildingAggregate]:
        """
        Find all active building aggregates.
        
        Returns:
            List of active building aggregates
        """
        active_status = Status.active()
        return self.find_by_status(active_status)
    
    def find_available_buildings(self) -> List[BuildingAggregate]:
        """
        Find all available building aggregates.
        
        Returns:
            List of available building aggregates
        """
        available_buildings = []
        for building in self._buildings.values():
            if building.building.is_available():
                available_buildings.append(building)
        return available_buildings
    
    def find_by_area_range(self, min_area: float, max_area: float) -> List[BuildingAggregate]:
        """
        Find building aggregates by area range.
        
        Args:
            min_area: Minimum area in square meters
            max_area: Maximum area in square meters
            
        Returns:
            List of building aggregates within the area range
        """
        matching_buildings = []
        for building in self._buildings.values():
            area = building.building.dimensions.area
            if min_area <= area <= max_area:
                matching_buildings.append(building)
        return matching_buildings
    
    def find_by_volume_range(self, min_volume: float, max_volume: float) -> List[BuildingAggregate]:
        """
        Find building aggregates by volume range.
        
        Args:
            min_volume: Minimum volume in cubic meters
            max_volume: Maximum volume in cubic meters
            
        Returns:
            List of building aggregates within the volume range
        """
        matching_buildings = []
        for building in self._buildings.values():
            volume = building.building.dimensions.volume
            if volume is not None and min_volume <= volume <= max_volume:
                matching_buildings.append(building)
        return matching_buildings
    
    def find_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[BuildingAggregate]:
        """
        Find all building aggregates with optional pagination.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of building aggregates
        """
        buildings = list(self._buildings.values())
        
        if offset is not None:
            buildings = buildings[offset:]
        
        if limit is not None:
            buildings = buildings[:limit]
        
        return buildings
    
    def count(self) -> int:
        """
        Get total count of building aggregates.
        
        Returns:
            Total count of building aggregates
        """
        return len(self._buildings)
    
    def count_by_status(self, status: Status) -> int:
        """
        Get count of building aggregates by status.
        
        Args:
            status: Building status
            
        Returns:
            Count of building aggregates with the specified status
        """
        return len(self.find_by_status(status))
    
    def exists(self, building_id: Identifier) -> bool:
        """
        Check if building aggregate exists.
        
        Args:
            building_id: Building identifier
            
        Returns:
            True if building aggregate exists, False otherwise
        """
        return str(building_id) in self._buildings
    
    def delete(self, building_id: Identifier) -> bool:
        """
        Delete building aggregate by ID.
        
        Args:
            building_id: Building identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        building_id_str = str(building_id)
        if building_id_str in self._buildings:
            del self._buildings[building_id_str]
            return True
        return False
    
    def delete_by_status(self, status: Status) -> int:
        """
        Delete building aggregates by status.
        
        Args:
            status: Building status
            
        Returns:
            Number of building aggregates deleted
        """
        buildings_to_delete = self.find_by_status(status)
        deleted_count = 0
        
        for building in buildings_to_delete:
            building_id = str(building.id)
            if building_id in self._buildings:
                del self._buildings[building_id]
                deleted_count += 1
        
        return deleted_count
    
    def update_status(self, building_id: Identifier, new_status: Status) -> bool:
        """
        Update building status.
        
        Args:
            building_id: Building identifier
            new_status: New building status
            
        Returns:
            True if updated successfully, False otherwise
        """
        building_aggregate = self.find_by_id(building_id)
        if building_aggregate:
            building_aggregate.change_status(new_status)
            self.save(building_aggregate)
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get building statistics.
        
        Returns:
            Dictionary containing building statistics
        """
        total_buildings = len(self._buildings)
        
        if total_buildings == 0:
            return {
                "total_buildings": 0,
                "total_area": 0.0,
                "total_volume": 0.0,
                "status_distribution": {},
                "type_distribution": {},
                "average_area": 0.0,
                "average_volume": 0.0
            }
        
        # Calculate statistics
        total_area = sum(b.building.dimensions.area for b in self._buildings.values())
        total_volume = sum(
            b.building.dimensions.volume or 0 
            for b in self._buildings.values() 
            if b.building.dimensions.volume is not None
        )
        
        # Status distribution
        status_distribution = {}
        for building in self._buildings.values():
            status = building.building.status.value
            status_distribution[status] = status_distribution.get(status, 0) + 1
        
        # Type distribution
        type_distribution = {}
        for building in self._buildings.values():
            building_type = building.building.building_type
            type_distribution[building_type] = type_distribution.get(building_type, 0) + 1
        
        # Averages
        average_area = total_area / total_buildings
        buildings_with_volume = [
            b for b in self._buildings.values() 
            if b.building.dimensions.volume is not None
        ]
        average_volume = total_volume / len(buildings_with_volume) if buildings_with_volume else 0.0
        
        return {
            "total_buildings": total_buildings,
            "total_area": total_area,
            "total_volume": total_volume,
            "status_distribution": status_distribution,
            "type_distribution": type_distribution,
            "average_area": average_area,
            "average_volume": average_volume
        }
    
    def clear(self):
        """Clear all buildings from the repository (for testing)."""
        self._buildings.clear()
        self._next_id = 1 