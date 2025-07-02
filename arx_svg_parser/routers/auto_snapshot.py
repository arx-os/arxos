"""
Auto-Snapshot Router for FastAPI

Provides REST API endpoints for auto-snapshot functionality including:
- Configuration management
- Manual snapshot creation
- Service monitoring
- Cleanup operations
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import asyncio
import logging

from arx_svg_parser.services.auto_snapshot import (
    AutoSnapshotService, SnapshotConfig, SnapshotTrigger, 
    SnapshotPriority, ChangeMetrics, create_auto_snapshot_service
)

logger = logging.getLogger(__name__)

# Global auto-snapshot service instance
auto_snapshot_service: Optional[AutoSnapshotService] = None

# Pydantic models for API requests/responses
class SnapshotConfigRequest(BaseModel):
    enabled: bool = True
    time_interval_minutes: int = Field(15, ge=1, le=1440)  # 1 minute to 24 hours
    change_threshold: int = Field(10, ge=1, le=1000)
    major_edit_threshold: int = Field(25, ge=1, le=1000)
    max_snapshots_per_hour: int = Field(4, ge=1, le=100)
    max_snapshots_per_day: int = Field(24, ge=1, le=1000)
    retention_days: int = Field(30, ge=1, le=365)
    cleanup_enabled: bool = True
    compression_enabled: bool = True
    backup_enabled: bool = True

class ManualSnapshotRequest(BaseModel):
    floor_id: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class SnapshotResponse(BaseModel):
    id: str
    floor_id: str
    created_at: datetime
    description: str
    tags: List[str]
    trigger: str
    priority: str
    is_auto_save: bool
    change_metrics: Dict[str, Any]
    metadata: Dict[str, Any]

class ServiceStatsResponse(BaseModel):
    active_floors: int
    running: bool
    config: Dict[str, Any]
    cleanup_stats: Dict[str, Any]
    scheduler_stats: Dict[str, Any]

class ChangeTrackingRequest(BaseModel):
    floor_id: str
    current_data: Dict[str, Any]
    previous_data: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

# Create router
router = APIRouter(prefix="/auto-snapshot", tags=["auto-snapshot"])

# Dependency to get auto-snapshot service
async def get_auto_snapshot_service() -> AutoSnapshotService:
    global auto_snapshot_service
    if auto_snapshot_service is None:
        auto_snapshot_service = create_auto_snapshot_service()
        await auto_snapshot_service.start()
    return auto_snapshot_service

@router.on_event("startup")
async def startup_event():
    """Initialize auto-snapshot service on startup"""
    global auto_snapshot_service
    auto_snapshot_service = create_auto_snapshot_service()
    await auto_snapshot_service.start()
    logger.info("Auto-snapshot service initialized")

@router.on_event("shutdown")
async def shutdown_event():
    """Shutdown auto-snapshot service"""
    global auto_snapshot_service
    if auto_snapshot_service:
        await auto_snapshot_service.stop()
        logger.info("Auto-snapshot service shutdown")

@router.get("/config", response_model=SnapshotConfigRequest)
async def get_config(service: AutoSnapshotService = Depends(get_auto_snapshot_service)):
    """Get current auto-snapshot configuration"""
    config = service.config
    return SnapshotConfigRequest(
        enabled=config.enabled,
        time_interval_minutes=config.time_interval_minutes,
        change_threshold=config.change_threshold,
        major_edit_threshold=config.major_edit_threshold,
        max_snapshots_per_hour=config.max_snapshots_per_hour,
        max_snapshots_per_day=config.max_snapshots_per_day,
        retention_days=config.retention_days,
        cleanup_enabled=config.cleanup_enabled,
        compression_enabled=config.compression_enabled,
        backup_enabled=config.backup_enabled
    )

@router.put("/config", response_model=SnapshotConfigRequest)
async def update_config(
    config_request: SnapshotConfigRequest,
    service: AutoSnapshotService = Depends(get_auto_snapshot_service)
):
    """Update auto-snapshot configuration"""
    try:
        # Create new config
        new_config = SnapshotConfig(
            enabled=config_request.enabled,
            time_interval_minutes=config_request.time_interval_minutes,
            change_threshold=config_request.change_threshold,
            major_edit_threshold=config_request.major_edit_threshold,
            max_snapshots_per_hour=config_request.max_snapshots_per_hour,
            max_snapshots_per_day=config_request.max_snapshots_per_day,
            retention_days=config_request.retention_days,
            cleanup_enabled=config_request.cleanup_enabled,
            compression_enabled=config_request.compression_enabled,
            backup_enabled=config_request.backup_enabled
        )
        
        # Update service config
        service.config = new_config
        service.scheduler.config = new_config
        service.cleanup_manager.config = new_config
        
        logger.info("Auto-snapshot configuration updated")
        return config_request
        
    except Exception as e:
        logger.error(f"Error updating auto-snapshot config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")

@router.post("/track-changes", response_model=Optional[SnapshotResponse])
async def track_changes(
    request: ChangeTrackingRequest,
    service: AutoSnapshotService = Depends(get_auto_snapshot_service)
):
    """Track changes and potentially create a snapshot"""
    try:
        snapshot = await service.track_changes(
            floor_id=request.floor_id,
            current_data=request.current_data,
            previous_data=request.previous_data,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        if snapshot:
            return SnapshotResponse(
                id=str(snapshot.get('id', '')),
                floor_id=snapshot['floor_id'],
                created_at=datetime.fromisoformat(snapshot['created_at']),
                description=snapshot['description'],
                tags=snapshot['tags'],
                trigger=snapshot['trigger'],
                priority=snapshot['priority'],
                is_auto_save=snapshot['is_auto_save'],
                change_metrics=snapshot['metadata'].change_metrics.__dict__,
                metadata=snapshot['metadata'].__dict__
            )
        
        return None
        
    except Exception as e:
        logger.error(f"Error tracking changes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to track changes: {str(e)}")

@router.post("/create-manual", response_model=SnapshotResponse)
async def create_manual_snapshot(
    request: ManualSnapshotRequest,
    service: AutoSnapshotService = Depends(get_auto_snapshot_service)
):
    """Create a manual snapshot"""
    try:
        # Get current floor data
        current_data = await service._get_floor_data(request.floor_id)
        if not current_data:
            raise HTTPException(status_code=404, detail="Floor data not found")
        
        # Create change metrics for manual snapshot
        change_metrics = service.change_detector.detect_changes(
            request.floor_id, current_data
        )
        
        # Create manual snapshot
        snapshot = await service._create_snapshot(
            floor_id=request.floor_id,
            data=current_data,
            change_metrics=change_metrics,
            trigger=SnapshotTrigger.MANUAL,
            priority=SnapshotPriority.NORMAL,
            reason="Manual snapshot request",
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        # Update description if provided
        if request.description:
            snapshot['description'] = request.description
        if request.tags:
            snapshot['tags'].extend(request.tags)
        
        return SnapshotResponse(
            id=str(snapshot.get('id', '')),
            floor_id=snapshot['floor_id'],
            created_at=datetime.fromisoformat(snapshot['created_at']),
            description=snapshot['description'],
            tags=snapshot['tags'],
            trigger=snapshot['trigger'],
            priority=snapshot['priority'],
            is_auto_save=snapshot['is_auto_save'],
            change_metrics=snapshot['metadata'].change_metrics.__dict__,
            metadata=snapshot['metadata'].__dict__
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating manual snapshot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create manual snapshot: {str(e)}")

@router.get("/stats", response_model=ServiceStatsResponse)
async def get_service_stats(service: AutoSnapshotService = Depends(get_auto_snapshot_service)):
    """Get auto-snapshot service statistics"""
    try:
        stats = service.get_service_stats()
        return ServiceStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting service stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get service stats: {str(e)}")

@router.post("/cleanup/{floor_id}")
async def trigger_cleanup(
    floor_id: str,
    background_tasks: BackgroundTasks,
    service: AutoSnapshotService = Depends(get_auto_snapshot_service)
):
    """Trigger cleanup for a specific floor"""
    try:
        # Run cleanup in background
        background_tasks.add_task(_run_cleanup, service, floor_id)
        
        return {"message": f"Cleanup triggered for floor {floor_id}"}
        
    except Exception as e:
        logger.error(f"Error triggering cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger cleanup: {str(e)}")

@router.post("/cleanup/all")
async def trigger_cleanup_all(
    background_tasks: BackgroundTasks,
    service: AutoSnapshotService = Depends(get_auto_snapshot_service)
):
    """Trigger cleanup for all floors"""
    try:
        # Get all floors
        floors = await service._get_floors_with_snapshots()
        
        # Run cleanup for each floor in background
        for floor_id in floors:
            background_tasks.add_task(_run_cleanup, service, floor_id)
        
        return {"message": f"Cleanup triggered for {len(floors)} floors"}
        
    except Exception as e:
        logger.error(f"Error triggering cleanup for all floors: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger cleanup: {str(e)}")

@router.get("/floors/{floor_id}/snapshots")
async def get_floor_snapshots(
    floor_id: str,
    limit: int = 50,
    offset: int = 0,
    service: AutoSnapshotService = Depends(get_auto_snapshot_service)
):
    """Get snapshots for a specific floor"""
    try:
        snapshots = await service._get_floor_snapshots(floor_id)
        
        # Apply pagination
        total = len(snapshots)
        snapshots = snapshots[offset:offset + limit]
        
        return {
            "snapshots": snapshots,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error getting floor snapshots: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get floor snapshots: {str(e)}")

@router.get("/floors/{floor_id}/activity")
async def get_floor_activity(
    floor_id: str,
    service: AutoSnapshotService = Depends(get_auto_snapshot_service)
):
    """Get activity data for a specific floor"""
    try:
        activity = service.scheduler.floor_activity.get(floor_id, {})
        history = list(service.scheduler.snapshot_history.get(floor_id, []))
        
        return {
            "floor_id": floor_id,
            "activity": activity,
            "snapshot_history": [ts.isoformat() for ts in history],
            "total_snapshots": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting floor activity: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get floor activity: {str(e)}")

@router.post("/floors/{floor_id}/activate")
async def activate_floor(
    floor_id: str,
    service: AutoSnapshotService = Depends(get_auto_snapshot_service)
):
    """Activate auto-snapshot for a specific floor"""
    try:
        service.active_floors.add(floor_id)
        logger.info(f"Auto-snapshot activated for floor {floor_id}")
        
        return {"message": f"Auto-snapshot activated for floor {floor_id}"}
        
    except Exception as e:
        logger.error(f"Error activating floor: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to activate floor: {str(e)}")

@router.post("/floors/{floor_id}/deactivate")
async def deactivate_floor(
    floor_id: str,
    service: AutoSnapshotService = Depends(get_auto_snapshot_service)
):
    """Deactivate auto-snapshot for a specific floor"""
    try:
        service.active_floors.discard(floor_id)
        logger.info(f"Auto-snapshot deactivated for floor {floor_id}")
        
        return {"message": f"Auto-snapshot deactivated for floor {floor_id}"}
        
    except Exception as e:
        logger.error(f"Error deactivating floor: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to deactivate floor: {str(e)}")

@router.get("/active-floors")
async def get_active_floors(service: AutoSnapshotService = Depends(get_auto_snapshot_service)):
    """Get list of active floors"""
    try:
        return {
            "active_floors": list(service.active_floors),
            "count": len(service.active_floors)
        }
        
    except Exception as e:
        logger.error(f"Error getting active floors: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active floors: {str(e)}")

@router.post("/reset")
async def reset_service(service: AutoSnapshotService = Depends(get_auto_snapshot_service)):
    """Reset the auto-snapshot service"""
    try:
        # Stop current service
        await service.stop()
        
        # Create new service
        global auto_snapshot_service
        auto_snapshot_service = create_auto_snapshot_service()
        await auto_snapshot_service.start()
        
        logger.info("Auto-snapshot service reset")
        return {"message": "Auto-snapshot service reset successfully"}
        
    except Exception as e:
        logger.error(f"Error resetting service: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset service: {str(e)}")

# Background task functions
async def _run_cleanup(service: AutoSnapshotService, floor_id: str):
    """Run cleanup for a specific floor"""
    try:
        snapshots = await service._get_floor_snapshots(floor_id)
        cleaned_snapshots = await service.cleanup_manager.cleanup_old_snapshots(
            floor_id, snapshots
        )
        await service._update_floor_snapshots(floor_id, cleaned_snapshots)
        
        logger.info(f"Cleanup completed for floor {floor_id}")
        
    except Exception as e:
        logger.error(f"Error running cleanup for floor {floor_id}: {e}")

# Health check endpoint
@router.get("/health")
async def health_check(service: AutoSnapshotService = Depends(get_auto_snapshot_service)):
    """Health check for auto-snapshot service"""
    try:
        stats = service.get_service_stats()
        return {
            "status": "healthy" if stats['running'] else "unhealthy",
            "service": "auto-snapshot",
            "running": stats['running'],
            "active_floors": stats['active_floors']
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "auto-snapshot",
            "error": str(e)
        } 