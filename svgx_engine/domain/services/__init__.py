"""
Domain Services - Business Logic Services

This module contains domain services that implement business logic
and coordinate between aggregates and repositories.
"""

from svgx_engine.domain.services.building_service import BuildingService

# Version and metadata
__version__ = "1.0.0"
__description__ = "Domain services for SVGX Engine"

# Export all services
__all__ = [
    "BuildingService"
] 