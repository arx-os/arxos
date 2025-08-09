"""
Unified Building Service

This service provides a unified interface for building operations,
eliminating duplication between different service implementations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from domain.unified.entities import Building
from domain.unified.repositories import BuildingRepository
from domain.unified.value_objects import BuildingId, Address, Dimensions, BuildingStatus
from domain.unified.exceptions import InvalidBuildingError, BuildingNotFoundError

class UnifiedBuildingService:
    """
    Unified building service that provides a single interface for building operations.

    This service combines the best features from different service implementations
    and provides a clean, consistent interface for building management.
    """

    def __init__(self, building_repository: BuildingRepository):
        """Initialize the unified building service."""
        self.building_repository = building_repository
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_building(
        self,
        name: str,
        address: Address,
        status: BuildingStatus = BuildingStatus.PLANNED,
        dimensions: Optional[Dimensions] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Building:
        """
        Create a new building.

        Args:
            name: Building name
            address: Building address
            status: Building status
            dimensions: Building dimensions
            description: Building description
            created_by: User who created the building
            metadata: Additional metadata

        Returns:
            Created building entity

        Raises:
            InvalidBuildingError: If building data is invalid
        """
        try:
            building = Building.create(
                name=name,
                address=address,
                status=status,
                dimensions=dimensions,
                description=description,
                created_by=created_by,
                metadata=metadata or {}
            )

            saved_building = self.building_repository.save(building)
            self.logger.info(f"Created building {saved_building.id} with name '{name}'")

            return saved_building

        except Exception as e:
            self.logger.error(f"Error creating building '{name}': {e}")
            raise InvalidBuildingError(f"Failed to create building: {e}")

    def get_building(self, building_id: str) -> Building:
        """
        Get a building by ID.

        Args:
            building_id: Building ID

        Returns:
            Building entity

        Raises:
            BuildingNotFoundError: If building is not found
        """
        building = self.building_repository.get_by_id(building_id)
        if not building:
            raise BuildingNotFoundError(f"Building with ID {building_id} not found")

        return building

    def get_all_buildings(self) -> List[Building]:
        """
        Get all buildings.

        Returns:
            List of building entities
        """
        return self.building_repository.get_all()

    def get_buildings_by_status(self, status: str) -> List[Building]:
        """
        Get buildings by status.

        Args:
            status: Building status

        Returns:
            List of buildings with the specified status
        """
        return self.building_repository.get_by_status(status)

    def get_buildings_by_address(self, address: str) -> List[Building]:
        """
        Get buildings by address.

        Args:
            address: Address to search for

        Returns:
            List of buildings matching the address
        """
        return self.building_repository.get_by_address(address)

    def update_building_name(self, building_id: str, new_name: str, updated_by: str) -> Building:
        """
        Update building name.

        Args:
            building_id: Building ID
            new_name: New building name
            updated_by: User who updated the building

        Returns:
            Updated building entity

        Raises:
            BuildingNotFoundError: If building is not found
            InvalidBuildingError: If new name is invalid
        """
        building = self.get_building(building_id)
        building.update_name(new_name, updated_by)

        saved_building = self.building_repository.save(building)
        self.logger.info(f"Updated building {building_id} name to '{new_name}'")

        return saved_building

    def update_building_status(self, building_id: str, new_status: BuildingStatus, updated_by: str) -> Building:
        """
        Update building status.

        Args:
            building_id: Building ID
            new_status: New building status
            updated_by: User who updated the building

        Returns:
            Updated building entity

        Raises:
            BuildingNotFoundError: If building is not found
            InvalidStatusTransitionError: If status transition is invalid
        """
        building = self.get_building(building_id)
        building.update_status(new_status, updated_by)

        saved_building = self.building_repository.save(building)
        self.logger.info(f"Updated building {building_id} status to {new_status.value}")

        return saved_building

    def update_building_dimensions(self, building_id: str, dimensions: Dimensions, updated_by: str) -> Building:
        """
        Update building dimensions.

        Args:
            building_id: Building ID
            dimensions: New building dimensions
            updated_by: User who updated the building

        Returns:
            Updated building entity

        Raises:
            BuildingNotFoundError: If building is not found
            InvalidBuildingError: If dimensions are invalid
        """
        building = self.get_building(building_id)
        building.update_dimensions(dimensions, updated_by)

        saved_building = self.building_repository.save(building)
        self.logger.info(f"Updated building {building_id} dimensions")

        return saved_building

    def add_building_metadata(self, building_id: str, key: str, value: Any, updated_by: str) -> Building:
        """
        Add metadata to building.

        Args:
            building_id: Building ID
            key: Metadata key
            value: Metadata value
            updated_by: User who updated the building

        Returns:
            Updated building entity

        Raises:
            BuildingNotFoundError: If building is not found
        """
        building = self.get_building(building_id)
        building.add_metadata(key, value, updated_by)

        saved_building = self.building_repository.save(building)
        self.logger.info(f"Added metadata '{key}' to building {building_id}")

        return saved_building

    def remove_building_metadata(self, building_id: str, key: str, updated_by: str) -> Building:
        """
        Remove metadata from building.

        Args:
            building_id: Building ID
            key: Metadata key to remove
            updated_by: User who updated the building

        Returns:
            Updated building entity

        Raises:
            BuildingNotFoundError: If building is not found
        """
        building = self.get_building(building_id)
        building.remove_metadata(key, updated_by)

        saved_building = self.building_repository.save(building)
        self.logger.info(f"Removed metadata '{key}' from building {building_id}")

        return saved_building

    def delete_building(self, building_id: str) -> bool:
        """
        Delete a building.

        Args:
            building_id: Building ID

        Returns:
            True if building was deleted, False otherwise

        Raises:
            BuildingNotFoundError: If building is not found
        """
        building = self.get_building(building_id)

        success = self.building_repository.delete(building_id)
        if success:
            self.logger.info(f"Deleted building {building_id}")
        else:
            self.logger.error(f"Failed to delete building {building_id}")

        return success

    def get_building_statistics(self) -> Dict[str, Any]:
        """
        Get building statistics.

        Returns:
            Dictionary with building statistics
        """
        buildings = self.get_all_buildings()

        stats = {
            "total_buildings": len(buildings),
            "buildings_by_status": {},
            "total_floors": sum(b.floor_count for b in buildings),
            "total_rooms": sum(b.room_count for b in buildings),
            "total_devices": sum(b.device_count for b in buildings),
            "average_area": 0,
            "average_volume": 0
        }

        # Calculate status distribution
        for building in buildings:
            status = building.status.value
            stats["buildings_by_status"][status] = stats["buildings_by_status"].get(status, 0) + 1

        # Calculate averages
        buildings_with_area = [b for b in buildings if b.area is not None]
        buildings_with_volume = [b for b in buildings if b.volume is not None]

        if buildings_with_area:
            stats["average_area"] = sum(b.area for b in buildings_with_area) / len(buildings_with_area)

        if buildings_with_volume:
            stats["average_volume"] = sum(b.volume for b in buildings_with_volume) / len(buildings_with_volume)

        return stats
