"""
Building Repository - Abstract Repository Interface
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import logging

from svgx_engine.domain.entities.building import Building
from svgx_engine.domain.aggregates.building_aggregate import BuildingAggregate
from svgx_engine.domain.value_objects.identifier import Identifier
from svgx_engine.domain.value_objects.address import Address
from svgx_engine.domain.value_objects.coordinates import Coordinates
from svgx_engine.domain.value_objects.status import Status

logger = logging.getLogger(__name__)

class BuildingRepository(ABC):
    """
    Abstract repository interface for building persistence operations.
    """

    @abstractmethod
def save(self, building: BuildingAggregate) -> None:
        """
        Save a building aggregate to the repository.

        Args:
            building: The building aggregate to save
        """
        pass

    @abstractmethod
def get_by_id(self, building_id: str) -> Optional[BuildingAggregate]:
        """
        Get a building aggregate by its ID.

        Args:
            building_id: The ID of the building to retrieve

        Returns:
            The building aggregate if found, None otherwise
        """
        pass

    @abstractmethod
def get_all(self) -> List[BuildingAggregate]:
        """
        Get all building aggregates from the repository.

        Returns:
            List of all building aggregates
        """
        pass

    @abstractmethod
def delete(self, building_id: str) -> bool:
        """
        Delete a building aggregate by its ID.

        Args:
            building_id: The ID of the building to delete

        Returns:
            True if the building was deleted, False if not found
        """
        pass

    @abstractmethod
def get_by_status(self, status: Status) -> List[BuildingAggregate]:
        """
        Get building aggregates filtered by status.

        Args:
            status: The status to filter by

        Returns:
            List of building aggregates with the specified status
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
def get_by_address(self, address: Address) -> List[BuildingAggregate]:
        """
        Get building aggregates by address.

        Args:
            address: The address to search for

        Returns:
            List of building aggregates with the specified address
        """
        pass

    @abstractmethod
def count(self) -> int:
        """
        Get the total count of building aggregates in the repository.

        Returns:
            The total count of building aggregates
        """
        pass

    @abstractmethod
def exists(self, building_id: str) -> bool:
        """
        Check if a building aggregate exists by its ID.

        Args:
            building_id: The ID of the building to check

        Returns:
            True if the building exists, False otherwise
        """
        pass

    def get_by_name(self, name: str) -> List[BuildingAggregate]:
        """
        Get building aggregates by name (partial match).

        Args:
            name: The name to search for (case-insensitive partial match)

        Returns:
            List of building aggregates with matching names
        """
        all_buildings = self.get_all()
        return [
            building for building in all_buildings
            if name.lower() in building.name.lower()
        ]

    def get_active_buildings(self) -> List[BuildingAggregate]:
        """
        Get all active building aggregates.

        Returns:
            List of active building aggregates
        """
        from svgx_engine.domain.value_objects.status import Status, StatusType
        active_status = Status(StatusType.ACTIVE)
        return self.get_by_status(active_status)

    def get_inactive_buildings(self) -> List[BuildingAggregate]:
        """
        Get all inactive building aggregates.

        Returns:
            List of inactive building aggregates
        """
        from svgx_engine.domain.value_objects.status import Status, StatusType
        inactive_status = Status(StatusType.INACTIVE)
        return self.get_by_status(inactive_status)
