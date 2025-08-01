"""
Room management API routes.

This module provides REST endpoints for room management operations
using the application services layer.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from api.dependencies import (
    User, require_read_permission, require_write_permission,
    format_success_response, format_error_response
)
from application.logging import get_logger
from infrastructure import get_repository_factory
from application.factory import get_room_service
from application.dto import (
    CreateRoomRequest, UpdateRoomRequest, GetRoomRequest
)

logger = get_logger("api.room_routes")
router = APIRouter(prefix="/rooms", tags=["rooms"])


# Request/Response Models
class RoomCreateRequest(BaseModel):
    """Request model for creating a room."""
    floor_id: str = Field(..., description="Floor ID where the room is located")
    room_number: str = Field(..., description="Room number", min_length=1, max_length=50)
    name: str = Field(..., description="Room name", min_length=1, max_length=255)
    room_type: str = Field(..., description="Type of room", min_length=1, max_length=100)
    area: Optional[float] = Field(None, ge=0, description="Room area in square meters")
    capacity: Optional[int] = Field(None, ge=0, description="Room capacity")
    description: Optional[str] = Field(None, description="Room description", max_length=1000)
    status: str = Field(default="active", description="Room status")
    created_by: Optional[str] = Field(None, description="User who created the room")


class RoomUpdateRequest(BaseModel):
    """Request model for updating a room."""
    room_number: Optional[str] = Field(None, description="Room number", min_length=1, max_length=50)
    name: Optional[str] = Field(None, description="Room name", min_length=1, max_length=255)
    room_type: Optional[str] = Field(None, description="Type of room", min_length=1, max_length=100)
    area: Optional[float] = Field(None, ge=0, description="Room area in square meters")
    capacity: Optional[int] = Field(None, ge=0, description="Room capacity")
    description: Optional[str] = Field(None, description="Room description", max_length=1000)
    status: Optional[str] = Field(None, description="Room status")
    updated_by: Optional[str] = Field(None, description="User who updated the room")


def get_room_application_service():
    """Dependency to get room application service."""
    factory = get_repository_factory()
    uow = factory.create_unit_of_work()
    return get_room_service(uow)


# API Endpoints
@router.post(
    "/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new room",
    description="Create a new room with the specified properties."
)
async def create_room(
    request: RoomCreateRequest,
    user: User = Depends(require_write_permission),
    room_service = Depends(get_room_application_service)
) -> Dict[str, Any]:
    """Create a new room."""
    try:
        # Convert API request to application DTO
        create_request = CreateRoomRequest(
            floor_id=request.floor_id,
            room_number=request.room_number,
            name=request.name,
            room_type=request.room_type,
            area=request.area,
            capacity=request.capacity,
            description=request.description,
            status=request.status,
            created_by=user.user_id
        )
        
        # Use application service to create room
        result = room_service.create_room(
            floor_id=create_request.floor_id,
            room_number=create_request.room_number,
            name=create_request.name,
            room_type=create_request.room_type,
            area=create_request.area,
            capacity=create_request.capacity,
            description=create_request.description,
            created_by=create_request.created_by
        )
        
        if result.success:
            return format_success_response(
                data={
                    "room_id": str(result.room_id),
                    "floor_id": str(result.floor_id),
                    "room_number": result.room_number,
                    "name": result.name,
                    "room_type": result.room_type,
                    "area": result.area,
                    "capacity": result.capacity,
                    "description": result.description,
                    "status": result.status,
                    "created_by": result.created_by,
                    "created_at": result.created_at.isoformat() if result.created_at else datetime.utcnow().isoformat()
                },
                message="Room created successfully"
            )
        else:
            return format_error_response(
                error_code="ROOM_CREATION_ERROR",
                message=result.error_message or "Failed to create room",
                details={"error": result.error_message}
            )
            
    except Exception as e:
        logger.error(f"Failed to create room: {str(e)}")
        return format_error_response(
            error_code="ROOM_CREATION_ERROR",
            message="Failed to create room",
            details={"error": str(e)}
        )


@router.get(
    "/",
    response_model=Dict[str, Any],
    summary="List rooms",
    description="Retrieve a list of rooms with optional filtering and pagination."
)
async def list_rooms(
    floor_id: Optional[str] = Query(None, description="Filter by floor ID"),
    room_type: Optional[str] = Query(None, description="Filter by room type"),
    status: Optional[str] = Query(None, description="Filter by room status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    user: User = Depends(require_read_permission),
    room_service = Depends(get_room_application_service)
) -> Dict[str, Any]:
    """List rooms with filtering and pagination."""
    try:
        # Use application service to list rooms
        result = room_service.list_rooms(
            floor_id=floor_id,
            room_type=room_type,
            status=status,
            page=page,
            page_size=page_size
        )
        
        if result.success:
            return format_success_response(
                data={
                    "rooms": [
                        {
                            "room_id": str(room.room_id),
                            "floor_id": str(room.floor_id),
                            "room_number": room.room_number,
                            "name": room.name,
                            "room_type": room.room_type,
                            "area": room.area,
                            "capacity": room.capacity,
                            "description": room.description,
                            "status": room.status,
                            "created_by": room.created_by,
                            "created_at": room.created_at.isoformat() if room.created_at else None
                        }
                        for room in result.rooms
                    ],
                    "pagination": {
                        "page": result.page,
                        "page_size": result.page_size,
                        "total_count": result.total_count,
                        "total_pages": result.total_pages
                    }
                },
                message="Rooms retrieved successfully"
            )
        else:
            return format_error_response(
                error_code="ROOM_LIST_ERROR",
                message=result.error_message or "Failed to retrieve rooms",
                details={"error": result.error_message}
            )
            
    except Exception as e:
        logger.error(f"Failed to list rooms: {str(e)}")
        return format_error_response(
            error_code="ROOM_LIST_ERROR",
            message="Failed to retrieve rooms",
            details={"error": str(e)}
        )


@router.get(
    "/{room_id}",
    response_model=Dict[str, Any],
    summary="Get room details",
    description="Retrieve detailed information about a specific room."
)
async def get_room(
    room_id: str,
    user: User = Depends(require_read_permission),
    room_service = Depends(get_room_application_service)
) -> Dict[str, Any]:
    """Get room details by ID."""
    try:
        # Use application service to get room
        result = room_service.get_room(room_id=room_id)
        
        if result.success and result.room:
            room = result.room
            return format_success_response(
                data={
                    "room_id": str(room.room_id),
                    "floor_id": str(room.floor_id),
                    "room_number": room.room_number,
                    "name": room.name,
                    "room_type": room.room_type,
                    "area": room.area,
                    "capacity": room.capacity,
                    "description": room.description,
                    "status": room.status,
                    "created_by": room.created_by,
                    "created_at": room.created_at.isoformat() if room.created_at else None,
                    "updated_at": room.updated_at.isoformat() if room.updated_at else None
                },
                message="Room retrieved successfully"
            )
        else:
            return format_error_response(
                error_code="ROOM_NOT_FOUND",
                message=result.error_message or "Room not found",
                details={"room_id": room_id}
            )
            
    except Exception as e:
        logger.error(f"Failed to get room {room_id}: {str(e)}")
        return format_error_response(
            error_code="ROOM_RETRIEVAL_ERROR",
            message="Failed to retrieve room",
            details={"error": str(e), "room_id": room_id}
        )


@router.put(
    "/{room_id}",
    response_model=Dict[str, Any],
    summary="Update room",
    description="Update an existing room with new information."
)
async def update_room(
    room_id: str,
    request: RoomUpdateRequest,
    user: User = Depends(require_write_permission),
    room_service = Depends(get_room_application_service)
) -> Dict[str, Any]:
    """Update room by ID."""
    try:
        # Convert API request to application DTO
        update_request = UpdateRoomRequest(
            room_id=room_id,
            room_number=request.room_number,
            name=request.name,
            room_type=request.room_type,
            area=request.area,
            capacity=request.capacity,
            description=request.description,
            status=request.status,
            updated_by=user.user_id
        )
        
        # Use application service to update room
        result = room_service.update_room(
            room_id=room_id,
            room_number=update_request.room_number,
            name=update_request.name,
            room_type=update_request.room_type,
            area=update_request.area,
            capacity=update_request.capacity,
            description=update_request.description,
            status=update_request.status,
            updated_by=update_request.updated_by
        )
        
        if result.success:
            return format_success_response(
                data={
                    "room_id": str(result.room_id),
                    "floor_id": str(result.floor_id),
                    "room_number": result.room_number,
                    "name": result.name,
                    "room_type": result.room_type,
                    "area": result.area,
                    "capacity": result.capacity,
                    "description": result.description,
                    "status": result.status,
                    "updated_by": result.updated_by,
                    "updated_at": result.updated_at.isoformat() if result.updated_at else datetime.utcnow().isoformat()
                },
                message="Room updated successfully"
            )
        else:
            return format_error_response(
                error_code="ROOM_UPDATE_ERROR",
                message=result.error_message or "Failed to update room",
                details={"error": result.error_message, "room_id": room_id}
            )
            
    except Exception as e:
        logger.error(f"Failed to update room {room_id}: {str(e)}")
        return format_error_response(
            error_code="ROOM_UPDATE_ERROR",
            message="Failed to update room",
            details={"error": str(e), "room_id": room_id}
        )


@router.delete(
    "/{room_id}",
    response_model=Dict[str, Any],
    summary="Delete room",
    description="Delete a room and all associated data."
)
async def delete_room(
    room_id: str,
    user: User = Depends(require_write_permission),
    room_service = Depends(get_room_application_service)
) -> Dict[str, Any]:
    """Delete room by ID."""
    try:
        # Use application service to delete room
        result = room_service.delete_room(
            room_id=room_id,
            deleted_by=user.user_id
        )
        
        if result.success:
            return format_success_response(
                data={
                    "room_id": room_id,
                    "deleted_by": user.user_id,
                    "deleted_at": datetime.utcnow().isoformat()
                },
                message="Room deleted successfully"
            )
        else:
            return format_error_response(
                error_code="ROOM_DELETE_ERROR",
                message=result.error_message or "Failed to delete room",
                details={"error": result.error_message, "room_id": room_id}
            )
            
    except Exception as e:
        logger.error(f"Failed to delete room {room_id}: {str(e)}")
        return format_error_response(
            error_code="ROOM_DELETE_ERROR",
            message="Failed to delete room",
            details={"error": str(e), "room_id": room_id}
        )


@router.get(
    "/{room_id}/devices",
    response_model=Dict[str, Any],
    summary="Get room devices",
    description="Retrieve all devices in a specific room."
)
async def get_room_devices(
    room_id: str,
    device_type: Optional[str] = Query(None, description="Filter by device type"),
    status: Optional[str] = Query(None, description="Filter by device status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    user: User = Depends(require_read_permission),
    room_service = Depends(get_room_application_service)
) -> Dict[str, Any]:
    """Get devices for a specific room."""
    try:
        # Use application service to get room devices
        result = room_service.get_room_devices(
            room_id=room_id,
            device_type=device_type,
            status=status,
            page=page,
            page_size=page_size
        )
        
        if result.success:
            return format_success_response(
                data={
                    "room_id": room_id,
                    "devices": [
                        {
                            "device_id": str(device.device_id),
                            "device_type": device.device_type,
                            "name": device.name,
                            "manufacturer": device.manufacturer,
                            "model": device.model,
                            "serial_number": device.serial_number,
                            "description": device.description,
                            "status": device.status,
                            "created_at": device.created_at.isoformat() if device.created_at else None
                        }
                        for device in result.devices
                    ],
                    "pagination": {
                        "page": result.page,
                        "page_size": result.page_size,
                        "total_count": result.total_count,
                        "total_pages": result.total_pages
                    }
                },
                message="Room devices retrieved successfully"
            )
        else:
            return format_error_response(
                error_code="ROOM_DEVICES_ERROR",
                message=result.error_message or "Failed to retrieve room devices",
                details={"error": result.error_message, "room_id": room_id}
            )
            
    except Exception as e:
        logger.error(f"Failed to get devices for room {room_id}: {str(e)}")
        return format_error_response(
            error_code="ROOM_DEVICES_ERROR",
            message="Failed to retrieve room devices",
            details={"error": str(e), "room_id": room_id}
        )


@router.get(
    "/{room_id}/statistics",
    response_model=Dict[str, Any],
    summary="Get room statistics",
    description="Retrieve statistics and metrics for a specific room."
)
async def get_room_statistics(
    room_id: str,
    user: User = Depends(require_read_permission),
    room_service = Depends(get_room_application_service)
) -> Dict[str, Any]:
    """Get room statistics."""
    try:
        # Use application service to get room statistics
        result = room_service.get_room_statistics(room_id=room_id)
        
        if result.success:
            return format_success_response(
                data={
                    "room_id": room_id,
                    "statistics": {
                        "total_devices": result.total_devices,
                        "active_devices": result.active_devices,
                        "inactive_devices": result.inactive_devices,
                        "device_types": result.device_types,
                        "status_distribution": result.status_distribution,
                        "area_utilization": result.area_utilization,
                        "capacity_utilization": result.capacity_utilization
                    },
                    "last_updated": datetime.utcnow().isoformat()
                },
                message="Room statistics retrieved successfully"
            )
        else:
            return format_error_response(
                error_code="ROOM_STATISTICS_ERROR",
                message=result.error_message or "Failed to retrieve room statistics",
                details={"error": result.error_message, "room_id": room_id}
            )
            
    except Exception as e:
        logger.error(f"Failed to get statistics for room {room_id}: {str(e)}")
        return format_error_response(
            error_code="ROOM_STATISTICS_ERROR",
            message="Failed to retrieve room statistics",
            details={"error": str(e), "room_id": room_id}
        ) 