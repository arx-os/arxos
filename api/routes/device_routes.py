"""
Device management API routes.

This module provides REST endpoints for device management operations
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
from application.factory import get_device_service
from application.dto import CreateDeviceRequest, UpdateDeviceRequest, GetDeviceRequest

logger = get_logger("api.device_routes")
router = APIRouter(prefix="/devices", tags=["devices"])


# Request/Response Models
class DeviceCreateRequest(BaseModel):
    """Request model for creating a device."""

    room_id: str = Field(..., description="Room ID where device is located")
    device_type: str = Field(
        ..., description="Type of device", min_length=1, max_length=100
    )
    name: str = Field(..., description="Device name", min_length=1, max_length=255)
    manufacturer: Optional[str] = Field(
        None, description="Device manufacturer", max_length=100
    )
    model: Optional[str] = Field(None, description="Device model", max_length=100)
    serial_number: Optional[str] = Field(
        None, description="Device serial number", max_length=100
    )
    description: Optional[str] = Field(
        None, description="Device description", max_length=1000
    )
    status: str = Field(default="installed", description="Device status")
    created_by: Optional[str] = Field(None, description="User who created the device")


class DeviceUpdateRequest(BaseModel):
    """Request model for updating a device."""

    device_type: Optional[str] = Field(
        None, description="Type of device", min_length=1, max_length=100
    )
    name: Optional[str] = Field(
        None, description="Device name", min_length=1, max_length=255
    )
    manufacturer: Optional[str] = Field(
        None, description="Device manufacturer", max_length=100
    )
    model: Optional[str] = Field(None, description="Device model", max_length=100)
    serial_number: Optional[str] = Field(
        None, description="Device serial number", max_length=100
    )
    description: Optional[str] = Field(
        None, description="Device description", max_length=1000
    )
    status: Optional[str] = Field(None, description="Device status")
    updated_by: Optional[str] = Field(None, description="User who updated the device")


def get_device_application_service():
    """Dependency to get device application service."""
    factory = get_repository_factory()
    uow = factory.create_unit_of_work()
    return get_device_service(uow)


# API Endpoints
@router.post(
    "/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new device",
    description="Create a new device with the specified properties.",
)
async def create_device(
    request: DeviceCreateRequest,
    user: User = Depends(require_write_permission),
    device_service=Depends(get_device_application_service),
) -> Dict[str, Any]:
    """Create a new device."""
    try:
        # Convert API request to application DTO
        create_request = CreateDeviceRequest(
            room_id=request.room_id,
            device_type=request.device_type,
            name=request.name,
            manufacturer=request.manufacturer,
            model=request.model,
            serial_number=request.serial_number,
            description=request.description,
            status=request.status,
            created_by=user.user_id,
        )

        # Use application service to create device
        result = device_service.create_device(
            room_id=create_request.room_id,
            device_type=create_request.device_type,
            name=create_request.name,
            manufacturer=create_request.manufacturer,
            model=create_request.model,
            serial_number=create_request.serial_number,
            description=create_request.description,
            created_by=create_request.created_by,
        )

        if result.success:
            return format_success_response(
                data={
                    "device_id": str(result.device_id),
                    "room_id": result.room_id,
                    "device_type": result.device_type,
                    "name": result.name,
                    "manufacturer": result.manufacturer,
                    "model": result.model,
                    "serial_number": result.serial_number,
                    "description": result.description,
                    "status": result.status,
                    "created_by": result.created_by,
                    "created_at": (
                        result.created_at.isoformat()
                        if result.created_at
                        else datetime.utcnow().isoformat()
                    ),
                },
                message="Device created successfully",
            )
        else:
            return format_error_response(
                error_code="DEVICE_CREATION_ERROR",
                message=result.error_message or "Failed to create device",
                details={"error": result.error_message},
            )

    except Exception as e:
        logger.error(f"Failed to create device: {str(e)}")
        return format_error_response(
            error_code="DEVICE_CREATION_ERROR",
            message="Failed to create device",
            details={"error": str(e)},
        )


@router.get(
    "/",
    response_model=Dict[str, Any],
    summary="List devices",
    description="Retrieve a list of devices with optional filtering and pagination.",
)
async def list_devices(
    room_id: Optional[str] = Query(None, description="Filter by room ID"),
    device_type: Optional[str] = Query(None, description="Filter by device type"),
    status: Optional[str] = Query(None, description="Filter by device status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    user: User = Depends(require_read_permission),
    device_service=Depends(get_device_application_service),
) -> Dict[str, Any]:
    """List devices with filtering and pagination."""
    try:
        # Use application service to list devices
        result = device_service.list_devices(
            room_id=room_id,
            device_type=device_type,
            status=status,
            page=page,
            page_size=page_size,
        )

        if result.success:
            return format_success_response(
                data={
                    "devices": [
                        {
                            "device_id": str(device.device_id),
                            "room_id": str(device.room_id),
                            "device_type": device.device_type,
                            "name": device.name,
                            "manufacturer": device.manufacturer,
                            "model": device.model,
                            "serial_number": device.serial_number,
                            "description": device.description,
                            "status": device.status,
                            "created_by": device.created_by,
                            "created_at": (
                                device.created_at.isoformat()
                                if device.created_at
                                else None
                            ),
                        }
                        for device in result.devices
                    ],
                    "pagination": {
                        "page": result.page,
                        "page_size": result.page_size,
                        "total_count": result.total_count,
                        "total_pages": result.total_pages,
                    },
                },
                message="Devices retrieved successfully",
            )
        else:
            return format_error_response(
                error_code="DEVICE_LIST_ERROR",
                message=result.error_message or "Failed to retrieve devices",
                details={"error": result.error_message},
            )

    except Exception as e:
        logger.error(f"Failed to list devices: {str(e)}")
        return format_error_response(
            error_code="DEVICE_LIST_ERROR",
            message="Failed to retrieve devices",
            details={"error": str(e)},
        )


@router.get(
    "/{device_id}",
    response_model=Dict[str, Any],
    summary="Get device details",
    description="Retrieve detailed information about a specific device.",
)
async def get_device(
    device_id: str,
    user: User = Depends(require_read_permission),
    device_service=Depends(get_device_application_service),
) -> Dict[str, Any]:
    """Get device details by ID."""
    try:
        # Use application service to get device
        result = device_service.get_device(device_id=device_id)

        if result.success and result.device:
            device = result.device
            return format_success_response(
                data={
                    "device_id": str(device.device_id),
                    "room_id": str(device.room_id),
                    "device_type": device.device_type,
                    "name": device.name,
                    "manufacturer": device.manufacturer,
                    "model": device.model,
                    "serial_number": device.serial_number,
                    "description": device.description,
                    "status": device.status,
                    "created_by": device.created_by,
                    "created_at": (
                        device.created_at.isoformat() if device.created_at else None
                    ),
                    "updated_at": (
                        device.updated_at.isoformat() if device.updated_at else None
                    ),
                },
                message="Device retrieved successfully",
            )
        else:
            return format_error_response(
                error_code="DEVICE_NOT_FOUND",
                message=result.error_message or "Device not found",
                details={"device_id": device_id},
            )

    except Exception as e:
        logger.error(f"Failed to get device {device_id}: {str(e)}")
        return format_error_response(
            error_code="DEVICE_RETRIEVAL_ERROR",
            message="Failed to retrieve device",
            details={"error": str(e), "device_id": device_id},
        )


@router.put(
    "/{device_id}",
    response_model=Dict[str, Any],
    summary="Update device",
    description="Update an existing device with new information.",
)
async def update_device(
    device_id: str,
    request: DeviceUpdateRequest,
    user: User = Depends(require_write_permission),
    device_service=Depends(get_device_application_service),
) -> Dict[str, Any]:
    """Update device by ID."""
    try:
        # Convert API request to application DTO
        update_request = UpdateDeviceRequest(
            device_id=device_id,
            device_type=request.device_type,
            name=request.name,
            manufacturer=request.manufacturer,
            model=request.model,
            serial_number=request.serial_number,
            description=request.description,
            status=request.status,
            updated_by=user.user_id,
        )

        # Use application service to update device
        result = device_service.update_device(
            device_id=device_id,
            device_type=update_request.device_type,
            name=update_request.name,
            manufacturer=update_request.manufacturer,
            model=update_request.model,
            serial_number=update_request.serial_number,
            description=update_request.description,
            status=update_request.status,
            updated_by=update_request.updated_by,
        )

        if result.success:
            return format_success_response(
                data={
                    "device_id": str(result.device_id),
                    "room_id": str(result.room_id),
                    "device_type": result.device_type,
                    "name": result.name,
                    "manufacturer": result.manufacturer,
                    "model": result.model,
                    "serial_number": result.serial_number,
                    "description": result.description,
                    "status": result.status,
                    "updated_by": result.updated_by,
                    "updated_at": (
                        result.updated_at.isoformat()
                        if result.updated_at
                        else datetime.utcnow().isoformat()
                    ),
                },
                message="Device updated successfully",
            )
        else:
            return format_error_response(
                error_code="DEVICE_UPDATE_ERROR",
                message=result.error_message or "Failed to update device",
                details={"error": result.error_message, "device_id": device_id},
            )

    except Exception as e:
        logger.error(f"Failed to update device {device_id}: {str(e)}")
        return format_error_response(
            error_code="DEVICE_UPDATE_ERROR",
            message="Failed to update device",
            details={"error": str(e), "device_id": device_id},
        )


@router.delete(
    "/{device_id}",
    response_model=Dict[str, Any],
    summary="Delete device",
    description="Delete a device and all associated data.",
)
async def delete_device(
    device_id: str,
    user: User = Depends(require_write_permission),
    device_service=Depends(get_device_application_service),
) -> Dict[str, Any]:
    """Delete device by ID."""
    try:
        # Use application service to delete device
        result = device_service.delete_device(
            device_id=device_id, deleted_by=user.user_id
        )

        if result.success:
            return format_success_response(
                data={
                    "device_id": device_id,
                    "deleted_by": user.user_id,
                    "deleted_at": datetime.utcnow().isoformat(),
                },
                message="Device deleted successfully",
            )
        else:
            return format_error_response(
                error_code="DEVICE_DELETE_ERROR",
                message=result.error_message or "Failed to delete device",
                details={"error": result.error_message, "device_id": device_id},
            )

    except Exception as e:
        logger.error(f"Failed to delete device {device_id}: {str(e)}")
        return format_error_response(
            error_code="DEVICE_DELETE_ERROR",
            message="Failed to delete device",
            details={"error": str(e), "device_id": device_id},
        )


@router.get(
    "/{device_id}/statistics",
    response_model=Dict[str, Any],
    summary="Get device statistics",
    description="Retrieve statistics and metrics for a specific device.",
)
async def get_device_statistics(
    device_id: str,
    user: User = Depends(require_read_permission),
    device_service=Depends(get_device_application_service),
) -> Dict[str, Any]:
    """Get device statistics."""
    try:
        # Use application service to get device statistics
        result = device_service.get_device_statistics(device_id=device_id)

        if result.success:
            return format_success_response(
                data={
                    "device_id": device_id,
                    "statistics": {
                        "total_devices": result.total_devices,
                        "active_devices": result.active_devices,
                        "inactive_devices": result.inactive_devices,
                        "device_types": result.device_types,
                        "status_distribution": result.status_distribution,
                        "manufacturer_distribution": result.manufacturer_distribution,
                        "room_distribution": result.room_distribution,
                    },
                    "last_updated": datetime.utcnow().isoformat(),
                },
                message="Device statistics retrieved successfully",
            )
        else:
            return format_error_response(
                error_code="DEVICE_STATISTICS_ERROR",
                message=result.error_message or "Failed to retrieve device statistics",
                details={"error": result.error_message, "device_id": device_id},
            )

    except Exception as e:
        logger.error(f"Failed to get statistics for device {device_id}: {str(e)}")
        return format_error_response(
            error_code="DEVICE_STATISTICS_ERROR",
            message="Failed to retrieve device statistics",
            details={"error": str(e), "device_id": device_id},
        )
