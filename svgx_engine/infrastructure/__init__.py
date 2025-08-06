"""
Infrastructure Layer - External Interfaces and Implementations

This module contains infrastructure layer components including repositories,
external service adapters, and infrastructure services that handle
persistence, external APIs, and technical concerns.
"""

from svgx_engine.infrastructure.repositories import (
    PostgresBuildingRepository,
    InMemoryBuildingRepository,
)

# Version and metadata
__version__ = "1.0.0"
__description__ = "Infrastructure layer for SVGX Engine"

# Export all infrastructure components
__all__ = [
    # Repository Implementations
    "InMemoryBuildingRepository",
    "PostgreSQLBuildingRepository",
    # Container
    "container",
]
