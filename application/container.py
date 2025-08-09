"""
Dependency Injection Container

This module provides dependency injection configuration for the application layer,
wiring infrastructure services to application services.
"""

from typing import Dict, Any, Optional
from contextlib import contextmanager
import logging

from infrastructure.database.config import DatabaseConfig
from infrastructure.database.connection import DatabaseConnection
from infrastructure.database.session import DatabaseSession
from infrastructure.repositories.building_repository import SQLAlchemyBuildingRepository
from infrastructure.repositories.floor_repository import SQLAlchemyFloorRepository
from infrastructure.repositories.room_repository import SQLAlchemyRoomRepository
from infrastructure.repositories.device_repository import SQLAlchemyDeviceRepository
from infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from infrastructure.repositories.project_repository import SQLAlchemyProjectRepository
from infrastructure.services.cache_service import RedisCacheService
from infrastructure.services.event_store import EventStoreService
from infrastructure.services.message_queue import MessageQueueService
from infrastructure.monitoring.health_check import HealthCheckService
from infrastructure.monitoring.metrics import MetricsCollector
from infrastructure.monitoring.logging import StructuredLogger
from infrastructure.caching.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class ApplicationContainer:
    """Dependency injection container for the application layer."""

    def __init__(self):
        """Initialize the application container."""
        self._services: Dict[str, Any] = {}
        self._database_connection: Optional[DatabaseConnection] = None
        self._cache_service: Optional[RedisCacheService] = None
        self._event_store: Optional[EventStoreService] = None
        self._message_queue: Optional[MessageQueueService] = None
        self._health_check: Optional[HealthCheckService] = None
        self._metrics: Optional[MetricsCollector] = None
        self._logger: Optional[StructuredLogger] = None
        self._cache_manager: Optional[CacheManager] = None

        self._initialized = False

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize all services with configuration."""
        if self._initialized:
            logger.warning("Application container already initialized")
            return

        try:
            # Initialize database connection
            db_config = DatabaseConfig(
                host=config.get('database', {}).get('host', 'localhost'),
                port=config.get('database', {}).get('port', 5432),
                database=config.get('database', {}).get('database', 'arxos'),
                username=config.get('database', {}).get('username', 'arxos_user'),
                password=config.get('database', {}).get('password', ''),
                pool_size=config.get('database', {}).get('pool_size', 10),
                max_overflow=config.get('database', {}).get('max_overflow', 20)
            )
            self._database_connection = DatabaseConnection(db_config)
            self._services['database_connection'] = self._database_connection

            # Initialize cache service
            cache_config = config.get('cache', {})
            self._cache_service = RedisCacheService(
                host=cache_config.get('host', 'localhost'),
                port=cache_config.get('port', 6379),
                db=cache_config.get('db', 0),
                password=cache_config.get('password'),
                max_connections=cache_config.get('max_connections', 10)
            )
            self._services['cache_service'] = self._cache_service

            # Initialize cache manager
            self._cache_manager = CacheManager()
            self._cache_manager.add_strategy('redis', self._cache_service)
            self._services['cache_manager'] = self._cache_manager

            # Initialize event store
            self._event_store = EventStoreService(self._database_connection.session_factory())
            self._services['event_store'] = self._event_store

            # Initialize message queue
            mq_config = config.get('message_queue', {})
            self._message_queue = MessageQueueService(
                host=mq_config.get('host', 'localhost'),
                port=mq_config.get('port', 5672),
                username=mq_config.get('username'),
                password=mq_config.get('password')
            )
            self._services['message_queue'] = self._message_queue

            # Initialize monitoring services
            self._health_check = HealthCheckService()
            self._metrics = MetricsCollector()
            self._logger = StructuredLogger(name="arxos")

            self._services['health_check'] = self._health_check
            self._services['metrics'] = self._metrics
            self._services['logger'] = self._logger

            # Register health checks
            self._register_health_checks()

            self._initialized = True
            logger.info("Application container initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize application container: {e}")
            raise

    def _register_health_checks(self) -> None:
        """Register health checks for all services."""
        if self._health_check and self._database_connection:
            self._health_check.register_check(
                "database",
                self._database_connection.test_connection
            )

        if self._health_check and self._cache_service:
            self._health_check.register_check(
                "cache",
                self._cache_service.health_check
            )

        if self._health_check and self._message_queue:
            self._health_check.register_check(
                "message_queue",
                self._message_queue.health_check
            )

    def get_database_session(self) -> DatabaseSession:
        """Get database session."""
        if not self._database_connection:
            raise RuntimeError("Database connection not initialized")
        return DatabaseSession(self._database_connection.session_factory)

    def get_building_repository(self) -> SQLAlchemyBuildingRepository:
        """Get building repository."""
        session = self.get_database_session()
        return SQLAlchemyBuildingRepository(session.session_factory())
    def get_floor_repository(self) -> SQLAlchemyFloorRepository:
        """Get floor repository."""
        session = self.get_database_session()
        return SQLAlchemyFloorRepository(session.session_factory())
    def get_room_repository(self) -> SQLAlchemyRoomRepository:
        """Get room repository."""
        session = self.get_database_session()
        return SQLAlchemyRoomRepository(session.session_factory())
    def get_device_repository(self) -> SQLAlchemyDeviceRepository:
        """Get device repository."""
        session = self.get_database_session()
        return SQLAlchemyDeviceRepository(session.session_factory())
    def get_user_repository(self) -> SQLAlchemyUserRepository:
        """Get user repository."""
        session = self.get_database_session()
        return SQLAlchemyUserRepository(session.session_factory())
    def get_project_repository(self) -> SQLAlchemyProjectRepository:
        """Get project repository."""
        session = self.get_database_session()
        return SQLAlchemyProjectRepository(session.session_factory())
    def get_cache_service(self) -> RedisCacheService:
        """Get cache service."""
        if not self._cache_service:
            raise RuntimeError("Cache service not initialized")
        return self._cache_service

    def get_cache_manager(self) -> CacheManager:
        """Get cache manager."""
        if not self._cache_manager:
            raise RuntimeError("Cache manager not initialized")
        return self._cache_manager

    def get_event_store(self) -> EventStoreService:
        """Get event store service."""
        if not self._event_store:
            raise RuntimeError("Event store not initialized")
        return self._event_store

    def get_message_queue(self) -> MessageQueueService:
        """Get message queue service."""
        if not self._message_queue:
            raise RuntimeError("Message queue not initialized")
        return self._message_queue

    def get_health_check(self) -> HealthCheckService:
        """Get health check service."""
        if not self._health_check:
            raise RuntimeError("Health check service not initialized")
        return self._health_check

    def get_metrics(self) -> MetricsCollector:
        """Get metrics collector."""
        if not self._metrics:
            raise RuntimeError("Metrics collector not initialized")
        return self._metrics

    def get_logger(self) -> StructuredLogger:
        """Get structured logger."""
        if not self._logger:
            raise RuntimeError("Logger not initialized")
        return self._logger

    def get_service(self, service_name: str) -> Any:
        """Get a service by name."""
        if service_name not in self._services:
            raise ValueError(f"Service '{service_name}' not found")
        return self._services[service_name]

    @contextmanager
    def get_transaction(self):
        """Get a database transaction context."""
        if not self._database_connection:
            raise RuntimeError("Database connection not initialized")

        with self._database_connection.get_session() as session:
            yield session

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all services."""
        if not self._health_check:
            return {"status": "error", "message": "Health check service not initialized"}

        return self._health_check.run_all_checks()

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        if not self._metrics:
            return {"status": "error", "message": "Metrics collector not initialized"}

        return self._metrics.get_all_metrics()

    def shutdown(self) -> None:
        """Shutdown all services."""
        try:
            if self._database_connection:
                self._database_connection.dispose()

            if self._message_queue:
                self._message_queue.disconnect()

            self._initialized = False
            logger.info("Application container shutdown successfully")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Global container instance
container = ApplicationContainer()
