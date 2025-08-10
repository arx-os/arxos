"""
Device Application Service - High-Level Device Operations

This module contains the device application service that coordinates
device use cases and provides high-level business operations for
device management with infrastructure integration.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from domain.entities import Device
from domain.value_objects import DeviceId, RoomId, DeviceStatus
from domain.repositories import UnitOfWork
from domain.events import DeviceCreated, DeviceUpdated, DeviceDeleted
from application.dto.device_dto import (
    CreateDeviceRequest, CreateDeviceResponse,
    UpdateDeviceRequest, UpdateDeviceResponse,
    GetDeviceResponse, ListDevicesResponse,
    DeleteDeviceResponse
)
from application.services.base_service import BaseApplicationService
from infrastructure.services.cache_service import RedisCacheService
from infrastructure.services.event_store import EventStoreService
from infrastructure.services.message_queue import MessageQueueService
from infrastructure.monitoring.metrics import MetricsCollector


class DeviceApplicationService(BaseApplicationService[Device]):
    """Application service for device operations with comprehensive infrastructure integration."""

    def __init__(self, unit_of_work: UnitOfWork,
                 cache_service: Optional[RedisCacheService] = None,
                 event_store: Optional[EventStoreService] = None,
                 message_queue: Optional[MessageQueueService] = None,
                 metrics: Optional[MetricsCollector] = None):
        """Initialize device application service with infrastructure dependencies."""
        super().__init__(
            unit_of_work=unit_of_work,
            entity_name="Device",
            cache_service=cache_service,
            event_store=event_store,
            message_queue=message_queue,
            metrics=metrics
        )

    def create_device(self, room_id: str, device_type: str, name: str,
                     manufacturer: Optional[str] = None,
                     model: Optional[str] = None,
                     serial_number: Optional[str] = None,
                     description: Optional[str] = None,
                     created_by: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> CreateDeviceResponse:
        """Create a new device with infrastructure integration."""
        start_time = time.time()

        try:
            # Log the operation
            if self.logger:
                self.logger.info(
                    "Creating device",
                    device_name=name,
                    device_type=device_type,
                    room_id=room_id,
                    created_by=created_by
                )

            # Execute use case directly with UnitOfWork
            from application.use_cases.device_use_cases import CreateDeviceUseCase
            create_device_uc = CreateDeviceUseCase(self.unit_of_work)

            request = CreateDeviceRequest(
                room_id=room_id,
                device_type=device_type,
                name=name,
                manufacturer=manufacturer,
                model=model,
                serial_number=serial_number,
                description=description,
                created_by=created_by,
                metadata=metadata
            )
            result = create_device_uc.execute(request)

            if result.success:
                # Publish domain event
                if self.event_store:
                    device_created_event = DeviceCreated(
                        device_id=str(result.device_id),
                        room_id=room_id,
                        device_type=device_type,
                        name=name,
                        created_by=created_by
                    )
                    self.event_store.store_event(device_created_event)

                # Publish message to queue
                if self.message_queue:
                    message = {
                        'event_type': 'device.created',
                        'device_id': str(result.device_id),
                        'device_name': name,
                        'device_type': device_type,
                        'room_id': room_id,
                        'created_by': created_by,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    self.message_queue.publish('device.events', message)

                # Clear cache
                if self.cache_service:
                    self.cache_service.delete(f'room:{room_id}:devices')
                    self.cache_service.delete('devices:list')
                    self.cache_service.delete('devices:statistics')

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('device.create', time.time() - start_time)
                    self.metrics.increment_counter('device.created')

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('device.create.error')

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to create device",
                    device_name=name,
                    device_type=device_type,
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('device.create.error')

            return CreateDeviceResponse(
                success=False,
                error_message=f"Failed to create device: {str(e)}"
            )

    def update_device(self, device_id: str, name: Optional[str] = None,
                     device_type: Optional[str] = None,
                     manufacturer: Optional[str] = None,
                     model: Optional[str] = None,
                     serial_number: Optional[str] = None,
                     description: Optional[str] = None,
                     status: Optional[str] = None,
                     updated_by: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> UpdateDeviceResponse:
        """Update a device with infrastructure integration."""
        start_time = time.time()

        try:
            # Log the operation
            if self.logger:
                self.logger.info(
                    "Updating device",
                    device_id=device_id,
                    updated_by=updated_by
                )

            # Execute use case directly with UnitOfWork
            from application.use_cases.device_use_cases import UpdateDeviceUseCase
            update_device_uc = UpdateDeviceUseCase(self.unit_of_work)

            request = UpdateDeviceRequest(
                device_id=device_id,
                name=name,
                device_type=device_type,
                manufacturer=manufacturer,
                model=model,
                serial_number=serial_number,
                description=description,
                status=status,
                updated_by=updated_by,
                metadata=metadata
            )
            result = update_device_uc.execute(request)

            if result.success:
                # Publish domain event
                if self.event_store:
                    device_updated_event = DeviceUpdated(
                        device_id=device_id,
                        updated_fields=[field for field in [name, device_type, status] if field is not None],
                        updated_by=updated_by
                    )
                    self.event_store.store_event(device_updated_event)

                # Clear cache
                if self.cache_service:
                    self.cache_service.delete(f'device:{device_id}')
                    self.cache_service.delete('devices:list')

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('device.update', time.time() - start_time)
                    self.metrics.increment_counter('device.updated')

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('device.update.error')

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to update device",
                    device_id=device_id,
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('device.update.error')

            return UpdateDeviceResponse(
                success=False,
                error_message=f"Failed to update device: {str(e)}"
            )

    def get_device(self, device_id: str) -> GetDeviceResponse:
        """Get a device with infrastructure integration."""
        start_time = time.time()

        try:
            # Check cache first
            if self.cache_service:
                cached_device = self.cache_service.get(f'device:{device_id}')
                if cached_device:
                    if self.metrics:
                        self.metrics.increment_counter('device.get.cache_hit')
                    return GetDeviceResponse(
                        success=True,
                        device=cached_device
                    )

            # Execute use case directly with UnitOfWork
            from application.use_cases.device_use_cases import GetDeviceUseCase
            get_device_uc = GetDeviceUseCase(self.unit_of_work)

            result = get_device_uc.execute(device_id)

            if result.success:
                # Cache the result
                if self.cache_service:
                    self.cache_service.set(f'device:{device_id}', result.device, ttl=300)

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('device.get', time.time() - start_time)
                    self.metrics.increment_counter('device.get.cache_miss')

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('device.get.error')

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to get device",
                    device_id=device_id,
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('device.get.error')

            return GetDeviceResponse(
                success=False,
                error_message=f"Failed to get device: {str(e)}"
            )

    def list_devices(self, room_id: Optional[str] = None,
                    device_type: Optional[str] = None,
                    status: Optional[str] = None,
                    page: int = 1, page_size: int = 10) -> ListDevicesResponse:
        """List devices with infrastructure integration."""
        start_time = time.time()

        try:
            # Check cache first
            cache_key = f'devices:list:{room_id or "all"}:{device_type or "all"}:{status or "all"}:{page}:{page_size}'
            if self.cache_service:
                cached_devices = self.cache_service.get(cache_key)
                if cached_devices:
                    if self.metrics:
                        self.metrics.increment_counter('device.list.cache_hit')
                    return ListDevicesResponse(**cached_devices)

            # Execute use case directly with UnitOfWork
            from application.use_cases.device_use_cases import ListDevicesUseCase
            list_devices_uc = ListDevicesUseCase(self.unit_of_work)

            result = list_devices_uc.execute(room_id, device_type, status, page, page_size)

            if result.success:
                # Cache the result
                if self.cache_service:
                    self.cache_service.set(cache_key, result.__dict__, ttl=60)

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('device.list', time.time() - start_time)
                    self.metrics.increment_counter('device.list.cache_miss')

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('device.list.error')

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to list devices",
                    room_id=room_id,
                    device_type=device_type,
                    status=status,
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('device.list.error')

            return ListDevicesResponse(
                success=False,
                error_message=f"Failed to list devices: {str(e)}"
            )

    def delete_device(self, device_id: str) -> DeleteDeviceResponse:
        """Delete a device with infrastructure integration."""
        start_time = time.time()

        try:
            # Log the operation
            if self.logger:
                self.logger.info(
                    "Deleting device",
                    device_id=device_id
                )

            # Execute use case directly with UnitOfWork
            from application.use_cases.device_use_cases import DeleteDeviceUseCase
            delete_device_uc = DeleteDeviceUseCase(self.unit_of_work)

            result = delete_device_uc.execute(device_id)

            if result.success:
                # Publish domain event
                if self.event_store:
                    device_deleted_event = DeviceDeleted(
                        device_id=device_id,
                        device_name="",  # Would need to get from device import device
                        deleted_by="system"
                    )
                    self.event_store.store_event(device_deleted_event)

                # Clear cache
                if self.cache_service:
                    self.cache_service.delete(f'device:{device_id}')
                    self.cache_service.delete('devices:list')
                    self.cache_service.delete('devices:statistics')

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing('device.delete', time.time() - start_time)
                    self.metrics.increment_counter('device.deleted')

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter('device.delete.error')

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to delete device",
                    device_id=device_id,
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('device.delete.error')

            return DeleteDeviceResponse(
                success=False,
                error_message=f"Failed to delete device: {str(e)}"
            )

    def get_device_statistics(self) -> Dict[str, Any]:
        """Get device statistics with infrastructure integration."""
        start_time = time.time()

        try:
            # Check cache first
            if self.cache_service:
                cached_stats = self.cache_service.get('devices:statistics')
                if cached_stats:
                    if self.metrics:
                        self.metrics.increment_counter('device.statistics.cache_hit')
                    return cached_stats

            # Get statistics using UnitOfWork
            devices = self.unit_of_work.devices.get_all()

            stats = {
                'total_devices': len(devices),
                'by_status': {},
                'by_type': {},
                'by_manufacturer': {},
                'created_today': 0,
                'updated_today': 0
            }

            today = datetime.utcnow().date()

            for device in devices:
                # Status breakdown
                status = device.status.value
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1

                # Type breakdown
                device_type = device.device_type
                stats['by_type'][device_type] = stats['by_type'].get(device_type, 0) + 1

                # Manufacturer breakdown
                manufacturer = device.manufacturer or 'unknown'
                stats['by_manufacturer'][manufacturer] = stats['by_manufacturer'].get(manufacturer, 0) + 1

                # Today's activity'
                if device.created_at and device.created_at.date() == today:
                    stats['created_today'] += 1
                if device.updated_at and device.updated_at.date() == today:
                    stats['updated_today'] += 1

            # Cache the result
            if self.cache_service:
                self.cache_service.set('devices:statistics', stats, ttl=300)

            # Record metrics
            if self.metrics:
                self.metrics.record_timing('device.statistics', time.time() - start_time)
                self.metrics.increment_counter('device.statistics.cache_miss')

            return stats

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to get device statistics",
                    error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter('device.statistics.error')

            return {
                'error': f"Failed to get device statistics: {str(e)}"
            }
