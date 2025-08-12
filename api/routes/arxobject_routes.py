"""
ArxObject API Routes

This module provides RESTful API endpoints for ArxObject operations,
following the OpenAPI specification and best practices.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
import logging

from core.spatial.arxobject_core import ArxObjectType, ArxObjectPrecision
from core.arxobject.engine import RelationshipType
from core.arxobject.service import (
    ArxObjectService, ArxObjectQuery, ArxObjectUpdate, BulkOperation
)
from api.dependencies import get_arxobject_service, get_current_user

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/arxobjects",
    tags=["ArxObjects"],
    responses={404: {"description": "Not found"}}
)


# ==========================================
# Request/Response Models
# ==========================================

class GeometryModel(BaseModel):
    """Geometry specification for API"""
    x: float = Field(0.0, description="X coordinate in feet")
    y: float = Field(0.0, description="Y coordinate in feet")
    z: float = Field(0.0, description="Z coordinate in feet")
    length: float = Field(1.0, description="Length in feet")
    width: float = Field(1.0, description="Width in feet")
    height: float = Field(1.0, description="Height in feet")
    rotation_x: float = Field(0.0, description="X rotation in radians")
    rotation_y: float = Field(0.0, description="Y rotation in radians")
    rotation_z: float = Field(0.0, description="Z rotation in radians")
    shape_type: str = Field("box", description="Shape type")
    
    class Config:
        schema_extra = {
            "example": {
                "x": 100.0,
                "y": 200.0,
                "z": 10.0,
                "length": 1.0,
                "width": 0.5,
                "height": 0.25
            }
        }


class CreateArxObjectRequest(BaseModel):
    """Request model for creating an ArxObject"""
    object_type: str = Field(..., description="Type of ArxObject")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Object properties")
    geometry: Optional[GeometryModel] = Field(None, description="Object geometry")
    relationships: Optional[List[Dict[str, Any]]] = Field(None, description="Initial relationships")
    constraints: Optional[List[Dict[str, Any]]] = Field(None, description="Constraints to apply")
    tags: Optional[List[str]] = Field(None, description="Object tags")
    
    @validator('object_type')
    def validate_object_type(cls, v):
        try:
            ArxObjectType(v)
        except ValueError:
            raise ValueError(f"Invalid object type: {v}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "object_type": "electrical_outlet",
                "properties": {
                    "voltage": 120,
                    "amperage": 20,
                    "gfci": True
                },
                "geometry": {
                    "x": 100.0,
                    "y": 200.0,
                    "z": 3.0
                },
                "tags": ["floor-1", "room-101"]
            }
        }


class UpdateArxObjectRequest(BaseModel):
    """Request model for updating an ArxObject"""
    properties: Optional[Dict[str, Any]] = Field(None, description="Properties to update")
    geometry: Optional[GeometryModel] = Field(None, description="New geometry")
    add_tags: Optional[List[str]] = Field(None, description="Tags to add")
    remove_tags: Optional[List[str]] = Field(None, description="Tags to remove")
    validate_constraints: bool = Field(True, description="Whether to validate constraints")
    
    class Config:
        schema_extra = {
            "example": {
                "properties": {
                    "voltage": 240
                },
                "add_tags": ["upgraded"],
                "validate_constraints": True
            }
        }


class ArxObjectResponse(BaseModel):
    """Response model for ArxObject"""
    id: str
    object_type: str
    properties: Dict[str, Any]
    geometry: GeometryModel
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    version: int
    metadata: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "object_type": "electrical_outlet",
                "properties": {"voltage": 120, "amperage": 20},
                "geometry": {"x": 100.0, "y": 200.0, "z": 3.0},
                "tags": ["floor-1"],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "version": 1,
                "metadata": {}
            }
        }


class QueryArxObjectsRequest(BaseModel):
    """Request model for querying ArxObjects"""
    object_types: Optional[List[str]] = Field(None, description="Filter by object types")
    property_filters: Optional[Dict[str, Any]] = Field(None, description="Filter by properties")
    spatial_bounds: Optional[List[float]] = Field(None, min_items=6, max_items=6, 
                                                  description="[min_x, min_y, min_z, max_x, max_y, max_z]")
    near_point: Optional[List[float]] = Field(None, min_items=3, max_items=3,
                                              description="[x, y, z] point for proximity search")
    radius: Optional[float] = Field(None, gt=0, description="Search radius for proximity")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    limit: int = Field(100, ge=1, le=1000, description="Maximum results")
    offset: int = Field(0, ge=0, description="Result offset")


class CreateRelationshipRequest(BaseModel):
    """Request model for creating a relationship"""
    source_id: str = Field(..., description="Source object ID")
    target_id: str = Field(..., description="Target object ID")
    relationship_type: str = Field(..., description="Type of relationship")
    properties: Optional[Dict[str, Any]] = Field(None, description="Relationship properties")
    
    @validator('relationship_type')
    def validate_relationship_type(cls, v):
        try:
            RelationshipType(v)
        except ValueError:
            raise ValueError(f"Invalid relationship type: {v}")
        return v


class BulkOperationRequest(BaseModel):
    """Request model for bulk operations"""
    operation_type: str = Field(..., description="Type of operation: create, update, delete")
    objects: List[Dict[str, Any]] = Field(..., description="Objects to operate on")
    transaction_mode: bool = Field(True, description="Use transaction")
    continue_on_error: bool = Field(False, description="Continue on error")


# ==========================================
# CRUD Endpoints
# ==========================================

@router.post("/", response_model=ArxObjectResponse, status_code=201)
async def create_arxobject(
    request: CreateArxObjectRequest,
    service: ArxObjectService = Depends(get_arxobject_service),
    current_user: Dict = Depends(get_current_user)
):
    """
    Create a new ArxObject.
    
    Creates a new ArxObject with the specified type, properties, and geometry.
    Optionally creates initial relationships and applies constraints.
    """
    try:
        # Convert geometry if provided
        geometry = None
        if request.geometry:
            from core.spatial.arxobject_core import ArxObjectGeometry
            geometry = ArxObjectGeometry(**request.geometry.dict())
        
        # Create object
        obj = await service.create_object(
            object_type=ArxObjectType(request.object_type),
            properties=request.properties,
            geometry=geometry,
            relationships=request.relationships,
            constraints=request.constraints,
            tags=request.tags,
            user_id=current_user.get("id")
        )
        
        # Convert to response model
        return ArxObjectResponse(
            id=obj.id,
            object_type=obj.object_type.value,
            properties=obj.properties,
            geometry=GeometryModel(
                x=obj.geometry.x,
                y=obj.geometry.y,
                z=obj.geometry.z,
                length=obj.geometry.length,
                width=obj.geometry.width,
                height=obj.geometry.height,
                rotation_x=obj.geometry.rotation_x,
                rotation_y=obj.geometry.rotation_y,
                rotation_z=obj.geometry.rotation_z,
                shape_type=obj.geometry.shape_type
            ),
            tags=obj.tags,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            version=obj.version,
            metadata=obj.metadata
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating ArxObject: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{object_id}", response_model=ArxObjectResponse)
async def get_arxobject(
    object_id: str = Path(..., description="ArxObject ID"),
    include_relationships: bool = Query(False, description="Include relationships"),
    include_constraints: bool = Query(False, description="Include constraints"),
    service: ArxObjectService = Depends(get_arxobject_service)
):
    """
    Get an ArxObject by ID.
    
    Retrieves an ArxObject with optional inclusion of relationships and constraints.
    """
    obj = await service.get_object(
        object_id,
        include_relationships=include_relationships,
        include_constraints=include_constraints
    )
    
    if not obj:
        raise HTTPException(status_code=404, detail="ArxObject not found")
    
    return ArxObjectResponse(
        id=obj.id,
        object_type=obj.object_type.value,
        properties=obj.properties,
        geometry=GeometryModel(
            x=obj.geometry.x,
            y=obj.geometry.y,
            z=obj.geometry.z,
            length=obj.geometry.length,
            width=obj.geometry.width,
            height=obj.geometry.height,
            rotation_x=obj.geometry.rotation_x,
            rotation_y=obj.geometry.rotation_y,
            rotation_z=obj.geometry.rotation_z,
            shape_type=obj.geometry.shape_type
        ),
        tags=obj.tags,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
        version=obj.version,
        metadata=obj.metadata
    )


@router.put("/{object_id}", response_model=ArxObjectResponse)
async def update_arxobject(
    object_id: str = Path(..., description="ArxObject ID"),
    request: UpdateArxObjectRequest = Body(...),
    service: ArxObjectService = Depends(get_arxobject_service),
    current_user: Dict = Depends(get_current_user)
):
    """
    Update an ArxObject.
    
    Updates an ArxObject's properties, geometry, and/or tags.
    Optionally validates constraints after update.
    """
    try:
        # Convert geometry if provided
        geometry = None
        if request.geometry:
            from core.spatial.arxobject_core import ArxObjectGeometry
            geometry = ArxObjectGeometry(**request.geometry.dict())
        
        # Create update specification
        update = ArxObjectUpdate(
            object_id=object_id,
            properties=request.properties,
            geometry=geometry,
            add_tags=request.add_tags,
            remove_tags=request.remove_tags,
            validate_constraints=request.validate_constraints
        )
        
        # Update object
        obj = await service.update_object(update, user_id=current_user.get("id"))
        
        return ArxObjectResponse(
            id=obj.id,
            object_type=obj.object_type.value,
            properties=obj.properties,
            geometry=GeometryModel(
                x=obj.geometry.x,
                y=obj.geometry.y,
                z=obj.geometry.z,
                length=obj.geometry.length,
                width=obj.geometry.width,
                height=obj.geometry.height,
                rotation_x=obj.geometry.rotation_x,
                rotation_y=obj.geometry.rotation_y,
                rotation_z=obj.geometry.rotation_z,
                shape_type=obj.geometry.shape_type
            ),
            tags=obj.tags,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            version=obj.version,
            metadata=obj.metadata
        )
        
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating ArxObject: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{object_id}")
async def delete_arxobject(
    object_id: str = Path(..., description="ArxObject ID"),
    cascade: bool = Query(False, description="Cascade delete dependencies"),
    soft_delete: bool = Query(True, description="Soft delete (mark inactive)"),
    service: ArxObjectService = Depends(get_arxobject_service),
    current_user: Dict = Depends(get_current_user)
):
    """
    Delete an ArxObject.
    
    Deletes an ArxObject with optional cascade deletion of dependencies.
    By default performs soft delete (marks as inactive).
    """
    try:
        success = await service.delete_object(
            object_id,
            cascade=cascade,
            soft_delete=soft_delete,
            user_id=current_user.get("id")
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="ArxObject not found")
        
        return {"message": "ArxObject deleted successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting ArxObject: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ==========================================
# Query Endpoints
# ==========================================

@router.post("/query", response_model=List[ArxObjectResponse])
async def query_arxobjects(
    request: QueryArxObjectsRequest,
    service: ArxObjectService = Depends(get_arxobject_service)
):
    """
    Query ArxObjects with multiple filters.
    
    Supports filtering by type, properties, spatial bounds, proximity, and tags.
    """
    # Build query specification
    query = ArxObjectQuery(
        object_types=[ArxObjectType(t) for t in request.object_types] if request.object_types else None,
        property_filters=request.property_filters,
        spatial_bounds=tuple(request.spatial_bounds) if request.spatial_bounds else None,
        near_point=tuple(request.near_point) if request.near_point else None,
        radius=request.radius,
        tags=request.tags,
        limit=request.limit,
        offset=request.offset
    )
    
    # Execute query
    objects = await service.query_objects(query)
    
    # Convert to response models
    return [
        ArxObjectResponse(
            id=obj.id,
            object_type=obj.object_type.value,
            properties=obj.properties,
            geometry=GeometryModel(
                x=obj.geometry.x,
                y=obj.geometry.y,
                z=obj.geometry.z,
                length=obj.geometry.length,
                width=obj.geometry.width,
                height=obj.geometry.height,
                rotation_x=obj.geometry.rotation_x,
                rotation_y=obj.geometry.rotation_y,
                rotation_z=obj.geometry.rotation_z,
                shape_type=obj.geometry.shape_type
            ),
            tags=obj.tags,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            version=obj.version,
            metadata=obj.metadata
        )
        for obj in objects
    ]


@router.get("/{object_id}/nearby")
async def find_nearby_objects(
    object_id: str = Path(..., description="Reference ArxObject ID"),
    distance: float = Query(..., gt=0, description="Search distance"),
    object_types: Optional[List[str]] = Query(None, description="Filter by object types"),
    limit: int = Query(10, ge=1, le=100, description="Maximum results"),
    service: ArxObjectService = Depends(get_arxobject_service)
):
    """
    Find objects near another object.
    
    Returns objects within the specified distance from the reference object.
    """
    types = [ArxObjectType(t) for t in object_types] if object_types else None
    
    results = await service.find_objects_within_distance(
        object_id, distance, types
    )
    
    return [
        {
            "object": ArxObjectResponse(
                id=obj.id,
                object_type=obj.object_type.value,
                properties=obj.properties,
                geometry=GeometryModel(
                    x=obj.geometry.x,
                    y=obj.geometry.y,
                    z=obj.geometry.z,
                    length=obj.geometry.length,
                    width=obj.geometry.width,
                    height=obj.geometry.height,
                    rotation_x=obj.geometry.rotation_x,
                    rotation_y=obj.geometry.rotation_y,
                    rotation_z=obj.geometry.rotation_z,
                    shape_type=obj.geometry.shape_type
                ),
                tags=obj.tags,
                created_at=obj.created_at,
                updated_at=obj.updated_at,
                version=obj.version,
                metadata=obj.metadata
            ),
            "distance": dist
        }
        for obj, dist in results[:limit]
    ]


# ==========================================
# Relationship Endpoints
# ==========================================

@router.post("/relationships", status_code=201)
async def create_relationship(
    request: CreateRelationshipRequest,
    service: ArxObjectService = Depends(get_arxobject_service)
):
    """
    Create a relationship between two ArxObjects.
    """
    try:
        relationship = await service.create_relationship(
            source_id=request.source_id,
            target_id=request.target_id,
            relationship_type=RelationshipType(request.relationship_type),
            properties=request.properties
        )
        
        return {
            "id": relationship.id,
            "source_id": relationship.source_id,
            "target_id": relationship.target_id,
            "type": relationship.relationship_type.value,
            "properties": relationship.properties,
            "created_at": relationship.created_at
        }
        
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{object_id}/relationships")
async def get_object_relationships(
    object_id: str = Path(..., description="ArxObject ID"),
    relationship_type: Optional[str] = Query(None, description="Filter by type"),
    direction: str = Query("both", regex="^(both|outgoing|incoming)$"),
    service: ArxObjectService = Depends(get_arxobject_service)
):
    """
    Get relationships for an ArxObject.
    """
    rel_type = RelationshipType(relationship_type) if relationship_type else None
    
    relationships = await service.get_object_relationships(
        object_id, rel_type, direction
    )
    
    return [
        {
            "id": rel.id,
            "source_id": rel.source_id,
            "target_id": rel.target_id,
            "type": rel.relationship_type.value,
            "properties": rel.properties,
            "created_at": rel.created_at
        }
        for rel in relationships
    ]


@router.get("/{object_id}/connected")
async def get_connected_objects(
    object_id: str = Path(..., description="ArxObject ID"),
    relationship_type: Optional[str] = Query(None, description="Filter by relationship type"),
    depth: int = Query(1, ge=1, le=5, description="Traversal depth"),
    service: ArxObjectService = Depends(get_arxobject_service)
):
    """
    Get objects connected through relationships.
    """
    rel_type = RelationshipType(relationship_type) if relationship_type else None
    
    objects = await service.get_connected_objects(
        object_id, rel_type, depth, include_objects=True
    )
    
    return [
        ArxObjectResponse(
            id=obj.id,
            object_type=obj.object_type.value,
            properties=obj.properties,
            geometry=GeometryModel(
                x=obj.geometry.x,
                y=obj.geometry.y,
                z=obj.geometry.z,
                length=obj.geometry.length,
                width=obj.geometry.width,
                height=obj.geometry.height,
                rotation_x=obj.geometry.rotation_x,
                rotation_y=obj.geometry.rotation_y,
                rotation_z=obj.geometry.rotation_z,
                shape_type=obj.geometry.shape_type
            ),
            tags=obj.tags,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            version=obj.version,
            metadata=obj.metadata
        )
        for obj in objects
    ]


# ==========================================
# Validation Endpoints
# ==========================================

@router.post("/{object_id}/validate")
async def validate_arxobject(
    object_id: str = Path(..., description="ArxObject ID"),
    context: Optional[Dict[str, Any]] = Body(None, description="Validation context"),
    service: ArxObjectService = Depends(get_arxobject_service)
):
    """
    Validate an ArxObject against constraints.
    """
    result = await service.validate_object(object_id, context)
    return result


@router.get("/{object_id}/conflicts")
async def check_spatial_conflicts(
    object_id: str = Path(..., description="ArxObject ID"),
    clearance: float = Query(0.0, ge=0, description="Required clearance"),
    service: ArxObjectService = Depends(get_arxobject_service)
):
    """
    Check for spatial conflicts with other objects.
    """
    conflicts = await service.find_spatial_conflicts(object_id, clearance)
    return {"conflicts": conflicts}


# ==========================================
# Bulk Operations
# ==========================================

@router.post("/bulk")
async def bulk_operation(
    request: BulkOperationRequest,
    service: ArxObjectService = Depends(get_arxobject_service),
    current_user: Dict = Depends(get_current_user)
):
    """
    Perform bulk operations on multiple ArxObjects.
    """
    try:
        operation = BulkOperation(
            operation_type=request.operation_type,
            objects=request.objects,
            transaction_mode=request.transaction_mode,
            continue_on_error=request.continue_on_error
        )
        
        result = await service.bulk_operation(operation, user_id=current_user.get("id"))
        return result
        
    except Exception as e:
        logger.error(f"Bulk operation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Statistics Endpoint
# ==========================================

@router.get("/statistics")
async def get_statistics(
    service: ArxObjectService = Depends(get_arxobject_service)
):
    """
    Get ArxObject system statistics.
    """
    return service.get_statistics()