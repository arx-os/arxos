"""
Floor Use Cases - Application Layer Business Logic

This module contains use cases for floor-related operations including
create, read, update, delete, and list operations. Use cases orchestrate
domain objects and repositories to implement business workflows.
"""

from typing import List, Optional
from datetime import datetime

from domain.entities import Floor
from domain.repositories import FloorRepository
from domain.value_objects import FloorId, FloorStatus
from domain.exceptions import (
    InvalidFloorError, FloorNotFoundError, DuplicateFloorError,
    InvalidStatusTransitionError
)
from application.dto.floor_dto import (
    CreateFloorRequest, CreateFloorResponse,
    UpdateFloorRequest, UpdateFloorResponse,
    GetFloorResponse, ListFloorsResponse,
    DeleteFloorResponse
)


class CreateFloorUseCase:
    """Use case for creating a new floor."""
    
    def __init__(self, floor_repository: FloorRepository):
    """
    Perform __init__ operation

Args:
        floor_repository: Description of floor_repository

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.floor_repository = floor_repository
    
    def execute(self, request: CreateFloorRequest) -> CreateFloorResponse:
        """Execute the create floor use case."""
        try:
            # Validate request
            if not request.floor_number or request.floor_number < 0:
                return CreateFloorResponse(
                    success=False,
                    error_message="Valid floor number is required"
                )
            
            # Create domain objects
            floor_id = FloorId()
            
            # Create floor entity
            floor = Floor(
                id=floor_id,
                building_id=request.building_id,
                floor_number=request.floor_number,
                description=request.description,
                created_by=request.created_by,
                metadata=request.metadata or {}
            )
            
            # Save to repository
            self.floor_repository.save(floor)
            
            # Return success response
            return CreateFloorResponse(
                success=True,
                floor_id=str(floor_id),
                message="Floor created successfully",
                created_at=datetime.utcnow()
            )
            
        except DuplicateFloorError as e:
            return CreateFloorResponse(
                success=False,
                error_message=f"Floor already exists: {str(e)}"
            )
        except InvalidFloorError as e:
            return CreateFloorResponse(
                success=False,
                error_message=f"Invalid floor data: {str(e)}"
            )
        except Exception as e:
            return CreateFloorResponse(
                success=False,
                error_message=f"Failed to create floor: {str(e)}"
            )


class UpdateFloorUseCase:
    """
    Perform __init__ operation

Args:
        floor_repository: Description of floor_repository

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
    """Use case for updating an existing floor."""
    
    def __init__(self, floor_repository: FloorRepository):
        self.floor_repository = floor_repository
    
    def execute(self, request: UpdateFloorRequest) -> UpdateFloorResponse:
        """Execute the update floor use case."""
        try:
            # Get existing floor
            floor_id = FloorId(request.floor_id)
            floor = self.floor_repository.get_by_id(floor_id)
            
            if not floor:
                return UpdateFloorResponse(
                    success=False,
                    error_message="Floor not found"
                )
            
            # Update floor fields
            if request.floor_number is not None:
                floor.floor_number = request.floor_number
            
            if request.description is not None:
                floor.description = request.description
            
            if request.status is not None:
                new_status = FloorStatus(request.status)
                floor.update_status(new_status, request.updated_by or "system")
            
            if request.metadata is not None:
                floor.metadata.update(request.metadata)
            
            # Save updated floor
            self.floor_repository.save(floor)
            
            # Return success response
            return UpdateFloorResponse(
                success=True,
                floor_id=str(floor_id),
                message="Floor updated successfully",
                updated_at=datetime.utcnow()
            )
            
        except FloorNotFoundError:
            return UpdateFloorResponse(
                success=False,
                error_message="Floor not found"
            )
        except InvalidStatusTransitionError as e:
            return UpdateFloorResponse(
                success=False,
                error_message=f"Invalid status transition: {str(e)}"
            )
        except InvalidFloorError as e:
            return UpdateFloorResponse(
                success=False,
                error_message=f"Invalid floor data: {str(e)}"
            )
        except Exception as e:
            return UpdateFloorResponse(
                success=False,
                error_message=f"Failed to update floor: {str(e)}"
            )


class GetFloorUseCase:
    """Use case for getting a floor by ID."""
    
    def __init__(self, floor_repository: FloorRepository):
        self.floor_repository = floor_repository
    
    def execute(self, floor_id: str) -> GetFloorResponse:
        """Execute the get floor use case."""
        try:
            # Get floor from repository
            floor = self.floor_repository.get_by_id(FloorId(floor_id))
            
            if not floor:
                return GetFloorResponse(
                    success=False,
                    error_message="Floor not found"
                )
            
            # Convert to dictionary for response
            floor_data = {
                'id': str(floor.id),
                'building_id': floor.building_id,
                'floor_number': floor.floor_number,
                'status': floor.status.value,
                'description': floor.description,
                'room_count': floor.room_count,
                'device_count': floor.device_count,
                'created_at': floor.created_at.isoformat(),
                'updated_at': floor.updated_at.isoformat(),
                'created_by': floor.created_by,
                'metadata': floor.metadata
            }
            
            return GetFloorResponse(
                success=True,
                floor=floor_data
            )
            
        except Exception as e:
            return GetFloorResponse(
                success=False,
                error_message=f"Failed to get floor: {str(e)}"
            )


class ListFloorsUseCase:
    """Use case for listing floors with pagination."""
    
    def __init__(self, floor_repository: FloorRepository):
        self.floor_repository = floor_repository
    
    def execute(self, building_id: str, page: int = 1, page_size: int = 10,
                status: Optional[str] = None) -> ListFloorsResponse:
        """Execute the list floors use case."""
        try:
            # Get floors from repository
            floors = self.floor_repository.get_by_building_id(building_id)
            
            # Filter by status if provided
            if status:
                status_enum = FloorStatus(status)
                floors = [f for f in floors if f.status == status_enum]
            
            # Calculate pagination
            total_count = len(floors)
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_floors = floors[start_index:end_index]
            
            # Convert to list of dictionaries
            floors_data = []
            for floor in paginated_floors:
                floor_data = {
                    'id': str(floor.id),
                    'building_id': floor.building_id,
                    'floor_number': floor.floor_number,
                    'status': floor.status.value,
                    'room_count': floor.room_count,
                    'device_count': floor.device_count,
                    'created_at': floor.created_at.isoformat(),
                    'updated_at': floor.updated_at.isoformat()
                }
                floors_data.append(floor_data)
            
            return ListFloorsResponse(
                success=True,
                floors=floors_data,
                total_count=total_count,
                page=page,
                page_size=page_size
            )
            
        except Exception as e:
            return ListFloorsResponse(
                success=False,
                error_message=f"Failed to list floors: {str(e)}"
            )


class DeleteFloorUseCase:
    """Use case for deleting a floor."""
    
    def __init__(self, floor_repository: FloorRepository):
        self.floor_repository = floor_repository
    
    def execute(self, floor_id: str) -> DeleteFloorResponse:
        """Execute the delete floor use case."""
        try:
            # Check if floor exists
            floor = self.floor_repository.get_by_id(FloorId(floor_id))
            
            if not floor:
                return DeleteFloorResponse(
                    success=False,
                    error_message="Floor not found"
                )
            
            # Delete floor
            self.floor_repository.delete(FloorId(floor_id))
            
            return DeleteFloorResponse(
                success=True,
                floor_id=floor_id,
                message="Floor deleted successfully",
                deleted_at=datetime.utcnow()
            )
            
        except FloorNotFoundError:
            return DeleteFloorResponse(
                success=False,
                error_message="Floor not found"
            )
        except Exception as e:
            return DeleteFloorResponse(
                success=False,
                error_message=f"Failed to delete floor: {str(e)}"
            ) 