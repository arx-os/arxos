"""
Room Application Service - High-Level Room Operations

This module contains the room application service that coordinates
room use cases and provides high-level business operations for
room management with infrastructure integration.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import time

from domain.repositories import UnitOfWork
from domain.events import RoomCreated, RoomUpdated, RoomDeleted
from application.dto.room_dto import (
    CreateRoomRequest, CreateRoomResponse,
    UpdateRoomRequest, UpdateRoomResponse,
    GetRoomResponse, ListRoomsResponse,
    DeleteRoomResponse
)
from infrastructure.services.cache_service import RedisCacheService
from infrastructure.services.event_store import EventStoreService
from infrastructure.services.message_queue import MessageQueueService
from infrastructure.monitoring.metrics import MetricsCollector
from infrastructure.monitoring.logging import StructuredLogger


class RoomApplicationService:
    """Application service for room operations with infrastructure integration."""

    def __init__(self, unit_of_work: UnitOfWork,
                 cache_service: Optional[RedisCacheService] = None,
                 event_store: Optional[EventStoreService] = None,
                 message_queue: Optional[MessageQueueService] = None,
                 metrics: Optional[MetricsCollector] = None,
                 logger: Optional[StructuredLogger] = None):
        """Initialize room application service with infrastructure dependencies."""
        self.unit_of_work = unit_of_work
        self.cache_service = cache_service
        self.event_store = event_store
        self.message_queue = message_queue
        self.metrics = metrics
        self.logger = logger

    def create_room(self, floor_id: str, room_number: str, room_type: str,
                   name: Optional[str] = None,
                   description: Optional[str] = None,
                   area: Optional[float] = None,
                   capacity: Optional[int] = None,
                   created_by: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> CreateRoomResponse:
        """Create a new room with infrastructure integration."""
        start_time = time.time()

        try:
            # Log the operation
            if self.logger:
                self.logger.info(
                    "Creating room",
                    room_number=room_number,
                    room_type=room_type,
                    floor_id=floor_id,
                    created_by=created_by
                )

            # Execute use case directly with UnitOfWork
            from application.use_cases.room_use_cases import CreateRoomUseCase
            create_room_uc = CreateRoomUseCase(self.unit_of_work)

            request = CreateRoomRequest(
                floor_id=floor_id,
                room_number=room_number,
                room_type=room_type,
                name=name,
                description=description,
                area=area,
                capacity=capacity,
                created_by=created_by,
                metadata=metadata
            )
            result = create_room_uc.execute(request)

            if result.success:
                # Publish domain event
                if self.event_store:
                    room_created_event = RoomCreated(
                        room_id=str(result.room_id),
                        floor_id=floor_id,
                        room_number=room_number,
                        room_type=room_type,
                        created_by=created_by
                    )
                    self.event_store.store_event(room_created_event)

                # Publish message to queue
                if self.message_queue:
                    message = {
                        'event_type': 'room.created',
                        'room_id': str(result.room_id),
                        'room_number': room_number,
                        'room_type': room_type,
                        'floor_id': floor_id,
                        'created_by': created_by,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    self.message_queue.publish('room.events', message)

                # Clear cache
                if self.cache_service:
                    self.cache_service.delete(f'floor:{floor_id}:rooms')
                    self.cache_service.delete('rooms:list')
                    self.cache_service.delete('rooms:statistics')

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('room.create', time.time() - start_time)
                    self.metrics.increment_counter('room.created')

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('room.create.error')

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to create room",
                    room_number=room_number,
                    room_type=room_type,
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('room.create.error')

            return CreateRoomResponse(
                success=False,
                error_message=f"Failed to create room: {str(e)}"
            )

    def update_room(self, room_id: str, room_number: Optional[str] = None,
                   room_type: Optional[str] = None,
                   name: Optional[str] = None,
                   description: Optional[str] = None,
                   area: Optional[float] = None,
                   capacity: Optional[int] = None,
                   status: Optional[str] = None,
                   updated_by: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> UpdateRoomResponse:
        """Update a room with infrastructure integration."""
        start_time = time.time()

        try:
            # Log the operation
            if self.logger:
                self.logger.info(
                    "Updating room",
                    room_id=room_id,
                    updated_by=updated_by
                )

            # Execute use case directly with UnitOfWork
            from application.use_cases.room_use_cases import UpdateRoomUseCase
            update_room_uc = UpdateRoomUseCase(self.unit_of_work)

            request = UpdateRoomRequest(
                room_id=room_id,
                room_number=room_number,
                room_type=room_type,
                name=name,
                description=description,
                area=area,
                capacity=capacity,
                status=status,
                updated_by=updated_by,
                metadata=metadata
            )
            result = update_room_uc.execute(request)

            if result.success:
                # Publish domain event
                if self.event_store:
                    room_updated_event = RoomUpdated(
                        room_id=room_id,
                        updated_fields=[field for field in [room_number, room_type, status] if field is not None],
                        updated_by=updated_by
                    )
                    self.event_store.store_event(room_updated_event)

                # Clear cache
                if self.cache_service:
                    self.cache_service.delete(f'room:{room_id}')
                    self.cache_service.delete('rooms:list')

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('room.update', time.time() - start_time)
                    self.metrics.increment_counter('room.updated')

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('room.update.error')

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to update room",
                    room_id=room_id,
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('room.update.error')

            return UpdateRoomResponse(
                success=False,
                error_message=f"Failed to update room: {str(e)}"
            )

    def get_room(self, room_id: str) -> GetRoomResponse:
        """Get a room with infrastructure integration."""
        start_time = time.time()

        try:
            # Check cache first
            if self.cache_service:
                cached_room = self.cache_service.get(f'room:{room_id}')
                if cached_room:
                    if self.metrics:
                        self.metrics.increment_counter('room.get.cache_hit')
                    return GetRoomResponse(
                        success=True,
                        room=cached_room
                    )

            # Execute use case directly with UnitOfWork
            from application.use_cases.room_use_cases import GetRoomUseCase
            get_room_uc = GetRoomUseCase(self.unit_of_work)

            result = get_room_uc.execute(room_id)

            if result.success:
                # Cache the result
                if self.cache_service:
                    self.cache_service.set(f'room:{room_id}', result.room, ttl=300)

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('room.get', time.time() - start_time)
                    self.metrics.increment_counter('room.get.cache_miss')

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('room.get.error')

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to get room",
                    room_id=room_id,
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('room.get.error')

            return GetRoomResponse(
                success=False,
                error_message=f"Failed to get room: {str(e)}"
            )

    def list_rooms(self, floor_id: Optional[str] = None,
                  room_type: Optional[str] = None,
                  status: Optional[str] = None,
                  page: int = 1, page_size: int = 10) -> ListRoomsResponse:
        """List rooms with infrastructure integration."""
        start_time = time.time()

        try:
            # Check cache first
            cache_key = f'rooms:list:{floor_id or "all"}:{room_type or "all"}:{status or "all"}:{page}:{page_size}'
            if self.cache_service:
                cached_rooms = self.cache_service.get(cache_key)
                if cached_rooms:
                    if self.metrics:
                        self.metrics.increment_counter('room.list.cache_hit')
                    return ListRoomsResponse(**cached_rooms)

            # Execute use case directly with UnitOfWork
            from application.use_cases.room_use_cases import ListRoomsUseCase
            list_rooms_uc = ListRoomsUseCase(self.unit_of_work)

            result = list_rooms_uc.execute(floor_id, room_type, status, page, page_size)

            if result.success:
                # Cache the result
                if self.cache_service:
                    self.cache_service.set(cache_key, result.__dict__, ttl=60)

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('room.list', time.time() - start_time)
                    self.metrics.increment_counter('room.list.cache_miss')

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('room.list.error')

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to list rooms",
                    floor_id=floor_id,
                    room_type=room_type,
                    status=status,
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('room.list.error')

            return ListRoomsResponse(
                success=False,
                error_message=f"Failed to list rooms: {str(e)}"
            )

    def delete_room(self, room_id: str) -> DeleteRoomResponse:
        """Delete a room with infrastructure integration."""
        start_time = time.time()

        try:
            # Log the operation
            if self.logger:
                self.logger.info(
                    "Deleting room",
                    room_id=room_id
                )

            # Execute use case directly with UnitOfWork
            from application.use_cases.room_use_cases import DeleteRoomUseCase
            delete_room_uc = DeleteRoomUseCase(self.unit_of_work)

            result = delete_room_uc.execute(room_id)

            if result.success:
                # Publish domain event
                if self.event_store:
                    room_deleted_event = RoomDeleted(
                        room_id=room_id,
                        room_number="",  # Would need to get from room import room
                        deleted_by="system"
                    )
                    self.event_store.store_event(room_deleted_event)

                # Clear cache
                if self.cache_service:
                    self.cache_service.delete(f'room:{room_id}')
                    self.cache_service.delete('rooms:list')
                    self.cache_service.delete('rooms:statistics')

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('room.delete', time.time() - start_time)
                    self.metrics.increment_counter('room.deleted')

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('room.delete.error')

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to delete room",
                    room_id=room_id,
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('room.delete.error')

            return DeleteRoomResponse(
                success=False,
                error_message=f"Failed to delete room: {str(e)}"
            )

    def get_room_statistics(self) -> Dict[str, Any]:
        """Get room statistics with infrastructure integration."""
        start_time = time.time()

        try:
            # Check cache first
            if self.cache_service:
                cached_stats = self.cache_service.get('rooms:statistics')
                if cached_stats:
                    if self.metrics:
                        self.metrics.increment_counter('room.statistics.cache_hit')
                    return cached_stats

            # Get statistics using UnitOfWork
            rooms = self.unit_of_work.rooms.get_all()

            stats = {
                'total_rooms': len(rooms),
                'by_status': {},
                'by_type': {},
                'by_floor': {},
                'created_today': 0,
                'updated_today': 0
            }

            today = datetime.utcnow().date()

            for room in rooms:
                # Status breakdown
                status = room.status.value
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1

                # Type breakdown
                room_type = room.room_type
                stats['by_type'][room_type] = stats['by_type'].get(room_type, 0) + 1

                # Floor breakdown
                floor_id = str(room.floor_id)
                stats['by_floor'][floor_id] = stats['by_floor'].get(floor_id, 0) + 1

                # Today's activity'
                if room.created_at and room.created_at.date() == today:
                    stats['created_today'] += 1
                if room.updated_at and room.updated_at.date() == today:
                    stats['updated_today'] += 1

            # Cache the result
            if self.cache_service:
                self.cache_service.set('rooms:statistics', stats, ttl=300)

            # Record metrics
            if self.metrics:
                self.metrics.record_timing('room.statistics', time.time() - start_time)
                self.metrics.increment_counter('room.statistics.cache_miss')

            return stats

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to get room statistics",
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('room.statistics.error')

            return {
                'error': f"Failed to get room statistics: {str(e)}"
            }
