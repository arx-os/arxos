"""
Device Use Cases - Application Layer Business Logic

This module contains use cases for device-related operations including
create, read, update, delete, and list operations. Use cases orchestrate
domain objects and repositories to implement business workflows.
"""

from typing import List, Optional
from datetime import datetime

from domain.entities import Device
from domain.repositories import DeviceRepository
from domain.value_objects import DeviceId, RoomId, DeviceStatus
from domain.exceptions import (
    InvalidDeviceError, DeviceNotFoundError, DuplicateDeviceError,
    InvalidStatusTransitionError
)
from application.dto.device_dto import (
    CreateDeviceRequest, CreateDeviceResponse,
    UpdateDeviceRequest, UpdateDeviceResponse,
    GetDeviceResponse, ListDevicesResponse,
    DeleteDeviceResponse
)


class CreateDeviceUseCase:
    """Use case for creating a new device."""
    
    def __init__(self, device_repository: DeviceRepository):
    """
    Perform __init__ operation

Args:
        device_repository: Description of device_repository

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.device_repository = device_repository
    
    def execute(self, request: CreateDeviceRequest) -> CreateDeviceResponse:
        """Execute the create device use case."""
        try:
            # Validate request
            if not request.name or len(request.name.strip()) == 0:
                return CreateDeviceResponse(
                    success=False,
                    error_message="Device name is required"
                )
            
            if not request.device_type or len(request.device_type.strip()) == 0:
                return CreateDeviceResponse(
                    success=False,
                    error_message="Device type is required"
                )
            
            if not request.room_id or len(request.room_id.strip()) == 0:
                return CreateDeviceResponse(
                    success=False,
                    error_message="Room ID is required"
                )
            
            # Create domain objects
            device_id = DeviceId()
            room_id = RoomId(request.room_id)
            
            # Create device entity
            device = Device(
                id=device_id,
                room_id=room_id,
                device_id=f"DEV_{device_id.value[:8]}",  # Generate device ID
                device_type=request.device_type.strip(),
                name=request.name.strip(),
                manufacturer=request.manufacturer,
                model=request.model,
                serial_number=request.serial_number,
                description=request.description,
                created_by=request.created_by,
                metadata=request.metadata or {}
            )
            
            # Save to repository
            self.device_repository.save(device)
            
            # Return success response
            return CreateDeviceResponse(
                success=True,
                device_id=str(device_id),
                message="Device created successfully",
                created_at=datetime.utcnow()
            )
            
        except DuplicateDeviceError as e:
            return CreateDeviceResponse(
                success=False,
                error_message=f"Device already exists: {str(e)}"
            )
        except InvalidDeviceError as e:
            return CreateDeviceResponse(
                success=False,
                error_message=f"Invalid device data: {str(e)}"
            )
        except Exception as e:
            return CreateDeviceResponse(
                success=False,
                error_message=f"Failed to create device: {str(e)}"
            )


class UpdateDeviceUseCase:
    """
    Perform __init__ operation

Args:
        device_repository: Description of device_repository

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
    """Use case for updating a device."""
    
    def __init__(self, device_repository: DeviceRepository):
        self.device_repository = device_repository
    
    def execute(self, request: UpdateDeviceRequest) -> UpdateDeviceResponse:
        """Execute the update device use case."""
        try:
            # Validate request
            if not request.device_id or len(request.device_id.strip()) == 0:
                return UpdateDeviceResponse(
                    success=False,
                    error_message="Device ID is required"
                )
            
            # Get existing device
            device_id = DeviceId(request.device_id)
            device = self.device_repository.get_by_id(device_id)
            
            if not device:
                return UpdateDeviceResponse(
                    success=False,
                    error_message="Device not found"
                )
            
            # Update device fields
            if request.name is not None:
                device.update_name(request.name, request.updated_by or "system")
            
            if request.device_type is not None:
                if len(request.device_type.strip()) == 0:
                    return UpdateDeviceResponse(
                        success=False,
                        error_message="Device type cannot be empty"
                    )
                device.device_type = request.device_type.strip()
                device.updated_at = datetime.utcnow()
            
            if request.manufacturer is not None:
                device.manufacturer = request.manufacturer
                device.updated_at = datetime.utcnow()
            
            if request.model is not None:
                device.model = request.model
                device.updated_at = datetime.utcnow()
            
            if request.serial_number is not None:
                device.serial_number = request.serial_number
                device.updated_at = datetime.utcnow()
            
            if request.description is not None:
                device.description = request.description
                device.updated_at = datetime.utcnow()
            
            if request.status is not None:
                try:
                    new_status = DeviceStatus(request.status)
                    device.update_status(new_status, request.updated_by or "system")
                except ValueError:
                    return UpdateDeviceResponse(
                        success=False,
                        error_message=f"Invalid device status: {request.status}"
                    )
            
            if request.metadata is not None:
                device.metadata.update(request.metadata)
                device.updated_at = datetime.utcnow()
            
            # Save to repository
            self.device_repository.save(device)
            
            # Return success response
            return UpdateDeviceResponse(
                success=True,
                device_id=str(device_id),
                message="Device updated successfully",
                updated_at=datetime.utcnow()
            )
            
        except InvalidDeviceError as e:
            return UpdateDeviceResponse(
                success=False,
                error_message=f"Invalid device data: {str(e)}"
            )
        except InvalidStatusTransitionError as e:
            return UpdateDeviceResponse(
                success=False,
                error_message=f"Invalid status transition: {str(e)}"
            )
        except Exception as e:
            return UpdateDeviceResponse(
                success=False,
                error_message=f"Failed to update device: {str(e)}"
            )


class GetDeviceUseCase:
    """Use case for getting a device by ID."""
    
    def __init__(self, device_repository: DeviceRepository):
        self.device_repository = device_repository
    
    def execute(self, device_id: str) -> GetDeviceResponse:
        """Execute the get device use case."""
        try:
            # Validate request
            if not device_id or len(device_id.strip()) == 0:
                return GetDeviceResponse(
                    success=False,
                    error_message="Device ID is required"
                )
            
            # Get device from repository
            device = self.device_repository.get_by_id(DeviceId(device_id))
            
            if not device:
                return GetDeviceResponse(
                    success=False,
                    error_message="Device not found"
                )
            
            # Convert to dictionary
            device_dict = {
                "id": str(device.id),
                "room_id": str(device.room_id),
                "device_id": device.device_id,
                "name": device.name,
                "device_type": device.device_type,
                "status": device.status.value,
                "manufacturer": device.manufacturer,
                "model": device.model,
                "serial_number": device.serial_number,
                "description": device.description,
                "created_at": device.created_at.isoformat(),
                "updated_at": device.updated_at.isoformat(),
                "created_by": device.created_by,
                "metadata": device.metadata
            }
            
            return GetDeviceResponse(
                success=True,
                device=device_dict
            )
            
        except Exception as e:
            return GetDeviceResponse(
                success=False,
                error_message=f"Failed to get device: {str(e)}"
            )


class ListDevicesUseCase:
    """Use case for listing devices."""
    
    def __init__(self, device_repository: DeviceRepository):
        self.device_repository = device_repository
    
    def execute(self, room_id: Optional[str] = None, device_type: Optional[str] = None,
                status: Optional[str] = None, page: int = 1, page_size: int = 10) -> ListDevicesResponse:
        """Execute the list devices use case."""
        try:
            # Validate pagination parameters
            if page < 1:
                page = 1
            if page_size < 1 or page_size > 100:
                page_size = 10
            
            # Get devices from repository
            devices = []
            
            if room_id:
                # Get devices by room
                devices = self.device_repository.get_by_room_id(RoomId(room_id))
            elif device_type:
                # Get devices by type
                devices = self.device_repository.get_by_type(device_type)
            elif status:
                # Get devices by status
                try:
                    device_status = DeviceStatus(status)
                    devices = self.device_repository.get_by_status(device_status)
                except ValueError:
                    return ListDevicesResponse(
                        success=False,
                        error_message=f"Invalid device status: {status}"
                    )
            else:
                # Get all devices (this would need to be implemented in repository)
                # For now, return empty list
                devices = []
            
            # Apply pagination
            total_count = len(devices)
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_devices = devices[start_index:end_index]
            
            # Convert to dictionaries
            device_dicts = []
            for device in paginated_devices:
                device_dict = {
                    "id": str(device.id),
                    "room_id": str(device.room_id),
                    "device_id": device.device_id,
                    "name": device.name,
                    "device_type": device.device_type,
                    "status": device.status.value,
                    "manufacturer": device.manufacturer,
                    "model": device.model,
                    "serial_number": device.serial_number,
                    "description": device.description,
                    "created_at": device.created_at.isoformat(),
                    "updated_at": device.updated_at.isoformat(),
                    "created_by": device.created_by
                }
                device_dicts.append(device_dict)
            
            return ListDevicesResponse(
                success=True,
                devices=device_dicts,
                total_count=total_count,
                page=page,
                page_size=page_size
            )
            
        except Exception as e:
            return ListDevicesResponse(
                success=False,
                error_message=f"Failed to list devices: {str(e)}"
            )


class DeleteDeviceUseCase:
    """Use case for deleting a device."""
    
    def __init__(self, device_repository: DeviceRepository):
        self.device_repository = device_repository
    
    def execute(self, device_id: str) -> DeleteDeviceResponse:
        """Execute the delete device use case."""
        try:
            # Validate request
            if not device_id or len(device_id.strip()) == 0:
                return DeleteDeviceResponse(
                    success=False,
                    error_message="Device ID is required"
                )
            
            # Check if device exists
            device = self.device_repository.get_by_id(DeviceId(device_id))
            
            if not device:
                return DeleteDeviceResponse(
                    success=False,
                    error_message="Device not found"
                )
            
            # Delete from repository
            self.device_repository.delete(DeviceId(device_id))
            
            return DeleteDeviceResponse(
                success=True,
                device_id=device_id,
                message="Device deleted successfully",
                deleted_at=datetime.utcnow()
            )
            
        except Exception as e:
            return DeleteDeviceResponse(
                success=False,
                error_message=f"Failed to delete device: {str(e)}"
            ) 