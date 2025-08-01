"""
Project Repository Implementation

This module contains the SQLAlchemy implementation of the ProjectRepository
interface defined in the domain layer.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from domain.entities import Project
from domain.value_objects import ProjectId, ProjectStatus, BuildingId, UserId
from domain.repositories import ProjectRepository
from domain.exceptions import RepositoryError

from .base import BaseRepository
from infrastructure.database.models.project import ProjectModel


class SQLAlchemyProjectRepository(BaseRepository[Project, ProjectModel], ProjectRepository):
    """SQLAlchemy implementation of ProjectRepository."""
    
    def __init__(self, session: Session):
        """Initialize project repository."""
        super().__init__(session, Project, ProjectModel)
    
    def save(self, project: Project) -> None:
        """Save a project to the repository."""
        try:
            model = self._entity_to_model(project)
            self.session.add(model)
            self.session.flush()
        except Exception as e:
            raise RepositoryError(f"Failed to save project: {str(e)}")
    
    def get_by_id(self, project_id: ProjectId) -> Optional[Project]:
        """Get a project by its ID."""
        try:
            model = self.session.query(ProjectModel).filter(
                and_(
                    ProjectModel.id == project_id.value,
                    ProjectModel.deleted_at.is_(None)
                )
            ).first()
            
            if model is None:
                return None
                
            return self._model_to_entity(model)
        except Exception as e:
            raise RepositoryError(f"Failed to get project by ID: {str(e)}")
    
    def get_all(self) -> List[Project]:
        """Get all projects."""
        try:
            models = self.session.query(ProjectModel).filter(
                ProjectModel.deleted_at.is_(None)
            ).order_by(ProjectModel.name).all()
            
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to get all projects: {str(e)}")
    
    def get_by_building_id(self, building_id: BuildingId) -> List[Project]:
        """Get all projects for a building."""
        try:
            models = self.session.query(ProjectModel).filter(
                and_(
                    ProjectModel.building_id == building_id.value,
                    ProjectModel.deleted_at.is_(None)
                )
            ).order_by(ProjectModel.name).all()
            
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find projects by building ID: {str(e)}")
    
    def get_by_status(self, status: ProjectStatus) -> List[Project]:
        """Get projects by status."""
        try:
            models = self.session.query(ProjectModel).filter(
                and_(
                    ProjectModel.status == status,
                    ProjectModel.deleted_at.is_(None)
                )
            ).order_by(ProjectModel.name).all()
            
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find projects by status: {str(e)}")
    
    def get_by_user_id(self, user_id: UserId) -> List[Project]:
        """Get projects by user ID."""
        try:
            models = self.session.query(ProjectModel).filter(
                and_(
                    ProjectModel.created_by == user_id.value,
                    ProjectModel.deleted_at.is_(None)
                )
            ).order_by(ProjectModel.name).all()
            
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find projects by user ID: {str(e)}")
    
    def delete(self, project_id: ProjectId) -> None:
        """Delete a project by ID."""
        try:
            model = self.session.query(ProjectModel).filter(
                and_(
                    ProjectModel.id == project_id.value,
                    ProjectModel.deleted_at.is_(None)
                )
            ).first()
            
            if model is None:
                raise RepositoryError(f"Project with ID {project_id} not found")
            
            model.soft_delete()
            self.session.flush()
        except Exception as e:
            raise RepositoryError(f"Failed to delete project: {str(e)}")
    
    def exists(self, project_id: ProjectId) -> bool:
        """Check if a project exists."""
        try:
            return self.session.query(ProjectModel).filter(
                and_(
                    ProjectModel.id == project_id.value,
                    ProjectModel.deleted_at.is_(None)
                )
            ).first() is not None
        except Exception as e:
            raise RepositoryError(f"Failed to check project existence: {str(e)}")
    
    def count(self) -> int:
        """Get the total number of projects."""
        try:
            return self.session.query(ProjectModel).filter(
                ProjectModel.deleted_at.is_(None)
            ).count()
        except Exception as e:
            raise RepositoryError(f"Failed to count projects: {str(e)}")
    
    def count_by_building(self, building_id: BuildingId) -> int:
        """Get the number of projects for a building."""
        try:
            return self.session.query(ProjectModel).filter(
                and_(
                    ProjectModel.building_id == building_id.value,
                    ProjectModel.deleted_at.is_(None)
                )
            ).count()
        except Exception as e:
            raise RepositoryError(f"Failed to count projects by building: {str(e)}")
    
    def find_by_building_id(self, building_id) -> List[Project]:
        """Find projects by building ID."""
        try:
            models = self.session.query(ProjectModel).filter(
                and_(
                    ProjectModel.building_id == building_id.value,
                    ProjectModel.deleted_at.is_(None)
                )
            ).order_by(ProjectModel.name).all()
            
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find projects by building ID: {str(e)}")
    
    def find_by_status(self, status: ProjectStatus) -> List[Project]:
        """Find projects by status."""
        try:
            models = self.session.query(ProjectModel).filter(
                and_(
                    ProjectModel.status == status,
                    ProjectModel.deleted_at.is_(None)
                )
            ).order_by(ProjectModel.name).all()
            
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find projects by status: {str(e)}")
    
    def search_projects(self, search_term: str) -> List[Project]:
        """Search projects by name or description."""
        try:
            search_pattern = f"%{search_term}%"
            models = self.session.query(ProjectModel).filter(
                and_(
                    or_(
                        ProjectModel.name.ilike(search_pattern),
                        ProjectModel.description.ilike(search_pattern)
                    ),
                    ProjectModel.deleted_at.is_(None)
                )
            ).order_by(ProjectModel.name).all()
            
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to search projects: {str(e)}")
    
    def find_active_projects(self) -> List[Project]:
        """Find all active projects (not completed or cancelled)."""
        try:
            models = self.session.query(ProjectModel).filter(
                and_(
                    ProjectModel.status.in_([ProjectStatus.DRAFT, ProjectStatus.IN_PROGRESS, ProjectStatus.REVIEW]),
                    ProjectModel.deleted_at.is_(None)
                )
            ).order_by(ProjectModel.name).all()
            
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find active projects: {str(e)}")
    
    def _entity_to_model(self, entity: Project) -> ProjectModel:
        """Convert Project entity to ProjectModel."""
        model = ProjectModel(
            id=entity.id.value,
            building_id=entity.building_id.value,
            name=entity.name,
            description=entity.description,
            status=entity.status,
            start_date=entity.start_date,
            end_date=entity.end_date,
            created_by=entity.created_by,
            updated_by=entity.updated_by
        )
        
        # Copy metadata if available
        if hasattr(entity, 'metadata') and entity.metadata:
            model.metadata_json = entity.metadata
        
        return model
    
    def _model_to_entity(self, model: ProjectModel) -> Project:
        """Convert ProjectModel to Project entity."""
        from domain.value_objects import BuildingId
        
        project = Project(
            id=ProjectId(model.id),
            building_id=BuildingId(model.building_id),
            name=model.name,
            status=model.status,
            description=model.description,
            start_date=model.start_date,
            end_date=model.end_date,
            created_by=model.created_by,
            updated_by=model.updated_by
        )
        
        # Copy metadata if available
        if model.metadata_json:
            project.metadata = model.metadata_json
        
        return project 