"""
Repositories Module

This module contains all repository interfaces used in the domain layer.
Repositories define the contract for data access and persistence,
following the Repository pattern for clean separation of concerns.
"""

from .building_repository import BuildingRepository

__all__ = [
    'BuildingRepository'
] 