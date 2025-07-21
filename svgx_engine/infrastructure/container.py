"""
Dependency Injection Container

Container for managing dependencies and wiring up Clean Architecture components.
This container follows the Dependency Inversion Principle and provides
a clean way to configure and manage all dependencies.
"""

from typing import Dict, Any, Type
from dataclasses import dataclass

from ..domain.repositories.building_repository import BuildingRepository
from ..domain.services.building_service import BuildingService
from ..application.use_cases.building_use_cases import (
    CreateBuildingUseCase,
    UpdateBuildingUseCase,
    GetBuildingUseCase,
    ListBuildingsUseCase,
    DeleteBuildingUseCase
)
from ..infrastructure.repositories.in_memory_building_repository import InMemoryBuildingRepository


@dataclass
class ContainerConfig:
    """Configuration for the dependency injection container."""
    
    # Repository implementations
    building_repository_class: Type[BuildingRepository] = InMemoryBuildingRepository
    
    # Service configurations
    enable_caching: bool = True
    enable_logging: bool = True
    enable_metrics: bool = True


class Container:
    """
    Dependency injection container for managing all dependencies.
    
    This container follows the Dependency Inversion Principle and provides
    a clean way to configure and manage all dependencies in the application.
    """
    
    def __init__(self, config: ContainerConfig = None):
        """
        Initialize the container.
        
        Args:
            config: Container configuration
        """
        self.config = config or ContainerConfig()
        self._instances: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
        
        # Register default factories
        self._register_default_factories()
    
    def _register_default_factories(self):
        """Register default factory methods for dependencies."""
        
        # Repository factories
        self._factories['building_repository'] = self._create_building_repository
        
        # Service factories
        self._factories['building_service'] = self._create_building_service
        
        # Use case factories
        self._factories['create_building_use_case'] = self._create_create_building_use_case
        self._factories['update_building_use_case'] = self._create_update_building_use_case
        self._factories['get_building_use_case'] = self._create_get_building_use_case
        self._factories['list_buildings_use_case'] = self._create_list_buildings_use_case
        self._factories['delete_building_use_case'] = self._create_delete_building_use_case
    
    def _create_building_repository(self) -> BuildingRepository:
        """Create building repository instance."""
        return self.config.building_repository_class()
    
    def _create_building_service(self) -> BuildingService:
        """Create building service instance."""
        repository = self.get('building_repository')
        return BuildingService(repository)
    
    def _create_create_building_use_case(self) -> CreateBuildingUseCase:
        """Create create building use case instance."""
        repository = self.get('building_repository')
        return CreateBuildingUseCase(repository)
    
    def _create_update_building_use_case(self) -> UpdateBuildingUseCase:
        """Create update building use case instance."""
        repository = self.get('building_repository')
        return UpdateBuildingUseCase(repository)
    
    def _create_get_building_use_case(self) -> GetBuildingUseCase:
        """Create get building use case instance."""
        repository = self.get('building_repository')
        return GetBuildingUseCase(repository)
    
    def _create_list_buildings_use_case(self) -> ListBuildingsUseCase:
        """Create list buildings use case instance."""
        repository = self.get('building_repository')
        return ListBuildingsUseCase(repository)
    
    def _create_delete_building_use_case(self) -> DeleteBuildingUseCase:
        """Create delete building use case instance."""
        repository = self.get('building_repository')
        return DeleteBuildingUseCase(repository)
    
    def get(self, name: str) -> Any:
        """
        Get a dependency by name.
        
        Args:
            name: Name of the dependency
            
        Returns:
            Dependency instance
            
        Raises:
            KeyError: If dependency not found
        """
        # Return cached instance if available
        if name in self._instances:
            return self._instances[name]
        
        # Create new instance if factory exists
        if name in self._factories:
            instance = self._factories[name]()
            self._instances[name] = instance
            return instance
        
        raise KeyError(f"Dependency '{name}' not found")
    
    def register(self, name: str, factory: callable):
        """
        Register a factory for a dependency.
        
        Args:
            name: Name of the dependency
            factory: Factory function to create the dependency
        """
        self._factories[name] = factory
    
    def register_instance(self, name: str, instance: Any):
        """
        Register an existing instance.
        
        Args:
            name: Name of the dependency
            instance: Instance to register
        """
        self._instances[name] = instance
    
    def clear(self):
        """Clear all cached instances."""
        self._instances.clear()
    
    def get_all_use_cases(self) -> Dict[str, Any]:
        """
        Get all use case instances.
        
        Returns:
            Dictionary of use case instances
        """
        return {
            'create_building': self.get('create_building_use_case'),
            'update_building': self.get('update_building_use_case'),
            'get_building': self.get('get_building_use_case'),
            'list_buildings': self.get('list_buildings_use_case'),
            'delete_building': self.get('delete_building_use_case')
        }
    
    def get_all_services(self) -> Dict[str, Any]:
        """
        Get all service instances.
        
        Returns:
            Dictionary of service instances
        """
        return {
            'building_service': self.get('building_service')
        }
    
    def get_all_repositories(self) -> Dict[str, Any]:
        """
        Get all repository instances.
        
        Returns:
            Dictionary of repository instances
        """
        return {
            'building_repository': self.get('building_repository')
        }


# Global container instance
_container: Container = None


def get_container() -> Container:
    """
    Get the global container instance.
    
    Returns:
        Global container instance
    """
    global _container
    if _container is None:
        _container = Container()
    return _container


def set_container(container: Container):
    """
    Set the global container instance.
    
    Args:
        container: Container instance to set
    """
    global _container
    _container = container


def get_use_case(name: str) -> Any:
    """
    Get a use case by name.
    
    Args:
        name: Name of the use case
        
    Returns:
        Use case instance
    """
    container = get_container()
    use_cases = container.get_all_use_cases()
    return use_cases.get(name)


def get_service(name: str) -> Any:
    """
    Get a service by name.
    
    Args:
        name: Name of the service
        
    Returns:
        Service instance
    """
    container = get_container()
    services = container.get_all_services()
    return services.get(name)


def get_repository(name: str) -> Any:
    """
    Get a repository by name.
    
    Args:
        name: Name of the repository
        
    Returns:
        Repository instance
    """
    container = get_container()
    repositories = container.get_all_repositories()
    return repositories.get(name) 