#!/usr/bin/env python3
"""
Data API Structuring Router

Provides RESTful API endpoints for structured JSON responses with system object lists,
filtering, pagination, contributor attribution, and data anonymization.
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Body
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging

from services.data_api_structuring import (
    DataAPIStructuringService, QueryFilter, ObjectType, ObjectStatus, 
    ObjectCondition, ContributorRole
)
from utils.logger import get_logger

logger = get_logger(__name__)

# Initialize router
router = APIRouter(prefix="/data", tags=["Data API Structuring"])

# Initialize service
data_service = DataAPIStructuringService()


# System Objects Endpoints

@router.get("/systems")
async def get_systems(
    object_type: Optional[str] = Query(None, description="Filter by object type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    condition: Optional[str] = Query(None, description="Filter by condition"),
    contributor_id: Optional[str] = Query(None, description="Filter by contributor ID"),
    date_from: Optional[str] = Query(None, description="Filter by installation date from (ISO format)"),
    date_to: Optional[str] = Query(None, description="Filter by installation date to (ISO format)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Page size"),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    user_id: Optional[str] = Query(None, description="User ID for access control"),
    user_license_level: str = Query("basic", description="User license level")
) -> Dict[str, Any]:
    """
    Get system objects with filtering, pagination, and anonymization.
    
    Args:
        object_type: Filter by object type
        status: Filter by status
        condition: Filter by condition
        contributor_id: Filter by contributor ID
        date_from: Filter by installation date from
        date_to: Filter by installation date to
        page: Page number
        page_size: Page size
        sort_by: Sort by field
        sort_order: Sort order
        user_id: User ID for access control
        user_license_level: User license level for anonymization
        
    Returns:
        System objects with pagination and anonymization info
    """
    try:
        # Build filters
        filters = QueryFilter()
        
        if object_type:
            try:
                filters.object_type = ObjectType(object_type.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid object type: {object_type}")
        
        if status:
            try:
                filters.status = ObjectStatus(status.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        if condition:
            try:
                filters.condition = ObjectCondition(condition.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid condition: {condition}")
        
        if contributor_id:
            filters.contributor_id = contributor_id
        
        if date_from:
            try:
                filters.date_from = datetime.fromisoformat(date_from)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid date_from format: {date_from}")
        
        if date_to:
            try:
                filters.date_to = datetime.fromisoformat(date_to)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid date_to format: {date_to}")
        
        # Query objects
        result = data_service.query_system_objects(
            filters=filters,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            user_id=user_id,
            user_license_level=user_license_level
        )
        
        return {
            "status": "success",
            "data": {
                "objects": [asdict(obj) for obj in result.objects],
                "pagination": asdict(result.pagination),
                "filters_applied": result.filters_applied,
                "query_time": result.query_time,
                "anonymized_count": result.anonymized_count
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get systems failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/systems/{object_id}")
async def get_system_object(
    object_id: str,
    user_id: Optional[str] = Query(None, description="User ID for access control"),
    user_license_level: str = Query("basic", description="User license level")
) -> Dict[str, Any]:
    """
    Get a specific system object by ID.
    
    Args:
        object_id: Object ID to retrieve
        user_id: User ID for access control
        user_license_level: User license level for anonymization
        
    Returns:
        System object details
    """
    try:
        obj = data_service.get_system_object(
            object_id=object_id,
            user_id=user_id,
            user_license_level=user_license_level
        )
        
        if not obj:
            raise HTTPException(status_code=404, detail=f"Object {object_id} not found")
        
        return {
            "status": "success",
            "data": asdict(obj),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get system object failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/objects")
async def get_objects(
    object_type: Optional[str] = Query(None, description="Filter by object type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    condition: Optional[str] = Query(None, description="Filter by condition"),
    contributor_id: Optional[str] = Query(None, description="Filter by contributor ID"),
    date_from: Optional[str] = Query(None, description="Filter by installation date from (ISO format)"),
    date_to: Optional[str] = Query(None, description="Filter by installation date to (ISO format)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Page size"),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    user_id: Optional[str] = Query(None, description="User ID for access control"),
    user_license_level: str = Query("basic", description="User license level")
) -> Dict[str, Any]:
    """
    Get objects with filtering, pagination, and anonymization.
    
    Args:
        object_type: Filter by object type
        status: Filter by status
        condition: Filter by condition
        contributor_id: Filter by contributor ID
        date_from: Filter by installation date from
        date_to: Filter by installation date to
        page: Page number
        page_size: Page size
        sort_by: Sort by field
        sort_order: Sort order
        user_id: User ID for access control
        user_license_level: User license level for anonymization
        
    Returns:
        Objects with pagination and anonymization info
    """
    try:
        # Build filters
        filters = QueryFilter()
        
        if object_type:
            try:
                filters.object_type = ObjectType(object_type.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid object type: {object_type}")
        
        if status:
            try:
                filters.status = ObjectStatus(status.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        if condition:
            try:
                filters.condition = ObjectCondition(condition.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid condition: {condition}")
        
        if contributor_id:
            filters.contributor_id = contributor_id
        
        if date_from:
            try:
                filters.date_from = datetime.fromisoformat(date_from)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid date_from format: {date_from}")
        
        if date_to:
            try:
                filters.date_to = datetime.fromisoformat(date_to)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid date_to format: {date_to}")
        
        # Query objects
        result = data_service.query_system_objects(
            filters=filters,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            user_id=user_id,
            user_license_level=user_license_level
        )
        
        return {
            "status": "success",
            "data": {
                "objects": [asdict(obj) for obj in result.objects],
                "pagination": asdict(result.pagination),
                "filters_applied": result.filters_applied,
                "query_time": result.query_time,
                "anonymized_count": result.anonymized_count
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get objects failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/objects/{object_id}")
async def get_object(
    object_id: str,
    user_id: Optional[str] = Query(None, description="User ID for access control"),
    user_license_level: str = Query("basic", description="User license level")
) -> Dict[str, Any]:
    """
    Get a specific object by ID.
    
    Args:
        object_id: Object ID to retrieve
        user_id: User ID for access control
        user_license_level: User license level for anonymization
        
    Returns:
        Object details
    """
    try:
        obj = data_service.get_system_object(
            object_id=object_id,
            user_id=user_id,
            user_license_level=user_license_level
        )
        
        if not obj:
            raise HTTPException(status_code=404, detail=f"Object {object_id} not found")
        
        return {
            "status": "success",
            "data": asdict(obj),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get object failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Contributor Endpoints

@router.get("/contributors/{contributor_id}/objects")
async def get_objects_by_contributor(
    contributor_id: str,
    object_type: Optional[str] = Query(None, description="Filter by object type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    condition: Optional[str] = Query(None, description="Filter by condition"),
    date_from: Optional[str] = Query(None, description="Filter by installation date from (ISO format)"),
    date_to: Optional[str] = Query(None, description="Filter by installation date to (ISO format)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Page size"),
    user_id: Optional[str] = Query(None, description="User ID for access control"),
    user_license_level: str = Query("basic", description="User license level")
) -> Dict[str, Any]:
    """
    Get objects by contributor with filtering and pagination.
    
    Args:
        contributor_id: Contributor ID to filter by
        object_type: Filter by object type
        status: Filter by status
        condition: Filter by condition
        date_from: Filter by installation date from
        date_to: Filter by installation date to
        page: Page number
        page_size: Page size
        user_id: User ID for access control
        user_license_level: User license level for anonymization
        
    Returns:
        Objects by contributor with pagination and anonymization info
    """
    try:
        # Build filters
        filters = QueryFilter()
        
        if object_type:
            try:
                filters.object_type = ObjectType(object_type.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid object type: {object_type}")
        
        if status:
            try:
                filters.status = ObjectStatus(status.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        if condition:
            try:
                filters.condition = ObjectCondition(condition.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid condition: {condition}")
        
        if date_from:
            try:
                filters.date_from = datetime.fromisoformat(date_from)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid date_from format: {date_from}")
        
        if date_to:
            try:
                filters.date_to = datetime.fromisoformat(date_to)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid date_to format: {date_to}")
        
        # Query objects by contributor
        result = data_service.get_objects_by_contributor(
            contributor_id=contributor_id,
            filters=filters,
            page=page,
            page_size=page_size,
            user_id=user_id,
            user_license_level=user_license_level
        )
        
        return {
            "status": "success",
            "data": {
                "contributor_id": contributor_id,
                "objects": [asdict(obj) for obj in result.objects],
                "pagination": asdict(result.pagination),
                "filters_applied": result.filters_applied,
                "query_time": result.query_time,
                "anonymized_count": result.anonymized_count
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get objects by contributor failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Summary and Analytics Endpoints

@router.get("/summary")
async def get_system_summary(
    user_id: Optional[str] = Query(None, description="User ID for access control"),
    user_license_level: str = Query("basic", description="User license level")
) -> Dict[str, Any]:
    """
    Get system summary statistics.
    
    Args:
        user_id: User ID for access control
        user_license_level: User license level for anonymization
        
    Returns:
        System summary statistics
    """
    try:
        summary = data_service.get_system_summary(
            user_id=user_id,
            user_license_level=user_license_level
        )
        
        return {
            "status": "success",
            "data": summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get system summary failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics")
async def get_access_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
) -> Dict[str, Any]:
    """
    Get access analytics for the specified period.
    
    Args:
        days: Number of days to analyze
        
    Returns:
        Access analytics data
    """
    try:
        analytics = data_service.get_access_analytics(days=days)
        
        return {
            "status": "success",
            "data": analytics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get access analytics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Export Endpoints

@router.get("/export")
async def export_objects(
    object_type: Optional[str] = Query(None, description="Filter by object type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    condition: Optional[str] = Query(None, description="Filter by condition"),
    contributor_id: Optional[str] = Query(None, description="Filter by contributor ID"),
    date_from: Optional[str] = Query(None, description="Filter by installation date from (ISO format)"),
    date_to: Optional[str] = Query(None, description="Filter by installation date to (ISO format)"),
    format: str = Query("json", description="Export format (json, csv)"),
    user_id: Optional[str] = Query(None, description="User ID for access control"),
    user_license_level: str = Query("basic", description="User license level")
) -> Dict[str, Any]:
    """
    Export objects in specified format.
    
    Args:
        object_type: Filter by object type
        status: Filter by status
        condition: Filter by condition
        contributor_id: Filter by contributor ID
        date_from: Filter by installation date from
        date_to: Filter by installation date to
        format: Export format (json, csv)
        user_id: User ID for access control
        user_license_level: User license level for anonymization
        
    Returns:
        Exported data
    """
    try:
        if format.lower() not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
        
        # Build filters
        filters = QueryFilter()
        
        if object_type:
            try:
                filters.object_type = ObjectType(object_type.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid object type: {object_type}")
        
        if status:
            try:
                filters.status = ObjectStatus(status.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        if condition:
            try:
                filters.condition = ObjectCondition(condition.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid condition: {condition}")
        
        if contributor_id:
            filters.contributor_id = contributor_id
        
        if date_from:
            try:
                filters.date_from = datetime.fromisoformat(date_from)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid date_from format: {date_from}")
        
        if date_to:
            try:
                filters.date_to = datetime.fromisoformat(date_to)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid date_to format: {date_to}")
        
        # Export objects
        exported_data = data_service.export_objects(
            filters=filters,
            format=format,
            user_id=user_id,
            user_license_level=user_license_level
        )
        
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
        logger.error(f"Export objects failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Status and Health Endpoints

@router.get("/status")
async def get_data_api_status() -> Dict[str, Any]:
    """
    Get Data API service status.
    
    Returns:
        Service status information
    """
    try:
        metrics = data_service.get_performance_metrics()
        
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
        logger.error(f"Failed to get data API status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def data_api_health_check() -> Dict[str, Any]:
    """
    Health check for Data API service.
    
    Returns:
        Service health status and metrics
    """
    try:
        metrics = data_service.get_performance_metrics()
        
        if "error" in metrics:
            return {
                "status": "error",
                "data": {
                    "healthy": False,
                    "error": metrics["error"],
                    "service": "Data API Structuring"
                },
                "timestamp": datetime.now().isoformat()
            }
        
        # Check service health
        is_healthy = (
            metrics.get("total_objects", 0) >= 0 and
            metrics.get("avg_response_time", 0) >= 0
        )
        
        return {
            "status": "success",
            "data": {
                "healthy": is_healthy,
                "metrics": metrics,
                "service": "Data API Structuring",
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
                "service": "Data API Structuring"
            },
            "timestamp": datetime.now().isoformat()
        }


# Filter and Options Endpoints

@router.get("/filters/object-types")
async def get_object_types() -> Dict[str, Any]:
    """
    Get available object types.
    
    Returns:
        List of available object types
    """
    try:
        object_types = [obj_type.value for obj_type in ObjectType]
        
        return {
            "status": "success",
            "data": {
                "object_types": object_types,
                "count": len(object_types)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get object types failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/filters/statuses")
async def get_statuses() -> Dict[str, Any]:
    """
    Get available object statuses.
    
    Returns:
        List of available object statuses
    """
    try:
        statuses = [status.value for status in ObjectStatus]
        
        return {
            "status": "success",
            "data": {
                "statuses": statuses,
                "count": len(statuses)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get statuses failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/filters/conditions")
async def get_conditions() -> Dict[str, Any]:
    """
    Get available object conditions.
    
    Returns:
        List of available object conditions
    """
    try:
        conditions = [condition.value for condition in ObjectCondition]
        
        return {
            "status": "success",
            "data": {
                "conditions": conditions,
                "count": len(conditions)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get conditions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/filters/contributors")
async def get_contributors() -> Dict[str, Any]:
    """
    Get available contributors.
    
    Returns:
        List of available contributors
    """
    try:
        # This would typically query the contributors table
        # For now, return sample contributors
        contributors = [
            {"contributor_id": "contrib_001", "name": "John Smith", "role": "owner"},
            {"contributor_id": "contrib_002", "name": "Sarah Johnson", "role": "contributor"},
            {"contributor_id": "contrib_003", "name": "Mike Wilson", "role": "viewer"},
            {"contributor_id": "contrib_004", "name": "Lisa Brown", "role": "admin"}
        ]
        
        return {
            "status": "success",
            "data": {
                "contributors": contributors,
                "count": len(contributors)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get contributors failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Advanced Query Endpoints

@router.post("/query")
async def advanced_query(
    filters: Dict[str, Any] = Body(..., description="Query filters"),
    page: int = Body(1, ge=1, description="Page number"),
    page_size: int = Body(50, ge=1, le=1000, description="Page size"),
    sort_by: str = Body("created_at", description="Sort by field"),
    sort_order: str = Body("desc", description="Sort order (asc/desc)"),
    user_id: Optional[str] = Body(None, description="User ID for access control"),
    user_license_level: str = Body("basic", description="User license level")
) -> Dict[str, Any]:
    """
    Advanced query with custom filters.
    
    Args:
        filters: Custom query filters
        page: Page number
        page_size: Page size
        sort_by: Sort by field
        sort_order: Sort order
        user_id: User ID for access control
        user_license_level: User license level for anonymization
        
    Returns:
        Query results with pagination and anonymization info
    """
    try:
        # Build filters from request body
        query_filters = QueryFilter()
        
        if "object_type" in filters:
            try:
                query_filters.object_type = ObjectType(filters["object_type"].lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid object type: {filters['object_type']}")
        
        if "status" in filters:
            try:
                query_filters.status = ObjectStatus(filters["status"].lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {filters['status']}")
        
        if "condition" in filters:
            try:
                query_filters.condition = ObjectCondition(filters["condition"].lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid condition: {filters['condition']}")
        
        if "contributor_id" in filters:
            query_filters.contributor_id = filters["contributor_id"]
        
        if "date_from" in filters:
            try:
                query_filters.date_from = datetime.fromisoformat(filters["date_from"])
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid date_from format: {filters['date_from']}")
        
        if "date_to" in filters:
            try:
                query_filters.date_to = datetime.fromisoformat(filters["date_to"])
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid date_to format: {filters['date_to']}")
        
        # Query objects
        result = data_service.query_system_objects(
            filters=query_filters,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            user_id=user_id,
            user_license_level=user_license_level
        )
        
        return {
            "status": "success",
            "data": {
                "objects": [asdict(obj) for obj in result.objects],
                "pagination": asdict(result.pagination),
                "filters_applied": result.filters_applied,
                "query_time": result.query_time,
                "anonymized_count": result.anonymized_count
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Advanced query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 