"""
Project Use Cases - Application Layer Business Logic

This module contains use cases for project-related operations including
create, read, update, delete, and list operations. Use cases orchestrate
domain objects and repositories to implement business workflows.
"""

from typing import List, Optional
from datetime import datetime

from domain.entities import Project
from domain.repositories import ProjectRepository
from domain.value_objects import ProjectId, BuildingId, ProjectStatus
from domain.exceptions import (
    InvalidProjectError,
    ProjectNotFoundError,
    DuplicateProjectError,
    InvalidStatusTransitionError,
)
from application.dto.project_dto import (
    CreateProjectRequest,
    CreateProjectResponse,
    UpdateProjectRequest,
    UpdateProjectResponse,
    GetProjectResponse,
    ListProjectsResponse,
    DeleteProjectResponse,
)


class CreateProjectUseCase:
    """Use case for creating a new project."""

    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    def execute(self, request: CreateProjectRequest) -> CreateProjectResponse:
        """Execute the create project use case."""
        try:
            # Validate request
            if not request.name or len(request.name.strip()) == 0:
                return CreateProjectResponse(
                    success=False, error_message="Project name is required"
                )

            if not request.building_id or len(request.building_id.strip()) == 0:
                return CreateProjectResponse(
                    success=False, error_message="Building ID is required"
                )

            # Create domain objects
            project_id = ProjectId()
            building_id = BuildingId(request.building_id)

            # Create project entity
            project = Project(
                id=project_id,
                name=request.name.strip(),
                building_id=building_id,
                description=request.description,
                start_date=request.start_date,
                end_date=request.end_date,
                created_by=request.created_by,
                metadata=request.metadata or {},
            )

            # Save to repository
            self.project_repository.save(project)

            # Return success response
            return CreateProjectResponse(
                success=True,
                project_id=str(project_id),
                message="Project created successfully",
                created_at=datetime.utcnow(),
            )

        except DuplicateProjectError as e:
            return CreateProjectResponse(
                success=False, error_message=f"Project already exists: {str(e)}"
            )
        except InvalidProjectError as e:
            return CreateProjectResponse(
                success=False, error_message=f"Invalid project data: {str(e)}"
            )
        except Exception as e:
            return CreateProjectResponse(
                success=False, error_message=f"Failed to create project: {str(e)}"
            )


class UpdateProjectUseCase:
    """Use case for updating a project."""

    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    def execute(self, request: UpdateProjectRequest) -> UpdateProjectResponse:
        """Execute the update project use case."""
        try:
            # Validate request
            if not request.project_id or len(request.project_id.strip()) == 0:
                return UpdateProjectResponse(
                    success=False, error_message="Project ID is required"
                )

            # Get existing project
            project_id = ProjectId(request.project_id)
            project = self.project_repository.get_by_id(project_id)

            if not project:
                return UpdateProjectResponse(
                    success=False, error_message="Project not found"
                )

            # Update project fields
            if request.name is not None:
                project.update_name(request.name, request.updated_by or "system")

            if request.description is not None:
                project.description = request.description
                project.updated_at = datetime.utcnow()

            if request.start_date is not None:
                project.start_date = request.start_date
                project.updated_at = datetime.utcnow()

            if request.end_date is not None:
                project.end_date = request.end_date
                project.updated_at = datetime.utcnow()

            if request.status is not None:
                try:
                    new_status = ProjectStatus(request.status)
                    project.update_status(new_status, request.updated_by or "system")
                except ValueError:
                    return UpdateProjectResponse(
                        success=False,
                        error_message=f"Invalid project status: {request.status}",
                    )

            if request.metadata is not None:
                project.metadata.update(request.metadata)
                project.updated_at = datetime.utcnow()

            # Save to repository
            self.project_repository.save(project)

            # Return success response
            return UpdateProjectResponse(
                success=True,
                project_id=str(project_id),
                message="Project updated successfully",
                updated_at=datetime.utcnow(),
            )

        except InvalidProjectError as e:
            return UpdateProjectResponse(
                success=False, error_message=f"Invalid project data: {str(e)}"
            )
        except InvalidStatusTransitionError as e:
            return UpdateProjectResponse(
                success=False, error_message=f"Invalid status transition: {str(e)}"
            )
        except Exception as e:
            return UpdateProjectResponse(
                success=False, error_message=f"Failed to update project: {str(e)}"
            )


class GetProjectUseCase:
    """Use case for getting a project by ID."""

    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    def execute(self, project_id: str) -> GetProjectResponse:
        """Execute the get project use case."""
        try:
            # Validate request
            if not project_id or len(project_id.strip()) == 0:
                return GetProjectResponse(
                    success=False, error_message="Project ID is required"
                )

            # Get project from repository
            project = self.project_repository.get_by_id(ProjectId(project_id))

            if not project:
                return GetProjectResponse(
                    success=False, error_message="Project not found"
                )

            # Convert to dictionary
            project_dict = {
                "id": str(project.id),
                "name": project.name,
                "building_id": str(project.building_id),
                "status": project.status.value,
                "description": project.description,
                "start_date": (
                    project.start_date.isoformat() if project.start_date else None
                ),
                "end_date": project.end_date.isoformat() if project.end_date else None,
                "duration_days": project.duration_days,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
                "created_by": project.created_by,
                "metadata": project.metadata,
            }

            return GetProjectResponse(success=True, project=project_dict)

        except Exception as e:
            return GetProjectResponse(
                success=False, error_message=f"Failed to get project: {str(e)}"
            )


class ListProjectsUseCase:
    """Use case for listing projects."""

    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    def execute(
        self,
        building_id: Optional[str] = None,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> ListProjectsResponse:
        """Execute the list projects use case."""
        try:
            # Validate pagination parameters
            if page < 1:
                page = 1
            if page_size < 1 or page_size > 100:
                page_size = 10

            # Get projects from repository
            projects = []

            if building_id:
                # Get projects by building
                projects = self.project_repository.get_by_building_id(
                    BuildingId(building_id)
                )
            elif status:
                # Get projects by status
                try:
                    project_status = ProjectStatus(status)
                    projects = self.project_repository.get_by_status(project_status)
                except ValueError:
                    return ListProjectsResponse(
                        success=False, error_message=f"Invalid project status: {status}"
                    )
            elif user_id:
                # Get projects by user
                from domain.value_objects import UserId

                projects = self.project_repository.get_by_user_id(UserId(user_id))
            else:
                # Get all projects
                projects = self.project_repository.get_all()

            # Apply pagination
            total_count = len(projects)
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_projects = projects[start_index:end_index]

            # Convert to dictionaries
            project_dicts = []
            for project in paginated_projects:
                project_dict = {
                    "id": str(project.id),
                    "name": project.name,
                    "building_id": str(project.building_id),
                    "status": project.status.value,
                    "description": project.description,
                    "start_date": (
                        project.start_date.isoformat() if project.start_date else None
                    ),
                    "end_date": (
                        project.end_date.isoformat() if project.end_date else None
                    ),
                    "duration_days": project.duration_days,
                    "created_at": project.created_at.isoformat(),
                    "updated_at": project.updated_at.isoformat(),
                    "created_by": project.created_by,
                }
                project_dicts.append(project_dict)

            return ListProjectsResponse(
                success=True,
                projects=project_dicts,
                total_count=total_count,
                page=page,
                page_size=page_size,
            )

        except Exception as e:
            return ListProjectsResponse(
                success=False, error_message=f"Failed to list projects: {str(e)}"
            )


class DeleteProjectUseCase:
    """Use case for deleting a project."""

    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    def execute(self, project_id: str) -> DeleteProjectResponse:
        """Execute the delete project use case."""
        try:
            # Validate request
            if not project_id or len(project_id.strip()) == 0:
                return DeleteProjectResponse(
                    success=False, error_message="Project ID is required"
                )

            # Check if project exists
            project = self.project_repository.get_by_id(ProjectId(project_id))

            if not project:
                return DeleteProjectResponse(
                    success=False, error_message="Project not found"
                )

            # Delete from repository
            self.project_repository.delete(ProjectId(project_id))

            return DeleteProjectResponse(
                success=True,
                project_id=project_id,
                message="Project deleted successfully",
                deleted_at=datetime.utcnow(),
            )

        except Exception as e:
            return DeleteProjectResponse(
                success=False, error_message=f"Failed to delete project: {str(e)}"
            )
