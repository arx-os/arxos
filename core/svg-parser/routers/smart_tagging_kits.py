"""
Smart Tagging Kits API Router

Provides RESTful API endpoints for QR + BLE tag assignment, scanning,
resolution, and management with offline capabilities.
"""

from fastapi import APIRouter, HTTPException, Body, Query, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import logging

from services.smart_tagging_kits import (
    SmartTaggingService, TagType, TagStatus, ScanResult
)
from utils.logger import get_logger

logger = get_logger(__name__)

# Initialize router
router = APIRouter(prefix="/smart-tagging", tags=["Smart Tagging Kits"])

# Initialize service
tagging_service = SmartTaggingService()


# Tag Management Endpoints

@router.post("/tags/assign")
async def assign_tag(
    object_id: str = Body(..., description="Object ID to assign tag to"),
    tag_type: str = Body(..., description="Type of tag (qr, ble, hybrid)"),
    tag_data: str = Body(..., description="Tag data content"),
    user_id: str = Body(..., description="User performing the assignment"),
    device_id: str = Body(..., description="Device performing the assignment"),
    metadata: Optional[Dict[str, Any]] = Body(None, description="Additional metadata")
) -> Dict[str, Any]:
    """
    Assign QR or BLE tag to maintainable object.
    
    Args:
        object_id: Object ID to assign tag to
        tag_type: Type of tag (qr, ble, or hybrid)
        tag_data: Tag data content
        user_id: User performing the assignment
        device_id: Device performing the assignment
        metadata: Additional metadata for the assignment
        
    Returns:
        Assignment result with status and details
    """
    try:
        # Validate tag type
        try:
            tag_type_enum = TagType(tag_type.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid tag type: {tag_type}")
        
        result = tagging_service.assign_tag(
            object_id=object_id,
            tag_type=tag_type_enum,
            tag_data=tag_data,
            user_id=user_id,
            device_id=device_id,
            metadata=metadata
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Tag assignment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags/scan/{tag_data}")
async def scan_tag(
    tag_data: str,
    tag_type: str = Query(..., description="Type of tag being scanned"),
    user_id: str = Query(..., description="User performing the scan"),
    device_id: str = Query(..., description="Device performing the scan"),
    location: Optional[Dict[str, float]] = Query(None, description="Optional location data")
) -> Dict[str, Any]:
    """
    Scan and resolve tag to object mapping.
    
    Args:
        tag_data: Tag data to scan
        tag_type: Type of tag being scanned
        user_id: User performing the scan
        device_id: Device performing the scan
        location: Optional location data
        
    Returns:
        Scan result with object information
    """
    try:
        # Validate tag type
        try:
            tag_type_enum = TagType(tag_type.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid tag type: {tag_type}")
        
        result = tagging_service.scan_tag(
            tag_data=tag_data,
            tag_type=tag_type_enum,
            user_id=user_id,
            device_id=device_id,
            location=location
        )
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Tag scanning failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags/resolve/{tag_data}")
async def resolve_tag(
    tag_data: str,
    tag_type: str = Query(..., description="Type of tag to resolve")
) -> Dict[str, Any]:
    """
    Resolve tag to object mapping (offline capable).
    
    Args:
        tag_data: Tag data to resolve
        tag_type: Type of tag to resolve
        
    Returns:
        Object resolution result
    """
    try:
        # Validate tag type
        try:
            tag_type_enum = TagType(tag_type.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid tag type: {tag_type}")
        
        result = tagging_service.resolve_object(tag_data, tag_type_enum)
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Tag resolution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags/history/{tag_data}")
async def get_tag_history(
    tag_data: str
) -> Dict[str, Any]:
    """
    Get complete tag assignment and usage history.
    
    Args:
        tag_data: Tag data to get history for
        
    Returns:
        List of historical events for the tag
    """
    try:
        history = tagging_service.get_tag_history(tag_data)
        
        return {
            "status": "success",
            "data": {
                "tag_data": tag_data,
                "history": history,
                "total_events": len(history)
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get tag history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/tags/update")
async def update_tag_mapping(
    tag_data: str = Body(..., description="Tag data to update"),
    object_id: str = Body(..., description="New object ID to assign"),
    user_id: str = Body(..., description="User performing the update"),
    device_id: str = Body(..., description="Device performing the update"),
    metadata: Optional[Dict[str, Any]] = Body(None, description="Additional metadata")
) -> Dict[str, Any]:
    """
    Update tag-to-object mapping.
    
    Args:
        tag_data: Tag data to update
        object_id: New object ID to assign
        user_id: User performing the update
        device_id: Device performing the update
        metadata: Additional metadata
        
    Returns:
        Update result
    """
    try:
        success = tagging_service.update_tag_mapping(
            tag_data=tag_data,
            object_id=object_id,
            user_id=user_id,
            device_id=device_id,
            metadata=metadata
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update tag mapping")
        
        return {
            "status": "success",
            "data": {
                "tag_data": tag_data,
                "object_id": object_id,
                "updated_at": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Tag mapping update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tags/remove")
async def remove_tag_assignment(
    tag_data: str = Body(..., description="Tag data to remove assignment from"),
    user_id: str = Body(..., description="User performing the removal"),
    device_id: str = Body(..., description="Device performing the removal")
) -> Dict[str, Any]:
    """
    Remove tag assignment from object.
    
    Args:
        tag_data: Tag data to remove assignment from
        user_id: User performing the removal
        device_id: Device performing the removal
        
    Returns:
        Removal result
    """
    try:
        success = tagging_service.remove_tag_assignment(
            tag_data=tag_data,
            user_id=user_id,
            device_id=device_id
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to remove tag assignment")
        
        return {
            "status": "success",
            "data": {
                "tag_data": tag_data,
                "removed_at": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Tag assignment removal failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags/object/{object_id}")
async def get_object_tags(
    object_id: str
) -> Dict[str, Any]:
    """
    Get all tags assigned to an object.
    
    Args:
        object_id: Object ID to get tags for
        
    Returns:
        List of tags assigned to the object
    """
    try:
        tags = tagging_service.get_object_tags(object_id)
        
        return {
            "status": "success",
            "data": {
                "object_id": object_id,
                "tags": tags,
                "total_tags": len(tags)
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get object tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Bulk Operations

@router.post("/tags/bulk-assign")
async def bulk_assign_tags(
    assignments: List[Dict[str, Any]] = Body(..., description="List of tag assignments")
) -> Dict[str, Any]:
    """
    Bulk assign multiple tags to objects.
    
    Args:
        assignments: List of assignment dictionaries
        
    Returns:
        Bulk assignment results
    """
    try:
        result = tagging_service.bulk_assign_tags(assignments)
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Bulk tag assignment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Import/Export Operations

@router.get("/tags/export")
async def export_tag_data(
    format: str = Query("json", description="Export format (json, csv)")
) -> Dict[str, Any]:
    """
    Export tag data in specified format.
    
    Args:
        format: Export format (json, csv)
        
    Returns:
        Exported data
    """
    try:
        if format.lower() not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
        
        exported_data = tagging_service.export_tag_data(format)
        
        if not exported_data:
            raise HTTPException(status_code=500, detail="Failed to export tag data")
        
        return {
            "status": "success",
            "data": {
                "format": format,
                "data": exported_data,
                "exported_at": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Tag data export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tags/import")
async def import_tag_data(
    data: str = Body(..., description="Data to import"),
    format: str = Body(..., description="Import format (json, csv)")
) -> Dict[str, Any]:
    """
    Import tag data from specified format.
    
    Args:
        data: Data to import
        format: Import format (json, csv)
        
    Returns:
        Import results
    """
    try:
        if format.lower() not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
        
        result = tagging_service.import_tag_data(data, format)
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Tag data import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Analytics and Reporting

@router.get("/tags/analytics")
async def get_tag_analytics(
    period_days: int = Query(30, description="Number of days to analyze")
) -> Dict[str, Any]:
    """
    Get tag analytics and usage statistics.
    
    Args:
        period_days: Number of days to analyze
        
    Returns:
        Analytics data
    """
    try:
        if period_days < 1 or period_days > 365:
            raise HTTPException(status_code=400, detail="Period must be between 1 and 365 days")
        
        analytics = tagging_service.get_analytics(period_days)
        
        if "error" in analytics:
            raise HTTPException(status_code=500, detail=analytics["error"])
        
        return {
            "status": "success",
            "data": analytics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Analytics generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Validation and Testing

@router.post("/tags/validate")
async def validate_tag(
    tag_data: str = Body(..., description="Tag data to validate"),
    tag_type: str = Body(..., description="Type of tag to validate")
) -> Dict[str, Any]:
    """
    Validate tag format and uniqueness.
    
    Args:
        tag_data: Tag data to validate
        tag_type: Type of tag to validate
        
    Returns:
        Validation result
    """
    try:
        # Validate tag type
        try:
            tag_type_enum = TagType(tag_type.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid tag type: {tag_type}")
        
        result = tagging_service.validate_tag(tag_data, tag_type_enum)
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Tag validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Status and Information

@router.get("/tags/status")
async def get_tagging_status() -> Dict[str, Any]:
    """
    Get overall tagging service status.
    
    Returns:
        Service status information
    """
    try:
        metrics = tagging_service.get_performance_metrics()
        
        if "error" in metrics:
            raise HTTPException(status_code=500, detail=metrics["error"])
        
        return {
            "status": "success",
            "data": {
                "service_status": "operational",
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get tagging status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags/inventory")
async def get_tag_inventory(
    status: Optional[str] = Query(None, description="Filter by tag status"),
    tag_type: Optional[str] = Query(None, description="Filter by tag type"),
    limit: int = Query(100, description="Maximum number of results"),
    offset: int = Query(0, description="Number of results to skip")
) -> Dict[str, Any]:
    """
    Get tag inventory with filtering options.
    
    Args:
        status: Optional status filter
        tag_type: Optional tag type filter
        limit: Maximum number of results
        offset: Number of results to skip
        
    Returns:
        Tag inventory with filtering and pagination
    """
    try:
        # Get all tags from service
        all_tags = []
        for tag_id, tag_data in tagging_service.tag_database.items():
            tag_dict = {
                "tag_id": tag_data.tag_id,
                "tag_type": tag_data.tag_type.value,
                "tag_data": tag_data.tag_data,
                "object_id": tag_data.object_id,
                "status": tag_data.status.value,
                "created_at": tag_data.created_at.isoformat(),
                "assigned_at": tag_data.assigned_at.isoformat() if tag_data.assigned_at else None,
                "scan_count": tag_data.scan_count,
                "last_scan_at": tag_data.last_scan_at.isoformat() if tag_data.last_scan_at else None,
                "device_id": tag_data.device_id,
                "user_id": tag_data.user_id
            }
            
            # Apply filters
            if status and tag_data.status.value != status:
                continue
            if tag_type and tag_data.tag_type.value != tag_type:
                continue
            
            all_tags.append(tag_dict)
        
        # Apply pagination
        total_count = len(all_tags)
        paginated_results = all_tags[offset:offset + limit]
        
        return {
            "status": "success",
            "data": {
                "tags": paginated_results,
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count,
                "filters": {
                    "status": status,
                    "tag_type": tag_type
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get tag inventory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health and Diagnostic Endpoints

@router.get("/health")
async def tagging_health_check() -> Dict[str, Any]:
    """
    Health check for tagging service.
    
    Returns:
        Service health status and metrics
    """
    try:
        metrics = tagging_service.get_performance_metrics()
        
        if "error" in metrics:
            return {
                "status": "error",
                "data": {
                    "healthy": False,
                    "error": metrics["error"],
                    "service": "Smart Tagging Kits"
                },
                "timestamp": datetime.now().isoformat()
            }
        
        # Check service health
        is_healthy = (
            metrics.get("total_tags", 0) >= 0 and
            metrics.get("assignment_rate", 0) >= 0 and
            metrics.get("avg_response_time", 0) >= 0
        )
        
        return {
            "status": "success",
            "data": {
                "healthy": is_healthy,
                "metrics": metrics,
                "service": "Smart Tagging Kits",
                "version": "1.0.0"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "data": {
                "healthy": False,
                "error": str(e),
                "service": "Smart Tagging Kits"
            },
            "timestamp": datetime.now().isoformat()
        }


@router.get("/diagnostics")
async def tagging_diagnostics() -> Dict[str, Any]:
    """
    Get detailed diagnostics for tagging service.
    
    Returns:
        Detailed diagnostic information
    """
    try:
        metrics = tagging_service.get_performance_metrics()
        
        diagnostics = {
            "service_status": "operational",
            "database_status": "connected",
            "total_tags": metrics.get("total_tags", 0),
            "assigned_tags": metrics.get("assigned_tags", 0),
            "assignment_rate": metrics.get("assignment_rate", 0),
            "total_scans": metrics.get("total_scans", 0),
            "avg_response_time": metrics.get("avg_response_time", 0),
            "cache_size": metrics.get("cache_size", 0),
            "database_size": metrics.get("database_size", 0),
            "performance_metrics": metrics
        }
        
        return {
            "status": "success",
            "data": diagnostics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Diagnostics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Advanced Features

@router.post("/tags/generate")
async def generate_tag(
    tag_type: str = Body(..., description="Type of tag to generate"),
    prefix: Optional[str] = Body(None, description="Optional prefix for tag data"),
    metadata: Optional[Dict[str, Any]] = Body(None, description="Additional metadata")
) -> Dict[str, Any]:
    """
    Generate a new tag with specified type.
    
    Args:
        tag_type: Type of tag to generate
        prefix: Optional prefix for tag data
        metadata: Additional metadata
        
    Returns:
        Generated tag information
    """
    try:
        # Validate tag type
        try:
            tag_type_enum = TagType(tag_type.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid tag type: {tag_type}")
        
        # Generate tag data
        import uuid
        import time
        
        if tag_type_enum == TagType.QR:
            tag_data = f"{prefix or 'QR'}{int(time.time())}{uuid.uuid4().hex[:8]}"
        elif tag_type_enum == TagType.BLE:
            tag_data = uuid.uuid4().hex[:16]
        elif tag_type_enum == TagType.HYBRID:
            qr_part = f"{prefix or 'QR'}{int(time.time())}{uuid.uuid4().hex[:8]}"
            ble_part = uuid.uuid4().hex[:16]
            tag_data = f"{qr_part}:{ble_part}"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported tag type: {tag_type}")
        
        # Validate generated tag
        validation_result = tagging_service.validate_tag(tag_data, tag_type_enum)
        
        if not validation_result["valid"]:
            raise HTTPException(status_code=500, detail=f"Generated tag validation failed: {validation_result['error']}")
        
        return {
            "status": "success",
            "data": {
                "tag_data": tag_data,
                "tag_type": tag_type_enum.value,
                "generated_at": datetime.now().isoformat(),
                "metadata": metadata or {}
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Tag generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tags/cleanup")
async def cleanup_tags(
    days_old: int = Body(90, description="Remove tags older than specified days"),
    dry_run: bool = Body(True, description="Perform dry run without actual deletion")
) -> Dict[str, Any]:
    """
    Clean up old unused tags.
    
    Args:
        days_old: Remove tags older than specified days
        dry_run: Perform dry run without actual deletion
        
    Returns:
        Cleanup results
    """
    try:
        if days_old < 1:
            raise HTTPException(status_code=400, detail="Days must be at least 1")
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Find old unused tags
        old_tags = []
        for tag in tagging_service.tag_database.values():
            if (tag.created_at < cutoff_date and 
                tag.status == TagStatus.UNASSIGNED and 
                tag.scan_count == 0):
                old_tags.append(tag)
        
        if dry_run:
            return {
                "status": "success",
                "data": {
                    "dry_run": True,
                    "tags_to_remove": len(old_tags),
                    "cutoff_date": cutoff_date.isoformat(),
                    "message": f"Would remove {len(old_tags)} old unused tags"
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Actually remove the tags
            removed_count = 0
            for tag in old_tags:
                try:
                    del tagging_service.tag_database[tag.tag_id]
                    removed_count += 1
                except Exception as e:
                    logger.error(f"Failed to remove tag {tag.tag_id}: {e}")
            
            return {
                "status": "success",
                "data": {
                    "dry_run": False,
                    "tags_removed": removed_count,
                    "cutoff_date": cutoff_date.isoformat(),
                    "message": f"Removed {removed_count} old unused tags"
                },
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Tag cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 