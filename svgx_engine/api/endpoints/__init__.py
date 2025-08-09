"""
API Endpoints - REST API Route Handlers

This module contains API endpoint handlers that process HTTP requests
and responses for the REST API interface.
"""

from svgx_engine.api.endpoints.building_api import BuildingAPI
from svgx_engine.api.endpoints.health_api import HealthAPI

# Version and metadata
__version__ = "1.0.0"
__description__ = "API endpoints for SVGX Engine"

# Export all endpoints
__all__ = [
    "BuildingAPI",
    "HealthAPI"
]
