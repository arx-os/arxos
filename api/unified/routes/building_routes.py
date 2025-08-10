"""
Building Routes - Unified Building API Endpoints

This module provides unified building API routes that use the new
controllers and schemas for consistent, well-documented endpoints.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from ..controllers.building_controller import BuildingController
from ..schemas.building_schemas import (
    CreateBuildingRequest,
    UpdateBuildingRequest,
    BuildingResponse,
    BuildingListResponse,
    BuildingFilterSchema,
    BuildingPaginationSchema,
    FloorSummarySchema,
    DeviceSummarySchema,
)
from ..middleware.auth_middleware import AuthMiddleware
from .dependencies import (
    get_building_controller,
    get_auth_middleware,
    get_building_list_use_case,
    get_unified_building_use_case,
    require_building_create_permission,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/buildings", tags=["buildings"])


@router.post("/", response_model=BuildingResponse, status_code=201)
async def create_building(
    payload: CreateBuildingRequest,
    controller: BuildingController = Depends(get_building_controller),
    user: Dict[str, Any] = Depends(require_building_create_permission)
):
    """Create a new building."""
    try:
        building_dto = await controller.create(payload.model_dump())
        return BuildingResponse(
            success=True,
            message="Building created successfully",
            data=building_dto,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    request: Request,
    filters: BuildingFilterSchema = Depends(),
    pagination: BuildingPaginationSchema = Depends(),
    controller: BuildingController = Depends(get_building_controller),
    auth: AuthMiddleware = Depends(get_auth_middleware),
    list_uc = Depends(get_building_list_use_case)
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
        # Repo factory should be initialized in app lifespan; do not initialize here

        building_dtos = await controller.get_all(
            filters=filters.model_dump(exclude_none=True),
            pagination=pagination.model_dump(exclude_none=True)
        )

        # Obtain total count from use case if available
        try:
            total_count = await list_uc.count(filters.model_dump(exclude_none=True))
        except Exception:
            total_count = len(building_dtos)

        response = BuildingListResponse.from_dtos(
            dtos=building_dtos,
            total_count=total_count,
            page=pagination.page,
            page_size=pagination.page_size,
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


@router.get("/{building_id}/floors", response_model=List[FloorSummarySchema])
async def get_building_floors(
    building_id: str,
    request: Request,
    controller: BuildingController = Depends(get_building_controller),
    auth: AuthMiddleware = Depends(get_auth_middleware),
    uc = Depends(get_unified_building_use_case),
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

        # Use unified use case to fetch hierarchy and return floors
        hierarchy = uc.get_building_hierarchy(building_id)
        floors = [
            {
                "id": f.get("floor", {}).get("id") or f.get("id"),
                "floor_number": f.get("floor", {}).get("floor_number", f.get("floor_number")),
                "name": f.get("floor", {}).get("name", f.get("name")),
                "status": f.get("floor", {}).get("status") or f.get("status"),
                "room_count": len(f.get("rooms", [])),
            }
            for f in hierarchy.get("floors", [])
        ]

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


@router.get("/{building_id}/devices", response_model=List[DeviceSummarySchema])
async def get_building_devices(
    building_id: str,
    request: Request,
    controller: BuildingController = Depends(get_building_controller),
    auth: AuthMiddleware = Depends(get_auth_middleware),
    uc = Depends(get_unified_building_use_case),
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

        # Use unified use case to fetch hierarchy and flatten devices
        hierarchy = uc.get_building_hierarchy(building_id)
        devices = []
        for f in hierarchy.get("floors", []):
            for r in f.get("rooms", []):
                for d in r.get("devices", []):
                    devices.append(
                        {
                            "id": d.get("id"),
                            "room_id": r.get("id"),
                            "device_id": d.get("device_id"),
                            "device_type": d.get("device_type"),
                            "name": d.get("name"),
                            "status": d.get("status"),
                        }
                    )

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

@router.get("/{building_id}/hierarchy", response_model=dict)
async def get_building_hierarchy(
    building_id: str,
    request: Request,
    controller: BuildingController = Depends(get_building_controller),
    auth: AuthMiddleware = Depends(get_auth_middleware),
    uc = Depends(get_unified_building_use_case),
):
    """
    Get full building hierarchy (building -> floors -> rooms -> devices).

    Requires authentication and appropriate permissions.
    """
    try:
        user = await auth.authenticate(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        await auth.authorize(request, required_permissions=["buildings:read"])

        hierarchy = uc.get_building_hierarchy(building_id)
        logger.info(f"Building hierarchy retrieved successfully: {building_id}")
        return hierarchy

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving building hierarchy {building_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
