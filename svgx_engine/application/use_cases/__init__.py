"""
Use Cases - Application Layer Business Logic

This module contains use cases that orchestrate domain logic and
handle external interfaces for specific business operations.
"""

from svgx_engine.application.use_cases.building_use_cases import (
    CreateBuildingUseCase,
    UpdateBuildingUseCase,
    GetBuildingUseCase,
    DeleteBuildingUseCase,
    ListBuildingsUseCase
)

# Version and metadata
__version__ = "1.0.0"
__description__ = "Use cases for SVGX Engine"

# Export all use cases
__all__ = [
    "CreateBuildingUseCase",
    "UpdateBuildingUseCase",
    "GetBuildingUseCase",
    "DeleteBuildingUseCase",
    "ListBuildingsUseCase"
]
