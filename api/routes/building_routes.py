"""
Building management API routes.

This module provides REST endpoints for building management operations
using the application services layer.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from api.dependencies import (
    User,
    require_read_permission,
    require_write_permission,
    format_success_response,
    format_error_response,
)
from application.logging import get_logger
from infrastructure import get_repository_factory
from application.factory import get_building_service
from application.dto import (
    CreateBuildingRequest,
    UpdateBuildingRequest,
    GetBuildingRequest,
)

logger = get_logger("api.building_routes")
router = APIRouter(prefix="/buildings", tags=["buildings"])


# Request/Response Models
class BuildingCreateRequest(BaseModel):
    """Request model for creating a building."""

    name: str = Field(..., description="Building name", min_length=1, max_length=255)
    address: str = Field(
        ..., description="Building address", min_length=1, max_length=500
    )
    description: Optional[str] = Field(
        None, description="Building description", max_length=1000
    )
    building_type: str = Field(default="commercial", description="Type of building")
    floors: int = Field(default=1, ge=1, description="Number of floors")
    total_area: Optional[float] = Field(
        None, ge=0, description="Total building area in square meters"
    )
    status: str = Field(default="active", description="Building status")
    created_by: Optional[str] = Field(None, description="User who created the building")


class BuildingUpdateRequest(BaseModel):
    """Request model for updating a building."""

    name: Optional[str] = Field(
        None, description="Building name", min_length=1, max_length=255
    )
    address: Optional[str] = Field(
        None, description="Building address", min_length=1, max_length=500
    )
    description: Optional[str] = Field(
        None, description="Building description", max_length=1000
    )
    building_type: Optional[str] = Field(None, description="Type of building")
    floors: Optional[int] = Field(None, ge=1, description="Number of floors")
    total_area: Optional[float] = Field(
        None, ge=0, description="Total building area in square meters"
    )
    status: Optional[str] = Field(None, description="Building status")
    updated_by: Optional[str] = Field(None, description="User who updated the building")


def get_building_application_service():
    """Dependency to get building application service."""
    factory = get_repository_factory()
    uow = factory.create_unit_of_work()
    return get_building_service(uow)


# API Endpoints
@router.post(
    "/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new building",
    description="Create a new building with the specified properties.",
)
async def create_building(
    request: BuildingCreateRequest,
    user: User = Depends(require_write_permission),
    building_service=Depends(get_building_application_service),
) -> Dict[str, Any]:
    """Create a new building."""
    try:
        # Convert API request to application DTO
        create_request = CreateBuildingRequest(
            name=request.name,
            address=request.address,
            description=request.description,
            building_type=request.building_type,
            floors=request.floors,
            total_area=request.total_area,
            status=request.status,
            created_by=user.user_id,
        )

        # Use application service to create building
        result = building_service.create_building(
            name=create_request.name,
            address=create_request.address,
            description=create_request.description,
            building_type=create_request.building_type,
            floors=create_request.floors,
            total_area=create_request.total_area,
            status=create_request.status,
            created_by=create_request.created_by,
        )

        if result.success:
            return format_success_response(
                data={
                    "building_id": str(result.building_id),
                    "name": result.name,
                    "address": result.address,
                    "description": result.description,
                    "building_type": result.building_type,
                    "floors": result.floors,
                    "total_area": result.total_area,
                    "status": result.status,
                    "created_by": result.created_by,
                    "created_at": (
                        result.created_at.isoformat()
                        if result.created_at
                        else datetime.utcnow().isoformat()
                    ),
                },
                message="Building created successfully",
            )
        else:
            return format_error_response(
                error_code="BUILDING_CREATION_ERROR",
                message=result.error_message or "Failed to create building",
                details={"error": result.error_message},
            )

    except Exception as e:
        logger.error(f"Failed to create building: {str(e)}")
        return format_error_response(
            error_code="BUILDING_CREATION_ERROR",
            message="Failed to create building",
            details={"error": str(e)},
        )


@router.get(
    "/",
    response_model=Dict[str, Any],
    summary="List buildings",
    description="Retrieve a list of buildings with optional filtering and pagination.",
)
async def list_buildings(
    building_type: Optional[str] = Query(None, description="Filter by building type"),
    status: Optional[str] = Query(None, description="Filter by building status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    user: User = Depends(require_read_permission),
    building_service=Depends(get_building_application_service),
) -> Dict[str, Any]:
    """List buildings with filtering and pagination."""
    try:
        # Use application service to list buildings
        result = building_service.list_buildings(
            building_type=building_type, status=status, page=page, page_size=page_size
        )

        if result.success:
            return format_success_response(
                data={
                    "buildings": [
                        {
                            "building_id": str(building.building_id),
                            "name": building.name,
                            "address": building.address,
                            "description": building.description,
                            "building_type": building.building_type,
                            "floors": building.floors,
                            "total_area": building.total_area,
                            "status": building.status,
                            "created_by": building.created_by,
                            "created_at": (
                                building.created_at.isoformat()
                                if building.created_at
                                else None
                            ),
                        }
                        for building in result.buildings
                    ],
                    "pagination": {
                        "page": result.page,
                        "page_size": result.page_size,
                        "total_count": result.total_count,
                        "total_pages": result.total_pages,
                    },
                },
                message="Buildings retrieved successfully",
            )
        else:
            return format_error_response(
                error_code="BUILDING_LIST_ERROR",
                message=result.error_message or "Failed to retrieve buildings",
                details={"error": result.error_message},
            )

    except Exception as e:
        logger.error(f"Failed to list buildings: {str(e)}")
        return format_error_response(
            error_code="BUILDING_LIST_ERROR",
            message="Failed to retrieve buildings",
            details={"error": str(e)},
        )


@router.get(
    "/{building_id}",
    response_model=Dict[str, Any],
    summary="Get building details",
    description="Retrieve detailed information about a specific building.",
)
async def get_building(
    building_id: str,
    user: User = Depends(require_read_permission),
    building_service=Depends(get_building_application_service),
) -> Dict[str, Any]:
    """Get building details by ID."""
    try:
        # Use application service to get building
        result = building_service.get_building(building_id=building_id)

        if result.success and result.building:
            building = result.building
            return format_success_response(
                data={
                    "building_id": str(building.building_id),
                    "name": building.name,
                    "address": building.address,
                    "description": building.description,
                    "building_type": building.building_type,
                    "floors": building.floors,
                    "total_area": building.total_area,
                    "status": building.status,
                    "created_by": building.created_by,
                    "created_at": (
                        building.created_at.isoformat() if building.created_at else None
                    ),
                    "updated_at": (
                        building.updated_at.isoformat() if building.updated_at else None
                    ),
                },
                message="Building retrieved successfully",
            )
        else:
            return format_error_response(
                error_code="BUILDING_NOT_FOUND",
                message=result.error_message or "Building not found",
                details={"building_id": building_id},
            )

    except Exception as e:
        logger.error(f"Failed to get building {building_id}: {str(e)}")
        return format_error_response(
            error_code="BUILDING_RETRIEVAL_ERROR",
            message="Failed to retrieve building",
            details={"error": str(e), "building_id": building_id},
        )


@router.put(
    "/{building_id}",
    response_model=Dict[str, Any],
    summary="Update building",
    description="Update an existing building with new information.",
)
async def update_building(
    building_id: str,
    request: BuildingUpdateRequest,
    user: User = Depends(require_write_permission),
    building_service=Depends(get_building_application_service),
) -> Dict[str, Any]:
    """Update building by ID."""
    try:
        # Convert API request to application DTO
        update_request = UpdateBuildingRequest(
            building_id=building_id,
            name=request.name,
            address=request.address,
            description=request.description,
            building_type=request.building_type,
            floors=request.floors,
            total_area=request.total_area,
            status=request.status,
            updated_by=user.user_id,
        )

        # Use application service to update building
        result = building_service.update_building(
            building_id=building_id,
            name=update_request.name,
            address=update_request.address,
            description=update_request.description,
            building_type=update_request.building_type,
            floors=update_request.floors,
            total_area=update_request.total_area,
            status=update_request.status,
            updated_by=update_request.updated_by,
        )

        if result.success:
            return format_success_response(
                data={
                    "building_id": str(result.building_id),
                    "name": result.name,
                    "address": result.address,
                    "description": result.description,
                    "building_type": result.building_type,
                    "floors": result.floors,
                    "total_area": result.total_area,
                    "status": result.status,
                    "updated_by": result.updated_by,
                    "updated_at": (
                        result.updated_at.isoformat()
                        if result.updated_at
                        else datetime.utcnow().isoformat()
                    ),
                },
                message="Building updated successfully",
            )
        else:
            return format_error_response(
                error_code="BUILDING_UPDATE_ERROR",
                message=result.error_message or "Failed to update building",
                details={"error": result.error_message, "building_id": building_id},
            )

    except Exception as e:
        logger.error(f"Failed to update building {building_id}: {str(e)}")
        return format_error_response(
            error_code="BUILDING_UPDATE_ERROR",
            message="Failed to update building",
            details={"error": str(e), "building_id": building_id},
        )


@router.delete(
    "/{building_id}",
    response_model=Dict[str, Any],
    summary="Delete building",
    description="Delete a building and all associated data.",
)
async def delete_building(
    building_id: str,
    user: User = Depends(require_write_permission),
    building_service=Depends(get_building_application_service),
) -> Dict[str, Any]:
    """Delete building by ID."""
    try:
        # Use application service to delete building
        result = building_service.delete_building(
            building_id=building_id, deleted_by=user.user_id
        )

        if result.success:
            return format_success_response(
                data={
                    "building_id": building_id,
                    "deleted_by": user.user_id,
                    "deleted_at": datetime.utcnow().isoformat(),
                },
                message="Building deleted successfully",
            )
        else:
            return format_error_response(
                error_code="BUILDING_DELETE_ERROR",
                message=result.error_message or "Failed to delete building",
                details={"error": result.error_message, "building_id": building_id},
            )

    except Exception as e:
        logger.error(f"Failed to delete building {building_id}: {str(e)}")
        return format_error_response(
            error_code="BUILDING_DELETE_ERROR",
            message="Failed to delete building",
            details={"error": str(e), "building_id": building_id},
        )


@router.get(
    "/{building_id}/rooms",
    response_model=Dict[str, Any],
    summary="Get building rooms",
    description="Retrieve all rooms in a specific building.",
)
async def get_building_rooms(
    building_id: str,
    floor: Optional[int] = Query(None, description="Filter by floor number"),
    room_type: Optional[str] = Query(None, description="Filter by room type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    user: User = Depends(require_read_permission),
    building_service=Depends(get_building_application_service),
) -> Dict[str, Any]:
    """Get rooms for a specific building."""
    try:
        # Use application service to get building rooms
        result = building_service.get_building_rooms(
            building_id=building_id,
            floor=floor,
            room_type=room_type,
            page=page,
            page_size=page_size,
        )

        if result.success:
            return format_success_response(
                data={
                    "building_id": building_id,
                    "rooms": [
                        {
                            "room_id": str(room.room_id),
                            "room_number": room.room_number,
                            "name": room.name,
                            "room_type": room.room_type,
                            "floor_id": str(room.floor_id),
                            "area": room.area,
                            "capacity": room.capacity,
                            "status": room.status,
                            "created_at": (
                                room.created_at.isoformat() if room.created_at else None
                            ),
                        }
                        for room in result.rooms
                    ],
                    "pagination": {
                        "page": result.page,
                        "page_size": result.page_size,
                        "total_count": result.total_count,
                        "total_pages": result.total_pages,
                    },
                },
                message="Building rooms retrieved successfully",
            )
        else:
            return format_error_response(
                error_code="BUILDING_ROOMS_ERROR",
                message=result.error_message or "Failed to retrieve building rooms",
                details={"error": result.error_message, "building_id": building_id},
            )

    except Exception as e:
        logger.error(f"Failed to get rooms for building {building_id}: {str(e)}")
        return format_error_response(
            error_code="BUILDING_ROOMS_ERROR",
            message="Failed to retrieve building rooms",
            details={"error": str(e), "building_id": building_id},
        )


@router.get(
    "/{building_id}/statistics",
    response_model=Dict[str, Any],
    summary="Get building statistics",
    description="Retrieve statistics and metrics for a specific building.",
)
async def get_building_statistics(
    building_id: str,
    user: User = Depends(require_read_permission),
    building_service=Depends(get_building_application_service),
) -> Dict[str, Any]:
    """Get building statistics."""
    try:
        # Use application service to get building statistics
        result = building_service.get_building_statistics(building_id=building_id)

        if result.success:
            return format_success_response(
                data={
                    "building_id": building_id,
                    "statistics": {
                        "total_floors": result.total_floors,
                        "total_rooms": result.total_rooms,
                        "total_devices": result.total_devices,
                        "total_area": result.total_area,
                        "occupancy_rate": result.occupancy_rate,
                        "device_density": result.device_density,
                        "room_types": result.room_types,
                        "device_types": result.device_types,
                        "status_distribution": result.status_distribution,
                    },
                    "last_updated": datetime.utcnow().isoformat(),
                },
                message="Building statistics retrieved successfully",
            )
        else:
            return format_error_response(
                error_code="BUILDING_STATISTICS_ERROR",
                message=result.error_message
                or "Failed to retrieve building statistics",
                details={"error": result.error_message, "building_id": building_id},
            )

    except Exception as e:
        logger.error(f"Failed to get statistics for building {building_id}: {str(e)}")
        return format_error_response(
            error_code="BUILDING_STATISTICS_ERROR",
            message="Failed to retrieve building statistics",
            details={"error": str(e), "building_id": building_id},
        )
