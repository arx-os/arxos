"""
Building Domain Service

Contains business logic for building operations that don't belong to specific entities.
This service implements domain logic that spans multiple entities or aggregates.
"""

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from ..aggregates.building_aggregate import BuildingAggregate
from ..repositories.building_repository import BuildingRepository
from ..value_objects.address import Address
from ..value_objects.coordinates import Coordinates
from ..value_objects.dimensions import Dimensions
from ..value_objects.status import Status
from ..value_objects.money import Money


class BuildingService(ABC):
    """
    Domain service for building-related business logic.
    
    This service contains business logic that doesn't belong to any specific
    building entity or aggregate, following the Domain Service pattern.
    """
    
    def __init__(self, building_repository: BuildingRepository):
        """
        Initialize building service.
        
        Args:
            building_repository: Repository for building data access
        """
        self.building_repository = building_repository
    
    def find_nearest_buildings(self, coordinates: Coordinates, 
                              limit: int = 10, 
                              max_distance_km: float = 50.0) -> List[BuildingAggregate]:
        """
        Find the nearest buildings to given coordinates.
        
        Args:
            coordinates: Target coordinates
            limit: Maximum number of buildings to return
            max_distance_km: Maximum distance in kilometers
            
        Returns:
            List of nearest building aggregates
        """
        # Get all buildings within the maximum distance
        nearby_buildings = self.building_repository.find_by_coordinates(
            coordinates, radius_km=max_distance_km
        )
        
        # Sort by distance and limit results
        sorted_buildings = sorted(
            nearby_buildings,
            key=lambda building: building.calculate_distance_to(coordinates)
        )
        
        return sorted_buildings[:limit]
    
    def find_buildings_by_area_requirements(self, 
                                          min_area: float, 
                                          max_area: float,
                                          building_type: Optional[str] = None,
                                          status: Optional[Status] = None) -> List[BuildingAggregate]:
        """
        Find buildings that meet area requirements.
        
        Args:
            min_area: Minimum required area in square meters
            max_area: Maximum required area in square meters
            building_type: Optional building type filter
            status: Optional status filter
            
        Returns:
            List of building aggregates meeting the requirements
        """
        # Get buildings by area range
        buildings = self.building_repository.find_by_area_range(min_area, max_area)
        
        # Apply additional filters
        if building_type:
            buildings = [b for b in buildings if b.building_type == building_type]
        
        if status:
            buildings = [b for b in buildings if b.status == status]
        
        return buildings
    
    def calculate_total_building_area(self, buildings: List[BuildingAggregate]) -> float:
        """
        Calculate total area of multiple buildings.
        
        Args:
            buildings: List of building aggregates
            
        Returns:
            Total area in square meters
        """
        return sum(building.get_area() for building in buildings)
    
    def calculate_total_building_volume(self, buildings: List[BuildingAggregate]) -> float:
        """
        Calculate total volume of multiple buildings.
        
        Args:
            buildings: List of building aggregates
            
        Returns:
            Total volume in cubic meters
        """
        total_volume = 0.0
        for building in buildings:
            volume = building.get_volume()
            if volume is not None:
                total_volume += volume
        return total_volume
    
    def find_buildings_by_capacity_requirements(self, 
                                             min_capacity: float,
                                             max_capacity: float,
                                             capacity_type: str = "area") -> List[BuildingAggregate]:
        """
        Find buildings that meet capacity requirements.
        
        Args:
            min_capacity: Minimum required capacity
            max_capacity: Maximum required capacity
            capacity_type: Type of capacity ("area" or "volume")
            
        Returns:
            List of building aggregates meeting the capacity requirements
        """
        if capacity_type == "area":
            return self.building_repository.find_by_area_range(min_capacity, max_capacity)
        elif capacity_type == "volume":
            return self.building_repository.find_by_volume_range(min_capacity, max_capacity)
        else:
            raise ValueError("Capacity type must be 'area' or 'volume'")
    
    def get_building_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive building statistics.
        
        Returns:
            Dictionary containing building statistics
        """
        all_buildings = self.building_repository.find_all()
        
        if not all_buildings:
            return {
                "total_buildings": 0,
                "total_area": 0.0,
                "total_volume": 0.0,
                "status_distribution": {},
                "type_distribution": {},
                "average_area": 0.0,
                "average_volume": 0.0
            }
        
        # Calculate basic statistics
        total_buildings = len(all_buildings)
        total_area = self.calculate_total_building_area(all_buildings)
        total_volume = self.calculate_total_building_volume(all_buildings)
        
        # Calculate status distribution
        status_distribution = {}
        for building in all_buildings:
            status = building.status.value
            status_distribution[status] = status_distribution.get(status, 0) + 1
        
        # Calculate type distribution
        type_distribution = {}
        for building in all_buildings:
            building_type = building.building_type
            type_distribution[building_type] = type_distribution.get(building_type, 0) + 1
        
        # Calculate averages
        average_area = total_area / total_buildings if total_buildings > 0 else 0.0
        
        buildings_with_volume = [b for b in all_buildings if b.get_volume() is not None]
        average_volume = (self.calculate_total_building_volume(buildings_with_volume) / 
                         len(buildings_with_volume)) if buildings_with_volume else 0.0
        
        return {
            "total_buildings": total_buildings,
            "total_area": total_area,
            "total_volume": total_volume,
            "status_distribution": status_distribution,
            "type_distribution": type_distribution,
            "average_area": average_area,
            "average_volume": average_volume
        }
    
    def validate_building_placement(self, 
                                  address: Address,
                                  coordinates: Coordinates,
                                  dimensions: Dimensions) -> Dict[str, Any]:
        """
        Validate if a building can be placed at the given location.
        
        Args:
            address: Proposed building address
            coordinates: Proposed building coordinates
            dimensions: Proposed building dimensions
            
        Returns:
            Dictionary containing validation results
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "nearby_buildings": []
        }
        
        # Check for existing buildings at the same address
        existing_buildings = self.building_repository.find_by_address(address)
        if existing_buildings:
            validation_result["is_valid"] = False
            validation_result["errors"].append(
                f"Building already exists at address: {address.full_address}"
            )
        
        # Check for nearby buildings that might conflict
        nearby_buildings = self.building_repository.find_by_coordinates(
            coordinates, radius_km=0.1  # 100 meters
        )
        
        if nearby_buildings:
            validation_result["warnings"].append(
                f"Found {len(nearby_buildings)} buildings within 100 meters"
            )
            validation_result["nearby_buildings"] = [
                {
                    "id": str(building.id),
                    "name": building.name,
                    "distance": building.calculate_distance_to(coordinates)
                }
                for building in nearby_buildings
            ]
        
        # Validate dimensions
        if dimensions.area < 1.0:  # Minimum 1 square meter
            validation_result["is_valid"] = False
            validation_result["errors"].append("Building area must be at least 1 square meter")
        
        if dimensions.volume is not None and dimensions.volume < 1.0:
            validation_result["is_valid"] = False
            validation_result["errors"].append("Building volume must be at least 1 cubic meter")
        
        return validation_result
    
    def estimate_building_cost(self, 
                             dimensions: Dimensions,
                             building_type: str,
                             location_factor: float = 1.0) -> Money:
        """
        Estimate building construction cost.
        
        Args:
            dimensions: Building dimensions
            building_type: Type of building
            location_factor: Location cost factor
            
        Returns:
            Estimated cost as Money value object
        """
        # Base costs per square meter for different building types
        base_costs = {
            "residential": 1500.0,
            "commercial": 2000.0,
            "industrial": 1800.0,
            "office": 2200.0,
            "warehouse": 1200.0,
            "retail": 2500.0
        }
        
        base_cost_per_sqm = base_costs.get(building_type.lower(), 2000.0)
        area = dimensions.area
        
        # Calculate base cost
        base_cost = base_cost_per_sqm * area * location_factor
        
        # Add volume factor for 3D buildings
        if dimensions.is_3d and dimensions.volume:
            volume_factor = dimensions.volume / area  # Height factor
            base_cost *= (1 + (volume_factor - 3) * 0.1)  # 10% increase per meter above 3m
        
        return Money.from_float(base_cost, "USD")
    
    def __str__(self) -> str:
        """String representation of building service."""
        return f"BuildingService(repository={self.building_repository})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"BuildingService(building_repository={self.building_repository})" 