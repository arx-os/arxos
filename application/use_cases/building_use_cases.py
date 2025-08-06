"""
Building Use Cases - Application Layer Business Logic

This module contains use cases for building-related operations including
create, read, update, delete, and list operations. Use cases orchestrate
domain objects and repositories to implement business workflows.
"""

from typing import List, Optional
from datetime import datetime

from domain.entities import Building
from domain.repositories import UnitOfWork
from domain.value_objects import (
    BuildingId,
    Address,
    BuildingStatus,
    Coordinates,
    Dimensions,
)
from domain.exceptions import (
    InvalidBuildingError,
    BuildingNotFoundError,
    DuplicateBuildingError,
    InvalidStatusTransitionError,
)
from application.dto.building_dto import (
    CreateBuildingRequest,
    CreateBuildingResponse,
    UpdateBuildingRequest,
    UpdateBuildingResponse,
    GetBuildingResponse,
    ListBuildingsResponse,
    DeleteBuildingResponse,
)


class CreateBuildingUseCase:
    """Use case for creating a new building."""

    def __init__(self, unit_of_work: UnitOfWork):
        self.unit_of_work = unit_of_work

    def execute(self, request: CreateBuildingRequest) -> CreateBuildingResponse:
        """Execute the create building use case."""
        try:
            # Validate request
            if not request.name or len(request.name.strip()) == 0:
                return CreateBuildingResponse(
                    success=False, error_message="Building name is required"
                )

            if not request.address or len(request.address.strip()) == 0:
                return CreateBuildingResponse(
                    success=False, error_message="Building address is required"
                )

            # Create domain objects
            building_id = BuildingId()
            address = Address.from_string(request.address)

            # Create coordinates if provided
            coordinates = None
            if request.coordinates:
                coordinates = Coordinates(
                    latitude=request.coordinates.get("latitude", 0.0),
                    longitude=request.coordinates.get("longitude", 0.0),
                )

            # Create dimensions if provided
            dimensions = None
            if request.dimensions:
                dimensions = Dimensions(
                    width=request.dimensions.get("width", 0.0),
                    length=request.dimensions.get("length", 0.0),
                    height=request.dimensions.get("height", 0.0),
                )

            # Create building entity
            building = Building(
                id=building_id,
                name=request.name.strip(),
                address=address,
                coordinates=coordinates,
                dimensions=dimensions,
                description=request.description,
                created_by=request.created_by,
                metadata=request.metadata or {},
            )

            # Save to repository using UnitOfWork
            self.unit_of_work.buildings.save(building)

            # Return success response
            return CreateBuildingResponse(
                success=True,
                building_id=str(building_id),
                message="Building created successfully",
                created_at=datetime.utcnow(),
            )

        except DuplicateBuildingError as e:
            return CreateBuildingResponse(
                success=False, error_message=f"Building already exists: {str(e)}"
            )
        except InvalidBuildingError as e:
            return CreateBuildingResponse(
                success=False, error_message=f"Invalid building data: {str(e)}"
            )
        except Exception as e:
            return CreateBuildingResponse(
                success=False, error_message=f"Failed to create building: {str(e)}"
            )


class UpdateBuildingUseCase:
    """Use case for updating an existing building."""

    def __init__(self, unit_of_work: UnitOfWork):
        self.unit_of_work = unit_of_work

    def execute(self, request: UpdateBuildingRequest) -> UpdateBuildingResponse:
        """Execute the update building use case."""
        try:
            # Get existing building
            building_id = BuildingId(request.building_id)
            building = self.unit_of_work.buildings.get_by_id(building_id)

            if not building:
                return UpdateBuildingResponse(
                    success=False, error_message="Building not found"
                )

            # Update fields if provided
            if request.name is not None:
                building.update_name(request.name, request.updated_by or "system")

            if request.address is not None:
                address = Address.from_string(request.address)
                # Note: Address update would need to be implemented in the Building entity
                # For now, we'll just update the address field
                building.address = address
                building.updated_at = datetime.utcnow()
                building.updated_by = request.updated_by or "system"

            if request.description is not None:
                building.description = request.description
                building.updated_at = datetime.utcnow()
                building.updated_by = request.updated_by or "system"

            if request.status is not None:
                try:
                    new_status = BuildingStatus(request.status)
                    building.update_status(new_status, request.updated_by or "system")
                except ValueError:
                    return UpdateBuildingResponse(
                        success=False, error_message=f"Invalid status: {request.status}"
                    )

            if request.coordinates is not None:
                coordinates = Coordinates(
                    latitude=request.coordinates.get("latitude", 0.0),
                    longitude=request.coordinates.get("longitude", 0.0),
                )
                building.coordinates = coordinates
                building.updated_at = datetime.utcnow()
                building.updated_by = request.updated_by or "system"

            if request.dimensions is not None:
                dimensions = Dimensions(
                    width=request.dimensions.get("width", 0.0),
                    length=request.dimensions.get("length", 0.0),
                    height=request.dimensions.get("height", 0.0),
                )
                building.dimensions = dimensions
                building.updated_at = datetime.utcnow()
                building.updated_by = request.updated_by or "system"

            if request.metadata is not None:
                building.metadata.update(request.metadata)
                building.updated_at = datetime.utcnow()
                building.updated_by = request.updated_by or "system"

            # Save updated building
            self.unit_of_work.buildings.save(building)

            return UpdateBuildingResponse(
                success=True,
                building_id=request.building_id,
                message="Building updated successfully",
                updated_at=datetime.utcnow(),
            )

        except BuildingNotFoundError as e:
            return UpdateBuildingResponse(
                success=False, error_message=f"Building not found: {str(e)}"
            )
        except InvalidStatusTransitionError as e:
            return UpdateBuildingResponse(
                success=False, error_message=f"Invalid status transition: {str(e)}"
            )
        except Exception as e:
            return UpdateBuildingResponse(
                success=False, error_message=f"Failed to update building: {str(e)}"
            )


class GetBuildingUseCase:
    """Use case for getting a building by ID."""

    def __init__(self, unit_of_work: UnitOfWork):
        self.unit_of_work = unit_of_work

    def execute(self, building_id: str) -> GetBuildingResponse:
        """Execute the get building use case."""
        try:
            building = self.unit_of_work.buildings.get_by_id(BuildingId(building_id))

            if not building:
                return GetBuildingResponse(
                    success=False, error_message="Building not found"
                )

            # Convert building to dictionary for response
            building_data = {
                "id": str(building.id),
                "name": building.name,
                "address": str(building.address),
                "status": building.status.value,
                "description": building.description,
                "created_at": (
                    building.created_at.isoformat() if building.created_at else None
                ),
                "updated_at": (
                    building.updated_at.isoformat() if building.updated_at else None
                ),
                "created_by": building.created_by,
                "updated_by": building.updated_by,
                "metadata": building.metadata,
            }

            if building.coordinates:
                building_data["coordinates"] = {
                    "latitude": building.coordinates.latitude,
                    "longitude": building.coordinates.longitude,
                }

            if building.dimensions:
                building_data["dimensions"] = {
                    "width": building.dimensions.width,
                    "length": building.dimensions.length,
                    "height": building.dimensions.height,
                    "unit": building.dimensions.unit,
                }

            return GetBuildingResponse(success=True, building=building_data)

        except Exception as e:
            return GetBuildingResponse(
                success=False, error_message=f"Failed to get building: {str(e)}"
            )


class ListBuildingsUseCase:
    """Use case for listing buildings with pagination and filtering."""

    def __init__(self, unit_of_work: UnitOfWork):
        self.unit_of_work = unit_of_work

    def execute(
        self, page: int = 1, page_size: int = 10, status: Optional[str] = None
    ) -> ListBuildingsResponse:
        """Execute the list buildings use case."""
        try:
            # Calculate offset for pagination
            offset = (page - 1) * page_size

            # Get buildings based on filters
            if status:
                try:
                    building_status = BuildingStatus(status)
                    buildings = self.unit_of_work.buildings.get_by_status(
                        building_status
                    )
                except ValueError:
                    return ListBuildingsResponse(
                        success=False, error_message=f"Invalid status: {status}"
                    )
            else:
                buildings = self.unit_of_work.buildings.get_all()

            # Apply pagination
            total_count = len(buildings)
            paginated_buildings = buildings[offset : offset + page_size]

            # Convert buildings to dictionaries
            building_list = []
            for building in paginated_buildings:
                building_data = {
                    "id": str(building.id),
                    "name": building.name,
                    "address": str(building.address),
                    "status": building.status.value,
                    "description": building.description,
                    "created_at": (
                        building.created_at.isoformat() if building.created_at else None
                    ),
                    "updated_at": (
                        building.updated_at.isoformat() if building.updated_at else None
                    ),
                    "created_by": building.created_by,
                    "updated_by": building.updated_by,
                }

                if building.coordinates:
                    building_data["coordinates"] = {
                        "latitude": building.coordinates.latitude,
                        "longitude": building.coordinates.longitude,
                    }

                if building.dimensions:
                    building_data["dimensions"] = {
                        "width": building.dimensions.width,
                        "length": building.dimensions.length,
                        "height": building.dimensions.height,
                        "unit": building.dimensions.unit,
                    }

                building_list.append(building_data)

            return ListBuildingsResponse(
                success=True,
                buildings=building_list,
                total_count=total_count,
                page=page,
                page_size=page_size,
            )

        except Exception as e:
            return ListBuildingsResponse(
                success=False, error_message=f"Failed to list buildings: {str(e)}"
            )


class DeleteBuildingUseCase:
    """Use case for deleting a building."""

    def __init__(self, unit_of_work: UnitOfWork):
        self.unit_of_work = unit_of_work

    def execute(self, building_id: str) -> DeleteBuildingResponse:
        """Execute the delete building use case."""
        try:
            # Check if building exists
            building = self.unit_of_work.buildings.get_by_id(BuildingId(building_id))

            if not building:
                return DeleteBuildingResponse(
                    success=False, error_message="Building not found"
                )

            # Delete building
            self.unit_of_work.buildings.delete(BuildingId(building_id))

            return DeleteBuildingResponse(
                success=True,
                building_id=building_id,
                message="Building deleted successfully",
                deleted_at=datetime.utcnow(),
            )

        except BuildingNotFoundError as e:
            return DeleteBuildingResponse(
                success=False, error_message=f"Building not found: {str(e)}"
            )
        except Exception as e:
            return DeleteBuildingResponse(
                success=False, error_message=f"Failed to delete building: {str(e)}"
            )
