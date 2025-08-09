"""
Room Use Cases - Application Layer Business Logic

This module contains use cases for room-related operations including
create, read, update, delete, and list operations. Use cases orchestrate
domain objects and repositories to implement business workflows.
"""

from typing import List, Optional
from datetime import datetime

from domain.entities import Room
from domain.repositories import RoomRepository
from domain.value_objects import RoomId, FloorId, RoomStatus, Dimensions
from domain.exceptions import (
    InvalidRoomError, RoomNotFoundError, DuplicateRoomError,
    InvalidStatusTransitionError
)
from application.dto.room_dto import (
    CreateRoomRequest, CreateRoomResponse,
    UpdateRoomRequest, UpdateRoomResponse,
    GetRoomResponse, ListRoomsResponse,
    DeleteRoomResponse
)


class CreateRoomUseCase:
    """Use case for creating a new room."""

    def __init__(self, room_repository: RoomRepository):
    """
    Perform __init__ operation

Args:
        room_repository: Description of room_repository

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.room_repository = room_repository

    def execute(self, request: CreateRoomRequest) -> CreateRoomResponse:
        """Execute the create room use case."""
        try:
            # Validate request
            if not request.name or len(request.name.strip()) == 0:
                return CreateRoomResponse(
                    success=False,
                    error_message="Room name is required"
                )

            if not request.room_number or len(request.room_number.strip()) == 0:
                return CreateRoomResponse(
                    success=False,
                    error_message="Room number is required"
                )

            if not request.floor_id or len(request.floor_id.strip()) == 0:
                return CreateRoomResponse(
                    success=False,
                    error_message="Floor ID is required"
                )

            # Create domain objects
            room_id = RoomId()
            floor_id = FloorId(request.floor_id)

            # Create dimensions if provided
            dimensions = None
            if request.dimensions:
                dimensions = Dimensions(
                    width=request.dimensions.get('width', 0.0),
                    length=request.dimensions.get('length', 0.0),
                    height=request.dimensions.get('height', 0.0)
            # Create room entity
            room = Room(
                id=room_id,
                floor_id=floor_id,
                room_number=request.room_number.strip(),
                name=request.name.strip(),
                room_type=request.room_type or "general",
                dimensions=dimensions,
                description=request.description,
                created_by=request.created_by,
                metadata=request.metadata or {}
            )

            # Save to repository
            self.room_repository.save(room)

            # Return success response
            return CreateRoomResponse(
                success=True,
                room_id=str(room_id),
                message="Room created successfully",
                created_at=datetime.utcnow()
        except DuplicateRoomError as e:
            return CreateRoomResponse(
                success=False,
                error_message=f"Room already exists: {str(e)}"
            )
        except InvalidRoomError as e:
            return CreateRoomResponse(
                success=False,
                error_message=f"Invalid room data: {str(e)}"
            )
        except Exception as e:
            return CreateRoomResponse(
                success=False,
                error_message=f"Failed to create room: {str(e)}"
            )


class UpdateRoomUseCase:
    """
    Perform __init__ operation

Args:
        room_repository: Description of room_repository

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
    """Use case for updating a room."""

    def __init__(self, room_repository: RoomRepository):
        self.room_repository = room_repository

    def execute(self, request: UpdateRoomRequest) -> UpdateRoomResponse:
        """Execute the update room use case."""
        try:
            # Validate request
            if not request.room_id or len(request.room_id.strip()) == 0:
                return UpdateRoomResponse(
                    success=False,
                    error_message="Room ID is required"
                )

            # Get existing room
            room_id = RoomId(request.room_id)
            room = self.room_repository.get_by_id(room_id)

            if not room:
                return UpdateRoomResponse(
                    success=False,
                    error_message="Room not found"
                )

            # Update room fields
            if request.name is not None:
                room.update_name(request.name, request.updated_by or "system")

            if request.room_number is not None:
                if len(request.room_number.strip()) == 0:
                    return UpdateRoomResponse(
                        success=False,
                        error_message="Room number cannot be empty"
                    )
                room.room_number = request.room_number.strip()
                room.updated_at = datetime.utcnow()

            if request.room_type is not None:
                room.room_type = request.room_type
                room.updated_at = datetime.utcnow()

            if request.description is not None:
                room.description = request.description
                room.updated_at = datetime.utcnow()

            if request.dimensions is not None:
                room.dimensions = Dimensions(
                    width=request.dimensions.get('width', 0.0),
                    length=request.dimensions.get('length', 0.0),
                    height=request.dimensions.get('height', 0.0)
                room.updated_at = datetime.utcnow()

            if request.status is not None:
                try:
                    new_status = RoomStatus(request.status)
                    room.update_status(new_status, request.updated_by or "system")
                except ValueError:
                    return UpdateRoomResponse(
                        success=False,
                        error_message=f"Invalid room status: {request.status}"
                    )

            if request.metadata is not None:
                room.metadata.update(request.metadata)
                room.updated_at = datetime.utcnow()

            # Save to repository
            self.room_repository.save(room)

            # Return success response
            return UpdateRoomResponse(
                success=True,
                room_id=str(room_id),
                message="Room updated successfully",
                updated_at=datetime.utcnow()
        except InvalidRoomError as e:
            return UpdateRoomResponse(
                success=False,
                error_message=f"Invalid room data: {str(e)}"
            )
        except InvalidStatusTransitionError as e:
            return UpdateRoomResponse(
                success=False,
                error_message=f"Invalid status transition: {str(e)}"
            )
        except Exception as e:
            return UpdateRoomResponse(
                success=False,
                error_message=f"Failed to update room: {str(e)}"
            )


class GetRoomUseCase:
    """Use case for getting a room by ID."""

    def __init__(self, room_repository: RoomRepository):
        self.room_repository = room_repository

    def execute(self, room_id: str) -> GetRoomResponse:
        """Execute the get room use case."""
        try:
            # Validate request
            if not room_id or len(room_id.strip()) == 0:
                return GetRoomResponse(
                    success=False,
                    error_message="Room ID is required"
                )

            # Get room from repository import repository
            room = self.room_repository.get_by_id(RoomId(room_id)
            if not room:
                return GetRoomResponse(
                    success=False,
                    error_message="Room not found"
                )

            # Convert to dictionary
            room_dict = {
                "id": str(room.id),
                "floor_id": str(room.floor_id),
                "room_number": room.room_number,
                "name": room.name,
                "room_type": room.room_type,
                "status": room.status.value,
                "description": room.description,
                "created_at": room.created_at.isoformat(),
                "updated_at": room.updated_at.isoformat(),
                "created_by": room.created_by,
                "metadata": room.metadata
            }

            # Add dimensions if available
            if room.dimensions:
                room_dict["dimensions"] = {
                    "width": room.dimensions.width,
                    "length": room.dimensions.length,
                    "height": room.dimensions.height,
                    "area": room.dimensions.area,
                    "volume": room.dimensions.volume
                }

            return GetRoomResponse(
                success=True,
                room=room_dict
            )

        except Exception as e:
            return GetRoomResponse(
                success=False,
                error_message=f"Failed to get room: {str(e)}"
            )


class ListRoomsUseCase:
    """Use case for listing rooms."""

    def __init__(self, room_repository: RoomRepository):
        self.room_repository = room_repository

    def execute(self, floor_id: Optional[str] = None, building_id: Optional[str] = None,
                status: Optional[str] = None, page: int = 1, page_size: int = 10) -> ListRoomsResponse:
        """Execute the list rooms use case."""
        try:
            # Validate pagination parameters
            if page < 1:
                page = 1
            if page_size < 1 or page_size > 100:
                page_size = 10

            # Get rooms from repository import repository
            rooms = []

            if floor_id:
                # Get rooms by floor
                rooms = self.room_repository.get_by_floor_id(FloorId(floor_id)
            elif building_id:
                # Get rooms by building
                from domain.value_objects import BuildingId
                rooms = self.room_repository.get_by_building_id(BuildingId(building_id)
            elif status:
                # Get rooms by status
                try:
                    room_status = RoomStatus(status)
                    rooms = self.room_repository.get_by_status(room_status)
                except ValueError:
                    return ListRoomsResponse(
                        success=False,
                        error_message=f"Invalid room status: {status}"
                    )
            else:
                # Get all rooms (this would need to be implemented in repository)
                # For now, return empty list
                rooms = []

            # Apply pagination
            total_count = len(rooms)
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_rooms = rooms[start_index:end_index]

            # Convert to dictionaries
            room_dicts = []
            for room in paginated_rooms:
                room_dict = {
                    "id": str(room.id),
                    "floor_id": str(room.floor_id),
                    "room_number": room.room_number,
                    "name": room.name,
                    "room_type": room.room_type,
                    "status": room.status.value,
                    "description": room.description,
                    "created_at": room.created_at.isoformat(),
                    "updated_at": room.updated_at.isoformat(),
                    "created_by": room.created_by
                }

                # Add dimensions if available
                if room.dimensions:
                    room_dict["dimensions"] = {
                        "width": room.dimensions.width,
                        "length": room.dimensions.length,
                        "height": room.dimensions.height,
                        "area": room.dimensions.area,
                        "volume": room.dimensions.volume
                    }

                room_dicts.append(room_dict)

            return ListRoomsResponse(
                success=True,
                rooms=room_dicts,
                total_count=total_count,
                page=page,
                page_size=page_size
            )

        except Exception as e:
            return ListRoomsResponse(
                success=False,
                error_message=f"Failed to list rooms: {str(e)}"
            )


class DeleteRoomUseCase:
    """Use case for deleting a room."""

    def __init__(self, room_repository: RoomRepository):
        self.room_repository = room_repository

    def execute(self, room_id: str) -> DeleteRoomResponse:
        """Execute the delete room use case."""
        try:
            # Validate request
            if not room_id or len(room_id.strip()) == 0:
                return DeleteRoomResponse(
                    success=False,
                    error_message="Room ID is required"
                )

            # Check if room exists
            room = self.room_repository.get_by_id(RoomId(room_id)
            if not room:
                return DeleteRoomResponse(
                    success=False,
                    error_message="Room not found"
                )

            # Delete from repository import repository
            self.room_repository.delete(RoomId(room_id)
            return DeleteRoomResponse(
                success=True,
                room_id=room_id,
                message="Room deleted successfully",
                deleted_at=datetime.utcnow()
        except Exception as e:
            return DeleteRoomResponse(
                success=False,
                error_message=f"Failed to delete room: {str(e)}"
            )
