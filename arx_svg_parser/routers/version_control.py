"""
Advanced Version Control Router
Handles branching, merging, conflict resolution, annotations, and comments
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime
from arx_svg_parser.services.version_control import version_control_service, VersionType, MergeStatus
from arx_svg_parser.utils.auth import get_current_user_optional

router = APIRouter(prefix="/version-control", tags=["version_control"])

# --- Version Management ---
@router.post("/version")
async def create_version(
    floor_data: Dict[str, Any],
    floor_id: str,
    building_id: str,
    branch_name: str,
    commit_message: str,
    author: str,
    parent_version_id: Optional[str] = None,
    version_type: VersionType = VersionType.MINOR,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Create a new version"""
    try:
        result = version_control_service.create_version(
            floor_data, floor_id, building_id, branch_name,
            commit_message, author, parent_version_id, version_type
        )
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/versions/{building_id}/{floor_id}")
async def get_version_history(
    building_id: str,
    floor_id: str,
    branch_name: Optional[str] = None,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Get version history for a floor or branch"""
    try:
        result = version_control_service.get_version_history(floor_id, building_id, branch_name)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/version/{version_id}")
async def get_version_data(
    version_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Get version data"""
    try:
        result = version_control_service.get_version_data(version_id)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Branch Management ---
@router.post("/branch")
async def create_branch(
    branch_name: str,
    floor_id: str,
    building_id: str,
    base_version_id: str,
    created_by: str,
    description: str = "",
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Create a new branch"""
    try:
        result = version_control_service.create_branch(
            branch_name, floor_id, building_id, base_version_id, created_by, description
        )
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/branches/{building_id}/{floor_id}")
async def get_branches(
    building_id: str,
    floor_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Get all branches for a floor"""
    try:
        result = version_control_service.get_branches(floor_id, building_id)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Merge Management ---
@router.post("/merge-request")
async def create_merge_request(
    source_branch: str,
    target_branch: str,
    floor_id: str,
    building_id: str,
    created_by: str,
    description: str = "",
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Create a merge request"""
    try:
        result = version_control_service.create_merge_request(
            source_branch, target_branch, floor_id, building_id, created_by, description
        )
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/merge/{merge_id}/resolve-conflict")
async def resolve_conflict(
    merge_id: str,
    conflict_id: str,
    resolution: str,
    resolved_by: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Resolve a conflict"""
    try:
        result = version_control_service.resolve_conflict(conflict_id, resolution, resolved_by)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/merge/{merge_id}/execute")
async def execute_merge(
    merge_id: str,
    executed_by: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Execute a merge"""
    try:
        result = version_control_service.execute_merge(merge_id, executed_by)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Annotations ---
@router.post("/annotation")
async def add_annotation(
    version_id: str,
    floor_id: str,
    building_id: str,
    title: str,
    content: str,
    author: str,
    object_id: Optional[str] = None,
    position_x: Optional[float] = None,
    position_y: Optional[float] = None,
    annotation_type: str = "note",
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Add an annotation to a version"""
    try:
        result = version_control_service.add_annotation(
            version_id, floor_id, building_id, title, content, author,
            object_id, position_x, position_y, annotation_type
        )
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/annotations/{version_id}")
async def get_annotations(
    version_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Get annotations for a version"""
    try:
        result = version_control_service.get_annotations(version_id)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/annotations/search/{building_id}/{floor_id}")
async def search_annotations(
    building_id: str,
    floor_id: str,
    query: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Search annotations by content"""
    try:
        result = version_control_service.search_annotations(floor_id, building_id, query)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Comments ---
@router.post("/comment")
async def add_comment(
    parent_id: str,
    parent_type: str,
    content: str,
    author: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Add a comment to a version or annotation"""
    try:
        result = version_control_service.add_comment(parent_id, parent_type, content, author)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comments/{parent_id}")
async def get_comments(
    parent_id: str,
    parent_type: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Get comments for a version or annotation"""
    try:
        result = version_control_service.get_comments(parent_id, parent_type)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Branch Visualization ---
@router.get("/branch-graph/{building_id}/{floor_id}")
async def get_branch_graph(
    building_id: str,
    floor_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Get branch visualization data"""
    try:
        # Get branches and versions for visualization
        branches_result = version_control_service.get_branches(floor_id, building_id)
        versions_result = version_control_service.get_version_history(floor_id, building_id)
        
        if not branches_result["success"] or not versions_result["success"]:
            return JSONResponse({"success": False, "message": "Failed to get branch data"})
        
        # Create graph data
        graph_data = {
            "nodes": [],
            "edges": [],
            "branches": branches_result["branches"],
            "versions": versions_result["versions"]
        }
        
        # Add version nodes
        for version in versions_result["versions"]:
            graph_data["nodes"].append({
                "id": version["version_id"],
                "type": "version",
                "label": version["version_number"],
                "branch": version["branch_name"],
                "author": version["author"],
                "created_at": version["created_at"]
            })
        
        # Add edges between versions
        for version in versions_result["versions"]:
            if version["parent_version_id"]:
                graph_data["edges"].append({
                    "source": version["parent_version_id"],
                    "target": version["version_id"],
                    "type": "parent"
                })
        
        return JSONResponse({"success": True, "graph": graph_data})
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Export/Import ---
@router.get("/export/{building_id}/{floor_id}")
async def export_version_data(
    building_id: str,
    floor_id: str,
    include_annotations: bool = True,
    include_comments: bool = True,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Export version control data for a floor"""
    try:
        # Get all data
        branches_result = version_control_service.get_branches(floor_id, building_id)
        versions_result = version_control_service.get_version_history(floor_id, building_id)
        
        export_data = {
            "building_id": building_id,
            "floor_id": floor_id,
            "export_date": datetime.utcnow().isoformat(),
            "branches": branches_result.get("branches", []),
            "versions": versions_result.get("versions", [])
        }
        
        if include_annotations:
            annotations = []
            for version in versions_result.get("versions", []):
                annotations_result = version_control_service.get_annotations(version["version_id"])
                if annotations_result["success"]:
                    annotations.extend(annotations_result["annotations"])
            export_data["annotations"] = annotations
        
        if include_comments:
            comments = []
            for version in versions_result.get("versions", []):
                comments_result = version_control_service.get_comments(version["version_id"], "version")
                if comments_result["success"]:
                    comments.extend(comments_result["comments"])
            export_data["comments"] = comments
        
        return JSONResponse({
            "success": True,
            "export_data": export_data,
            "filename": f"version_control_export_{building_id}_{floor_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 