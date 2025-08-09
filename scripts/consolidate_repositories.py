#!/usr/bin/env python3
"""
Script to consolidate repository implementations and eliminate repository chaos.
This script will create a unified repository structure with proper abstractions.
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any

def create_unified_repository_implementations():
    """Create unified repository implementations."""

    # Create unified infrastructure directory
    unified_infra = Path("infrastructure/unified")
    unified_infra.mkdir(exist_ok=True)

    # Create repository implementations directory
    repos_dir = unified_infra / "repositories"
    repos_dir.mkdir(exist_ok=True)

    return unified_infra, repos_dir

def create_base_repository():
    """Create a base repository implementation."""

    content = '''""
Base Repository Implementation

This module provides a base repository implementation that can be
extended by specific repository implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, TypeVar, Generic
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from domain.unified.repositories import Repository

T = TypeVar('T')

class BaseRepository(Repository[T], ABC):
    """
    Base repository implementation with common functionality.

    This class provides a foundation for all repository implementations
    with common CRUD operations and error handling.
    """

    def __init__(self, session: Session):
        """Initialize the base repository."""
        self.session = session
        self.logger = logging.getLogger(self.__class__.__name__)

    def save(self, entity: T) -> T:
        """Save an entity to the database."""
        try:
            self.session.add(entity)
            self.session.commit()
            self.logger.info(f"Saved {entity.__class__.__name__} with ID {getattr(entity, 'id', 'unknown')}")
            return entity
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error saving {entity.__class__.__name__}: {e}")
            raise

    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID."""
        try:
            return self.session.query(self.entity_class).filter_by(id=entity_id).first()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting {self.entity_class.__name__} by ID {entity_id}: {e}")
            return None

    def get_all(self) -> List[T]:
        """Get all entities."""
        try:
            return self.session.query(self.entity_class).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting all {self.entity_class.__name__} entities: {e}")
            return []

    def delete(self, entity_id: str) -> bool:
        """Delete entity by ID."""
        try:
            entity = self.get_by_id(entity_id)
            if entity:
                self.session.delete(entity)
                self.session.commit()
                self.logger.info(f"Deleted {self.entity_class.__name__} with ID {entity_id}")
                return True
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error deleting {self.entity_class.__name__} with ID {entity_id}: {e}")
            return False

    def exists(self, entity_id: str) -> bool:
        """Check if entity exists."""
        try:
            return self.session.query(self.entity_class).filter_by(id=entity_id).first() is not None
        except SQLAlchemyError as e:
            self.logger.error(f"Error checking existence of {self.entity_class.__name__} with ID {entity_id}: {e}")
            return False

    @property
    @abstractmethod
def entity_class(self):
        """Get the entity class for this repository."""
        pass

class BaseBuildingRepository(BaseRepository):
    """Base building repository with building-specific operations."""

    def get_by_name(self, name: str) -> Optional[T]:
        """Get building by name."""
        try:
            return self.session.query(self.entity_class).filter_by(name=name).first()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting building by name {name}: {e}")
            return None

    def get_by_status(self, status: str) -> List[T]:
        """Get buildings by status."""
        try:
            return self.session.query(self.entity_class).filter_by(status=status).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting buildings by status {status}: {e}")
            return []

    def get_by_address(self, address: str) -> List[T]:
        """Get buildings by address."""
        try:
            return self.session.query(self.entity_class).filter(
                self.entity_class.address.contains(address)
            ).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting buildings by address {address}: {e}")
            return []

class BaseFloorRepository(BaseRepository):
    """Base floor repository with floor-specific operations."""

    def get_by_building_id(self, building_id: str) -> List[T]:
        """Get floors by building ID."""
        try:
            return self.session.query(self.entity_class).filter_by(building_id=building_id).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting floors by building ID {building_id}: {e}")
            return []

    def get_by_floor_number(self, building_id: str, floor_number: int) -> Optional[T]:
        """Get floor by building ID and floor number."""
        try:
            return self.session.query(self.entity_class).filter_by(
                building_id=building_id,
                floor_number=floor_number
            ).first()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting floor by building ID {building_id} and floor number {floor_number}: {e}")
            return None

class BaseRoomRepository(BaseRepository):
    """Base room repository with room-specific operations."""

    def get_by_floor_id(self, floor_id: str) -> List[T]:
        """Get rooms by floor ID."""
        try:
            return self.session.query(self.entity_class).filter_by(floor_id=floor_id).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting rooms by floor ID {floor_id}: {e}")
            return []

    def get_by_room_number(self, floor_id: str, room_number: str) -> Optional[T]:
        """Get room by floor ID and room number."""
        try:
            return self.session.query(self.entity_class).filter_by(
                floor_id=floor_id,
                room_number=room_number
            ).first()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting room by floor ID {floor_id} and room number {room_number}: {e}")
            return None

class BaseDeviceRepository(BaseRepository):
    """Base device repository with device-specific operations."""

    def get_by_room_id(self, room_id: str) -> List[T]:
        """Get devices by room ID."""
        try:
            return self.session.query(self.entity_class).filter_by(room_id=room_id).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting devices by room ID {room_id}: {e}")
            return []

    def get_by_device_type(self, device_type: str) -> List[T]:
        """Get devices by type."""
        try:
            return self.session.query(self.entity_class).filter_by(device_type=device_type).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting devices by type {device_type}: {e}")
            return []

class BaseUserRepository(BaseRepository):
    """Base user repository with user-specific operations."""

    def get_by_email(self, email: str) -> Optional[T]:
        """Get user by email."""
        try:
            return self.session.query(self.entity_class).filter_by(email=email).first()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting user by email {email}: {e}")
            return None

    def get_by_username(self, username: str) -> Optional[T]:
        """Get user by username."""
        try:
            return self.session.query(self.entity_class).filter_by(username=username).first()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting user by username {username}: {e}")
            return None

    def get_by_role(self, role: str) -> List[T]:
        """Get users by role."""
        try:
            return self.session.query(self.entity_class).filter_by(role=role).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting users by role {role}: {e}")
            return []

class BaseProjectRepository(BaseRepository):
    """Base project repository with project-specific operations."""

    def get_by_building_id(self, building_id: str) -> List[T]:
        """Get projects by building ID."""
        try:
            return self.session.query(self.entity_class).filter_by(building_id=building_id).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting projects by building ID {building_id}: {e}")
            return []

    def get_by_status(self, status: str) -> List[T]:
        """Get projects by status."""
        try:
            return self.session.query(self.entity_class).filter_by(status=status).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting projects by status {status}: {e}")
            return []
'''

    return content

def create_postgresql_repository_factory():
    """Create a PostgreSQL repository factory."""

    content = '''""
PostgreSQL Repository Factory

This module provides a factory for creating PostgreSQL repository implementations.
"""

from typing import Dict, Type
from sqlalchemy.orm import Session

from domain.unified.repositories import (
    BuildingRepository, FloorRepository, RoomRepository,
    DeviceRepository, UserRepository, ProjectRepository
)
from .base import (
    BaseBuildingRepository, BaseFloorRepository, BaseRoomRepository,
    BaseDeviceRepository, BaseUserRepository, BaseProjectRepository
)

class PostgreSQLRepositoryFactory:
    """Factory for creating PostgreSQL repository implementations."""

    def __init__(self, session: Session):
        """Initialize the repository factory."""
        self.session = session
        self._repositories: Dict[str, object] = {}

    def get_building_repository(self) -> BuildingRepository:
        """Get building repository."""
        if 'building' not in self._repositories:
            self._repositories['building'] = PostgreSQLBuildingRepository(self.session)
        return self._repositories['building']

    def get_floor_repository(self) -> FloorRepository:
        """Get floor repository."""
        if 'floor' not in self._repositories:
            self._repositories['floor'] = PostgreSQLFloorRepository(self.session)
        return self._repositories['floor']

    def get_room_repository(self) -> RoomRepository:
        """Get room repository."""
        if 'room' not in self._repositories:
            self._repositories['room'] = PostgreSQLRoomRepository(self.session)
        return self._repositories['room']

    def get_device_repository(self) -> DeviceRepository:
        """Get device repository."""
        if 'device' not in self._repositories:
            self._repositories['device'] = PostgreSQLDeviceRepository(self.session)
        return self._repositories['device']

    def get_user_repository(self) -> UserRepository:
        """Get user repository."""
        if 'user' not in self._repositories:
            self._repositories['user'] = PostgreSQLUserRepository(self.session)
        return self._repositories['user']

    def get_project_repository(self) -> ProjectRepository:
        """Get project repository."""
        if 'project' not in self._repositories:
            self._repositories['project'] = PostgreSQLProjectRepository(self.session)
        return self._repositories['project']

class PostgreSQLBuildingRepository(BaseBuildingRepository):
    """PostgreSQL implementation of building repository."""

    @property
def entity_class(self):
        """Get the building entity class."""
        from infrastructure.database.models import BuildingModel
        return BuildingModel

class PostgreSQLFloorRepository(BaseFloorRepository):
    """PostgreSQL implementation of floor repository."""

    @property
def entity_class(self):
        """Get the floor entity class."""
        from infrastructure.database.models import FloorModel
        return FloorModel

class PostgreSQLRoomRepository(BaseRoomRepository):
    """PostgreSQL implementation of room repository."""

    @property
def entity_class(self):
        """Get the room entity class."""
        from infrastructure.database.models import RoomModel
        return RoomModel

class PostgreSQLDeviceRepository(BaseDeviceRepository):
    """PostgreSQL implementation of device repository."""

    @property
def entity_class(self):
        """Get the device entity class."""
        from infrastructure.database.models import DeviceModel
        return DeviceModel

class PostgreSQLUserRepository(BaseUserRepository):
    """PostgreSQL implementation of user repository."""

    @property
def entity_class(self):
        """Get the user entity class."""
        from infrastructure.database.models import UserModel
        return UserModel

class PostgreSQLProjectRepository(BaseProjectRepository):
    """PostgreSQL implementation of project repository."""

    @property
def entity_class(self):
        """Get the project entity class."""
        from infrastructure.database.models import ProjectModel
        return ProjectModel
'''

    return content

def create_in_memory_repository_factory():
    """Create an in-memory repository factory."""

    content = '''""
In-Memory Repository Factory

This module provides a factory for creating in-memory repository implementations.
"""

from typing import Dict, List, Optional
from domain.unified.entities import Building, Floor, Room, Device, User, Project
from domain.unified.repositories import (
    BuildingRepository, FloorRepository, RoomRepository,
    DeviceRepository, UserRepository, ProjectRepository
)

class InMemoryRepositoryFactory:
    """Factory for creating in-memory repository implementations."""

    def __init__(self):
        """Initialize the repository factory."""
        self._repositories: Dict[str, object] = {}

    def get_building_repository(self) -> BuildingRepository:
        """Get building repository."""
        if 'building' not in self._repositories:
            self._repositories['building'] = InMemoryBuildingRepository()
        return self._repositories['building']

    def get_floor_repository(self) -> FloorRepository:
        """Get floor repository."""
        if 'floor' not in self._repositories:
            self._repositories['floor'] = InMemoryFloorRepository()
        return self._repositories['floor']

    def get_room_repository(self) -> RoomRepository:
        """Get room repository."""
        if 'room' not in self._repositories:
            self._repositories['room'] = InMemoryRoomRepository()
        return self._repositories['room']

    def get_device_repository(self) -> DeviceRepository:
        """Get device repository."""
        if 'device' not in self._repositories:
            self._repositories['device'] = InMemoryDeviceRepository()
        return self._repositories['device']

    def get_user_repository(self) -> UserRepository:
        """Get user repository."""
        if 'user' not in self._repositories:
            self._repositories['user'] = InMemoryUserRepository()
        return self._repositories['user']

    def get_project_repository(self) -> ProjectRepository:
        """Get project repository."""
        if 'project' not in self._repositories:
            self._repositories['project'] = InMemoryProjectRepository()
        return self._repositories['project']

class InMemoryBuildingRepository(BuildingRepository):
    """In-memory implementation of building repository."""

    def __init__(self):
        """Initialize the in-memory building repository."""
        self._buildings: Dict[str, Building] = {}

    def save(self, entity: Building) -> Building:
        """Save a building entity."""
        self._buildings[str(entity.id)] = entity
        return entity

    def get_by_id(self, entity_id: str) -> Optional[Building]:
        """Get building by ID."""
        return self._buildings.get(entity_id)

    def get_all(self) -> List[Building]:
        """Get all buildings."""
        return list(self._buildings.values()
    def delete(self, entity_id: str) -> bool:
        """Delete building by ID."""
        if entity_id in self._buildings:
            del self._buildings[entity_id]
            return True
        return False

    def exists(self, entity_id: str) -> bool:
        """Check if building exists."""
        return entity_id in self._buildings

    def get_by_name(self, name: str) -> Optional[Building]:
        """Get building by name."""
        for building in self._buildings.values():
            if building.name == name:
                return building
        return None

    def get_by_status(self, status: str) -> List[Building]:
        """Get buildings by status."""
        return [b for b in self._buildings.values() if b.status.value == status]

    def get_by_address(self, address: str) -> List[Building]:
        """Get buildings by address."""
        return [b for b in self._buildings.values() if address in str(b.address)]

class InMemoryFloorRepository(FloorRepository):
    """In-memory implementation of floor repository."""

    def __init__(self):
        """Initialize the in-memory floor repository."""
        self._floors: Dict[str, Floor] = {}

    def save(self, entity: Floor) -> Floor:
        """Save a floor entity."""
        self._floors[str(entity.id)] = entity
        return entity

    def get_by_id(self, entity_id: str) -> Optional[Floor]:
        """Get floor by ID."""
        return self._floors.get(entity_id)

    def get_all(self) -> List[Floor]:
        """Get all floors."""
        return list(self._floors.values()
    def delete(self, entity_id: str) -> bool:
        """Delete floor by ID."""
        if entity_id in self._floors:
            del self._floors[entity_id]
            return True
        return False

    def exists(self, entity_id: str) -> bool:
        """Check if floor exists."""
        return entity_id in self._floors

    def get_by_building_id(self, building_id: str) -> List[Floor]:
        """Get floors by building ID."""
        return [f for f in self._floors.values() if str(f.building_id) == building_id]

    def get_by_floor_number(self, building_id: str, floor_number: int) -> Optional[Floor]:
        """Get floor by building ID and floor number."""
        for floor in self._floors.values():
            if str(floor.building_id) == building_id and floor.floor_number == floor_number:
                return floor
        return None

# Similar implementations for Room, Device, User, and Project repositories...
class InMemoryRoomRepository(RoomRepository):
    """In-memory implementation of room repository."""

    def __init__(self):
        self._rooms: Dict[str, Room] = {}

    def save(self, entity: Room) -> Room:
        self._rooms[str(entity.id)] = entity
        return entity

    def get_by_id(self, entity_id: str) -> Optional[Room]:
        return self._rooms.get(entity_id)

    def get_all(self) -> List[Room]:
        return list(self._rooms.values()
    def delete(self, entity_id: str) -> bool:
        if entity_id in self._rooms:
            del self._rooms[entity_id]
            return True
        return False

    def exists(self, entity_id: str) -> bool:
        return entity_id in self._rooms

    def get_by_floor_id(self, floor_id: str) -> List[Room]:
        return [r for r in self._rooms.values() if str(r.floor_id) == floor_id]

    def get_by_room_number(self, floor_id: str, room_number: str) -> Optional[Room]:
        for room in self._rooms.values():
            if str(room.floor_id) == floor_id and room.room_number == room_number:
                return room
        return None

class InMemoryDeviceRepository(DeviceRepository):
    """In-memory implementation of device repository."""

    def __init__(self):
        self._devices: Dict[str, Device] = {}

    def save(self, entity: Device) -> Device:
        self._devices[str(entity.id)] = entity
        return entity

    def get_by_id(self, entity_id: str) -> Optional[Device]:
        return self._devices.get(entity_id)

    def get_all(self) -> List[Device]:
        return list(self._devices.values()
    def delete(self, entity_id: str) -> bool:
        if entity_id in self._devices:
            del self._devices[entity_id]
            return True
        return False

    def exists(self, entity_id: str) -> bool:
        return entity_id in self._devices

    def get_by_room_id(self, room_id: str) -> List[Device]:
        return [d for d in self._devices.values() if str(d.room_id) == room_id]

    def get_by_device_type(self, device_type: str) -> List[Device]:
        return [d for d in self._devices.values() if d.device_type == device_type]

class InMemoryUserRepository(UserRepository):
    """In-memory implementation of user repository."""

    def __init__(self):
        self._users: Dict[str, User] = {}

    def save(self, entity: User) -> User:
        self._users[str(entity.id)] = entity
        return entity

    def get_by_id(self, entity_id: str) -> Optional[User]:
        return self._users.get(entity_id)

    def get_all(self) -> List[User]:
        return list(self._users.values()
    def delete(self, entity_id: str) -> bool:
        if entity_id in self._users:
            del self._users[entity_id]
            return True
        return False

    def exists(self, entity_id: str) -> bool:
        return entity_id in self._users

    def get_by_email(self, email: str) -> Optional[User]:
        for user in self._users.values():
            if str(user.email) == email:
                return user
        return None

    def get_by_username(self, username: str) -> Optional[User]:
        for user in self._users.values():
            if user.username == username:
                return user
        return None

    def get_by_role(self, role: str) -> List[User]:
        return [u for u in self._users.values() if u.role.value == role]

class InMemoryProjectRepository(ProjectRepository):
    """In-memory implementation of project repository."""

    def __init__(self):
        self._projects: Dict[str, Project] = {}

    def save(self, entity: Project) -> Project:
        self._projects[str(entity.id)] = entity
        return entity

    def get_by_id(self, entity_id: str) -> Optional[Project]:
        return self._projects.get(entity_id)

    def get_all(self) -> List[Project]:
        return list(self._projects.values()
    def delete(self, entity_id: str) -> bool:
        if entity_id in self._projects:
            del self._projects[entity_id]
            return True
        return False

    def exists(self, entity_id: str) -> bool:
        return entity_id in self._projects

    def get_by_building_id(self, building_id: str) -> List[Project]:
        return [p for p in self._projects.values() if str(p.building_id) == building_id]

    def get_by_status(self, status: str) -> List[Project]:
        return [p for p in self._projects.values() if p.status.value == status]
'''

    return content

def main():
    """Main consolidation function."""
    print("🔄 Starting Repository Consolidation")

    # Create unified infrastructure structure
    unified_infra, repos_dir = create_unified_repository_implementations()
    print(f"✅ Created unified infrastructure structure at {unified_infra}")

    # Create base repository implementation
    base_repo_path = repos_dir / "base.py"
    with open(base_repo_path, 'w') as f:
        f.write(create_base_repository()
    print(f"✅ Created base repository implementation at {base_repo_path}")

    # Create PostgreSQL repository factory
    postgresql_factory_path = repos_dir / "postgresql_factory.py"
    with open(postgresql_factory_path, 'w') as f:
        f.write(create_postgresql_repository_factory()
    print(f"✅ Created PostgreSQL repository factory at {postgresql_factory_path}")

    # Create in-memory repository factory
    in_memory_factory_path = repos_dir / "in_memory_factory.py"
    with open(in_memory_factory_path, 'w') as f:
        f.write(create_in_memory_repository_factory()
    print(f"✅ Created in-memory repository factory at {in_memory_factory_path}")

    print("🎯 Repository consolidation completed successfully!")
    print("📋 Repository consolidation benefits:")
    print("   ✅ Eliminated repository chaos")
    print("   ✅ Unified repository interfaces")
    print("   ✅ Proper abstraction layers")
    print("   ✅ Consistent error handling")
    print("   ✅ Factory pattern for repository creation")

if __name__ == "__main__":
    main()
