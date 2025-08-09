"""
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
