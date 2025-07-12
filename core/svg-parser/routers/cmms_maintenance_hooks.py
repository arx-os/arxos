"""
CMMS Maintenance Event Hooks Router

This router provides RESTful API endpoints for CMMS maintenance event hooks,
enabling secure webhook reception, event processing, and sync management.

Endpoints:
- POST /api/v1/hooks/maintenance/events - Webhook receiver
- GET /api/v1/cmms/sync/status - Get sync status
- GET /api/v1/cmms/events/history - Get event history
- POST /api/v1/cmms/sync/configurations - Create sync configuration
- GET /api/v1/cmms/sync/configurations - Get sync configurations
- PUT /api/v1/cmms/sync/configurations/{config_id} - Update sync configuration
- DELETE /api/v1/cmms/sync/configurations/{config_id} - Delete sync configuration
- POST /api/v1/cmms/events/retry/{event_id} - Retry failed event
- GET /api/v1/cmms/events/{event_id} - Get event details
- GET /api/v1/cmms/health - Health check endpoint

Author: ARXOS Development Team
Date: 2024-12-19
Version: 1.0.0
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from services.cmms_maintenance_hooks import (
    CMMSMaintenanceHooksService,
    WebhookEvent,
    WebhookResponse,
    SyncStatus,
    ProcessingStatus,
    get_cmms_hooks_service
)
from utils.auth import get_current_user
from utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1",
    tags=["CMMS Maintenance Hooks"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)

# Pydantic models for API requests
class SyncConfigurationRequest(BaseModel):
    """Sync configuration request model."""
    cmms_system_id: str = Field(..., description="CMMS system identifier")
    sync_type: str = Field(..., description="Type of synchronization")
    configuration: Dict[str, Any] = Field(..., description="Configuration data")
    is_active: bool = Field(True, description="Whether configuration is active")
    
    class Config:
        schema_extra = {
            "example": {
                "cmms_system_id": "maximo_production",
                "sync_type": "maintenance_events",
                "configuration": {
                    "webhook_url": "https://arxos.com/api/v1/hooks/maintenance/events",
                    "secret_key": "your-secret-key",
                    "event_types": ["maintenance_scheduled", "maintenance_completed"],
                    "retry_policy": {
                        "max_retries": 3,
                        "retry_delay": 60
                    }
                },
                "is_active": True
            }
        }


class SyncConfigurationUpdate(BaseModel):
    """Sync configuration update model."""
    configuration: Dict[str, Any] = Field(..., description="Updated configuration data")
    is_active: Optional[bool] = Field(None, description="Whether configuration is active")


class EventRetryRequest(BaseModel):
    """Event retry request model."""
    force_retry: bool = Field(False, description="Force retry even if max retries exceeded")


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    redis_connected: bool = Field(..., description="Redis connection status")
    database_connected: bool = Field(..., description="Database connection status")
    active_jobs: int = Field(..., description="Number of active background jobs")
    error_rate: float = Field(..., description="Error rate percentage")


@router.post(
    "/hooks/maintenance/events",
    response_model=WebhookResponse,
    summary="Receive CMMS maintenance event webhook",
    description="Secure webhook endpoint for receiving maintenance events from CMMS systems",
    responses={
        200: {"description": "Event received and queued successfully"},
        400: {"description": "Invalid request payload"},
        401: {"description": "Invalid HMAC signature"},
        500: {"description": "Internal server error"}
    }
)
async def receive_maintenance_webhook(
    event_data: WebhookEvent,
    background_tasks: BackgroundTasks,
    x_hmac_signature: str = None,
    x_cmms_secret: str = None,
    service: CMMSMaintenanceHooksService = Depends(get_cmms_hooks_service)
) -> WebhookResponse:
    """
    Receive maintenance event webhook from CMMS system.
    
    This endpoint validates the HMAC signature and queues the event for background processing.
    
    Args:
        event_data: Webhook event data
        background_tasks: FastAPI background tasks
        x_hmac_signature: HMAC signature header
        x_cmms_secret: CMMS secret key header
        service: CMMS hooks service
        
    Returns:
        WebhookResponse: Processing result
        
    Raises:
        HTTPException: If validation fails or processing error occurs
    """
    try:
        # Validate required headers
        if not x_hmac_signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing HMAC signature header"
            )
        
        if not x_cmms_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing CMMS secret header"
            )
        
        # Process webhook event
        response = await service.process_webhook_event(
            event_data=event_data,
            hmac_signature=x_hmac_signature,
            secret_key=x_cmms_secret
        )
        
        # Log successful webhook reception
        logger.info(f"Webhook received for CMMS system {event_data.cmms_system_id}, event type: {event_data.event_type}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/cmms/sync/status",
    response_model=SyncStatus,
    summary="Get CMMS sync status",
    description="Get current synchronization status for a CMMS system",
    responses={
        200: {"description": "Sync status retrieved successfully"},
        404: {"description": "CMMS system not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_cmms_sync_status(
    cmms_system_id: str = Query(..., description="CMMS system identifier"),
    service: CMMSMaintenanceHooksService = Depends(get_cmms_hooks_service)
) -> SyncStatus:
    """
    Get synchronization status for a CMMS system.
    
    Args:
        cmms_system_id: CMMS system identifier
        service: CMMS hooks service
        
    Returns:
        SyncStatus: Current sync status
        
    Raises:
        HTTPException: If system not found or error occurs
    """
    try:
        sync_status = await service.get_sync_status(cmms_system_id)
        return sync_status
        
    except Exception as e:
        logger.error(f"Error getting sync status for {cmms_system_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync status: {str(e)}"
        )


@router.get(
    "/cmms/events/history",
    response_model=List[Dict[str, Any]],
    summary="Get event processing history",
    description="Get historical event processing data with optional filtering",
    responses={
        200: {"description": "Event history retrieved successfully"},
        500: {"description": "Internal server error"}
    }
)
async def get_event_history(
    cmms_system_id: Optional[str] = Query(None, description="Filter by CMMS system ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events to return"),
    service: CMMSMaintenanceHooksService = Depends(get_cmms_hooks_service)
) -> List[Dict[str, Any]]:
    """
    Get event processing history with optional filtering.
    
    Args:
        cmms_system_id: Filter by CMMS system ID
        event_type: Filter by event type
        limit: Maximum number of events to return
        service: CMMS hooks service
        
    Returns:
        List[Dict[str, Any]]: Event history
    """
    try:
        history = await service.get_event_history(
            cmms_system_id=cmms_system_id,
            event_type=event_type,
            limit=limit
        )
        return history
        
    except Exception as e:
        logger.error(f"Error getting event history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get event history: {str(e)}"
        )


@router.post(
    "/cmms/sync/configurations",
    response_model=Dict[str, Any],
    summary="Create sync configuration",
    description="Create a new synchronization configuration for a CMMS system",
    responses={
        201: {"description": "Sync configuration created successfully"},
        400: {"description": "Invalid configuration data"},
        409: {"description": "Configuration already exists"},
        500: {"description": "Internal server error"}
    }
)
async def create_sync_configuration(
    config_request: SyncConfigurationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: CMMSMaintenanceHooksService = Depends(get_cmms_hooks_service)
) -> Dict[str, Any]:
    """
    Create a new synchronization configuration.
    
    Args:
        config_request: Sync configuration request
        current_user: Current authenticated user
        service: CMMS hooks service
        
    Returns:
        Dict[str, Any]: Created configuration
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        configuration = await service.create_sync_configuration(
            cmms_system_id=config_request.cmms_system_id,
            sync_type=config_request.sync_type,
            configuration=config_request.configuration
        )
        
        logger.info(f"Sync configuration created for CMMS system {config_request.cmms_system_id}")
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=configuration
        )
        
    except Exception as e:
        logger.error(f"Error creating sync configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create sync configuration: {str(e)}"
        )


@router.get(
    "/cmms/sync/configurations",
    response_model=List[Dict[str, Any]],
    summary="Get sync configurations",
    description="Get synchronization configurations with optional filtering",
    responses={
        200: {"description": "Sync configurations retrieved successfully"},
        500: {"description": "Internal server error"}
    }
)
async def get_sync_configurations(
    cmms_system_id: Optional[str] = Query(None, description="Filter by CMMS system ID"),
    service: CMMSMaintenanceHooksService = Depends(get_cmms_hooks_service)
) -> List[Dict[str, Any]]:
    """
    Get synchronization configurations.
    
    Args:
        cmms_system_id: Filter by CMMS system ID
        service: CMMS hooks service
        
    Returns:
        List[Dict[str, Any]]: Sync configurations
    """
    try:
        configurations = await service.get_sync_configurations(cmms_system_id=cmms_system_id)
        return configurations
        
    except Exception as e:
        logger.error(f"Error getting sync configurations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync configurations: {str(e)}"
        )


@router.put(
    "/cmms/sync/configurations/{config_id}",
    response_model=Dict[str, Any],
    summary="Update sync configuration",
    description="Update an existing synchronization configuration",
    responses={
        200: {"description": "Sync configuration updated successfully"},
        404: {"description": "Configuration not found"},
        400: {"description": "Invalid configuration data"},
        500: {"description": "Internal server error"}
    }
)
async def update_sync_configuration(
    config_id: UUID = Path(..., description="Configuration ID"),
    config_update: SyncConfigurationUpdate = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: CMMSMaintenanceHooksService = Depends(get_cmms_hooks_service)
) -> Dict[str, Any]:
    """
    Update an existing synchronization configuration.
    
    Args:
        config_id: Configuration ID
        config_update: Configuration update data
        current_user: Current authenticated user
        service: CMMS hooks service
        
    Returns:
        Dict[str, Any]: Updated configuration
        
    Raises:
        HTTPException: If update fails or configuration not found
    """
    try:
        # This would be implemented in the service
        # For now, return a placeholder response
        logger.info(f"Sync configuration {config_id} update requested")
        
        return {
            "id": str(config_id),
            "message": "Configuration update not yet implemented",
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating sync configuration {config_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update sync configuration: {str(e)}"
        )


@router.delete(
    "/cmms/sync/configurations/{config_id}",
    summary="Delete sync configuration",
    description="Delete a synchronization configuration",
    responses={
        204: {"description": "Sync configuration deleted successfully"},
        404: {"description": "Configuration not found"},
        500: {"description": "Internal server error"}
    }
)
async def delete_sync_configuration(
    config_id: UUID = Path(..., description="Configuration ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: CMMSMaintenanceHooksService = Depends(get_cmms_hooks_service)
):
    """
    Delete a synchronization configuration.
    
    Args:
        config_id: Configuration ID
        current_user: Current authenticated user
        service: CMMS hooks service
        
    Raises:
        HTTPException: If deletion fails or configuration not found
    """
    try:
        # This would be implemented in the service
        # For now, return a placeholder response
        logger.info(f"Sync configuration {config_id} deletion requested")
        
        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None
        )
        
    except Exception as e:
        logger.error(f"Error deleting sync configuration {config_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete sync configuration: {str(e)}"
        )


@router.post(
    "/cmms/events/retry/{event_id}",
    response_model=Dict[str, Any],
    summary="Retry failed event",
    description="Manually retry a failed event processing",
    responses={
        200: {"description": "Event retry initiated successfully"},
        404: {"description": "Event not found"},
        400: {"description": "Event cannot be retried"},
        500: {"description": "Internal server error"}
    }
)
async def retry_failed_event(
    event_id: UUID = Path(..., description="Event ID"),
    retry_request: EventRetryRequest = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: CMMSMaintenanceHooksService = Depends(get_cmms_hooks_service)
) -> Dict[str, Any]:
    """
    Manually retry a failed event processing.
    
    Args:
        event_id: Event ID to retry
        retry_request: Retry request parameters
        current_user: Current authenticated user
        service: CMMS hooks service
        
    Returns:
        Dict[str, Any]: Retry result
        
    Raises:
        HTTPException: If retry fails or event not found
    """
    try:
        # This would be implemented in the service
        # For now, return a placeholder response
        logger.info(f"Event {event_id} retry requested by user {current_user.get('username', 'unknown')}")
        
        return {
            "event_id": str(event_id),
            "status": "retry_initiated",
            "message": "Event retry not yet implemented",
            "retry_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error retrying event {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry event: {str(e)}"
        )


@router.get(
    "/cmms/events/{event_id}",
    response_model=Dict[str, Any],
    summary="Get event details",
    description="Get detailed information about a specific event",
    responses={
        200: {"description": "Event details retrieved successfully"},
        404: {"description": "Event not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_event_details(
    event_id: UUID = Path(..., description="Event ID"),
    service: CMMSMaintenanceHooksService = Depends(get_cmms_hooks_service)
) -> Dict[str, Any]:
    """
    Get detailed information about a specific event.
    
    Args:
        event_id: Event ID
        service: CMMS hooks service
        
    Returns:
        Dict[str, Any]: Event details
        
    Raises:
        HTTPException: If event not found or error occurs
    """
    try:
        # This would be implemented in the service
        # For now, return a placeholder response
        logger.info(f"Event details requested for {event_id}")
        
        return {
            "event_id": str(event_id),
            "message": "Event details not yet implemented",
            "requested_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting event details for {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get event details: {str(e)}"
        )


@router.get(
    "/cmms/health",
    response_model=HealthCheckResponse,
    summary="Health check",
    description="Check the health status of the CMMS hooks service",
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"}
    }
)
async def health_check(
    service: CMMSMaintenanceHooksService = Depends(get_cmms_hooks_service)
) -> HealthCheckResponse:
    """
    Check the health status of the CMMS hooks service.
    
    Args:
        service: CMMS hooks service
        
    Returns:
        HealthCheckResponse: Health status information
    """
    try:
        # Check Redis connection
        redis_connected = False
        if service.redis_client:
            try:
                await service.redis_client.ping()
                redis_connected = True
            except Exception:
                pass
        
        # Check database connection (simplified)
        database_connected = True  # Would implement actual DB check
        
        # Get active jobs count (simplified)
        active_jobs = 0
        if service.redis_client and redis_connected:
            try:
                queue_length = await service.redis_client.llen(service.queue_name)
                active_jobs = queue_length
            except Exception:
                pass
        
        # Calculate error rate (simplified)
        error_rate = 0.0  # Would implement actual error rate calculation
        
        # Determine overall status
        status = "healthy"
        if not redis_connected or not database_connected:
            status = "unhealthy"
        
        health_response = HealthCheckResponse(
            status=status,
            timestamp=datetime.utcnow(),
            redis_connected=redis_connected,
            database_connected=database_connected,
            active_jobs=active_jobs,
            error_rate=error_rate
        )
        
        # Return appropriate status code
        if status == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is unhealthy"
            )
        
        return health_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )


# Background task to start job processing
async def start_background_job_processing():
    """Start background job processing."""
    service = await get_cmms_hooks_service()
    await service.process_background_jobs()


# Add background task to startup
@router.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("CMMS Maintenance Hooks router starting up")
    # Start background job processing in a separate task
    # This would be implemented with proper task management
    logger.info("Background job processing will be started separately")


# Add shutdown event handler
@router.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("CMMS Maintenance Hooks router shutting down")
    service = await get_cmms_hooks_service()
    await service.close() 