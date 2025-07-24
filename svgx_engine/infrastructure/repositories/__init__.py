"""
Infrastructure Repositories - Data Access Implementations

This module contains repository implementations that provide concrete
data access and persistence operations.
"""

from svgx_engine.infrastructure.repositories.in_memory_building_repository import InMemoryBuildingRepository
from svgx_engine.infrastructure.repositories.postgresql_building_repository import PostgreSQLBuildingRepository

# Version and metadata
__version__ = "1.0.0"
__description__ = "Infrastructure repositories for SVGX Engine"

# Export all repository implementations
__all__ = [
    "InMemoryBuildingRepository",
    "PostgreSQLBuildingRepository"
] 