"""
Unit of Work Implementation

This module contains the SQLAlchemy implementation of the UnitOfWork
interface defined in the domain layer.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session, sessionmaker

from domain.repositories import (
    UnitOfWork, BuildingRepository, FloorRepository, RoomRepository,
    DeviceRepository, UserRepository, ProjectRepository, ContributionRepository,
    RevenueRepository, DividendRepository, VerificationRepository
)

from .repositories import (
    SQLAlchemyBuildingRepository, SQLAlchemyFloorRepository, SQLAlchemyRoomRepository,
    SQLAlchemyDeviceRepository, SQLAlchemyUserRepository, SQLAlchemyProjectRepository,
    SQLAlchemyContributionRepository, SQLAlchemyRevenueRepository, SQLAlchemyDividendRepository,
    SQLAlchemyVerificationRepository
)

logger = logging.getLogger(__name__)


class SQLAlchemyUnitOfWork(UnitOfWork):
    """SQLAlchemy implementation of UnitOfWork."""
    
    def __init__(self, session_factory: sessionmaker):
        """Initialize with session factory."""
        self.session_factory = session_factory
        self._session: Optional[Session] = None
        self._building_repository: Optional[BuildingRepository] = None
        self._floor_repository: Optional[FloorRepository] = None
        self._room_repository: Optional[RoomRepository] = None
        self._device_repository: Optional[DeviceRepository] = None
        self._user_repository: Optional[UserRepository] = None
        self._project_repository: Optional[ProjectRepository] = None
        self._contribution_repository: Optional[ContributionRepository] = None
        self._revenue_repository: Optional[RevenueRepository] = None
        self._dividend_repository: Optional[DividendRepository] = None
        self._verification_repository: Optional[VerificationRepository] = None
    
    def _get_session(self) -> Session:
        """Get or create a database session."""
        if self._session is None:
            self._session = self.session_factory()
        return self._session
    
    @property
    def buildings(self) -> BuildingRepository:
        """Get the building repository."""
        if self._building_repository is None:
            self._building_repository = SQLAlchemyBuildingRepository(self._get_session())
        return self._building_repository
    
    @property
    def floors(self) -> FloorRepository:
        """Get the floor repository."""
        if self._floor_repository is None:
            self._floor_repository = SQLAlchemyFloorRepository(self._get_session())
        return self._floor_repository
    
    @property
    def rooms(self) -> RoomRepository:
        """Get the room repository."""
        if self._room_repository is None:
            self._room_repository = SQLAlchemyRoomRepository(self._get_session())
        return self._room_repository
    
    @property
    def devices(self) -> DeviceRepository:
        """Get the device repository."""
        if self._device_repository is None:
            self._device_repository = SQLAlchemyDeviceRepository(self._get_session())
        return self._device_repository
    
    @property
    def users(self) -> UserRepository:
        """Get the user repository."""
        if self._user_repository is None:
            self._user_repository = SQLAlchemyUserRepository(self._get_session())
        return self._user_repository
    
    @property
    def projects(self) -> ProjectRepository:
        """Get the project repository."""
        if self._project_repository is None:
            self._project_repository = SQLAlchemyProjectRepository(self._get_session())
        return self._project_repository
    
    @property
    def contributions(self) -> ContributionRepository:
        """Get the contribution repository."""
        if self._contribution_repository is None:
            self._contribution_repository = SQLAlchemyContributionRepository(self._get_session())
        return self._contribution_repository
    
    @property
    def revenue(self) -> RevenueRepository:
        """Get the revenue repository."""
        if self._revenue_repository is None:
            self._revenue_repository = SQLAlchemyRevenueRepository(self._get_session())
        return self._revenue_repository
    
    @property
    def dividends(self) -> DividendRepository:
        """Get the dividend repository."""
        if self._dividend_repository is None:
            self._dividend_repository = SQLAlchemyDividendRepository(self._get_session())
        return self._dividend_repository
    
    @property
    def verifications(self) -> VerificationRepository:
        """Get the verification repository."""
        if self._verification_repository is None:
            self._verification_repository = SQLAlchemyVerificationRepository(self._get_session())
        return self._verification_repository
    
    def commit(self) -> None:
        """Commit the unit of work."""
        try:
            if self._session:
                self._session.commit()
                logger.info("Unit of work committed successfully")
        except Exception as e:
            logger.error(f"Error committing unit of work: {str(e)}")
            self.rollback()
            raise
    
    def rollback(self) -> None:
        """Rollback the unit of work."""
        try:
            if self._session:
                self._session.rollback()
                logger.info("Unit of work rolled back successfully")
        except Exception as e:
            logger.error(f"Error rolling back unit of work: {str(e)}")
            raise
    
    def __enter__(self):
        """Enter the unit of work context."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the unit of work context."""
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        
        if self._session:
            self._session.close()
            self._session = None 