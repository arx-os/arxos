"""
Repository Interfaces - Abstract Data Access Layer

This module contains abstract repository interfaces that define the
contract for data access operations. These interfaces follow the
Repository pattern and provide a clean separation between domain
logic and data persistence concerns.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .value_objects import (
    BuildingId, FloorId, RoomId, DeviceId, UserId, ProjectId,
    BuildingStatus, FloorStatus, RoomStatus, DeviceStatus, UserRole, ProjectStatus
)
from .exceptions import (
    RepositoryError, RepositoryConnectionError, RepositoryQueryError,
    RepositoryTransactionError, BuildingNotFoundError, FloorNotFoundError,
    RoomNotFoundError, DeviceNotFoundError, UserNotFoundError, ProjectNotFoundError
)


class BuildingRepository(ABC):
    """Abstract building repository interface."""
    
    @abstractmethod
    def save(self, building: 'Building') -> None:
        """Save a building to the repository."""
        pass
    
    @abstractmethod
    def get_by_id(self, building_id: BuildingId) -> Optional['Building']:
        """Get a building by its ID."""
        pass
    
    @abstractmethod
    def get_all(self) -> List['Building']:
        """Get all buildings."""
        pass
    
    @abstractmethod
    def get_by_status(self, status: BuildingStatus) -> List['Building']:
        """Get buildings by status."""
        pass
    
    @abstractmethod
    def get_by_address(self, address: str) -> List['Building']:
        """Get buildings by address."""
        pass
    
    @abstractmethod
    def delete(self, building_id: BuildingId) -> None:
        """Delete a building by ID."""
        pass
    
    @abstractmethod
    def exists(self, building_id: BuildingId) -> bool:
        """Check if a building exists."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Get the total number of buildings."""
        pass
    
    @abstractmethod
    def get_with_floors(self, building_id: BuildingId) -> Optional['Building']:
        """Get a building with all its floors."""
        pass


class FloorRepository(ABC):
    """Abstract floor repository interface."""
    
    @abstractmethod
    def save(self, floor: 'Floor') -> None:
        """Save a floor to the repository."""
        pass
    
    @abstractmethod
    def get_by_id(self, floor_id: FloorId) -> Optional['Floor']:
        """Get a floor by its ID."""
        pass
    
    @abstractmethod
    def get_by_building_id(self, building_id: BuildingId) -> List['Floor']:
        """Get all floors for a building."""
        pass
    
    @abstractmethod
    def get_by_building_and_number(self, building_id: BuildingId, floor_number: int) -> Optional['Floor']:
        """Get a floor by building ID and floor number."""
        pass
    
    @abstractmethod
    def get_by_status(self, status: FloorStatus) -> List['Floor']:
        """Get floors by status."""
        pass
    
    @abstractmethod
    def delete(self, floor_id: FloorId) -> None:
        """Delete a floor by ID."""
        pass
    
    @abstractmethod
    def exists(self, floor_id: FloorId) -> bool:
        """Check if a floor exists."""
        pass
    
    @abstractmethod
    def count_by_building(self, building_id: BuildingId) -> int:
        """Get the number of floors in a building."""
        pass


class RoomRepository(ABC):
    """Abstract room repository interface."""
    
    @abstractmethod
    def save(self, room: 'Room') -> None:
        """Save a room to the repository."""
        pass
    
    @abstractmethod
    def get_by_id(self, room_id: RoomId) -> Optional['Room']:
        """Get a room by its ID."""
        pass
    
    @abstractmethod
    def get_by_floor_id(self, floor_id: FloorId) -> List['Room']:
        """Get all rooms for a floor."""
        pass
    
    @abstractmethod
    def get_by_building_id(self, building_id: BuildingId) -> List['Room']:
        """Get all rooms for a building."""
        pass
    
    @abstractmethod
    def get_by_floor_and_number(self, floor_id: FloorId, room_number: str) -> Optional['Room']:
        """Get a room by floor ID and room number."""
        pass
    
    @abstractmethod
    def get_by_status(self, status: RoomStatus) -> List['Room']:
        """Get rooms by status."""
        pass
    
    @abstractmethod
    def delete(self, room_id: RoomId) -> None:
        """Delete a room by ID."""
        pass
    
    @abstractmethod
    def exists(self, room_id: RoomId) -> bool:
        """Check if a room exists."""
        pass
    
    @abstractmethod
    def count_by_floor(self, floor_id: FloorId) -> int:
        """Get the number of rooms on a floor."""
        pass
    
    @abstractmethod
    def count_by_building(self, building_id: BuildingId) -> int:
        """Get the number of rooms in a building."""
        pass


class DeviceRepository(ABC):
    """Abstract device repository interface."""
    
    @abstractmethod
    def save(self, device: 'Device') -> None:
        """Save a device to the repository."""
        pass
    
    @abstractmethod
    def get_by_id(self, device_id: DeviceId) -> Optional['Device']:
        """Get a device by its ID."""
        pass
    
    @abstractmethod
    def get_by_room_id(self, room_id: RoomId) -> List['Device']:
        """Get all devices in a room."""
        pass
    
    @abstractmethod
    def get_by_floor_id(self, floor_id: FloorId) -> List['Device']:
        """Get all devices on a floor."""
        pass
    
    @abstractmethod
    def get_by_building_id(self, building_id: BuildingId) -> List['Device']:
        """Get all devices in a building."""
        pass
    
    @abstractmethod
    def get_by_type(self, device_type: str) -> List['Device']:
        """Get devices by type."""
        pass
    
    @abstractmethod
    def get_by_status(self, status: DeviceStatus) -> List['Device']:
        """Get devices by status."""
        pass
    
    @abstractmethod
    def delete(self, device_id: DeviceId) -> None:
        """Delete a device by ID."""
        pass
    
    @abstractmethod
    def exists(self, device_id: DeviceId) -> bool:
        """Check if a device exists."""
        pass
    
    @abstractmethod
    def count_by_room(self, room_id: RoomId) -> int:
        """Get the number of devices in a room."""
        pass
    
    @abstractmethod
    def count_by_floor(self, floor_id: FloorId) -> int:
        """Get the number of devices on a floor."""
        pass
    
    @abstractmethod
    def count_by_building(self, building_id: BuildingId) -> int:
        """Get the number of devices in a building."""
        pass


class UserRepository(ABC):
    """Abstract user repository interface."""
    
    @abstractmethod
    def save(self, user: 'User') -> None:
        """Save a user to the repository."""
        pass
    
    @abstractmethod
    def get_by_id(self, user_id: UserId) -> Optional['User']:
        """Get a user by their ID."""
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional['User']:
        """Get a user by email address."""
        pass
    
    @abstractmethod
    def get_all(self) -> List['User']:
        """Get all users."""
        pass
    
    @abstractmethod
    def get_by_role(self, role: UserRole) -> List['User']:
        """Get users by role."""
        pass
    
    @abstractmethod
    def get_active_users(self) -> List['User']:
        """Get all active users."""
        pass
    
    @abstractmethod
    def delete(self, user_id: UserId) -> None:
        """Delete a user by ID."""
        pass
    
    @abstractmethod
    def exists(self, user_id: UserId) -> bool:
        """Check if a user exists."""
        pass
    
    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """Check if a user exists by email."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Get the total number of users."""
        pass


class ProjectRepository(ABC):
    """Abstract project repository interface."""
    
    @abstractmethod
    def save(self, project: 'Project') -> None:
        """Save a project to the repository."""
        pass
    
    @abstractmethod
    def get_by_id(self, project_id: ProjectId) -> Optional['Project']:
        """Get a project by its ID."""
        pass
    
    @abstractmethod
    def get_all(self) -> List['Project']:
        """Get all projects."""
        pass
    
    @abstractmethod
    def get_by_building_id(self, building_id: BuildingId) -> List['Project']:
        """Get all projects for a building."""
        pass
    
    @abstractmethod
    def get_by_status(self, status: ProjectStatus) -> List['Project']:
        """Get projects by status."""
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: UserId) -> List['Project']:
        """Get projects by user ID."""
        pass
    
    @abstractmethod
    def delete(self, project_id: ProjectId) -> None:
        """Delete a project by ID."""
        pass
    
    @abstractmethod
    def exists(self, project_id: ProjectId) -> bool:
        """Check if a project exists."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Get the total number of projects."""
        pass
    
    @abstractmethod
    def count_by_building(self, building_id: BuildingId) -> int:
        """Get the number of projects for a building."""
        pass


class UnitOfWork(ABC):
    """Abstract unit of work interface for transaction management."""
    
    @abstractmethod
    def __enter__(self):
        """Enter the unit of work context."""
        pass
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the unit of work context."""
        pass
    
    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""
        pass
    
    @abstractmethod
    def rollback(self) -> None:
        """Rollback the current transaction."""
        pass
    
    @property
    @abstractmethod
    def buildings(self) -> BuildingRepository:
        """Get the building repository."""
        pass
    
    @property
    @abstractmethod
    def floors(self) -> FloorRepository:
        """Get the floor repository."""
        pass
    
    @property
    @abstractmethod
    def rooms(self) -> RoomRepository:
        """Get the room repository."""
        pass
    
    @property
    @abstractmethod
    def devices(self) -> DeviceRepository:
        """Get the device repository."""
        pass
    
    @property
    @abstractmethod
    def users(self) -> UserRepository:
        """Get the user repository."""
        pass
    
    @property
    @abstractmethod
    def projects(self) -> ProjectRepository:
        """Get the project repository."""
        pass


class RepositoryFactory(ABC):
    """Abstract repository factory interface."""
    
    @abstractmethod
    def create_building_repository(self) -> BuildingRepository:
        """Create a building repository instance."""
        pass
    
    @abstractmethod
    def create_floor_repository(self) -> FloorRepository:
        """Create a floor repository instance."""
        pass
    
    @abstractmethod
    def create_room_repository(self) -> RoomRepository:
        """Create a room repository instance."""
        pass
    
    @abstractmethod
    def create_device_repository(self) -> DeviceRepository:
        """Create a device repository instance."""
        pass
    
    @abstractmethod
    def create_user_repository(self) -> UserRepository:
        """Create a user repository instance."""
        pass
    
    @abstractmethod
    def create_project_repository(self) -> ProjectRepository:
        """Create a project repository instance."""
        pass
    
    @abstractmethod
    def create_unit_of_work(self) -> UnitOfWork:
        """Create a unit of work instance."""
        pass 