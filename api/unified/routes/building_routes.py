"""
Building Routes - Unified Building API Endpoints

This module provides unified building API routes that use the new
controllers and schemas for consistent, well-documented endpoints.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import JSONResponse
import logging

from ..controllers.building_controller import BuildingController
from ..schemas.building_schemas import (
    CreateBuildingRequest,
    UpdateBuildingRequest,
    BuildingResponse,
    BuildingListResponse,
    BuildingFilterSchema,
    BuildingPaginationSchema
)
from ..middleware.auth_middleware import AuthMiddleware
from .dependencies import get_building_controller, get_auth_middleware

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/buildings", tags=["buildings"])


@router.post("/", response_model=BuildingResponse, status_code=status.HTTP_201_CREATED)
async def create_building(
    payload: CreateBuildingRequest,
    request: Request,
    controller: BuildingController = Depends(get_building_controller),
    auth: AuthMiddleware = Depends(get_auth_middleware)
):
    """
    Create a new building.

    This endpoint creates a new building with the provided data.
    Requires authentication and appropriate permissions.
    """
    try:
        # Authenticate and authorize user
        user = await auth.authenticate(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        # Authorize user for building creation
        await auth.authorize(request, required_permissions=["buildings:create"])

        # Create building
        building_dto = await controller.create(payload.dict())

        # Convert to response schema
        response = BuildingResponse.from_dto(building_dto)

        logger.info(f"Building created successfully: {response.id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating building: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{building_id}", response_model=BuildingResponse)
async def get_building(
    building_id: str,
    request: Request,
    controller: BuildingController = Depends(get_building_controller),
    auth: AuthMiddleware = Depends(get_auth_middleware)
):
    """
    Get a building by ID.

    This endpoint retrieves a building by its unique identifier.
    Requires authentication and appropriate permissions.
    """
    try:
        # Authenticate user
        user = await auth.authenticate(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        # Authorize user for building read
        await auth.authorize(request, required_permissions=["buildings:read"])

        # Get building
        building_dto = await controller.get_by_id(building_id)

        # Convert to response schema
        response = BuildingResponse.from_dto(building_dto)

        logger.info(f"Building retrieved successfully: {building_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving building {building_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/", response_model=BuildingListResponse)
async def list_buildings(
    filters: BuildingFilterSchema = Depends(),
    pagination: BuildingPaginationSchema = Depends(),
    request: Request,
    controller: BuildingController = Depends(get_building_controller),
    auth: AuthMiddleware = Depends(get_auth_middleware)
):
    """
    List buildings with filtering and pagination.

    This endpoint retrieves a list of buildings with optional filtering
    and pagination parameters. Requires authentication and appropriate permissions.
    """
    try:
        # Authenticate user
        user = await auth.authenticate(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        # Authorize user for building read
        await auth.authorize(request, required_permissions=["buildings:read"])

        # Get buildings with filters and pagination
        building_dtos = await controller.get_all(
            filters=filters.dict(exclude_none=True),
            pagination=pagination.dict(exclude_none=True)
        )

        # Convert to response schema
        response = BuildingListResponse.from_dtos(
            dtos=building_dtos,
            total_count=len(building_dtos),  # This should come from the use case
            page=pagination.page,
            page_size=pagination.page_size
        )

        logger.info(f"Buildings retrieved successfully: {len(building_dtos)} buildings")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving buildings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/{building_id}", response_model=BuildingResponse)
async def update_building(
    building_id: str,
    payload: UpdateBuildingRequest,
    request: Request,
    controller: BuildingController = Depends(get_building_controller),
    auth: AuthMiddleware = Depends(get_auth_middleware)
):
    """
    Update a building.

    This endpoint updates an existing building with the provided data.
    Requires authentication and appropriate permissions.
    """
    try:
        # Authenticate user
        user = await auth.authenticate(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        # Authorize user for building update
        await auth.authorize(request, required_permissions=["buildings:update"])

        # Update building
        building_dto = await controller.update(building_id, payload.dict(exclude_none=True))

        # Convert to response schema
        response = BuildingResponse.from_dto(building_dto)

        logger.info(f"Building updated successfully: {building_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating building {building_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/{building_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_building(
    building_id: str,
    request: Request,
    controller: BuildingController = Depends(get_building_controller),
    auth: AuthMiddleware = Depends(get_auth_middleware)
):
    """
    Delete a building.

    This endpoint deletes an existing building by its ID.
    Requires authentication and appropriate permissions.
    """
    try:
        # Authenticate user
        user = await auth.authenticate(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        # Authorize user for building delete
        await auth.authorize(request, required_permissions=["buildings:delete"])

        # Delete building
        success = await controller.delete(building_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Building not found"
            )

        logger.info(f"Building deleted successfully: {building_id}")
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting building {building_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{building_id}/floors", response_model=List[dict])
async def get_building_floors(
    building_id: str,
    request: Request,
    controller: BuildingController = Depends(get_building_controller),
    auth: AuthMiddleware = Depends(get_auth_middleware)
):
    """
    Get floors for a building.

    This endpoint retrieves all floors associated with a building.
    Requires authentication and appropriate permissions.
    """
    try:
        # Authenticate user
        user = await auth.authenticate(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        # Authorize user for building read
        await auth.authorize(request, required_permissions=["buildings:read"])

        # Get building floors (this would need to be implemented in the controller)
        # For now, return empty list as placeholder
        floors = []

        logger.info(f"Building floors retrieved successfully: {building_id}")
        return floors

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving building floors {building_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{building_id}/devices", response_model=List[dict])
async def get_building_devices(
    building_id: str,
    request: Request,
    controller: BuildingController = Depends(get_building_controller),
    auth: AuthMiddleware = Depends(get_auth_middleware)
):
    """
    Get devices for a building.

    This endpoint retrieves all devices associated with a building.
    Requires authentication and appropriate permissions.
    """
    try:
        # Authenticate user
        user = await auth.authenticate(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        # Authorize user for building read
        await auth.authorize(request, required_permissions=["buildings:read"])

        # Get building devices (this would need to be implemented in the controller)
        # For now, return empty list as placeholder
        devices = []

        logger.info(f"Building devices retrieved successfully: {building_id}")
        return devices

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving building devices {building_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
