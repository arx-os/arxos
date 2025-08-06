"""
Application Layer

This module contains the application layer components that coordinate
use cases and provide high-level business operations with infrastructure integration.
"""

from .container import container, ApplicationContainer
from .config import get_settings, Settings
from .factory import (
    ApplicationServiceFactory,
    get_building_service,
    get_health_check,
    get_metrics,
    get_logger,
)
from .services.building_service import BuildingApplicationService

__all__ = [
    # Container
    "container",
    "ApplicationContainer",
    # Configuration
    "get_settings",
    "Settings",
    # Factory
    "ApplicationServiceFactory",
    "get_building_service",
    "get_health_check",
    "get_metrics",
    "get_logger",
    # Services
    "BuildingApplicationService",
]
