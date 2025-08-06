"""
Building API Endpoints

This module provides REST API endpoints for building operations,
following Clean Architecture principles with dependency injection of use cases.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging

from svgx_engine.application.use_cases.building_use_cases import (
    CreateBuildingUseCase,
    UpdateBuildingUseCase,
    GetBuildingUseCase,
    ListBuildingsUseCase,
    DeleteBuildingUseCase,
)
from svgx_engine.application.dto.building_dto import (
    BuildingDTO,
    CreateBuildingRequest,
    UpdateBuildingRequest,
    BuildingListResponse,
    BuildingSearchRequest,
)
from svgx_engine.infrastructure.container import Container
from svgx_engine.utils.errors import ResourceNotFoundError, ValidationError

logger = logging.getLogger(__name__)

router = APIRouter()


def get_container() -> Container:
    """Get the dependency injection container."""
    from fastapi import Request

    request = Request()
    return request.app.state.container


def get_create_use_case(
    container: Container = Depends(get_container),
) -> CreateBuildingUseCase:
    """Get the create building use case."""
    return container.get("create_building_use_case")


def get_update_use_case(
    container: Container = Depends(get_container),
) -> UpdateBuildingUseCase:
    """Get the update building use case."""
    return container.get("update_building_use_case")


def get_get_use_case(
    container: Container = Depends(get_container),
) -> GetBuildingUseCase:
    """Get the get building use case."""
    return container.get("get_building_use_case")


def get_list_use_case(
    container: Container = Depends(get_container),
) -> ListBuildingsUseCase:
    """Get the list buildings use case."""
    return container.get("list_buildings_use_case")


def get_delete_use_case(
    container: Container = Depends(get_container),
) -> DeleteBuildingUseCase:
    """Get the delete building use case."""
    return container.get("delete_building_use_case")


@router.post("/", response_model=BuildingDTO, status_code=201)
async def create_building(
    request: CreateBuildingRequest,
    use_case: CreateBuildingUseCase = Depends(get_create_use_case),
):
    """
    Create a new building.

    Args:
        request: Building creation request
        use_case: Create building use case

    Returns:
        Created building DTO

    Raises:
        HTTPException: If creation fails
    """
    try:
        logger.info(f"Creating building: {request.name}")
        result = use_case.execute(request)
        logger.info(f"Building created successfully: {result.id}")
        return result
    except ValidationError as e:
        logger.warning(f"Validation error creating building: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating building: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{building_id}", response_model=BuildingDTO)
async def get_building(
    building_id: str, use_case: GetBuildingUseCase = Depends(get_get_use_case)
):
    """
    Get a building by ID.

    Args:
        building_id: Building identifier
        use_case: Get building use case

    Returns:
        Building DTO

    Raises:
        HTTPException: If building not found
    """
    try:
        logger.info(f"Getting building: {building_id}")
        result = use_case.execute(building_id)
        return result
    except ResourceNotFoundError as e:
        logger.warning(f"Building not found: {building_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting building: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=BuildingListResponse)
async def list_buildings(
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of buildings to return"
    ),
    offset: int = Query(0, ge=0, description="Number of buildings to skip"),
    name: Optional[str] = Query(None, description="Filter by building name"),
    building_type: Optional[str] = Query(None, description="Filter by building type"),
    city: Optional[str] = Query(None, description="Filter by city"),
    use_case: ListBuildingsUseCase = Depends(get_list_use_case),
):
    """
    List buildings with optional filtering and pagination.

    Args:
        limit: Maximum number of buildings to return
        offset: Number of buildings to skip
        name: Filter by building name
        building_type: Filter by building type
        city: Filter by city
        use_case: List buildings use case

    Returns:
        List of building DTOs with pagination info
    """
    try:
        logger.info(
            f"Listing buildings with filters: name={name}, type={building_type}, city={city}"
        )

        # Build search criteria
        criteria = {}
        if name:
            criteria["name"] = name
        if building_type:
            criteria["building_type"] = building_type
        if city:
            criteria["city"] = city

        result = use_case.execute(limit=limit, offset=offset, criteria=criteria)
        return result
    except Exception as e:
        logger.error(f"Error listing buildings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{building_id}", response_model=BuildingDTO)
async def update_building(
    building_id: str,
    request: UpdateBuildingRequest,
    use_case: UpdateBuildingUseCase = Depends(get_update_use_case),
):
    """
    Update a building.

    Args:
        building_id: Building identifier
        request: Building update request
        use_case: Update building use case

    Returns:
        Updated building DTO

    Raises:
        HTTPException: If building not found or update fails
    """
    try:
        logger.info(f"Updating building: {building_id}")
        result = use_case.execute(building_id, request)
        logger.info(f"Building updated successfully: {building_id}")
        return result
    except ResourceNotFoundError as e:
        logger.warning(f"Building not found for update: {building_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        logger.warning(f"Validation error updating building: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating building: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{building_id}", status_code=204)
async def delete_building(
    building_id: str, use_case: DeleteBuildingUseCase = Depends(get_delete_use_case)
):
    """
    Delete a building.

    Args:
        building_id: Building identifier
        use_case: Delete building use case

    Raises:
        HTTPException: If building not found or deletion fails
    """
    try:
        logger.info(f"Deleting building: {building_id}")
        success = use_case.execute(building_id)
        if success:
            logger.info(f"Building deleted successfully: {building_id}")
        else:
            logger.warning(f"Building not found for deletion: {building_id}")
            raise HTTPException(status_code=404, detail="Building not found")
    except ResourceNotFoundError as e:
        logger.warning(f"Building not found for deletion: {building_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting building: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{building_id}/events")
async def get_building_events(
    building_id: str, use_case: GetBuildingUseCase = Depends(get_get_use_case)
):
    """
    Get domain events for a building.

    Args:
        building_id: Building identifier
        use_case: Get building use case

    Returns:
        List of domain events

    Raises:
        HTTPException: If building not found
    """
    try:
        logger.info(f"Getting events for building: {building_id}")
        building = use_case.execute(building_id)

        # Get domain events from the building entity
        events = building.get_domain_events()

        return {
            "building_id": building_id,
            "events": [event.to_dict() for event in events],
            "total_events": len(events),
        }
    except ResourceNotFoundError as e:
        logger.warning(f"Building not found for events: {building_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting building events: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
