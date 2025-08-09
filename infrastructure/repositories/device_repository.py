"""
Device Repository Implementation

This module contains the SQLAlchemy implementation of the DeviceRepository
interface defined in the domain layer.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from domain.entities import Device
from domain.value_objects import DeviceId, DeviceStatus, RoomId, FloorId, BuildingId
from domain.repositories import DeviceRepository
from domain.exceptions import RepositoryError

from .base import BaseRepository
from infrastructure.database.models.device import DeviceModel


class SQLAlchemyDeviceRepository(BaseRepository[Device, DeviceModel], DeviceRepository):
    """SQLAlchemy implementation of DeviceRepository."""

    def __init__(self, session: Session):
        """Initialize device repository."""
        super().__init__(session, Device, DeviceModel)

    def save(self, device: Device) -> None:
        """Save a device to the repository."""
        try:
            model = self._entity_to_model(device)
            self.session.add(model)
            self.session.flush()
        except Exception as e:
            raise RepositoryError(f"Failed to save device: {str(e)}")

    def get_by_id(self, device_id: DeviceId) -> Optional[Device]:
        """Get a device by its ID."""
        try:
            model = self.session.query(DeviceModel).filter(
                and_(
                    DeviceModel.id == device_id.value,
                    DeviceModel.deleted_at.is_(None)
                )
            ).first()

            if model is None:
                return None

            return self._model_to_entity(model)
        except Exception as e:
            raise RepositoryError(f"Failed to get device by ID: {str(e)}")

    def get_by_room_id(self, room_id: RoomId) -> List[Device]:
        """Get all devices in a room."""
        try:
            models = self.session.query(DeviceModel).filter(
                and_(
                    DeviceModel.room_id == room_id.value,
                    DeviceModel.deleted_at.is_(None)
                )
            ).order_by(DeviceModel.name).all()

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find devices by room ID: {str(e)}")

    def get_by_floor_id(self, floor_id: FloorId) -> List[Device]:
        """Get all devices on a floor."""
        try:
            # Join with rooms to get devices by floor
            models = self.session.query(DeviceModel).join(
                DeviceModel.room
            ).filter(
                and_(
                    DeviceModel.room.has(room_id=floor_id.value),
                    DeviceModel.deleted_at.is_(None)
                )
            ).order_by(DeviceModel.name).all()

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find devices by floor ID: {str(e)}")

    def get_by_building_id(self, building_id: BuildingId) -> List[Device]:
        """Get all devices in a building."""
        try:
            # Join with rooms and floors to get devices by building
            models = self.session.query(DeviceModel).join(
                DeviceModel.room
            ).join(
                DeviceModel.room.floor
            ).filter(
                and_(
                    DeviceModel.room.floor.has(building_id=building_id.value),
                    DeviceModel.deleted_at.is_(None)
                )
            ).order_by(DeviceModel.name).all()

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find devices by building ID: {str(e)}")

    def get_by_type(self, device_type: str) -> List[Device]:
        """Get devices by type."""
        try:
            models = self.session.query(DeviceModel).filter(
                and_(
                    DeviceModel.device_type == device_type,
                    DeviceModel.deleted_at.is_(None)
                )
            ).order_by(DeviceModel.name).all()

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find devices by type: {str(e)}")

    def get_by_status(self, status: DeviceStatus) -> List[Device]:
        """Get devices by status."""
        try:
            models = self.session.query(DeviceModel).filter(
                and_(
                    DeviceModel.status == status,
                    DeviceModel.deleted_at.is_(None)
                )
            ).order_by(DeviceModel.name).all()

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find devices by status: {str(e)}")

    def delete(self, device_id: DeviceId) -> None:
        """Delete a device by ID."""
        try:
            model = self.session.query(DeviceModel).filter(
                and_(
                    DeviceModel.id == device_id.value,
                    DeviceModel.deleted_at.is_(None)
                )
            ).first()

            if model is None:
                raise RepositoryError(f"Device with ID {device_id} not found")

            model.soft_delete()
            self.session.flush()
        except Exception as e:
            raise RepositoryError(f"Failed to delete device: {str(e)}")

    def exists(self, device_id: DeviceId) -> bool:
        """Check if a device exists."""
        try:
            return self.session.query(DeviceModel).filter(
                and_(
                    DeviceModel.id == device_id.value,
                    DeviceModel.deleted_at.is_(None)
                )
            ).first() is not None
        except Exception as e:
            raise RepositoryError(f"Failed to check device existence: {str(e)}")

    def count_by_room(self, room_id: RoomId) -> int:
        """Get the number of devices in a room."""
        try:
            return self.session.query(DeviceModel).filter(
                and_(
                    DeviceModel.room_id == room_id.value,
                    DeviceModel.deleted_at.is_(None)
                )
            ).count()
        except Exception as e:
            raise RepositoryError(f"Failed to count devices by room: {str(e)}")

    def count_by_floor(self, floor_id: FloorId) -> int:
        """Get the number of devices on a floor."""
        try:
            return self.session.query(DeviceModel).join(
                DeviceModel.room
            ).filter(
                and_(
                    DeviceModel.room.has(room_id=floor_id.value),
                    DeviceModel.deleted_at.is_(None)
                )
            ).count()
        except Exception as e:
            raise RepositoryError(f"Failed to count devices by floor: {str(e)}")

    def count_by_building(self, building_id: BuildingId) -> int:
        """Get the number of devices in a building."""
        try:
            return self.session.query(DeviceModel).join(
                DeviceModel.room
            ).join(
                DeviceModel.room.floor
            ).filter(
                and_(
                    DeviceModel.room.floor.has(building_id=building_id.value),
                    DeviceModel.deleted_at.is_(None)
                )
            ).count()
        except Exception as e:
            raise RepositoryError(f"Failed to count devices by building: {str(e)}")

    def _entity_to_model(self, entity: Device) -> DeviceModel:
        """Convert Device entity to DeviceModel."""
        model = DeviceModel(
            id=entity.id.value,
            room_id=entity.room_id.value,
            device_id=entity.device_id,
            name=entity.name,
            device_type=entity.device_type,
            description=entity.description,
            status=entity.status,
            manufacturer=entity.manufacturer,
            model=entity.model,
            serial_number=entity.serial_number,
            created_by=entity.created_by,
            updated_by=entity.updated_by
        )

        # Copy metadata if available
        if hasattr(entity, 'metadata') and entity.metadata:
            model.metadata_json = entity.metadata

        return model

    def _model_to_entity(self, model: DeviceModel) -> Device:
        """Convert DeviceModel to Device entity."""
        from domain.value_objects import RoomId

        device = Device(
            id=DeviceId(model.id),
            room_id=RoomId(model.room_id),
            device_id=model.device_id,
            name=model.name,
            device_type=model.device_type,
            status=model.status,
            description=model.description,
            manufacturer=model.manufacturer,
            model=model.model,
            serial_number=model.serial_number,
            created_by=model.created_by,
            updated_by=model.updated_by
        )

        # Copy metadata if available
        if model.metadata_json:
            device.metadata = model.metadata_json

        return device
