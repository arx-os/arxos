"""
Data Transfer Objects (DTOs) - Application Layer Data Models

This module contains data transfer objects that define the structure
of data exchanged between the application layer and external interfaces.
"""

from svgx_engine.application.dto.building_dto import (
    CreateBuildingRequest,
    UpdateBuildingRequest,
    BuildingResponse,
    BuildingSearchRequest,
    BuildingListResponse,
    AddressDTO,
    CoordinatesDTO,
    DimensionsDTO,
    StatusDTO,
    MoneyDTO,
    BuildingResponseDTO,
    CreateBuildingRequestDTO,
    UpdateBuildingRequestDTO,
    BuildingListResponseDTO,
    BuildingSearchRequestDTO,
)

# Version and metadata
__version__ = "1.0.0"
__description__ = "Data transfer objects for SVGX Engine"

# Export all DTOs
__all__ = [
    "CreateBuildingRequest",
    "UpdateBuildingRequest",
    "BuildingResponse",
    "BuildingSearchRequest",
    "BuildingListResponse",
    "AddressDTO",
    "CoordinatesDTO",
    "DimensionsDTO",
    "StatusDTO",
    "MoneyDTO",
    "BuildingResponseDTO",
    "CreateBuildingRequestDTO",
    "UpdateBuildingRequestDTO",
    "BuildingListResponseDTO",
    "BuildingSearchRequestDTO",
]
