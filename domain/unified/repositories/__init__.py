"""
Unified Repository Interface

This module provides a unified repository interface that eliminates
duplication between different repository implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic

T = TypeVar('T')

class Repository(ABC, Generic[T]):
    """Base repository interface for all entities."""

    @abstractmethod
    def save(self, entity: T) -> T:
        """Save an entity."""
        pass

    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[T]:
        """Get all entities."""
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete entity by ID."""
        pass

    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """Check if entity exists."""
        pass

class BuildingRepository(Repository[T]):
    """Repository interface for building entities."""

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Building]:
        """Get building by name."""
        pass

    @abstractmethod
    def get_by_status(self, status: str) -> List[Building]:
        """Get buildings by status."""
        pass

    @abstractmethod
    def get_by_address(self, address: str) -> List[Building]:
        """Get buildings by address."""
        pass

class FloorRepository(Repository[T]):
    """Repository interface for floor entities."""

    @abstractmethod
    def get_by_building_id(self, building_id: str) -> List[Floor]:
        """Get floors by building ID."""
        pass

    @abstractmethod
    def get_by_floor_number(self, building_id: str, floor_number: int) -> Optional[Floor]:
        """Get floor by building ID and floor number."""
        pass

class RoomRepository(Repository[T]):
    """Repository interface for room entities."""

    @abstractmethod
    def get_by_floor_id(self, floor_id: str) -> List[Room]:
        """Get rooms by floor ID."""
        pass

    @abstractmethod
    def get_by_room_number(self, floor_id: str, room_number: str) -> Optional[Room]:
        """Get room by floor ID and room number."""
        pass

class DeviceRepository(Repository[T]):
    """Repository interface for device entities."""

    @abstractmethod
    def get_by_room_id(self, room_id: str) -> List[Device]:
        """Get devices by room ID."""
        pass

    @abstractmethod
    def get_by_device_type(self, device_type: str) -> List[Device]:
        """Get devices by type."""
        pass

class UserRepository(Repository[T]):
    """Repository interface for user entities."""

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        pass

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        pass

    @abstractmethod
    def get_by_role(self, role: str) -> List[User]:
        """Get users by role."""
        pass

class ProjectRepository(Repository[T]):
    """Repository interface for project entities."""

    @abstractmethod
    def get_by_building_id(self, building_id: str) -> List[Project]:
        """Get projects by building ID."""
        pass

    @abstractmethod
    def get_by_status(self, status: str) -> List[Project]:
        """Get projects by status."""
        pass
