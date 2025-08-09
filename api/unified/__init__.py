"""
Unified API Layer - Consolidated API Endpoints

This module contains the unified API layer that consolidates all API endpoints
into a consistent, maintainable structure following Clean Architecture principles.

The unified API layer provides:
- Consistent controller patterns
- Unified middleware for authentication, validation, and logging
- Standardized request/response schemas
- Comprehensive error handling
- API versioning support
- OpenAPI/Swagger documentation
"""

from .controllers import *
from .middleware import *
from .schemas import *
from .validators import *
from .serializers import *
from .decorators import *

__version__ = "3.0.0"
__description__ = "Unified API Layer for Arxos Platform"

__all__ = [
    # Controllers
    "BuildingController",
    "FloorController",
    "RoomController",
    "DeviceController",
    "UserController",
    "ProjectController",
    "PDFController",

    # Middleware
    "AuthMiddleware",
    "ValidationMiddleware",
    "LoggingMiddleware",
    "ErrorMiddleware",

    # Schemas
    "BuildingSchemas",
    "FloorSchemas",
    "RoomSchemas",
    "DeviceSchemas",
    "UserSchemas",
    "ProjectSchemas",
    "PDFSchemas",

    # Validators
    "RequestValidator",
    "ResponseValidator",

    # Serializers
    "ResponseSerializer",
    "ErrorSerializer",

    # Decorators
    "api_version",
    "rate_limit",
    "cache_response"
]
