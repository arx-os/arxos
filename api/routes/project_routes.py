"""
Project management API routes.

This module provides REST endpoints for project management operations
using the application services layer.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from api.dependencies import (
    User, require_read_permission, require_write_permission,
    format_success_response, format_error_response
)
from application.logging import get_logger
from infrastructure import get_repository_factory
from application.factory import get_project_service
from application.dto import (
    CreateProjectRequest, UpdateProjectRequest, GetProjectRequest
)

logger = get_logger("api.project_routes")
router = APIRouter(prefix="/projects", tags=["projects"])


# Request/Response Models
class ProjectCreateRequest(BaseModel):
    """Request model for creating a project."""
    name: str = Field(..., description="Project name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Project description", max_length=1000)
    building_id: Optional[str] = Field(None, description="Associated building ID")
    status: str = Field(default="active", description="Project status")
    created_by: Optional[str] = Field(None, description="User who created the project")


class ProjectUpdateRequest(BaseModel):
    """Request model for updating a project."""
    name: Optional[str] = Field(None, description="Project name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Project description", max_length=1000)
    building_id: Optional[str] = Field(None, description="Associated building ID")
    status: Optional[str] = Field(None, description="Project status")
    updated_by: Optional[str] = Field(None, description="User who updated the project")


def get_project_application_service():
    """Dependency to get project application service."""
    factory = get_repository_factory()
    uow = factory.create_unit_of_work()
    return get_project_service(uow)


# API Endpoints
@router.post(
    "/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Create a new project with the specified properties."
)
async def create_project(
    request: ProjectCreateRequest,
    user: User = Depends(require_write_permission),
    project_service = Depends(get_project_application_service)
) -> Dict[str, Any]:
    """Create a new project."""
    try:
        # Convert API request to application DTO
        create_request = CreateProjectRequest(
            name=request.name,
            description=request.description,
            building_id=request.building_id,
            status=request.status,
            created_by=user.user_id
        )
        
        # Use application service to create project
        result = project_service.create_project(
            name=create_request.name,
            description=create_request.description,
            building_id=create_request.building_id,
            created_by=create_request.created_by
        )
        
        if result.success:
            return format_success_response(
                data={
                    "project_id": str(result.project_id),
                    "name": result.name,
                    "description": result.description,
                    "building_id": str(result.building_id) if result.building_id else None,
                    "status": result.status,
                    "created_by": result.created_by,
                    "created_at": result.created_at.isoformat() if result.created_at else datetime.utcnow().isoformat()
                },
                message="Project created successfully"
            )
        else:
            return format_error_response(
                error_code="PROJECT_CREATION_ERROR",
                message=result.error_message or "Failed to create project",
                details={"error": result.error_message}
            )
            
    except Exception as e:
        logger.error(f"Failed to create project: {str(e)}")
        return format_error_response(
            error_code="PROJECT_CREATION_ERROR",
            message="Failed to create project",
            details={"error": str(e)}
        )


@router.get(
    "/",
    response_model=Dict[str, Any],
    summary="List projects",
    description="Retrieve a list of projects with optional filtering and pagination."
)
async def list_projects(
    building_id: Optional[str] = Query(None, description="Filter by building ID"),
    status: Optional[str] = Query(None, description="Filter by project status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    user: User = Depends(require_read_permission),
    project_service = Depends(get_project_application_service)
) -> Dict[str, Any]:
    """List projects with filtering and pagination."""
    try:
        # Use application service to list projects
        result = project_service.list_projects(
            building_id=building_id,
            status=status,
            page=page,
            page_size=page_size
        )
        
        if result.success:
            return format_success_response(
                data={
                    "projects": [
                        {
                            "project_id": str(project.project_id),
                            "name": project.name,
                            "description": project.description,
                            "building_id": str(project.building_id) if project.building_id else None,
                            "status": project.status,
                            "created_by": project.created_by,
                            "created_at": project.created_at.isoformat() if project.created_at else None
                        }
                        for project in result.projects
                    ],
                    "pagination": {
                        "page": result.page,
                        "page_size": result.page_size,
                        "total_count": result.total_count,
                        "total_pages": result.total_pages
                    }
                },
                message="Projects retrieved successfully"
            )
        else:
            return format_error_response(
                error_code="PROJECT_LIST_ERROR",
                message=result.error_message or "Failed to retrieve projects",
                details={"error": result.error_message}
            )
            
    except Exception as e:
        logger.error(f"Failed to list projects: {str(e)}")
        return format_error_response(
            error_code="PROJECT_LIST_ERROR",
            message="Failed to retrieve projects",
            details={"error": str(e)}
        )


@router.get(
    "/{project_id}",
    response_model=Dict[str, Any],
    summary="Get project details",
    description="Retrieve detailed information about a specific project."
)
async def get_project(
    project_id: str,
    user: User = Depends(require_read_permission),
    project_service = Depends(get_project_application_service)
) -> Dict[str, Any]:
    """Get project details by ID."""
    try:
        # Use application service to get project
        result = project_service.get_project(project_id=project_id)
        
        if result.success and result.project:
            project = result.project
            return format_success_response(
                data={
                    "project_id": str(project.project_id),
                    "name": project.name,
                    "description": project.description,
                    "building_id": str(project.building_id) if project.building_id else None,
                    "status": project.status,
                    "created_by": project.created_by,
                    "created_at": project.created_at.isoformat() if project.created_at else None,
                    "updated_at": project.updated_at.isoformat() if project.updated_at else None
                },
                message="Project retrieved successfully"
            )
        else:
            return format_error_response(
                error_code="PROJECT_NOT_FOUND",
                message=result.error_message or "Project not found",
                details={"project_id": project_id}
            )
            
    except Exception as e:
        logger.error(f"Failed to get project {project_id}: {str(e)}")
        return format_error_response(
            error_code="PROJECT_RETRIEVAL_ERROR",
            message="Failed to retrieve project",
            details={"error": str(e), "project_id": project_id}
        )


@router.put(
    "/{project_id}",
    response_model=Dict[str, Any],
    summary="Update project",
    description="Update an existing project with new information."
)
async def update_project(
    project_id: str,
    request: ProjectUpdateRequest,
    user: User = Depends(require_write_permission),
    project_service = Depends(get_project_application_service)
) -> Dict[str, Any]:
    """Update project by ID."""
    try:
        # Convert API request to application DTO
        update_request = UpdateProjectRequest(
            project_id=project_id,
            name=request.name,
            description=request.description,
            building_id=request.building_id,
            status=request.status,
            updated_by=user.user_id
        )
        
        # Use application service to update project
        result = project_service.update_project(
            project_id=project_id,
            name=update_request.name,
            description=update_request.description,
            building_id=update_request.building_id,
            status=update_request.status,
            updated_by=update_request.updated_by
        )
        
        if result.success:
            return format_success_response(
                data={
                    "project_id": str(result.project_id),
                    "name": result.name,
                    "description": result.description,
                    "building_id": str(result.building_id) if result.building_id else None,
                    "status": result.status,
                    "updated_by": result.updated_by,
                    "updated_at": result.updated_at.isoformat() if result.updated_at else datetime.utcnow().isoformat()
                },
                message="Project updated successfully"
            )
        else:
            return format_error_response(
                error_code="PROJECT_UPDATE_ERROR",
                message=result.error_message or "Failed to update project",
                details={"error": result.error_message, "project_id": project_id}
            )
            
    except Exception as e:
        logger.error(f"Failed to update project {project_id}: {str(e)}")
        return format_error_response(
            error_code="PROJECT_UPDATE_ERROR",
            message="Failed to update project",
            details={"error": str(e), "project_id": project_id}
        )


@router.delete(
    "/{project_id}",
    response_model=Dict[str, Any],
    summary="Delete project",
    description="Delete a project and all associated data."
)
async def delete_project(
    project_id: str,
    user: User = Depends(require_write_permission),
    project_service = Depends(get_project_application_service)
) -> Dict[str, Any]:
    """Delete project by ID."""
    try:
        # Use application service to delete project
        result = project_service.delete_project(
            project_id=project_id,
            deleted_by=user.user_id
        )
        
        if result.success:
            return format_success_response(
                data={
                    "project_id": project_id,
                    "deleted_by": user.user_id,
                    "deleted_at": datetime.utcnow().isoformat()
                },
                message="Project deleted successfully"
            )
        else:
            return format_error_response(
                error_code="PROJECT_DELETE_ERROR",
                message=result.error_message or "Failed to delete project",
                details={"error": result.error_message, "project_id": project_id}
            )
            
    except Exception as e:
        logger.error(f"Failed to delete project {project_id}: {str(e)}")
        return format_error_response(
            error_code="PROJECT_DELETE_ERROR",
            message="Failed to delete project",
            details={"error": str(e), "project_id": project_id}
        )


@router.get(
    "/{project_id}/statistics",
    response_model=Dict[str, Any],
    summary="Get project statistics",
    description="Retrieve statistics and metrics for a specific project."
)
async def get_project_statistics(
    project_id: str,
    user: User = Depends(require_read_permission),
    project_service = Depends(get_project_application_service)
) -> Dict[str, Any]:
    """Get project statistics."""
    try:
        # Use application service to get project statistics
        result = project_service.get_project_statistics(project_id=project_id)
        
        if result.success:
            return format_success_response(
                data={
                    "project_id": project_id,
                    "statistics": {
                        "total_projects": result.total_projects,
                        "active_projects": result.active_projects,
                        "inactive_projects": result.inactive_projects,
                        "status_distribution": result.status_distribution,
                        "building_distribution": result.building_distribution,
                        "recent_activity": result.recent_activity
                    },
                    "last_updated": datetime.utcnow().isoformat()
                },
                message="Project statistics retrieved successfully"
            )
        else:
            return format_error_response(
                error_code="PROJECT_STATISTICS_ERROR",
                message=result.error_message or "Failed to retrieve project statistics",
                details={"error": result.error_message, "project_id": project_id}
            )
            
    except Exception as e:
        logger.error(f"Failed to get statistics for project {project_id}: {str(e)}")
        return format_error_response(
            error_code="PROJECT_STATISTICS_ERROR",
            message="Failed to retrieve project statistics",
            details={"error": str(e), "project_id": project_id}
        ) 