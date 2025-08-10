"""
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
