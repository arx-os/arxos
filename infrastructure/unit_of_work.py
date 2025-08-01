"""
Unit of Work Implementation

This module contains the SQLAlchemy implementation of the UnitOfWork
interface defined in the domain layer. This provides transaction
management and access to all repositories.
"""

import logging
from typing import Optional
from contextlib import contextmanager

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from domain.repositories import (
    UnitOfWork, BuildingRepository, FloorRepository, RoomRepository,
    DeviceRepository, UserRepository, ProjectRepository
)
from domain.exceptions import RepositoryError

from .repositories import (
    SQLAlchemyBuildingRepository, SQLAlchemyFloorRepository, SQLAlchemyRoomRepository,
    SQLAlchemyDeviceRepository, SQLAlchemyUserRepository, SQLAlchemyProjectRepository
)

logger = logging.getLogger(__name__)


class SQLAlchemyUnitOfWork(UnitOfWork):
    """SQLAlchemy implementation of UnitOfWork."""
    
    def __init__(self, session_factory):
        """Initialize unit of work with session factory."""
        self.session_factory = session_factory
        self.session: Optional[Session] = None
        self._repositories = {}
    
    def __enter__(self):
        """Enter the unit of work context."""
        self.session = self.session_factory()
        logger.debug("Unit of Work context entered")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the unit of work context."""
        try:
            if exc_type is not None:
                # Rollback on exception
                if self.session:
                    self.session.rollback()
                    logger.error(f"Unit of Work rolled back due to exception: {exc_val}")
            else:
                # Commit on success
                if self.session:
                    self.session.commit()
                    logger.debug("Unit of Work committed successfully")
        finally:
            # Always close the session
            if self.session:
                self.session.close()
                self.session = None
    
    def commit(self) -> None:
        """Commit the current transaction."""
        if not self.session:
            raise RepositoryError("No active session")
        
        try:
            self.session.commit()
            logger.debug("Unit of Work committed")
        except SQLAlchemyError as e:
            logger.error(f"Failed to commit transaction: {e}")
            self.session.rollback()
            raise RepositoryError(f"Failed to commit transaction: {str(e)}")
    
    def rollback(self) -> None:
        """Rollback the current transaction."""
        if not self.session:
            raise RepositoryError("No active session")
        
        try:
            self.session.rollback()
            logger.debug("Unit of Work rolled back")
        except SQLAlchemyError as e:
            logger.error(f"Failed to rollback transaction: {e}")
            raise RepositoryError(f"Failed to rollback transaction: {str(e)}")
    
    @property
    def buildings(self) -> BuildingRepository:
        """Get the building repository."""
        if 'buildings' not in self._repositories:
            self._repositories['buildings'] = SQLAlchemyBuildingRepository(self.session)
        return self._repositories['buildings']
    
    @property
    def floors(self) -> FloorRepository:
        """Get the floor repository."""
        if 'floors' not in self._repositories:
            self._repositories['floors'] = SQLAlchemyFloorRepository(self.session)
        return self._repositories['floors']
    
    @property
    def rooms(self) -> RoomRepository:
        """Get the room repository."""
        if 'rooms' not in self._repositories:
            self._repositories['rooms'] = SQLAlchemyRoomRepository(self.session)
        return self._repositories['rooms']
    
    @property
    def devices(self) -> DeviceRepository:
        """Get the device repository."""
        if 'devices' not in self._repositories:
            self._repositories['devices'] = SQLAlchemyDeviceRepository(self.session)
        return self._repositories['devices']
    
    @property
    def users(self) -> UserRepository:
        """Get the user repository."""
        if 'users' not in self._repositories:
            self._repositories['users'] = SQLAlchemyUserRepository(self.session)
        return self._repositories['users']
    
    @property
    def projects(self) -> ProjectRepository:
        """Get the project repository."""
        if 'projects' not in self._repositories:
            self._repositories['projects'] = SQLAlchemyProjectRepository(self.session)
        return self._repositories['projects']


class UnitOfWorkFactory:
    """Factory for creating UnitOfWork instances."""
    
    def __init__(self, session_factory):
        """Initialize factory with session factory."""
        self.session_factory = session_factory
    
    def create(self) -> UnitOfWork:
        """Create a new UnitOfWork instance."""
        return SQLAlchemyUnitOfWork(self.session_factory)


# Convenience function for using UnitOfWork as a context manager
@contextmanager
def unit_of_work(session_factory):
    """Context manager for UnitOfWork."""
    uow = SQLAlchemyUnitOfWork(session_factory)
    try:
        yield uow
    except Exception:
        uow.rollback()
        raise
    else:
        uow.commit() 