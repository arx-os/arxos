"""
Dependency Injection Container - Infrastructure Layer
"""

from typing import Dict, Any, Optional
import logging

from svgx_engine.domain.repositories.building_repository import BuildingRepository
from svgx_engine.domain.services.building_service import BuildingService
from svgx_engine.application.use_cases.building_use_cases import (
    CreateBuildingUseCase,
    UpdateBuildingUseCase,
    GetBuildingUseCase,
    DeleteBuildingUseCase,
    ListBuildingsUseCase
)
from svgx_engine.application.dto.building_dto import (
    CreateBuildingRequest,
    UpdateBuildingRequest,
    BuildingResponse
)
from svgx_engine.infrastructure.repositories.in_memory_building_repository import InMemoryBuildingRepository

logger = logging.getLogger(__name__)

class Container:
    """
    Dependency injection container for the application.

    This container manages the creation and configuration of all dependencies
    in the application, following the Dependency Inversion Principle.
    """

    def __init__(self):
        pass
    """
    Perform __init__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self._services: Dict[str, Any] = {}
        self._configure_services()

    def _configure_services(self):
        """Configure all services in the container."""
        # Configure repositories
        self._services['building_repository'] = InMemoryBuildingRepository()

        # Configure domain services
        self._services['building_service'] = BuildingService(
            building_repository=self._services['building_repository']
        )

        # Configure use cases
        self._services['create_building_use_case'] = CreateBuildingUseCase(
            building_service=self._services['building_service']
        )

        self._services['update_building_use_case'] = UpdateBuildingUseCase(
            building_service=self._services['building_service']
        )

        self._services['get_building_use_case'] = GetBuildingUseCase(
            building_service=self._services['building_service']
        )

        self._services['delete_building_use_case'] = DeleteBuildingUseCase(
            building_service=self._services['building_service']
        )

        self._services['list_buildings_use_case'] = ListBuildingsUseCase(
            building_service=self._services['building_service']
        )

        logger.info("Dependency injection container configured successfully")

    def get(self, service_name: str) -> Any:
        """
        Get a service from the container.

        Args:
            service_name: Name of the service to retrieve

        Returns:
            The requested service instance

        Raises:
            KeyError: If the service is not found
        """
        if service_name not in self._services:
            raise KeyError(f"Service '{service_name}' not found in container")

        return self._services[service_name]

    def register(self, service_name: str, service_instance: Any) -> None:
        """
        Register a service in the container.

        Args:
            service_name: Name of the service
            service_instance: Service instance to register
        """
        self._services[service_name] = service_instance
        logger.info(f"Registered service: {service_name}")

    def has(self, service_name: str) -> bool:
        """
        Check if a service exists in the container.

        Args:
            service_name: Name of the service to check

        Returns:
            True if the service exists, False otherwise
        """
        return service_name in self._services

    def get_building_repository(self) -> BuildingRepository:
        """Get the building repository."""
        return self.get('building_repository')

    def get_building_service(self) -> BuildingService:
        """Get the building service."""
        return self.get('building_service')

    def get_create_building_use_case(self) -> CreateBuildingUseCase:
        """Get the create building use case."""
        return self.get('create_building_use_case')

    def get_update_building_use_case(self) -> UpdateBuildingUseCase:
        """Get the update building use case."""
        return self.get('update_building_use_case')

    def get_get_building_use_case(self) -> GetBuildingUseCase:
        """Get the get building use case."""
        return self.get('get_building_use_case')

    def get_delete_building_use_case(self) -> DeleteBuildingUseCase:
        """Get the delete building use case."""
        return self.get('delete_building_use_case')

    def get_list_buildings_use_case(self) -> ListBuildingsUseCase:
        """Get the list buildings use case."""
        return self.get('list_buildings_use_case')

    def get_all_services(self) -> Dict[str, Any]:
        """
        Get all registered services.

        Returns:
            Dictionary of all registered services
        """
        return self._services.copy()

    def clear(self) -> None:
        """Clear all services from the container."""
        self._services.clear()
        logger.info("Container cleared")

    def reset(self) -> None:
        """Reset the container to its initial state."""
        self.clear()
        self._configure_services()
        logger.info("Container reset to initial state")

# Global container instance
container = Container()
