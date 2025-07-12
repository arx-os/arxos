"""
Offline Sync & Conflict Resolution API Router

This router provides RESTful API endpoints for offline sync and conflict resolution
operations, including sync initiation, conflict resolution, status monitoring,
and rollback capabilities.

Endpoints:
- POST /sync/initiate - Initiate a sync operation
- POST /sync/resolve-conflict - Resolve a specific conflict
- GET /sync/status/{device_id} - Get sync status for a device
- GET /sync/history/{device_id} - Get sync history for a device
- POST /sync/rollback - Rollback a failed sync operation
- GET /sync/metrics - Get sync performance metrics
- DELETE /sync/cleanup - Clean up old sync operations
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from pydantic import BaseModel, Field

from services.offline_sync_conflict_resolution import (
    OfflineSyncConflictResolutionService,
    ConflictType,
    SyncStatus
)

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/sync", tags=["Offline Sync & Conflict Resolution"])

# Initialize service
sync_service = OfflineSyncConflictResolutionService()


# Pydantic models for request/response
class SyncInitiateRequest(BaseModel):
    """Request model for initiating a sync operation."""
    device_id: str = Field(..., description="Unique device identifier")
    local_changes: List[Dict[str, Any]] = Field(..., description="Local changes to sync")
    remote_data: Dict[str, Any] = Field(..., description="Current remote data state")
    resolution_strategy: Optional[str] = Field("auto", description="Conflict resolution strategy")


class SyncInitiateResponse(BaseModel):
    """Response model for sync initiation."""
    status: str = Field(..., description="Sync operation status")
    operation_id: str = Field(..., description="Unique operation identifier")
    synced_changes: int = Field(..., description="Number of changes synced")
    conflicts_resolved: int = Field(..., description="Number of conflicts resolved")
    resolved_changes: int = Field(..., description="Number of changes resolved")
    duration_ms: int = Field(..., description="Sync operation duration in milliseconds")
    sync_state: Dict[str, Any] = Field(..., description="Updated sync state")


class ConflictResolutionRequest(BaseModel):
    """Request model for conflict resolution."""
    conflict_id: str = Field(..., description="Unique conflict identifier")
    conflict_type: str = Field(..., description="Type of conflict")
    local_data: Dict[str, Any] = Field(..., description="Local version of data")
    remote_data: Dict[str, Any] = Field(..., description="Remote version of data")
    resolution_strategy: str = Field(..., description="Resolution strategy to use")


class ConflictResolutionResponse(BaseModel):
    """Response model for conflict resolution."""
    conflict_id: str = Field(..., description="Conflict identifier")
    resolved_data: Dict[str, Any] = Field(..., description="Resolved data")
    resolution_strategy: str = Field(..., description="Strategy used for resolution")
    timestamp: str = Field(..., description="Resolution timestamp")


class SyncStatusResponse(BaseModel):
    """Response model for sync status."""
    device_id: str = Field(..., description="Device identifier")
    status: str = Field(..., description="Current sync status")
    last_sync: Optional[str] = Field(None, description="Last sync timestamp")
    unsynced_changes: int = Field(..., description="Number of unsynced changes")
    conflict_count: int = Field(..., description="Total conflicts encountered")
    success_count: int = Field(..., description="Successful sync operations")
    total_operations: int = Field(..., description="Total sync operations")


class SyncHistoryResponse(BaseModel):
    """Response model for sync history."""
    device_id: str = Field(..., description="Device identifier")
    operations: List[Dict[str, Any]] = Field(..., description="List of sync operations")
    total_operations: int = Field(..., description="Total number of operations")


class RollbackRequest(BaseModel):
    """Request model for sync rollback."""
    device_id: str = Field(..., description="Device identifier")
    operation_id: str = Field(..., description="Operation ID to rollback")


class RollbackResponse(BaseModel):
    """Response model for sync rollback."""
    status: str = Field(..., description="Rollback status")
    operation_id: str = Field(..., description="Rollback operation ID")
    rolled_back_operation: str = Field(..., description="Original operation ID")
    message: str = Field(..., description="Rollback result message")


class MetricsResponse(BaseModel):
    """Response model for sync metrics."""
    metrics: Dict[str, Any] = Field(..., description="Performance metrics")
    total_devices: int = Field(..., description="Total number of devices")
    database_size: int = Field(..., description="Database size in bytes")


class CleanupRequest(BaseModel):
    """Request model for cleanup operation."""
    days: int = Field(30, description="Number of days to keep operations")


class CleanupResponse(BaseModel):
    """Response model for cleanup operation."""
    deleted_count: int = Field(..., description="Number of operations deleted")
    message: str = Field(..., description="Cleanup result message")


@router.post("/initiate", response_model=SyncInitiateResponse)
async def initiate_sync(request: SyncInitiateRequest):
    """
    Initiate a two-way sync operation for a device.
    
    This endpoint performs comprehensive sync operations including:
    - Conflict detection between local and remote data
    - Automatic conflict resolution using specified strategy
    - Safe merging of changes
    - Complete audit trail and logging
    
    Args:
        request: Sync initiation request with device data and changes
        
    Returns:
        Sync operation result with status and metrics
        
    Raises:
        HTTPException: If sync operation fails
    """
    try:
        logger.info(f"Initiating sync for device {request.device_id}")
        
        # Validate request data
        if not request.device_id:
            raise HTTPException(status_code=400, detail="Device ID is required")
        
        if not request.local_changes and not request.remote_data:
            raise HTTPException(status_code=400, detail="Either local changes or remote data must be provided")
        
        # Perform sync operation
        result = sync_service.sync_data(
            device_id=request.device_id,
            local_changes=request.local_changes,
            remote_data=request.remote_data
        )
        
        logger.info(f"Sync completed for device {request.device_id}: {result['synced_changes']} changes, {result['conflicts_resolved']} conflicts")
        
        return SyncInitiateResponse(**result)
        
    except Exception as e:
        logger.error(f"Sync initiation failed for device {request.device_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Sync operation failed: {str(e)}")


@router.post("/resolve-conflict", response_model=ConflictResolutionResponse)
async def resolve_conflict(request: ConflictResolutionRequest):
    """
    Resolve a specific conflict between local and remote data.
    
    This endpoint provides manual conflict resolution capabilities
    for cases where automatic resolution is not sufficient.
    
    Args:
        request: Conflict resolution request with data and strategy
        
    Returns:
        Conflict resolution result with resolved data
        
    Raises:
        HTTPException: If conflict resolution fails
    """
    try:
        logger.info(f"Resolving conflict {request.conflict_id}")
        
        # Validate conflict type
        try:
            conflict_type = ConflictType(request.conflict_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid conflict type: {request.conflict_type}")
        
        # Resolve conflict
        resolved_data = sync_service.resolve_conflict(
            conflict_type=conflict_type,
            local_data=request.local_data,
            remote_data=request.remote_data,
            resolution_strategy=request.resolution_strategy
        )
        
        logger.info(f"Conflict {request.conflict_id} resolved using {request.resolution_strategy} strategy")
        
        return ConflictResolutionResponse(
            conflict_id=request.conflict_id,
            resolved_data=resolved_data,
            resolution_strategy=request.resolution_strategy,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Conflict resolution failed for {request.conflict_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Conflict resolution failed: {str(e)}")


@router.get("/status/{device_id}", response_model=SyncStatusResponse)
async def get_sync_status(device_id: str):
    """
    Get current sync status for a device.
    
    This endpoint provides comprehensive status information including:
    - Current sync status (pending, in_progress, completed, failed)
    - Last sync timestamp
    - Number of unsynced changes
    - Conflict and success statistics
    
    Args:
        device_id: Device identifier
        
    Returns:
        Current sync status information
        
    Raises:
        HTTPException: If device not found or status retrieval fails
    """
    try:
        logger.info(f"Getting sync status for device {device_id}")
        
        status = sync_service.get_sync_status(device_id)
        
        if status['status'] == 'not_initialized':
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        
        return SyncStatusResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sync status for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")


@router.get("/history/{device_id}", response_model=SyncHistoryResponse)
async def get_sync_history(device_id: str, limit: int = 50):
    """
    Get sync history for a device.
    
    This endpoint provides detailed history of sync operations including:
    - Operation timestamps and status
    - Operation types and durations
    - Error messages for failed operations
    
    Args:
        device_id: Device identifier
        limit: Maximum number of operations to return (default: 50)
        
    Returns:
        Sync operation history
        
    Raises:
        HTTPException: If history retrieval fails
    """
    try:
        logger.info(f"Getting sync history for device {device_id}, limit: {limit}")
        
        if limit < 1 or limit > 1000:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
        
        operations = sync_service.get_sync_history(device_id, limit)
        
        return SyncHistoryResponse(
            device_id=device_id,
            operations=operations,
            total_operations=len(operations)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sync history for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")


@router.post("/rollback", response_model=RollbackResponse)
async def rollback_sync(request: RollbackRequest):
    """
    Rollback a failed sync operation.
    
    This endpoint provides rollback capabilities for failed sync operations,
    restoring the system to a previous stable state.
    
    Args:
        request: Rollback request with device and operation identifiers
        
    Returns:
        Rollback operation result
        
    Raises:
        HTTPException: If rollback operation fails
    """
    try:
        logger.info(f"Rolling back sync operation {request.operation_id} for device {request.device_id}")
        
        result = sync_service.rollback_sync(
            device_id=request.device_id,
            operation_id=request.operation_id
        )
        
        logger.info(f"Rollback completed for operation {request.operation_id}")
        
        return RollbackResponse(**result)
        
    except ValueError as e:
        logger.error(f"Rollback failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Rollback failed for operation {request.operation_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Rollback operation failed: {str(e)}")


@router.get("/metrics", response_model=MetricsResponse)
async def get_sync_metrics():
    """
    Get sync performance metrics.
    
    This endpoint provides comprehensive performance metrics including:
    - Total sync operations and success rates
    - Conflict resolution statistics
    - Rollback counts and average sync times
    - System resource usage
    
    Returns:
        Sync performance metrics
        
    Raises:
        HTTPException: If metrics retrieval fails
    """
    try:
        logger.info("Getting sync performance metrics")
        
        metrics = sync_service.get_metrics()
        
        return MetricsResponse(**metrics)
        
    except Exception as e:
        logger.error(f"Failed to get sync metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")


@router.delete("/cleanup", response_model=CleanupResponse)
async def cleanup_old_operations(request: CleanupRequest):
    """
    Clean up old sync operations.
    
    This endpoint removes old sync operations to maintain database performance
    and storage efficiency.
    
    Args:
        request: Cleanup request with retention period
        
    Returns:
        Cleanup operation result
        
    Raises:
        HTTPException: If cleanup operation fails
    """
    try:
        logger.info(f"Cleaning up sync operations older than {request.days} days")
        
        if request.days < 1 or request.days > 365:
            raise HTTPException(status_code=400, detail="Days must be between 1 and 365")
        
        deleted_count = sync_service.cleanup_old_operations(request.days)
        
        logger.info(f"Cleanup completed: {deleted_count} operations deleted")
        
        return CleanupResponse(
            deleted_count=deleted_count,
            message=f"Successfully deleted {deleted_count} operations older than {request.days} days"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cleanup operation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup operation failed: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the sync service.
    
    Returns:
        Service health status
    """
    try:
        # Basic health check
        metrics = sync_service.get_metrics()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "offline_sync_conflict_resolution",
            "database_accessible": True,
            "metrics_available": bool(metrics)
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "service": "offline_sync_conflict_resolution",
                "error": str(e)
            }
        )


# Error handlers
@router.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with detailed error information."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )


@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions with logging."""
    logger.error(f"Unhandled exception in sync API: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    ) 