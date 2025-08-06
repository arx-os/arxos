"""
API Module - REST API and WebSocket Interfaces

This module contains API components including endpoints, models,
and middleware for REST API and WebSocket interfaces.
"""

from svgx_engine.api.endpoints import BuildingEndpoints, HealthEndpoints
from svgx_engine.api.models import (
    BuildingCreateRequest,
    BuildingUpdateRequest,
    BuildingResponse,
    ErrorResponse,
    HealthResponse,
)
from svgx_engine.api.middleware import (
    LoggingMiddleware,
    AuthenticationMiddleware,
    CORSMiddleware,
)

# Version and metadata
__version__ = "1.0.0"
__description__ = "API module for SVGX Engine"

# Export all API components
__all__ = [
    # Endpoints
    "BuildingAPI",
    "HealthAPI",
    # Models
    "APIRequest",
    "APIResponse",
    # Middleware
    "APIMiddleware",
    "CorsMiddleware",
]
