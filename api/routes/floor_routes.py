"""
Floor management API routes.

This module provides REST endpoints for floor management operations
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
from application.factory import get_floor_service
from application.dto import CreateFloorRequest, UpdateFloorRequest, GetFloorRequest

logger = get_logger("api.floor_routes")
router = APIRouter(prefix="/floors", tags=["floors"])


# Request/Response Models
class FloorCreateRequest(BaseModel):
    """Request model for creating a floor."""

    building_id: str = Field(..., description="Building ID where the floor is located")
    floor_number: int = Field(..., ge=0, description="Floor number")
    name: str = Field(..., description="Floor name", min_length=1, max_length=255)
    description: Optional[str] = Field(
        None, description="Floor description", max_length=1000
    )
    total_area: Optional[float] = Field(
        None, ge=0, description="Total floor area in square meters"
    )
    status: str = Field(default="active", description="Floor status")
    created_by: Optional[str] = Field(None, description="User who created the floor")


class FloorUpdateRequest(BaseModel):
    """Request model for updating a floor."""

    floor_number: Optional[int] = Field(None, ge=0, description="Floor number")
    name: Optional[str] = Field(
        None, description="Floor name", min_length=1, max_length=255
    )
    description: Optional[str] = Field(
        None, description="Floor description", max_length=1000
    )
    total_area: Optional[float] = Field(
        None, ge=0, description="Total floor area in square meters"
    )
    status: Optional[str] = Field(None, description="Floor status")
    updated_by: Optional[str] = Field(None, description="User who updated the floor")


def get_floor_application_service():
    """Dependency to get floor application service."""
    factory = get_repository_factory()
    uow = factory.create_unit_of_work()
    return get_floor_service(uow)


# API Endpoints
@router.post(
    "/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new floor",
    description="Create a new floor with the specified properties.",
)
async def create_floor(
    request: FloorCreateRequest,
    user: User = Depends(require_write_permission),
    floor_service=Depends(get_floor_application_service),
) -> Dict[str, Any]:
    """Create a new floor."""
    try:
        # Convert API request to application DTO
        create_request = CreateFloorRequest(
            building_id=request.building_id,
            floor_number=request.floor_number,
            name=request.name,
            description=request.description,
            total_area=request.total_area,
            status=request.status,
            created_by=user.user_id,
        )

        # Use application service to create floor
        result = floor_service.create_floor(
            building_id=create_request.building_id,
            floor_number=create_request.floor_number,
            name=create_request.name,
            description=create_request.description,
            total_area=create_request.total_area,
            created_by=create_request.created_by,
        )

        if result.success:
            return format_success_response(
                data={
                    "floor_id": str(result.floor_id),
                    "building_id": str(result.building_id),
                    "floor_number": result.floor_number,
                    "name": result.name,
                    "description": result.description,
                    "total_area": result.total_area,
                    "status": result.status,
                    "created_by": result.created_by,
                    "created_at": (
                        result.created_at.isoformat()
                        if result.created_at
                        else datetime.utcnow().isoformat()
                    ),
                },
                message="Floor created successfully",
            )
        else:
            return format_error_response(
                error_code="FLOOR_CREATION_ERROR",
                message=result.error_message or "Failed to create floor",
                details={"error": result.error_message},
            )

    except Exception as e:
        logger.error(f"Failed to create floor: {str(e)}")
        return format_error_response(
            error_code="FLOOR_CREATION_ERROR",
            message="Failed to create floor",
            details={"error": str(e)},
        )


@router.get(
    "/",
    response_model=Dict[str, Any],
    summary="List floors",
    description="Retrieve a list of floors with optional filtering and pagination.",
)
async def list_floors(
    building_id: Optional[str] = Query(None, description="Filter by building ID"),
    status: Optional[str] = Query(None, description="Filter by floor status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    user: User = Depends(require_read_permission),
    floor_service=Depends(get_floor_application_service),
) -> Dict[str, Any]:
    """List floors with filtering and pagination."""
    try:
        # Use application service to list floors
        result = floor_service.list_floors(
            building_id=building_id, status=status, page=page, page_size=page_size
        )

        if result.success:
            return format_success_response(
                data={
                    "floors": [
                        {
                            "floor_id": str(floor.floor_id),
                            "building_id": str(floor.building_id),
                            "floor_number": floor.floor_number,
                            "name": floor.name,
                            "description": floor.description,
                            "total_area": floor.total_area,
                            "status": floor.status,
                            "created_by": floor.created_by,
                            "created_at": (
                                floor.created_at.isoformat()
                                if floor.created_at
                                else None
                            ),
                        }
                        for floor in result.floors
                    ],
                    "pagination": {
                        "page": result.page,
                        "page_size": result.page_size,
                        "total_count": result.total_count,
                        "total_pages": result.total_pages,
                    },
                },
                message="Floors retrieved successfully",
            )
        else:
            return format_error_response(
                error_code="FLOOR_LIST_ERROR",
                message=result.error_message or "Failed to retrieve floors",
                details={"error": result.error_message},
            )

    except Exception as e:
        logger.error(f"Failed to list floors: {str(e)}")
        return format_error_response(
            error_code="FLOOR_LIST_ERROR",
            message="Failed to retrieve floors",
            details={"error": str(e)},
        )


@router.get(
    "/{floor_id}",
    response_model=Dict[str, Any],
    summary="Get floor details",
    description="Retrieve detailed information about a specific floor.",
)
async def get_floor(
    floor_id: str,
    user: User = Depends(require_read_permission),
    floor_service=Depends(get_floor_application_service),
) -> Dict[str, Any]:
    """Get floor details by ID."""
    try:
        # Use application service to get floor
        result = floor_service.get_floor(floor_id=floor_id)

        if result.success and result.floor:
            floor = result.floor
            return format_success_response(
                data={
                    "floor_id": str(floor.floor_id),
                    "building_id": str(floor.building_id),
                    "floor_number": floor.floor_number,
                    "name": floor.name,
                    "description": floor.description,
                    "total_area": floor.total_area,
                    "status": floor.status,
                    "created_by": floor.created_by,
                    "created_at": (
                        floor.created_at.isoformat() if floor.created_at else None
                    ),
                    "updated_at": (
                        floor.updated_at.isoformat() if floor.updated_at else None
                    ),
                },
                message="Floor retrieved successfully",
            )
        else:
            return format_error_response(
                error_code="FLOOR_NOT_FOUND",
                message=result.error_message or "Floor not found",
                details={"floor_id": floor_id},
            )

    except Exception as e:
        logger.error(f"Failed to get floor {floor_id}: {str(e)}")
        return format_error_response(
            error_code="FLOOR_RETRIEVAL_ERROR",
            message="Failed to retrieve floor",
            details={"error": str(e), "floor_id": floor_id},
        )


@router.put(
    "/{floor_id}",
    response_model=Dict[str, Any],
    summary="Update floor",
    description="Update an existing floor with new information.",
)
async def update_floor(
    floor_id: str,
    request: FloorUpdateRequest,
    user: User = Depends(require_write_permission),
    floor_service=Depends(get_floor_application_service),
) -> Dict[str, Any]:
    """Update floor by ID."""
    try:
        # Convert API request to application DTO
        update_request = UpdateFloorRequest(
            floor_id=floor_id,
            floor_number=request.floor_number,
            name=request.name,
            description=request.description,
            total_area=request.total_area,
            status=request.status,
            updated_by=user.user_id,
        )

        # Use application service to update floor
        result = floor_service.update_floor(
            floor_id=floor_id,
            floor_number=update_request.floor_number,
            name=update_request.name,
            description=update_request.description,
            total_area=update_request.total_area,
            status=update_request.status,
            updated_by=update_request.updated_by,
        )

        if result.success:
            return format_success_response(
                data={
                    "floor_id": str(result.floor_id),
                    "building_id": str(result.building_id),
                    "floor_number": result.floor_number,
                    "name": result.name,
                    "description": result.description,
                    "total_area": result.total_area,
                    "status": result.status,
                    "updated_by": result.updated_by,
                    "updated_at": (
                        result.updated_at.isoformat()
                        if result.updated_at
                        else datetime.utcnow().isoformat()
                    ),
                },
                message="Floor updated successfully",
            )
        else:
            return format_error_response(
                error_code="FLOOR_UPDATE_ERROR",
                message=result.error_message or "Failed to update floor",
                details={"error": result.error_message, "floor_id": floor_id},
            )

    except Exception as e:
        logger.error(f"Failed to update floor {floor_id}: {str(e)}")
        return format_error_response(
            error_code="FLOOR_UPDATE_ERROR",
            message="Failed to update floor",
            details={"error": str(e), "floor_id": floor_id},
        )


@router.delete(
    "/{floor_id}",
    response_model=Dict[str, Any],
    summary="Delete floor",
    description="Delete a floor and all associated data.",
)
async def delete_floor(
    floor_id: str,
    user: User = Depends(require_write_permission),
    floor_service=Depends(get_floor_application_service),
) -> Dict[str, Any]:
    """Delete floor by ID."""
    try:
        # Use application service to delete floor
        result = floor_service.delete_floor(floor_id=floor_id, deleted_by=user.user_id)

        if result.success:
            return format_success_response(
                data={
                    "floor_id": floor_id,
                    "deleted_by": user.user_id,
                    "deleted_at": datetime.utcnow().isoformat(),
                },
                message="Floor deleted successfully",
            )
        else:
            return format_error_response(
                error_code="FLOOR_DELETE_ERROR",
                message=result.error_message or "Failed to delete floor",
                details={"error": result.error_message, "floor_id": floor_id},
            )

    except Exception as e:
        logger.error(f"Failed to delete floor {floor_id}: {str(e)}")
        return format_error_response(
            error_code="FLOOR_DELETE_ERROR",
            message="Failed to delete floor",
            details={"error": str(e), "floor_id": floor_id},
        )


@router.get(
    "/{floor_id}/rooms",
    response_model=Dict[str, Any],
    summary="Get floor rooms",
    description="Retrieve all rooms on a specific floor.",
)
async def get_floor_rooms(
    floor_id: str,
    room_type: Optional[str] = Query(None, description="Filter by room type"),
    status: Optional[str] = Query(None, description="Filter by room status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    user: User = Depends(require_read_permission),
    floor_service=Depends(get_floor_application_service),
) -> Dict[str, Any]:
    """Get rooms for a specific floor."""
    try:
        # Use application service to get floor rooms
        result = floor_service.get_floor_rooms(
            floor_id=floor_id,
            room_type=room_type,
            status=status,
            page=page,
            page_size=page_size,
        )

        if result.success:
            return format_success_response(
                data={
                    "floor_id": floor_id,
                    "rooms": [
                        {
                            "room_id": str(room.room_id),
                            "room_number": room.room_number,
                            "name": room.name,
                            "room_type": room.room_type,
                            "area": room.area,
                            "capacity": room.capacity,
                            "description": room.description,
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
                message="Floor rooms retrieved successfully",
            )
        else:
            return format_error_response(
                error_code="FLOOR_ROOMS_ERROR",
                message=result.error_message or "Failed to retrieve floor rooms",
                details={"error": result.error_message, "floor_id": floor_id},
            )

    except Exception as e:
        logger.error(f"Failed to get rooms for floor {floor_id}: {str(e)}")
        return format_error_response(
            error_code="FLOOR_ROOMS_ERROR",
            message="Failed to retrieve floor rooms",
            details={"error": str(e), "floor_id": floor_id},
        )


@router.get(
    "/{floor_id}/statistics",
    response_model=Dict[str, Any],
    summary="Get floor statistics",
    description="Retrieve statistics and metrics for a specific floor.",
)
async def get_floor_statistics(
    floor_id: str,
    user: User = Depends(require_read_permission),
    floor_service=Depends(get_floor_application_service),
) -> Dict[str, Any]:
    """Get floor statistics."""
    try:
        # Use application service to get floor statistics
        result = floor_service.get_floor_statistics(floor_id=floor_id)

        if result.success:
            return format_success_response(
                data={
                    "floor_id": floor_id,
                    "statistics": {
                        "total_rooms": result.total_rooms,
                        "total_devices": result.total_devices,
                        "total_area": result.total_area,
                        "room_types": result.room_types,
                        "device_types": result.device_types,
                        "status_distribution": result.status_distribution,
                        "area_utilization": result.area_utilization,
                    },
                    "last_updated": datetime.utcnow().isoformat(),
                },
                message="Floor statistics retrieved successfully",
            )
        else:
            return format_error_response(
                error_code="FLOOR_STATISTICS_ERROR",
                message=result.error_message or "Failed to retrieve floor statistics",
                details={"error": result.error_message, "floor_id": floor_id},
            )

    except Exception as e:
        logger.error(f"Failed to get statistics for floor {floor_id}: {str(e)}")
        return format_error_response(
            error_code="FLOOR_STATISTICS_ERROR",
            message="Failed to retrieve floor statistics",
            details={"error": str(e), "floor_id": floor_id},
        )
