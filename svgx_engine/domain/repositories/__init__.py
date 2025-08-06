"""
Domain Repositories - Data Access Interfaces

This module contains repository interfaces that define the contract
for data access and persistence operations.
"""

from svgx_engine.domain.repositories.building_repository import BuildingRepository

# Version and metadata
__version__ = "1.0.0"
__description__ = "Domain repositories for SVGX Engine"

# Export all repositories
__all__ = ["BuildingRepository"]
