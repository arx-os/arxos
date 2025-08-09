"""
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
        return list(self._buildings.values())

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
        return list(self._floors.values())

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
        return list(self._rooms.values())

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
        return list(self._devices.values())

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
        return list(self._users.values())

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
        return list(self._projects.values())

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
