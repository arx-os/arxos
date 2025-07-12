#!/usr/bin/env python3
"""
AHJ API Router for Arxos Platform

This router provides secure RESTful endpoints for AHJ (Authorities Having Jurisdiction)
interactions with comprehensive validation, error handling, and audit trail logging.

Endpoints:
- POST /api/v1/ahj/inspections - Create new inspection
- GET /api/v1/ahj/inspections - List inspections
- GET /api/v1/ahj/inspections/{id} - Get inspection details
- POST /api/v1/ahj/inspections/{id}/annotations - Add annotation
- GET /api/v1/ahj/inspections/{id}/audit - Get audit trail
- POST /api/v1/ahj/inspections/{id}/violations - Add code violation
- PUT /api/v1/ahj/inspections/{id}/status - Update inspection status
- GET /api/v1/ahj/inspections/{id}/export - Export inspection data
- GET /api/v1/ahj/statistics - Get inspection statistics
- POST /api/v1/ahj/permissions - Manage user permissions
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, status, Query, Path as PathParam
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from services.ahj_api_service import (
    AHJAPIService, Inspection, Annotation, Violation, AuditEvent,
    InspectionStatus, AnnotationType, Coordinates, PermissionLevel
)
from services.advanced_security import AdvancedSecurityService
from utils.logger import setup_logger

# Initialize router
router = APIRouter(prefix="/api/v1/ahj", tags=["AHJ API"])

# Initialize services
ahj_service = AHJAPIService()
security_service = AdvancedSecurityService()
logger = setup_logger("ahj_api_router", level=logging.INFO)

# Pydantic models for request/response validation
class CreateInspectionRequest(BaseModel):
    """Request model for creating a new inspection."""
    building_id: str = Field(..., description="Building ID for the inspection")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('building_id')
    def validate_building_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Building ID is required')
        return v.strip()

class CoordinatesRequest(BaseModel):
    """Request model for coordinates."""
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    z: Optional[float] = Field(None, description="Z coordinate")
    floor: Optional[str] = Field(None, description="Floor identifier")
    room: Optional[str] = Field(None, description="Room identifier")
    
    @validator('x', 'y')
    def validate_coordinates(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError('Coordinates must be numeric')
        return float(v)

class AddAnnotationRequest(BaseModel):
    """Request model for adding an annotation."""
    object_id: str = Field(..., description="Object ID for the annotation")
    annotation_type: AnnotationType = Field(..., description="Type of annotation")
    content: str = Field(..., description="Annotation content", min_length=1, max_length=10000)
    coordinates: CoordinatesRequest = Field(..., description="Annotation coordinates")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('object_id')
    def validate_object_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Object ID is required')
        return v.strip()
    
    @validator('content')
    def validate_content(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Content is required')
        return v.strip()

class AddViolationRequest(BaseModel):
    """Request model for adding a code violation."""
    object_id: str = Field(..., description="Object ID for the violation")
    code_section: str = Field(..., description="Code section reference", min_length=1, max_length=100)
    description: str = Field(..., description="Violation description", min_length=1, max_length=2000)
    severity: str = Field(..., description="Violation severity", regex="^(low|medium|high|critical)$")
    
    @validator('object_id')
    def validate_object_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Object ID is required')
        return v.strip()
    
    @validator('code_section')
    def validate_code_section(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Code section is required')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Description is required')
        return v.strip()

class UpdateStatusRequest(BaseModel):
    """Request model for updating inspection status."""
    status: InspectionStatus = Field(..., description="New inspection status")

class PermissionRequest(BaseModel):
    """Request model for managing user permissions."""
    user_id: str = Field(..., description="User ID")
    permission: str = Field(..., description="Permission to add/remove")
    action: str = Field(..., description="Action: 'add' or 'remove'", regex="^(add|remove)$")
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('User ID is required')
        return v.strip()
    
    @validator('permission')
    def validate_permission(cls, v):
        valid_permissions = ['read', 'write', 'admin', 'inspector', 'reviewer']
        if v not in valid_permissions:
            raise ValueError(f'Invalid permission. Must be one of: {valid_permissions}')
        return v

# Response models
class InspectionResponse(BaseModel):
    """Response model for inspection data."""
    id: str
    building_id: str
    inspector_id: str
    inspection_date: datetime
    status: InspectionStatus
    annotations_count: int
    violations_count: int
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

class AnnotationResponse(BaseModel):
    """Response model for annotation data."""
    id: str
    inspection_id: str
    object_id: str
    annotation_type: AnnotationType
    content: str
    coordinates: Dict[str, Any]
    timestamp: datetime
    inspector_id: str
    immutable_hash: str
    metadata: Dict[str, Any]

class ViolationResponse(BaseModel):
    """Response model for violation data."""
    id: str
    inspection_id: str
    object_id: str
    code_section: str
    description: str
    severity: str
    timestamp: datetime
    inspector_id: str
    status: str
    resolution_date: Optional[datetime]
    immutable_hash: str

class AuditEventResponse(BaseModel):
    """Response model for audit event data."""
    event_id: str
    inspection_id: str
    user_id: str
    action: str
    resource: str
    timestamp: datetime
    details: Dict[str, Any]
    immutable_hash: str

class StatisticsResponse(BaseModel):
    """Response model for inspection statistics."""
    total_inspections: int
    status_counts: Dict[str, int]
    total_annotations: int
    total_violations: int
    average_annotations_per_inspection: float
    average_violations_per_inspection: float

# Authentication dependency (simplified for demo)
async def get_current_user() -> str:
    """Get current user ID from authentication."""
    # In production, this would extract user from JWT token
    # For demo purposes, we'll use a header or query parameter
    return "demo_inspector_001"

async def get_admin_user() -> str:
    """Get admin user ID for administrative operations."""
    # In production, this would validate admin permissions
    return "demo_admin_001"

# API Endpoints

@router.post("/inspections", response_model=InspectionResponse, status_code=status.HTTP_201_CREATED)
async def create_inspection(
    request: CreateInspectionRequest,
    current_user: str = Depends(get_current_user)
):
    """Create a new inspection."""
    try:
        logger.info(f"Creating inspection for building {request.building_id} by user {current_user}")
        
        inspection = await ahj_service.create_inspection(
            building_id=request.building_id,
            inspector_id=current_user,
            metadata=request.metadata
        )
        
        return InspectionResponse(
            id=inspection.id,
            building_id=inspection.building_id,
            inspector_id=inspection.inspector_id,
            inspection_date=inspection.inspection_date,
            status=inspection.status,
            annotations_count=len(inspection.annotations),
            violations_count=len(inspection.violations),
            created_at=inspection.created_at,
            updated_at=inspection.updated_at,
            metadata=inspection.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create inspection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create inspection"
        )

@router.get("/inspections", response_model=List[InspectionResponse])
async def list_inspections(
    building_id: Optional[str] = Query(None, description="Filter by building ID"),
    status: Optional[InspectionStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of inspections to return"),
    offset: int = Query(0, ge=0, description="Number of inspections to skip"),
    current_user: str = Depends(get_current_user)
):
    """List inspections with filtering and pagination."""
    try:
        logger.info(f"Listing inspections for user {current_user}")
        
        inspections = await ahj_service.list_inspections(
            user_id=current_user,
            building_id=building_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return [
            InspectionResponse(
                id=inspection.id,
                building_id=inspection.building_id,
                inspector_id=inspection.inspector_id,
                inspection_date=inspection.inspection_date,
                status=inspection.status,
                annotations_count=len(inspection.annotations),
                violations_count=len(inspection.violations),
                created_at=inspection.created_at,
                updated_at=inspection.updated_at,
                metadata=inspection.metadata
            )
            for inspection in inspections
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list inspections: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list inspections"
        )

@router.get("/inspections/{inspection_id}", response_model=InspectionResponse)
async def get_inspection(
    inspection_id: str = PathParam(..., description="Inspection ID"),
    current_user: str = Depends(get_current_user)
):
    """Get inspection details."""
    try:
        logger.info(f"Getting inspection {inspection_id} for user {current_user}")
        
        inspection = await ahj_service.get_inspection(
            inspection_id=inspection_id,
            user_id=current_user
        )
        
        return InspectionResponse(
            id=inspection.id,
            building_id=inspection.building_id,
            inspector_id=inspection.inspector_id,
            inspection_date=inspection.inspection_date,
            status=inspection.status,
            annotations_count=len(inspection.annotations),
            violations_count=len(inspection.violations),
            created_at=inspection.created_at,
            updated_at=inspection.updated_at,
            metadata=inspection.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get inspection {inspection_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get inspection"
        )

@router.post("/inspections/{inspection_id}/annotations", response_model=AnnotationResponse, status_code=status.HTTP_201_CREATED)
async def add_annotation(
    inspection_id: str = PathParam(..., description="Inspection ID"),
    request: AddAnnotationRequest = ...,
    current_user: str = Depends(get_current_user)
):
    """Add an annotation to an inspection."""
    try:
        logger.info(f"Adding annotation to inspection {inspection_id} by user {current_user}")
        
        # Convert coordinates request to Coordinates object
        coordinates = Coordinates(
            x=request.coordinates.x,
            y=request.coordinates.y,
            z=request.coordinates.z,
            floor=request.coordinates.floor,
            room=request.coordinates.room
        )
        
        annotation = await ahj_service.add_annotation(
            inspection_id=inspection_id,
            object_id=request.object_id,
            annotation_type=request.annotation_type,
            content=request.content,
            coordinates=coordinates,
            inspector_id=current_user,
            metadata=request.metadata
        )
        
        return AnnotationResponse(
            id=annotation.id,
            inspection_id=annotation.inspection_id,
            object_id=annotation.object_id,
            annotation_type=annotation.annotation_type,
            content=annotation.content,
            coordinates={
                "x": annotation.coordinates.x,
                "y": annotation.coordinates.y,
                "z": annotation.coordinates.z,
                "floor": annotation.coordinates.floor,
                "room": annotation.coordinates.room
            },
            timestamp=annotation.timestamp,
            inspector_id=annotation.inspector_id,
            immutable_hash=annotation.immutable_hash,
            metadata=annotation.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add annotation to inspection {inspection_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add annotation"
        )

@router.post("/inspections/{inspection_id}/violations", response_model=ViolationResponse, status_code=status.HTTP_201_CREATED)
async def add_violation(
    inspection_id: str = PathParam(..., description="Inspection ID"),
    request: AddViolationRequest = ...,
    current_user: str = Depends(get_current_user)
):
    """Add a code violation to an inspection."""
    try:
        logger.info(f"Adding violation to inspection {inspection_id} by user {current_user}")
        
        violation = await ahj_service.add_violation(
            inspection_id=inspection_id,
            object_id=request.object_id,
            code_section=request.code_section,
            description=request.description,
            severity=request.severity,
            inspector_id=current_user
        )
        
        return ViolationResponse(
            id=violation.id,
            inspection_id=violation.inspection_id,
            object_id=violation.object_id,
            code_section=violation.code_section,
            description=violation.description,
            severity=violation.severity,
            timestamp=violation.timestamp,
            inspector_id=violation.inspector_id,
            status=violation.status,
            resolution_date=violation.resolution_date,
            immutable_hash=violation.immutable_hash
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add violation to inspection {inspection_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add violation"
        )

@router.get("/inspections/{inspection_id}/audit", response_model=List[AuditEventResponse])
async def get_audit_trail(
    inspection_id: str = PathParam(..., description="Inspection ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of audit events to return"),
    offset: int = Query(0, ge=0, description="Number of audit events to skip"),
    current_user: str = Depends(get_current_user)
):
    """Get audit trail for an inspection."""
    try:
        logger.info(f"Getting audit trail for inspection {inspection_id} by user {current_user}")
        
        audit_events = await ahj_service.get_audit_trail(
            inspection_id=inspection_id,
            user_id=current_user,
            limit=limit,
            offset=offset
        )
        
        return [
            AuditEventResponse(
                event_id=event.event_id,
                inspection_id=event.inspection_id,
                user_id=event.user_id,
                action=event.action,
                resource=event.resource,
                timestamp=event.timestamp,
                details=event.details,
                immutable_hash=event.immutable_hash
            )
            for event in audit_events
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit trail for inspection {inspection_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit trail"
        )

@router.put("/inspections/{inspection_id}/status", response_model=InspectionResponse)
async def update_inspection_status(
    inspection_id: str = PathParam(..., description="Inspection ID"),
    request: UpdateStatusRequest = ...,
    current_user: str = Depends(get_current_user)
):
    """Update inspection status."""
    try:
        logger.info(f"Updating status for inspection {inspection_id} to {request.status} by user {current_user}")
        
        inspection = await ahj_service.update_inspection_status(
            inspection_id=inspection_id,
            status=request.status,
            user_id=current_user
        )
        
        return InspectionResponse(
            id=inspection.id,
            building_id=inspection.building_id,
            inspector_id=inspection.inspector_id,
            inspection_date=inspection.inspection_date,
            status=inspection.status,
            annotations_count=len(inspection.annotations),
            violations_count=len(inspection.violations),
            created_at=inspection.created_at,
            updated_at=inspection.updated_at,
            metadata=inspection.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update status for inspection {inspection_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update inspection status"
        )

@router.get("/inspections/{inspection_id}/export")
async def export_inspection_data(
    inspection_id: str = PathParam(..., description="Inspection ID"),
    format: str = Query("json", description="Export format (json, csv, pdf)"),
    current_user: str = Depends(get_current_user)
):
    """Export inspection data."""
    try:
        logger.info(f"Exporting inspection {inspection_id} data in {format} format by user {current_user}")
        
        export_data = await ahj_service.export_inspection_data(
            inspection_id=inspection_id,
            user_id=current_user,
            format=format
        )
        
        return JSONResponse(
            content=export_data,
            status_code=status.HTTP_200_OK,
            headers={
                "Content-Disposition": f"attachment; filename=inspection_{inspection_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export inspection {inspection_id} data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export inspection data"
        )

@router.get("/statistics", response_model=StatisticsResponse)
async def get_inspection_statistics(
    current_user: str = Depends(get_current_user)
):
    """Get inspection statistics for the current user."""
    try:
        logger.info(f"Getting inspection statistics for user {current_user}")
        
        statistics = await ahj_service.get_inspection_statistics(
            user_id=current_user
        )
        
        return StatisticsResponse(**statistics)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get inspection statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get inspection statistics"
        )

@router.post("/permissions")
async def manage_user_permissions(
    request: PermissionRequest = ...,
    admin_user: str = Depends(get_admin_user)
):
    """Manage user permissions (admin only)."""
    try:
        logger.info(f"Managing permissions for user {request.user_id} by admin {admin_user}")
        
        if request.action == "add":
            success = await ahj_service.add_user_permission(
                user_id=request.user_id,
                permission=request.permission,
                admin_user_id=admin_user
            )
        else:  # remove
            success = await ahj_service.remove_user_permission(
                user_id=request.user_id,
                permission=request.permission,
                admin_user_id=admin_user
            )
        
        if success:
            return {
                "success": True,
                "message": f"Permission {request.permission} {request.action}ed for user {request.user_id}",
                "user_id": request.user_id,
                "permission": request.permission,
                "action": request.action
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to {request.action} permission {request.permission} for user {request.user_id}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to manage user permissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to manage user permissions"
        )

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for AHJ API."""
    try:
        return {
            "status": "healthy",
            "service": "AHJ API",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

# Error handlers
@router.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with detailed error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions with generic error responses."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    ) 