"""
Infrastructure Layer - External Dependencies and Data Access

This module contains the infrastructure layer components that handle
external dependencies, data persistence, and integration with external
services. The infrastructure layer implements the interfaces defined
in the domain layer.
"""

from .database import *
from .repositories import *
from .unit_of_work import *
from .repository_factory import *
from .services import *
from .caching import *
from .monitoring import *

# PDF Analysis specific imports
from .repositories.postgresql_pdf_analysis_repository import PostgreSQLPDFAnalysisRepository
from .services.gus_service import GUSService, PDFAnalysisResult
from .services.file_storage_service import FileStorageService

__all__ = [
    # Database
    'DatabaseConfig', 'DatabaseConnection', 'DatabaseSession',
    'Base', 'BuildingModel', 'FloorModel', 'RoomModel', 'DeviceModel', 'UserModel', 'ProjectModel',
    
    # Repositories
    'BaseRepository', 'SQLAlchemyBuildingRepository', 'SQLAlchemyFloorRepository',
    'SQLAlchemyRoomRepository', 'SQLAlchemyDeviceRepository',
    'SQLAlchemyUserRepository', 'SQLAlchemyProjectRepository',
    'PostgreSQLPDFAnalysisRepository',
    
    # Unit of Work
    'SQLAlchemyUnitOfWork', 'UnitOfWorkFactory', 'unit_of_work',
    'PostgreSQLPDFAnalysisRepository',
    
    # Repository Factory
    'SQLAlchemyRepositoryFactory', 'RepositoryFactoryManager',
    'get_repository_factory', 'initialize_repository_factory', 'close_repository_factory',
    
    # Services
    'RedisCacheService', 'EventStoreService', 'MessageQueueService',
    'GUSService', 'PDFAnalysisResult', 'FileStorageService',
    
    # Caching
    'CacheManager', 'CacheStrategy',
    
    # Monitoring
    'HealthCheckService', 'MetricsCollector', 'StructuredLogger',
] 