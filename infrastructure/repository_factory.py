"""
Repository Factory Implementation

This module contains the SQLAlchemy implementation of the RepositoryFactory
interface defined in the domain layer. This provides factory methods for
creating repository instances and UnitOfWork.
"""

from typing import Optional

from sqlalchemy.orm import Session, sessionmaker

from domain.repositories import (
    RepositoryFactory, UnitOfWork, BuildingRepository, FloorRepository, RoomRepository,
    DeviceRepository, UserRepository, ProjectRepository, PDFAnalysisRepository
)

from .repositories import (
    SQLAlchemyBuildingRepository, SQLAlchemyFloorRepository, SQLAlchemyRoomRepository,
    SQLAlchemyDeviceRepository, SQLAlchemyUserRepository, SQLAlchemyProjectRepository
)
from .repositories.postgresql_pdf_analysis_repository import PostgreSQLPDFAnalysisRepository
from .unit_of_work import SQLAlchemyUnitOfWork


class SQLAlchemyRepositoryFactory(RepositoryFactory):
    """SQLAlchemy implementation of RepositoryFactory."""
    
    def __init__(self, session_factory: sessionmaker):
        """Initialize repository factory with session factory."""
        self.session_factory = session_factory
        self._session: Optional[Session] = None
    
    def _get_session(self) -> Session:
        """Get or create a database session."""
        if self._session is None:
            self._session = self.session_factory()
        return self._session
    
    def create_building_repository(self) -> BuildingRepository:
        """Create a building repository instance."""
        return SQLAlchemyBuildingRepository(self._get_session())
    
    def create_floor_repository(self) -> FloorRepository:
        """Create a floor repository instance."""
        return SQLAlchemyFloorRepository(self._get_session())
    
    def create_room_repository(self) -> RoomRepository:
        """Create a room repository instance."""
        return SQLAlchemyRoomRepository(self._get_session())
    
    def create_device_repository(self) -> DeviceRepository:
        """Create a device repository instance."""
        return SQLAlchemyDeviceRepository(self._get_session())
    
    def create_user_repository(self) -> UserRepository:
        """Create a user repository instance."""
        return SQLAlchemyUserRepository(self._get_session())
    
    def create_project_repository(self) -> ProjectRepository:
        """Create a project repository instance."""
        return SQLAlchemyProjectRepository(self._get_session())
    
    def create_pdf_analysis_repository(self) -> PDFAnalysisRepository:
        """Create a PDF analysis repository instance."""
        from .database.connection_manager import DatabaseConnectionManager
        connection_manager = DatabaseConnectionManager()
        return PostgreSQLPDFAnalysisRepository(connection_manager)
    
    def create_unit_of_work(self) -> UnitOfWork:
        """Create a unit of work instance."""
        return SQLAlchemyUnitOfWork(self.session_factory)
    
    def close_session(self):
        """Close the current session."""
        if self._session:
            self._session.close()
            self._session = None


class RepositoryFactoryManager:
    """Manager for repository factory instances."""
    
    def __init__(self):
        """Initialize repository factory manager."""
        self._factory: Optional[SQLAlchemyRepositoryFactory] = None
    
    def initialize(self, session_factory: sessionmaker):
        """Initialize the repository factory with a session factory."""
        self._factory = SQLAlchemyRepositoryFactory(session_factory)
    
    def get_factory(self) -> SQLAlchemyRepositoryFactory:
        """Get the repository factory instance."""
        if self._factory is None:
            raise RuntimeError("Repository factory not initialized. Call initialize() first.")
        return self._factory
    
    def close(self):
        """Close all sessions and cleanup."""
        if self._factory:
            self._factory.close_session()


# Global repository factory manager
repository_factory_manager = RepositoryFactoryManager()


def get_repository_factory() -> SQLAlchemyRepositoryFactory:
    """Get the global repository factory instance."""
    return repository_factory_manager.get_factory()


def initialize_repository_factory(session_factory: sessionmaker):
    """Initialize the global repository factory."""
    repository_factory_manager.initialize(session_factory)


def close_repository_factory():
    """Close the global repository factory."""
    repository_factory_manager.close() 