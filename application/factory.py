"""
Application Service Factory

This module provides factory methods for creating application services
with proper dependency injection from the infrastructure layer.
"""

from typing import Optional

from domain.repositories import UnitOfWork
from application.services.building_service import BuildingApplicationService
from application.services.device_service import DeviceApplicationService
from application.services.room_service import RoomApplicationService
from application.services.floor_service import FloorApplicationService
from application.services.user_service import UserApplicationService
from application.services.project_service import ProjectApplicationService
from application.container import container


class ApplicationServiceFactory:
    """Factory for creating application services with dependency injection."""

    @staticmethod
    def create_building_service(unit_of_work: UnitOfWork) -> BuildingApplicationService:
        """Create building application service with all dependencies."""
        # Get infrastructure services from container
        cache_service = container.get_cache_service()
        event_store = container.get_event_store()
        message_queue = container.get_message_queue()
        metrics = container.get_metrics()
        logger = container.get_logger()

        return BuildingApplicationService(
            unit_of_work=unit_of_work,
            cache_service=cache_service,
            event_store=event_store,
            message_queue=message_queue,
            metrics=metrics,
            logger=logger,
        )

    @staticmethod
    def create_device_service(unit_of_work: UnitOfWork) -> DeviceApplicationService:
        """Create device application service with all dependencies."""
        # Get infrastructure services from container
        cache_service = container.get_cache_service()
        event_store = container.get_event_store()
        message_queue = container.get_message_queue()
        metrics = container.get_metrics()
        logger = container.get_logger()

        return DeviceApplicationService(
            unit_of_work=unit_of_work,
            cache_service=cache_service,
            event_store=event_store,
            message_queue=message_queue,
            metrics=metrics,
            logger=logger,
        )

    @staticmethod
    def create_room_service(unit_of_work: UnitOfWork) -> RoomApplicationService:
        """Create room application service with all dependencies."""
        # Get infrastructure services from container
        cache_service = container.get_cache_service()
        event_store = container.get_event_store()
        message_queue = container.get_message_queue()
        metrics = container.get_metrics()
        logger = container.get_logger()

        return RoomApplicationService(
            unit_of_work=unit_of_work,
            cache_service=cache_service,
            event_store=event_store,
            message_queue=message_queue,
            metrics=metrics,
            logger=logger,
        )

    @staticmethod
    def create_floor_service(unit_of_work: UnitOfWork) -> FloorApplicationService:
        """Create floor application service with all dependencies."""
        # Get infrastructure services from container
        cache_service = container.get_cache_service()
        event_store = container.get_event_store()
        message_queue = container.get_message_queue()
        metrics = container.get_metrics()
        logger = container.get_logger()

        return FloorApplicationService(
            unit_of_work=unit_of_work,
            cache_service=cache_service,
            event_store=event_store,
            message_queue=message_queue,
            metrics=metrics,
            logger=logger,
        )

    @staticmethod
    def create_user_service(unit_of_work: UnitOfWork) -> UserApplicationService:
        """Create user application service with all dependencies."""
        # Get infrastructure services from container
        cache_service = container.get_cache_service()
        event_store = container.get_event_store()
        message_queue = container.get_message_queue()
        metrics = container.get_metrics()
        logger = container.get_logger()

        return UserApplicationService(
            unit_of_work=unit_of_work,
            cache_service=cache_service,
            event_store=event_store,
            message_queue=message_queue,
            metrics=metrics,
            logger=logger,
        )

    @staticmethod
    def create_project_service(unit_of_work: UnitOfWork) -> ProjectApplicationService:
        """Create project application service with all dependencies."""
        # Get infrastructure services from container
        cache_service = container.get_cache_service()
        event_store = container.get_event_store()
        message_queue = container.get_message_queue()
        metrics = container.get_metrics()
        logger = container.get_logger()

        return ProjectApplicationService(
            unit_of_work=unit_of_work,
            cache_service=cache_service,
            event_store=event_store,
            message_queue=message_queue,
            metrics=metrics,
            logger=logger,
        )


# Convenience functions for getting services
def get_building_service(unit_of_work: UnitOfWork) -> BuildingApplicationService:
    """Get building application service."""
    return ApplicationServiceFactory.create_building_service(unit_of_work)


def get_device_service(unit_of_work: UnitOfWork) -> DeviceApplicationService:
    """Get device application service."""
    return ApplicationServiceFactory.create_device_service(unit_of_work)


def get_room_service(unit_of_work: UnitOfWork) -> RoomApplicationService:
    """Get room application service."""
    return ApplicationServiceFactory.create_room_service(unit_of_work)


def get_floor_service(unit_of_work: UnitOfWork) -> FloorApplicationService:
    """Get floor application service."""
    return ApplicationServiceFactory.create_floor_service(unit_of_work)


def get_user_service(unit_of_work: UnitOfWork) -> UserApplicationService:
    """Get user application service."""
    return ApplicationServiceFactory.create_user_service(unit_of_work)


def get_project_service(unit_of_work: UnitOfWork) -> ProjectApplicationService:
    """Get project application service."""
    return ApplicationServiceFactory.create_project_service(unit_of_work)


def get_health_check():
    """Get health check service."""
    return container.get_health_check()


def get_metrics():
    """Get metrics service."""
    return container.get_metrics()


def get_logger():
    """Get logger service."""
    return container.get_logger()
