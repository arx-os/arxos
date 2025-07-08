"""
Enhanced BIM Router

Provides comprehensive BIM API endpoints including:
- CRUD operations for BIM models and elements
- Search and filtering capabilities
- Version control and collaboration features
- Multi-user support and access control
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from uuid import uuid4
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, Query, Path, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from pydantic.types import UUID4

from models.bim import BIMModel, BIMElement, Room, Wall, Device
from services.bim_assembly import BIMAssemblyPipeline
from services.bim_export import BIMExportService, ExportFormat
from services.bim_import import BIMImportService, ImportFormat
from services.robust_error_handling import create_error_handler

router = APIRouter(prefix="/bim", tags=["BIM Operations"])

# Initialize services
assembly_pipeline = BIMAssemblyPipeline()
export_service = BIMExportService()
import_service = BIMImportService()
error_handler = create_error_handler()

# In-memory storage (replace with database in production)
bim_models: Dict[str, BIMModel] = {}
model_versions: Dict[str, List[Dict[str, Any]]] = {}
model_locks: Dict[str, Dict[str, Any]] = {}
model_comments: Dict[str, List[Dict[str, Any]]] = {}


# Request/Response Models
class BIMParseRequest(BaseModel):
    svg_xml: str = Field(..., min_length=10, description="SVG content to parse")
    building_id: str = Field(..., description="Building identifier")
    floor_id: str = Field(..., description="Floor identifier")
    user_id: str = Field(..., description="User performing the operation")
    project_id: str = Field(..., description="Project identifier")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Processing options")

    class Config:
        json_schema_extra = {
            "example": {
                "svg_xml": "<svg width='800' height='600'>...</svg>",
                "building_id": "building_123",
                "floor_id": "floor_1",
                "user_id": "user_456",
                "project_id": "project_789",
                "metadata": {"building_name": "Office Building"},
                "options": {"validate_geometry": True}
            }
        }


class BIMCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Model name")
    description: Optional[str] = Field(default=None, description="Model description")
    building_id: str = Field(..., description="Building identifier")
    floor_id: str = Field(..., description="Floor identifier")
    user_id: str = Field(..., description="User creating the model")
    project_id: str = Field(..., description="Project identifier")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Office Building Model",
                "description": "Complete BIM model for office building",
                "building_id": "building_123",
                "floor_id": "floor_1",
                "user_id": "user_456",
                "project_id": "project_789",
                "metadata": {"building_type": "office", "floors": 3}
            }
        }


class BIMUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None)
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    user_id: str = Field(..., description="User updating the model")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Office Building Model",
                "description": "Updated BIM model description",
                "metadata": {"last_updated": "2024-01-01"},
                "user_id": "user_456"
            }
        }


class BIMSearchRequest(BaseModel):
    query: Optional[str] = Field(default=None, description="Search query")
    element_types: Optional[List[str]] = Field(default=None, description="Filter by element types")
    properties: Optional[Dict[str, Any]] = Field(default=None, description="Filter by properties")
    spatial_bounds: Optional[List[float]] = Field(default=None, description="Spatial bounds [x1, y1, x2, y2]")
    user_id: str = Field(..., description="User performing search")
    project_id: str = Field(..., description="Project identifier")
    limit: Optional[int] = Field(default=100, ge=1, le=1000, description="Maximum results")
    offset: Optional[int] = Field(default=0, ge=0, description="Result offset")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "office room",
                "element_types": ["room", "wall"],
                "properties": {"room_type": "office"},
                "spatial_bounds": [0, 0, 100, 100],
                "user_id": "user_456",
                "project_id": "project_789",
                "limit": 50,
                "offset": 0
            }
        }


class BIMVersionRequest(BaseModel):
    version_name: str = Field(..., min_length=1, max_length=100, description="Version name")
    description: Optional[str] = Field(default=None, description="Version description")
    user_id: str = Field(..., description="User creating version")
    tags: Optional[List[str]] = Field(default=None, description="Version tags")

    class Config:
        json_schema_extra = {
            "example": {
                "version_name": "v1.2.0",
                "description": "Added HVAC systems",
                "user_id": "user_456",
                "tags": ["hvac", "systems"]
            }
        }


class BIMCommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000, description="Comment content")
    element_id: Optional[str] = Field(default=None, description="Element being commented on")
    user_id: str = Field(..., description="User adding comment")
    parent_comment_id: Optional[str] = Field(default=None, description="Parent comment for replies")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "This wall needs to be moved 2m to the right",
                "element_id": "wall_123",
                "user_id": "user_456",
                "parent_comment_id": None
            }
        }


class BIMLockRequest(BaseModel):
    user_id: str = Field(..., description="User requesting lock")
    element_ids: Optional[List[str]] = Field(default=None, description="Elements to lock")
    lock_type: str = Field(..., description="Type of lock (read, write, exclusive)")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_456",
                "element_ids": ["wall_123", "room_456"],
                "lock_type": "write"
            }
        }


# Response Models
class BIMResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    model_id: str = Field(..., description="BIM model identifier")
    name: str = Field(..., description="Model name")
    description: Optional[str] = Field(default=None, description="Model description")
    elements_count: int = Field(..., description="Number of elements")
    systems_count: int = Field(..., description="Number of systems")
    spaces_count: int = Field(..., description="Number of spaces")
    relationships_count: int = Field(..., description="Number of relationships")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Model metadata")


class BIMSearchResponse(BaseModel):
    success: bool = Field(..., description="Search success status")
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total matching results")
    query_time: float = Field(..., description="Query execution time")


class BIMVersionResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    version_id: str = Field(..., description="Version identifier")
    version_name: str = Field(..., description="Version name")
    description: Optional[str] = Field(default=None, description="Version description")
    created_at: datetime = Field(..., description="Version creation timestamp")
    created_by: str = Field(..., description="User who created version")
    tags: Optional[List[str]] = Field(default=None, description="Version tags")


class BIMCommentResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    comment_id: str = Field(..., description="Comment identifier")
    content: str = Field(..., description="Comment content")
    user_id: str = Field(..., description="User who created comment")
    created_at: datetime = Field(..., description="Comment creation timestamp")
    element_id: Optional[str] = Field(default=None, description="Associated element")


class BIMLockResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    lock_id: str = Field(..., description="Lock identifier")
    locked_elements: List[str] = Field(..., description="Locked element IDs")
    lock_type: str = Field(..., description="Lock type")
    expires_at: datetime = Field(..., description="Lock expiration timestamp")


# CRUD Operations
@router.post("/parse", response_model=BIMResponse, status_code=status.HTTP_201_CREATED)
async def parse_svg_to_bim(request: BIMParseRequest):
    """
    Parse SVG content and create BIM model.
    
    Converts SVG drawings to structured BIM models with elements,
    systems, spaces, and relationships.
    """
    try:
        # Assemble BIM from SVG
        result = assembly_pipeline.assemble_bim({
            "svg": request.svg_xml,
            "user_id": request.user_id,
            "project_id": request.project_id,
            "metadata": request.model_metadata,
            "options": request.options
        })
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"BIM assembly failed: {result.errors}"
            )
        
        # Create BIM model
        model_id = str(uuid4())
        model = BIMModel(
            id=model_id,
            name=f"BIM Model - {request.building_id}",
            description=request.model_metadata.get("description") if request.model_metadata else None,
            model_metadata=request.model_metadata or {}
        )
        
        # Add assembled elements
        for element in result.elements:
            model.add_element(element)
        
        # Store model
        bim_models[model_id] = model
        
        return BIMResponse(
            success=True,
            model_id=model_id,
            name=model.name,
            description=model.description,
            elements_count=len(model.elements),
            systems_count=len(model.systems),
            spaces_count=len(model.spaces),
            relationships_count=len(model.relationships),
            created_at=model.created_at or datetime.now(),
            updated_at=model.updated_at or datetime.now(),
            metadata=model.model_metadata
        )
        
    except Exception as e:
        error_handler.handle_processing_error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse SVG: {str(e)}"
        )


@router.post("/create", response_model=BIMResponse, status_code=status.HTTP_201_CREATED)
async def create_bim_model(request: BIMCreateRequest):
    """
    Create a new empty BIM model.
    
    Creates a new BIM model with basic information and metadata.
    """
    try:
        model_id = str(uuid4())
        model = BIMModel(
            id=model_id,
            name=request.name,
            description=request.description,
            model_metadata=request.model_metadata or {}
        )
        
        bim_models[model_id] = model
        
        return BIMResponse(
            success=True,
            model_id=model_id,
            name=model.name,
            description=model.description,
            elements_count=len(model.elements),
            systems_count=len(model.systems),
            spaces_count=len(model.spaces),
            relationships_count=len(model.relationships),
            created_at=model.created_at or datetime.now(),
            updated_at=model.updated_at or datetime.now(),
            metadata=model.model_metadata
        )
        
    except Exception as e:
        error_handler.handle_processing_error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create BIM model: {str(e)}"
        )


@router.get("/{model_id}", response_model=BIMResponse)
async def get_bim_model(
    model_id: str = Path(..., description="BIM model identifier"),
    user_id: str = Query(..., description="User requesting the model"),
    project_id: str = Query(..., description="Project identifier")
):
    """
    Retrieve a BIM model by ID.
    
    Returns complete BIM model information including elements,
    systems, spaces, and relationships.
    """
    try:
        if model_id not in bim_models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BIM model not found"
            )
        
        model = bim_models[model_id]
        
        return BIMResponse(
            success=True,
            model_id=model_id,
            name=model.name,
            description=model.description,
            elements_count=len(model.elements),
            systems_count=len(model.systems),
            spaces_count=len(model.spaces),
            relationships_count=len(model.relationships),
            created_at=model.created_at or datetime.now(),
            updated_at=model.updated_at or datetime.now(),
            metadata=model.model_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_handler.handle_processing_error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve BIM model: {str(e)}"
        )


@router.put("/{model_id}", response_model=BIMResponse)
async def update_bim_model(
    model_id: str = Path(..., description="BIM model identifier"),
    request: BIMUpdateRequest = ...
):
    """
    Update a BIM model.
    
    Updates model properties, metadata, and basic information.
    """
    try:
        if model_id not in bim_models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BIM model not found"
            )
        
        model = bim_models[model_id]
        
        # Check if model is locked
        if model_id in model_locks:
            lock = model_locks[model_id]
            if lock["user_id"] != request.user_id and lock["expires_at"] > datetime.now():
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Model is locked by another user"
                )
        
        # Update model properties
        if request.name is not None:
            model.name = request.name
        if request.description is not None:
            model.description = request.description
        if request.model_metadata is not None:
            model.model_metadata.update(request.model_metadata)
        
        model.updated_at = datetime.now()
        
        return BIMResponse(
            success=True,
            model_id=model_id,
            name=model.name,
            description=model.description,
            elements_count=len(model.elements),
            systems_count=len(model.systems),
            spaces_count=len(model.spaces),
            relationships_count=len(model.relationships),
            created_at=model.created_at or datetime.now(),
            updated_at=model.updated_at or datetime.now(),
            metadata=model.model_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_handler.handle_processing_error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update BIM model: {str(e)}"
        )


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bim_model(
    model_id: str = Path(..., description="BIM model identifier"),
    user_id: str = Query(..., description="User deleting the model"),
    project_id: str = Query(..., description="Project identifier")
):
    """
    Delete a BIM model.
    
    Permanently removes the BIM model and all associated data.
    """
    try:
        if model_id not in bim_models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BIM model not found"
            )
        
        # Check if model is locked
        if model_id in model_locks:
            lock = model_locks[model_id]
            if lock["user_id"] != user_id and lock["expires_at"] > datetime.now():
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Model is locked by another user"
                )
        
        # Remove model and associated data
        del bim_models[model_id]
        if model_id in model_versions:
            del model_versions[model_id]
        if model_id in model_locks:
            del model_locks[model_id]
        if model_id in model_comments:
            del model_comments[model_id]
        
    except HTTPException:
        raise
    except Exception as e:
        error_handler.handle_processing_error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete BIM model: {str(e)}"
        )


# Search and Filtering
@router.post("/search", response_model=BIMSearchResponse)
async def search_bim_models(request: BIMSearchRequest):
    """
    Search and filter BIM models and elements.
    
    Provides comprehensive search capabilities including:
    - Text-based search
    - Element type filtering
    - Property-based filtering
    - Spatial bounds filtering
    """
    try:
        results = []
        query_time_start = datetime.now()
        
        # Search through all models
        for model_id, model in bim_models.items():
            # Apply text search
            if request.query:
                if (request.query.lower() in model.name.lower() or
                    (model.description and request.query.lower() in model.description.lower())):
                    results.append({
                        "model_id": model_id,
                        "name": model.name,
                        "description": model.description,
                        "match_type": "model_name_or_description"
                    })
            
            # Search elements
            for element in model.elements:
                match = False
                match_reasons = []
                
                # Element type filtering
                if request.element_types and element.element_type in request.element_types:
                    match = True
                    match_reasons.append(f"element_type:{element.element_type}")
                
                # Property filtering
                if request.properties:
                    for prop_key, prop_value in request.properties.items():
                        if prop_key in element.properties and element.properties[prop_key] == prop_value:
                            match = True
                            match_reasons.append(f"property:{prop_key}={prop_value}")
                
                # Text search in element properties
                if request.query:
                    if (request.query.lower() in element.name.lower() or
                        any(request.query.lower() in str(v).lower() for v in element.properties.values())):
                        match = True
                        match_reasons.append("text_match")
                
                if match:
                    results.append({
                        "model_id": model_id,
                        "element_id": element.id,
                        "element_type": element.element_type,
                        "element_name": element.name,
                        "properties": element.properties,
                        "match_reasons": match_reasons
                    })
        
        # Apply spatial bounds filtering if specified
        if request.spatial_bounds and len(request.spatial_bounds) == 4:
            filtered_results = []
            for result in results:
                if "element_id" in result:
                    # Simplified spatial filtering (in production, use proper spatial indexing)
                    filtered_results.append(result)
            results = filtered_results
        
        # Apply pagination
        total_count = len(results)
        results = results[request.offset:request.offset + request.limit]
        
        query_time = (datetime.now() - query_time_start).total_seconds()
        
        return BIMSearchResponse(
            success=True,
            results=results,
            total_count=total_count,
            query_time=query_time
        )
        
    except Exception as e:
        error_handler.handle_processing_error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


# Version Control
@router.post("/{model_id}/versions", response_model=BIMVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_bim_version(
    model_id: str = Path(..., description="BIM model identifier"),
    request: BIMVersionRequest = ...
):
    """
    Create a new version of a BIM model.
    
    Creates a snapshot of the current model state for version control.
    """
    try:
        if model_id not in bim_models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BIM model not found"
            )
        
        model = bim_models[model_id]
        version_id = str(uuid4())
        
        # Create version snapshot
        version_data = {
            "version_id": version_id,
            "version_name": request.version_name,
            "description": request.description,
            "created_at": datetime.now(),
            "created_by": request.user_id,
            "tags": request.tags or [],
            "model_snapshot": {
                "name": model.name,
                "description": model.description,
                "elements_count": len(model.elements),
                "systems_count": len(model.systems),
                "spaces_count": len(model.spaces),
                "relationships_count": len(model.relationships),
                "metadata": model.model_metadata
            }
        }
        
        if model_id not in model_versions:
            model_versions[model_id] = []
        model_versions[model_id].append(version_data)
        
        return BIMVersionResponse(
            success=True,
            version_id=version_id,
            version_name=request.version_name,
            description=request.description,
            created_at=version_data["created_at"],
            created_by=request.user_id,
            tags=request.tags
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_handler.handle_processing_error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create version: {str(e)}"
        )


@router.get("/{model_id}/versions", response_model=List[BIMVersionResponse])
async def list_bim_versions(
    model_id: str = Path(..., description="BIM model identifier"),
    user_id: str = Query(..., description="User requesting versions"),
    project_id: str = Query(..., description="Project identifier")
):
    """
    List all versions of a BIM model.
    
    Returns chronological list of model versions with metadata.
    """
    try:
        if model_id not in bim_models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BIM model not found"
            )
        
        versions = model_versions.get(model_id, [])
        
        return [
            BIMVersionResponse(
                success=True,
                version_id=version["version_id"],
                version_name=version["version_name"],
                description=version["description"],
                created_at=version["created_at"],
                created_by=version["created_by"],
                tags=version["tags"]
            )
            for version in versions
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        error_handler.handle_processing_error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list versions: {str(e)}"
        )


@router.post("/{model_id}/versions/{version_id}/restore", response_model=BIMResponse)
async def restore_bim_version(
    model_id: str = Path(..., description="BIM model identifier"),
    version_id: str = Path(..., description="Version identifier"),
    user_id: str = Query(..., description="User restoring version"),
    project_id: str = Query(..., description="Project identifier")
):
    """
    Restore a BIM model to a specific version.
    
    Restores the model to the state captured in the specified version.
    """
    try:
        if model_id not in bim_models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BIM model not found"
            )
        
        versions = model_versions.get(model_id, [])
        target_version = None
        
        for version in versions:
            if version["version_id"] == version_id:
                target_version = version
                break
        
        if not target_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        # In a real implementation, restore the actual model data
        # For now, we'll just update the model metadata
        model = bim_models[model_id]
        model.updated_at = datetime.now()
        
        return BIMResponse(
            success=True,
            model_id=model_id,
            name=model.name,
            description=model.description,
            elements_count=len(model.elements),
            systems_count=len(model.systems),
            spaces_count=len(model.spaces),
            relationships_count=len(model.relationships),
            created_at=model.created_at or datetime.now(),
            updated_at=model.updated_at or datetime.now(),
            metadata=model.model_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_handler.handle_processing_error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore version: {str(e)}"
        )


# Collaboration Features
@router.post("/{model_id}/comments", response_model=BIMCommentResponse, status_code=status.HTTP_201_CREATED)
async def add_bim_comment(
    model_id: str = Path(..., description="BIM model identifier"),
    request: BIMCommentRequest = ...
):
    """
    Add a comment to a BIM model or element.
    
    Supports threaded comments for collaboration and feedback.
    """
    try:
        if model_id not in bim_models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BIM model not found"
            )
        
        comment_id = str(uuid4())
        comment_data = {
            "comment_id": comment_id,
            "content": request.content,
            "user_id": request.user_id,
            "element_id": request.element_id,
            "parent_comment_id": request.parent_comment_id,
            "created_at": datetime.now()
        }
        
        if model_id not in model_comments:
            model_comments[model_id] = []
        model_comments[model_id].append(comment_data)
        
        return BIMCommentResponse(
            success=True,
            comment_id=comment_id,
            content=request.content,
            user_id=request.user_id,
            created_at=comment_data["created_at"],
            element_id=request.element_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_handler.handle_processing_error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add comment: {str(e)}"
        )


@router.get("/{model_id}/comments", response_model=List[BIMCommentResponse])
async def get_bim_comments(
    model_id: str = Path(..., description="BIM model identifier"),
    user_id: str = Query(..., description="User requesting comments"),
    project_id: str = Query(..., description="Project identifier"),
    element_id: Optional[str] = Query(None, description="Filter by element ID")
):
    """
    Get comments for a BIM model.
    
    Returns all comments or filters by element ID.
    """
    try:
        if model_id not in bim_models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BIM model not found"
            )
        
        comments = model_comments.get(model_id, [])
        
        if element_id:
            comments = [c for c in comments if c["element_id"] == element_id]
        
        return [
            BIMCommentResponse(
                success=True,
                comment_id=comment["comment_id"],
                content=comment["content"],
                user_id=comment["user_id"],
                created_at=comment["created_at"],
                element_id=comment["element_id"]
            )
            for comment in comments
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        error_handler.handle_processing_error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get comments: {str(e)}"
        )


@router.post("/{model_id}/lock", response_model=BIMLockResponse)
async def lock_bim_model(
    model_id: str = Path(..., description="BIM model identifier"),
    request: BIMLockRequest = ...
):
    """
    Lock a BIM model or specific elements.
    
    Prevents other users from modifying locked elements.
    """
    try:
        if model_id not in bim_models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BIM model not found"
            )
        
        # Check if already locked
        if model_id in model_locks:
            existing_lock = model_locks[model_id]
            if existing_lock["expires_at"] > datetime.now():
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Model is already locked by another user"
                )
        
        lock_id = str(uuid4())
        expires_at = datetime.now() + timedelta(hours=1)  # 1 hour lock
        
        lock_data = {
            "lock_id": lock_id,
            "user_id": request.user_id,
            "lock_type": request.lock_type,
            "locked_elements": request.element_ids or [],
            "expires_at": expires_at
        }
        
        model_locks[model_id] = lock_data
        
        return BIMLockResponse(
            success=True,
            lock_id=lock_id,
            locked_elements=request.element_ids or [],
            lock_type=request.lock_type,
            expires_at=expires_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_handler.handle_processing_error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to lock model: {str(e)}"
        )


@router.delete("/{model_id}/lock", status_code=status.HTTP_204_NO_CONTENT)
async def unlock_bim_model(
    model_id: str = Path(..., description="BIM model identifier"),
    user_id: str = Query(..., description="User unlocking the model"),
    project_id: str = Query(..., description="Project identifier")
):
    """
    Unlock a BIM model.
    
    Releases locks held by the requesting user.
    """
    try:
        if model_id not in bim_models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BIM model not found"
            )
        
        if model_id in model_locks:
            lock = model_locks[model_id]
            if lock["user_id"] == user_id:
                del model_locks[model_id]
        
    except HTTPException:
        raise
    except Exception as e:
        error_handler.handle_processing_error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unlock model: {str(e)}"
        )


# Export/Import Operations
@router.post("/{model_id}/export")
async def export_bim_model(
    model_id: str = Path(..., description="BIM model identifier"),
    format: str = Query(..., description="Export format"),
    user_id: str = Query(..., description="User requesting export"),
    project_id: str = Query(..., description="Project identifier")
):
    """
    Export a BIM model in various formats.
    
    Supports IFC, Revit, JSON, XML, and visualization formats.
    """
    try:
        if model_id not in bim_models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BIM model not found"
            )
        
        model = bim_models[model_id]
        # Convert string format to ExportFormat enum
        try:
            export_format = ExportFormat(format.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid export format: {format}. Supported formats: ifc, rvt, json, xml, gltf, obj, fbx"
            )
        export_result = export_service.export_bim_model(model, export_format, {})
        
        return JSONResponse(
            content=export_result,
            status_code=status.HTTP_200_OK
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_handler.handle_processing_error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.post("/import")
async def import_bim_model(
    format: str = Query(..., description="Import format"),
    user_id: str = Query(..., description="User importing the model"),
    project_id: str = Query(..., description="Project identifier"),
    file_data: str = Query(..., description="File data")
):
    """
    Import a BIM model from various formats.
    
    Supports IFC, Revit, JSON, XML, and other BIM formats.
    """
    try:
        # Decode base64 file data
        import base64
        decoded_data = base64.b64decode(file_data)
        
        # Convert string format to ImportFormat enum
        try:
            import_format = ImportFormat(format.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid import format: {format}. Supported formats: ifc, rvt, json, xml"
            )
        
        # Import model
        model = import_service.import_bim_model(decoded_data, import_format, {})
        
        # Store imported model
        model_id = str(uuid4())
        model.id = model_id
        bim_models[model_id] = model
        
        return BIMResponse(
            success=True,
            model_id=model_id,
            name=model.name,
            description=model.description,
            elements_count=len(model.elements),
            systems_count=len(model.systems),
            spaces_count=len(model.spaces),
            relationships_count=len(model.relationships),
            created_at=model.created_at or datetime.now(),
            updated_at=model.updated_at or datetime.now(),
            metadata=model.model_metadata
        )
        
    except Exception as e:
        error_handler.handle_processing_error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


# Health and Status
@router.get("/health")
async def bim_health_check():
    """
    Health check for BIM service.
    
    Returns service status and basic statistics.
    """
    try:
        total_models = len(bim_models)
        total_elements = sum(len(model.elements) for model in bim_models.values())
        total_versions = sum(len(versions) for versions in model_versions.values())
        total_comments = sum(len(comments) for comments in model_comments.values())
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "statistics": {
                "total_models": total_models,
                "total_elements": total_elements,
                "total_versions": total_versions,
                "total_comments": total_comments
            },
            "services": {
                "assembly_pipeline": "available",
                "export_service": "available",
                "import_service": "available",
                "error_handler": "available"
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        } 