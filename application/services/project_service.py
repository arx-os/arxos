"""
Project Application Service - High-Level Project Operations

This module contains the project application service that coordinates
project use cases and provides high-level business operations for
project management with infrastructure integration.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import time

from domain.repositories import UnitOfWork
from domain.events import ProjectCreated, ProjectUpdated, ProjectDeleted
from application.dto.project_dto import (
    CreateProjectRequest, CreateProjectResponse,
    UpdateProjectRequest, UpdateProjectResponse,
    GetProjectResponse, ListProjectsResponse,
    DeleteProjectResponse
)
from infrastructure.services.cache_service import RedisCacheService
from infrastructure.services.event_store import EventStoreService
from infrastructure.services.message_queue import MessageQueueService
from infrastructure.monitoring.metrics import MetricsCollector
from infrastructure.monitoring.logging import StructuredLogger


class ProjectApplicationService:
    """Application service for project operations with infrastructure integration."""
    
    def __init__(self, unit_of_work: UnitOfWork,
                 cache_service: Optional[RedisCacheService] = None,
                 event_store: Optional[EventStoreService] = None,
                 message_queue: Optional[MessageQueueService] = None,
                 metrics: Optional[MetricsCollector] = None,
                 logger: Optional[StructuredLogger] = None):
        """Initialize project application service with infrastructure dependencies."""
        self.unit_of_work = unit_of_work
        self.cache_service = cache_service
        self.event_store = event_store
        self.message_queue = message_queue
        self.metrics = metrics
        self.logger = logger
    
    def create_project(self, name: str, building_id: str,
                      description: Optional[str] = None,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      budget: Optional[float] = None,
                      created_by: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> CreateProjectResponse:
        """Create a new project with infrastructure integration."""
        start_time = time.time()
        
        try:
            # Log the operation
            if self.logger:
                self.logger.info(
                    "Creating project",
                    name=name,
                    building_id=building_id,
                    created_by=created_by
                )
            
            # Execute use case directly with UnitOfWork
            from application.use_cases.project_use_cases import CreateProjectUseCase
            create_project_uc = CreateProjectUseCase(self.unit_of_work)
            
            request = CreateProjectRequest(
                name=name,
                building_id=building_id,
                description=description,
                start_date=start_date,
                end_date=end_date,
                budget=budget,
                created_by=created_by,
                metadata=metadata
            )
            result = create_project_uc.execute(request)
            
            if result.success:
                # Publish domain event
                if self.event_store:
                    project_created_event = ProjectCreated(
                        project_id=str(result.project_id),
                        project_name=name,
                        building_id=building_id,
                        created_by=created_by
                    )
                    self.event_store.store_event(project_created_event)
                
                # Publish message to queue
                if self.message_queue:
                    message = {
                        'event_type': 'project.created',
                        'project_id': str(result.project_id),
                        'project_name': name,
                        'building_id': building_id,
                        'created_by': created_by,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    self.message_queue.publish('project.events', message)
                
                # Clear cache
                if self.cache_service:
                    self.cache_service.delete(f'building:{building_id}:projects')
                    self.cache_service.delete('projects:list')
                    self.cache_service.delete('projects:statistics')
                
                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('project.create', time.time() - start_time)
                    self.metrics.increment_counter('project.created')
                
                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('project.create.error')
                
                return result
                
        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to create project",
                    name=name,
                    building_id=building_id,
                    error=str(e)
                )
            
            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('project.create.error')
            
            return CreateProjectResponse(
                success=False,
                error_message=f"Failed to create project: {str(e)}"
            )
    
    def update_project(self, project_id: str, name: Optional[str] = None,
                      description: Optional[str] = None,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      budget: Optional[float] = None,
                      status: Optional[str] = None,
                      updated_by: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> UpdateProjectResponse:
        """Update a project with infrastructure integration."""
        start_time = time.time()
        
        try:
            # Log the operation
            if self.logger:
                self.logger.info(
                    "Updating project",
                    project_id=project_id,
                    updated_by=updated_by
                )
            
            # Execute use case directly with UnitOfWork
            from application.use_cases.project_use_cases import UpdateProjectUseCase
            update_project_uc = UpdateProjectUseCase(self.unit_of_work)
            
            request = UpdateProjectRequest(
                project_id=project_id,
                name=name,
                description=description,
                start_date=start_date,
                end_date=end_date,
                budget=budget,
                status=status,
                updated_by=updated_by,
                metadata=metadata
            )
            result = update_project_uc.execute(request)
            
            if result.success:
                # Publish domain event
                if self.event_store:
                    project_updated_event = ProjectUpdated(
                        project_id=project_id,
                        updated_fields=[field for field in [name, status] if field is not None],
                        updated_by=updated_by
                    )
                    self.event_store.store_event(project_updated_event)
                
                # Clear cache
                if self.cache_service:
                    self.cache_service.delete(f'project:{project_id}')
                    self.cache_service.delete('projects:list')
                
                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('project.update', time.time() - start_time)
                    self.metrics.increment_counter('project.updated')
                
                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('project.update.error')
                
                return result
                
        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to update project",
                    project_id=project_id,
                    error=str(e)
                )
            
            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('project.update.error')
            
            return UpdateProjectResponse(
                success=False,
                error_message=f"Failed to update project: {str(e)}"
            )
    
    def get_project(self, project_id: str) -> GetProjectResponse:
        """Get a project with infrastructure integration."""
        start_time = time.time()
        
        try:
            # Check cache first
            if self.cache_service:
                cached_project = self.cache_service.get(f'project:{project_id}')
                if cached_project:
                    if self.metrics:
                        self.metrics.increment_counter('project.get.cache_hit')
                    return GetProjectResponse(
                        success=True,
                        project=cached_project
                    )
            
            # Execute use case directly with UnitOfWork
            from application.use_cases.project_use_cases import GetProjectUseCase
            get_project_uc = GetProjectUseCase(self.unit_of_work)
            
            result = get_project_uc.execute(project_id)
            
            if result.success:
                # Cache the result
                if self.cache_service:
                    self.cache_service.set(f'project:{project_id}', result.project, ttl=300)
                
                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('project.get', time.time() - start_time)
                    self.metrics.increment_counter('project.get.cache_miss')
                
                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('project.get.error')
                
                return result
                
        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to get project",
                    project_id=project_id,
                    error=str(e)
                )
            
            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('project.get.error')
            
            return GetProjectResponse(
                success=False,
                error_message=f"Failed to get project: {str(e)}"
            )
    
    def list_projects(self, building_id: Optional[str] = None,
                     status: Optional[str] = None,
                     page: int = 1, page_size: int = 10) -> ListProjectsResponse:
        """List projects with infrastructure integration."""
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = f'projects:list:{building_id or "all"}:{status or "all"}:{page}:{page_size}'
            if self.cache_service:
                cached_projects = self.cache_service.get(cache_key)
                if cached_projects:
                    if self.metrics:
                        self.metrics.increment_counter('project.list.cache_hit')
                    return ListProjectsResponse(**cached_projects)
            
            # Execute use case directly with UnitOfWork
            from application.use_cases.project_use_cases import ListProjectsUseCase
            list_projects_uc = ListProjectsUseCase(self.unit_of_work)
            
            result = list_projects_uc.execute(building_id, status, page, page_size)
            
            if result.success:
                # Cache the result
                if self.cache_service:
                    self.cache_service.set(cache_key, result.__dict__, ttl=60)
                
                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('project.list', time.time() - start_time)
                    self.metrics.increment_counter('project.list.cache_miss')
                
                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('project.list.error')
                
                return result
                
        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to list projects",
                    building_id=building_id,
                    status=status,
                    error=str(e)
                )
            
            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('project.list.error')
            
            return ListProjectsResponse(
                success=False,
                error_message=f"Failed to list projects: {str(e)}"
            )
    
    def delete_project(self, project_id: str) -> DeleteProjectResponse:
        """Delete a project with infrastructure integration."""
        start_time = time.time()
        
        try:
            # Log the operation
            if self.logger:
                self.logger.info(
                    "Deleting project",
                    project_id=project_id
                )
            
            # Execute use case directly with UnitOfWork
            from application.use_cases.project_use_cases import DeleteProjectUseCase
            delete_project_uc = DeleteProjectUseCase(self.unit_of_work)
            
            result = delete_project_uc.execute(project_id)
            
            if result.success:
                # Publish domain event
                if self.event_store:
                    project_deleted_event = ProjectDeleted(
                        project_id=project_id,
                        project_name="",  # Would need to get from project
                        deleted_by="system"
                    )
                    self.event_store.store_event(project_deleted_event)
                
                # Clear cache
                if self.cache_service:
                    self.cache_service.delete(f'project:{project_id}')
                    self.cache_service.delete('projects:list')
                    self.cache_service.delete('projects:statistics')
                
                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('project.delete', time.time() - start_time)
                    self.metrics.increment_counter('project.deleted')
                
                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('project.delete.error')
                
                return result
                
        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to delete project",
                    project_id=project_id,
                    error=str(e)
                )
            
            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('project.delete.error')
            
            return DeleteProjectResponse(
                success=False,
                error_message=f"Failed to delete project: {str(e)}"
            )
    
    def get_project_statistics(self) -> Dict[str, Any]:
        """Get project statistics with infrastructure integration."""
        start_time = time.time()
        
        try:
            # Check cache first
            if self.cache_service:
                cached_stats = self.cache_service.get('projects:statistics')
                if cached_stats:
                    if self.metrics:
                        self.metrics.increment_counter('project.statistics.cache_hit')
                    return cached_stats
            
            # Get statistics using UnitOfWork
            projects = self.unit_of_work.projects.get_all()
            
            stats = {
                'total_projects': len(projects),
                'by_status': {},
                'by_building': {},
                'created_today': 0,
                'updated_today': 0
            }
            
            today = datetime.utcnow().date()
            
            for project in projects:
                # Status breakdown
                status = project.status.value
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                
                # Building breakdown
                building_id = str(project.building_id)
                stats['by_building'][building_id] = stats['by_building'].get(building_id, 0) + 1
                
                # Today's activity
                if project.created_at and project.created_at.date() == today:
                    stats['created_today'] += 1
                if project.updated_at and project.updated_at.date() == today:
                    stats['updated_today'] += 1
            
            # Cache the result
            if self.cache_service:
                self.cache_service.set('projects:statistics', stats, ttl=300)
            
            # Record metrics
            if self.metrics:
                self.metrics.record_timing('project.statistics', time.time() - start_time)
                self.metrics.increment_counter('project.statistics.cache_miss')
            
            return stats
            
        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to get project statistics",
                    error=str(e)
                )
            
            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('project.statistics.error')
            
            return {
                'error': f"Failed to get project statistics: {str(e)}"
            } 