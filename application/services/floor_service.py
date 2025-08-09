"""
Floor Application Service - High-Level Floor Operations

This module contains the floor application service that coordinates
floor use cases and provides high-level business operations for
floor management with infrastructure integration.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import time

from domain.repositories import UnitOfWork
from domain.events import FloorCreated, FloorUpdated, FloorDeleted
from application.dto.floor_dto import (
    CreateFloorRequest, CreateFloorResponse,
    UpdateFloorRequest, UpdateFloorResponse,
    GetFloorResponse, ListFloorsResponse,
    DeleteFloorResponse
)
from infrastructure.services.cache_service import RedisCacheService
from infrastructure.services.event_store import EventStoreService
from infrastructure.services.message_queue import MessageQueueService
from infrastructure.monitoring.metrics import MetricsCollector
from infrastructure.monitoring.logging import StructuredLogger


class FloorApplicationService:
    """Application service for floor operations with infrastructure integration."""

    def __init__(self, unit_of_work: UnitOfWork,
                 cache_service: Optional[RedisCacheService] = None,
                 event_store: Optional[EventStoreService] = None,
                 message_queue: Optional[MessageQueueService] = None,
                 metrics: Optional[MetricsCollector] = None,
                 logger: Optional[StructuredLogger] = None):
        """Initialize floor application service with infrastructure dependencies."""
        self.unit_of_work = unit_of_work
        self.cache_service = cache_service
        self.event_store = event_store
        self.message_queue = message_queue
        self.metrics = metrics
        self.logger = logger

    def create_floor(self, building_id: str, floor_number: int,
                    name: Optional[str] = None,
                    description: Optional[str] = None,
                    area: Optional[float] = None,
                    created_by: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> CreateFloorResponse:
        """Create a new floor with infrastructure integration."""
        start_time = time.time()

        try:
            # Log the operation
            if self.logger:
                self.logger.info(
                    "Creating floor",
                    floor_number=floor_number,
                    building_id=building_id,
                    created_by=created_by
                )

            # Execute use case directly with UnitOfWork
            from application.use_cases.floor_use_cases import CreateFloorUseCase
            create_floor_uc = CreateFloorUseCase(self.unit_of_work)

            request = CreateFloorRequest(
                building_id=building_id,
                floor_number=floor_number,
                name=name,
                description=description,
                area=area,
                created_by=created_by,
                metadata=metadata
            )
            result = create_floor_uc.execute(request)

            if result.success:
                # Publish domain event
                if self.event_store:
                    floor_created_event = FloorCreated(
                        floor_id=str(result.floor_id),
                        building_id=building_id,
                        floor_number=floor_number,
                        created_by=created_by
                    )
                    self.event_store.store_event(floor_created_event)

                # Publish message to queue
                if self.message_queue:
                    message = {
                        'event_type': 'floor.created',
                        'floor_id': str(result.floor_id),
                        'floor_number': floor_number,
                        'building_id': building_id,
                        'created_by': created_by,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    self.message_queue.publish('floor.events', message)

                # Clear cache
                if self.cache_service:
                    self.cache_service.delete(f'building:{building_id}:floors')
                    self.cache_service.delete('floors:list')
                    self.cache_service.delete('floors:statistics')

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('floor.create', time.time() - start_time)
                    self.metrics.increment_counter('floor.created')

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('floor.create.error')

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to create floor",
                    floor_number=floor_number,
                    building_id=building_id,
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('floor.create.error')

            return CreateFloorResponse(
                success=False,
                error_message=f"Failed to create floor: {str(e)}"
            )

    def update_floor(self, floor_id: str, floor_number: Optional[int] = None,
                    name: Optional[str] = None,
                    description: Optional[str] = None,
                    area: Optional[float] = None,
                    status: Optional[str] = None,
                    updated_by: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> UpdateFloorResponse:
        """Update a floor with infrastructure integration."""
        start_time = time.time()

        try:
            # Log the operation
            if self.logger:
                self.logger.info(
                    "Updating floor",
                    floor_id=floor_id,
                    updated_by=updated_by
                )

            # Execute use case directly with UnitOfWork
            from application.use_cases.floor_use_cases import UpdateFloorUseCase
            update_floor_uc = UpdateFloorUseCase(self.unit_of_work)

            request = UpdateFloorRequest(
                floor_id=floor_id,
                floor_number=floor_number,
                name=name,
                description=description,
                area=area,
                status=status,
                updated_by=updated_by,
                metadata=metadata
            )
            result = update_floor_uc.execute(request)

            if result.success:
                # Publish domain event
                if self.event_store:
                    floor_updated_event = FloorUpdated(
                        floor_id=floor_id,
                        updated_fields=[field for field in [floor_number, status] if field is not None],
                        updated_by=updated_by
                    )
                    self.event_store.store_event(floor_updated_event)

                # Clear cache
                if self.cache_service:
                    self.cache_service.delete(f'floor:{floor_id}')
                    self.cache_service.delete('floors:list')

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('floor.update', time.time() - start_time)
                    self.metrics.increment_counter('floor.updated')

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('floor.update.error')

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to update floor",
                    floor_id=floor_id,
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('floor.update.error')

            return UpdateFloorResponse(
                success=False,
                error_message=f"Failed to update floor: {str(e)}"
            )

    def get_floor(self, floor_id: str) -> GetFloorResponse:
        """Get a floor with infrastructure integration."""
        start_time = time.time()

        try:
            # Check cache first
            if self.cache_service:
                cached_floor = self.cache_service.get(f'floor:{floor_id}')
                if cached_floor:
                    if self.metrics:
                        self.metrics.increment_counter('floor.get.cache_hit')
                    return GetFloorResponse(
                        success=True,
                        floor=cached_floor
                    )

            # Execute use case directly with UnitOfWork
            from application.use_cases.floor_use_cases import GetFloorUseCase
            get_floor_uc = GetFloorUseCase(self.unit_of_work)

            result = get_floor_uc.execute(floor_id)

            if result.success:
                # Cache the result
                if self.cache_service:
                    self.cache_service.set(f'floor:{floor_id}', result.floor, ttl=300)

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('floor.get', time.time() - start_time)
                    self.metrics.increment_counter('floor.get.cache_miss')

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('floor.get.error')

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to get floor",
                    floor_id=floor_id,
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('floor.get.error')

            return GetFloorResponse(
                success=False,
                error_message=f"Failed to get floor: {str(e)}"
            )

    def list_floors(self, building_id: Optional[str] = None,
                   status: Optional[str] = None,
                   page: int = 1, page_size: int = 10) -> ListFloorsResponse:
        """List floors with infrastructure integration."""
        start_time = time.time()

        try:
            # Check cache first
            cache_key = f'floors:list:{building_id or "all"}:{status or "all"}:{page}:{page_size}'
            if self.cache_service:
                cached_floors = self.cache_service.get(cache_key)
                if cached_floors:
                    if self.metrics:
                        self.metrics.increment_counter('floor.list.cache_hit')
                    return ListFloorsResponse(**cached_floors)

            # Execute use case directly with UnitOfWork
            from application.use_cases.floor_use_cases import ListFloorsUseCase
            list_floors_uc = ListFloorsUseCase(self.unit_of_work)

            result = list_floors_uc.execute(building_id, status, page, page_size)

            if result.success:
                # Cache the result
                if self.cache_service:
                    self.cache_service.set(cache_key, result.__dict__, ttl=60)

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('floor.list', time.time() - start_time)
                    self.metrics.increment_counter('floor.list.cache_miss')

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('floor.list.error')

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to list floors",
                    building_id=building_id,
                    status=status,
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('floor.list.error')

            return ListFloorsResponse(
                success=False,
                error_message=f"Failed to list floors: {str(e)}"
            )

    def delete_floor(self, floor_id: str) -> DeleteFloorResponse:
        """Delete a floor with infrastructure integration."""
        start_time = time.time()

        try:
            # Log the operation
            if self.logger:
                self.logger.info(
                    "Deleting floor",
                    floor_id=floor_id
                )

            # Execute use case directly with UnitOfWork
            from application.use_cases.floor_use_cases import DeleteFloorUseCase
            delete_floor_uc = DeleteFloorUseCase(self.unit_of_work)

            result = delete_floor_uc.execute(floor_id)

            if result.success:
                # Publish domain event
                if self.event_store:
                    floor_deleted_event = FloorDeleted(
                        floor_id=floor_id,
                        floor_number=0,  # Would need to get from floor import floor
                        deleted_by="system"
                    )
                    self.event_store.store_event(floor_deleted_event)

                # Clear cache
                if self.cache_service:
                    self.cache_service.delete(f'floor:{floor_id}')
                    self.cache_service.delete('floors:list')
                    self.cache_service.delete('floors:statistics')

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('floor.delete', time.time() - start_time)
                    self.metrics.increment_counter('floor.deleted')

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('floor.delete.error')

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to delete floor",
                    floor_id=floor_id,
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('floor.delete.error')

            return DeleteFloorResponse(
                success=False,
                error_message=f"Failed to delete floor: {str(e)}"
            )

    def get_floor_statistics(self) -> Dict[str, Any]:
        """Get floor statistics with infrastructure integration."""
        start_time = time.time()

        try:
            # Check cache first
            if self.cache_service:
                cached_stats = self.cache_service.get('floors:statistics')
                if cached_stats:
                    if self.metrics:
                        self.metrics.increment_counter('floor.statistics.cache_hit')
                    return cached_stats

            # Get statistics using UnitOfWork
            floors = self.unit_of_work.floors.get_all()

            stats = {
                'total_floors': len(floors),
                'by_status': {},
                'by_building': {},
                'created_today': 0,
                'updated_today': 0
            }

            today = datetime.utcnow().date()

            for floor in floors:
                # Status breakdown
                status = floor.status.value
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1

                # Building breakdown
                building_id = str(floor.building_id)
                stats['by_building'][building_id] = stats['by_building'].get(building_id, 0) + 1

                # Today's activity'
                if floor.created_at and floor.created_at.date() == today:
                    stats['created_today'] += 1
                if floor.updated_at and floor.updated_at.date() == today:
                    stats['updated_today'] += 1

            # Cache the result
            if self.cache_service:
                self.cache_service.set('floors:statistics', stats, ttl=300)

            # Record metrics
            if self.metrics:
                self.metrics.record_timing('floor.statistics', time.time() - start_time)
                self.metrics.increment_counter('floor.statistics.cache_miss')

            return stats

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to get floor statistics",
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('floor.statistics.error')

            return {
                'error': f"Failed to get floor statistics: {str(e)}"
            }
