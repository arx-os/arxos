"""
Building Application Service - High-Level Building Operations

This module contains the building application service that coordinates
building use cases and provides high-level business operations for
building management with infrastructure integration.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import time

from domain.repositories import UnitOfWork
from domain.events import BuildingCreated, BuildingUpdated, BuildingDeleted
from application.dto.building_dto import (
    CreateBuildingRequest, CreateBuildingResponse,
    UpdateBuildingRequest, UpdateBuildingResponse,
    GetBuildingResponse, ListBuildingsResponse,
    DeleteBuildingResponse
)
from infrastructure.services.cache_service import RedisCacheService
from infrastructure.services.event_store import EventStoreService
from infrastructure.services.message_queue import MessageQueueService
from infrastructure.monitoring.metrics import MetricsCollector
from infrastructure.monitoring.logging import StructuredLogger


class BuildingApplicationService:
    """Application service for building operations with infrastructure integration."""

    def __init__(self, unit_of_work: UnitOfWork,
                 cache_service: Optional[RedisCacheService] = None,
                 event_store: Optional[EventStoreService] = None,
                 message_queue: Optional[MessageQueueService] = None,
                 metrics: Optional[MetricsCollector] = None,
                 logger: Optional[StructuredLogger] = None):
        """Initialize building application service with infrastructure dependencies."""
        self.unit_of_work = unit_of_work
        self.cache_service = cache_service
        self.event_store = event_store
        self.message_queue = message_queue
        self.metrics = metrics
        self.logger = logger

    def create_building(self, name: str, address: str, description: Optional[str] = None,
                       coordinates: Optional[Dict[str, float]] = None,
                       dimensions: Optional[Dict[str, float]] = None,
                       created_by: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> CreateBuildingResponse:
        """Create a new building with infrastructure integration."""
        start_time = time.time()

        try:
            # Log the operation
            if self.logger:
                self.logger.info(
                    "Creating building",
                    building_name=name,
                    address=address,
                    created_by=created_by
                )

            # Execute use case directly with UnitOfWork
            from application.use_cases.building_use_cases import CreateBuildingUseCase
            create_building_uc = CreateBuildingUseCase(self.unit_of_work)

            request = CreateBuildingRequest(
                name=name,
                address=address,
                description=description,
                coordinates=coordinates,
                dimensions=dimensions,
                created_by=created_by,
                metadata=metadata
            )
            result = create_building_uc.execute(request)

            if result.success:
                # Publish domain event
                if self.event_store:
                    building_created_event = BuildingCreated(
                        building_id=str(result.building_id),
                        building_name=name,
                        address=address,
                        created_by=created_by
                    )
                    self.event_store.store_event(building_created_event)

                # Publish message to queue
                if self.message_queue:
                    message = {
                        'event_type': 'building.created',
                        'building_id': str(result.building_id),
                        'building_name': name,
                        'address': address,
                        'created_by': created_by,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    self.message_queue.publish('building.events', message)

                # Clear cache
                if self.cache_service:
                    self.cache_service.delete('buildings:list')
                    self.cache_service.delete('buildings:statistics')

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('building.create', time.time() - start_time)
                    self.metrics.increment_counter('building.created')

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('building.create.error')

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to create building",
                    building_name=name,
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('building.create.error')

            return CreateBuildingResponse(
                success=False,
                error_message=f"Failed to create building: {str(e)}"
            )

    def update_building(self, building_id: str, name: Optional[str] = None,
                       address: Optional[str] = None, description: Optional[str] = None,
                       coordinates: Optional[Dict[str, float]] = None,
                       dimensions: Optional[Dict[str, float]] = None,
                       status: Optional[str] = None, updated_by: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> UpdateBuildingResponse:
        """Update a building with infrastructure integration."""
        start_time = time.time()

        try:
            # Log the operation
            if self.logger:
                self.logger.info(
                    "Updating building",
                    building_id=building_id,
                    updated_by=updated_by
                )

            # Execute use case directly with UnitOfWork
            from application.use_cases.building_use_cases import UpdateBuildingUseCase
            update_building_uc = UpdateBuildingUseCase(self.unit_of_work)

            request = UpdateBuildingRequest(
                building_id=building_id,
                name=name,
                address=address,
                description=description,
                coordinates=coordinates,
                dimensions=dimensions,
                status=status,
                updated_by=updated_by,
                metadata=metadata
            )
            result = update_building_uc.execute(request)

            if result.success:
                # Publish domain event
                if self.event_store:
                    building_updated_event = BuildingUpdated(
                        building_id=building_id,
                        updated_fields=[field for field in [name, address, description, status] if field is not None],
                        updated_by=updated_by
                    )
                    self.event_store.store_event(building_updated_event)

                # Clear cache
                if self.cache_service:
                    self.cache_service.delete(f'building:{building_id}')
                    self.cache_service.delete('buildings:list')

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('building.update', time.time() - start_time)
                    self.metrics.increment_counter('building.updated')

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('building.update.error')

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to update building",
                    building_id=building_id,
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('building.update.error')

            return UpdateBuildingResponse(
                success=False,
                error_message=f"Failed to update building: {str(e)}"
            )

    def get_building(self, building_id: str) -> GetBuildingResponse:
        """Get a building with infrastructure integration."""
        start_time = time.time()

        try:
            # Check cache first
            if self.cache_service:
                cached_building = self.cache_service.get(f'building:{building_id}')
                if cached_building:
                    if self.metrics:
                        self.metrics.increment_counter('building.get.cache_hit')
                    return GetBuildingResponse(
                        success=True,
                        building=cached_building
                    )

            # Execute use case directly with UnitOfWork
            from application.use_cases.building_use_cases import GetBuildingUseCase
            get_building_uc = GetBuildingUseCase(self.unit_of_work)

            result = get_building_uc.execute(building_id)

            if result.success:
                # Cache the result
                if self.cache_service:
                    self.cache_service.set(f'building:{building_id}', result.building, ttl=300)

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('building.get', time.time() - start_time)
                    self.metrics.increment_counter('building.get.cache_miss')

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('building.get.error')

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to get building",
                    building_id=building_id,
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('building.get.error')

            return GetBuildingResponse(
                success=False,
                error_message=f"Failed to get building: {str(e)}"
            )

    def list_buildings(self, page: int = 1, page_size: int = 10,
                      status: Optional[str] = None) -> ListBuildingsResponse:
        """List buildings with infrastructure integration."""
        start_time = time.time()

        try:
            # Check cache first
            cache_key = f'buildings:list:{page}:{page_size}:{status or "all"}'
            if self.cache_service:
                cached_buildings = self.cache_service.get(cache_key)
                if cached_buildings:
                    if self.metrics:
                        self.metrics.increment_counter('building.list.cache_hit')
                    return ListBuildingsResponse(**cached_buildings)

            # Execute use case directly with UnitOfWork
            from application.use_cases.building_use_cases import ListBuildingsUseCase
            list_buildings_uc = ListBuildingsUseCase(self.unit_of_work)

            result = list_buildings_uc.execute(page, page_size, status)

            if result.success:
                # Cache the result
                if self.cache_service:
                    self.cache_service.set(cache_key, result.__dict__, ttl=60)

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('building.list', time.time() - start_time)
                    self.metrics.increment_counter('building.list.cache_miss')

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('building.list.error')

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to list buildings",
                    page=page,
                    page_size=page_size,
                    status=status,
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('building.list.error')

            return ListBuildingsResponse(
                success=False,
                error_message=f"Failed to list buildings: {str(e)}"
            )

    def delete_building(self, building_id: str) -> DeleteBuildingResponse:
        """Delete a building with infrastructure integration."""
        start_time = time.time()

        try:
            # Log the operation
            if self.logger:
                self.logger.info(
                    "Deleting building",
                    building_id=building_id
                )

            # Execute use case directly with UnitOfWork
            from application.use_cases.building_use_cases import DeleteBuildingUseCase
            delete_building_uc = DeleteBuildingUseCase(self.unit_of_work)

            result = delete_building_uc.execute(building_id)

            if result.success:
                # Publish domain event
                if self.event_store:
                    building_deleted_event = BuildingDeleted(
                        building_id=building_id,
                        building_name="",  # Would need to get from building import building
                        deleted_by="system"
                    )
                    self.event_store.store_event(building_deleted_event)

                # Clear cache
                if self.cache_service:
                    self.cache_service.delete(f'building:{building_id}')
                    self.cache_service.delete('buildings:list')
                    self.cache_service.delete('buildings:statistics')

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('building.delete', time.time() - start_time)
                    self.metrics.increment_counter('building.deleted')

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('building.delete.error')

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to delete building",
                    building_id=building_id,
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('building.delete.error')

            return DeleteBuildingResponse(
                success=False,
                error_message=f"Failed to delete building: {str(e)}"
            )

    def get_building_statistics(self) -> Dict[str, Any]:
        """Get building statistics with infrastructure integration."""
        start_time = time.time()

        try:
            # Check cache first
            if self.cache_service:
                cached_stats = self.cache_service.get('buildings:statistics')
                if cached_stats:
                    if self.metrics:
                        self.metrics.increment_counter('building.statistics.cache_hit')
                    return cached_stats

            # Get statistics using UnitOfWork
            buildings = self.unit_of_work.buildings.get_all()

            stats = {
                'total_buildings': len(buildings),
                'by_status': {},
                'by_type': {},
                'created_today': 0,
                'updated_today': 0
            }

            today = datetime.utcnow().date()

            for building in buildings:
                # Status breakdown
                status = building.status.value
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1

                # Type breakdown (could be based on building type if available)
                building_type = getattr(building, 'building_type', 'unknown')
                stats['by_type'][building_type] = stats['by_type'].get(building_type, 0) + 1

                # Today's activity'
                if building.created_at and building.created_at.date() == today:
                    stats['created_today'] += 1
                if building.updated_at and building.updated_at.date() == today:
                    stats['updated_today'] += 1

            # Cache the result
            if self.cache_service:
                self.cache_service.set('buildings:statistics', stats, ttl=300)

            # Record metrics
            if self.metrics:
                self.metrics.record_timing('building.statistics', time.time() - start_time)
                self.metrics.increment_counter('building.statistics.cache_miss')

            return stats

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to get building statistics",
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('building.statistics.error')

            return {
                'error': f"Failed to get building statistics: {str(e)}"
            }

    def search_buildings(self, query: str, page: int = 1, page_size: int = 10) -> ListBuildingsResponse:
        """Search buildings with infrastructure integration."""
        start_time = time.time()

        try:
            # Check cache first
            cache_key = f'buildings:search:{query}:{page}:{page_size}'
            if self.cache_service:
                cached_results = self.cache_service.get(cache_key)
                if cached_results:
                    if self.metrics:
                        self.metrics.increment_counter('building.search.cache_hit')
                    return ListBuildingsResponse(**cached_results)

            # For now, implement simple search using existing list functionality
            # In a real implementation, you might use a search engine like Elasticsearch
            all_buildings = self.unit_of_work.buildings.get_all()

            # Simple text search
            matching_buildings = []
            query_lower = query.lower()

            for building in all_buildings:
                if (query_lower in building.name.lower() or
                    query_lower in str(building.address).lower() or
                    (building.description and query_lower in building.description.lower())):
                    matching_buildings.append(building)

            # Apply pagination
            total_count = len(matching_buildings)
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_buildings = matching_buildings[start_index:end_index]

            # Convert to response format
            buildings_data = []
            for building in paginated_buildings:
                building_data = {
                    'id': str(building.id),
                    'name': building.name,
                    'address': str(building.address),
                    'status': building.status.value,
                    'description': building.description,
                    'created_at': building.created_at.isoformat() if building.created_at else None,
                    'updated_at': building.updated_at.isoformat() if building.updated_at else None,
                    'created_by': building.created_by,
                    'updated_by': building.updated_by
                }
                buildings_data.append(building_data)

            result = ListBuildingsResponse(
                success=True,
                buildings=buildings_data,
                total_count=total_count,
                page=page,
                page_size=page_size
            )

            # Cache the result
            if self.cache_service:
                self.cache_service.set(cache_key, result.__dict__, ttl=60)

            # Record metrics
            if self.metrics:
                self.metrics.record_timing('building.search', time.time() - start_time)
                self.metrics.increment_counter('building.search.cache_miss')

            return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to search buildings",
                    query=query,
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('building.search.error')

            return ListBuildingsResponse(
                success=False,
                error_message=f"Failed to search buildings: {str(e)}"
            )
