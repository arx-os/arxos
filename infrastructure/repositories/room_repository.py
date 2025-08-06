"""
Room Repository Implementation

This module contains the SQLAlchemy implementation of the RoomRepository
interface defined in the domain layer.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from domain.entities import Room
from domain.value_objects import RoomId, RoomStatus, FloorId, BuildingId
from domain.repositories import RoomRepository
from domain.exceptions import RepositoryError

from .base import BaseRepository
from infrastructure.database.models.room import RoomModel


class SQLAlchemyRoomRepository(BaseRepository[Room, RoomModel], RoomRepository):
    """SQLAlchemy implementation of RoomRepository."""

    def __init__(self, session: Session):
        """Initialize room repository."""
        super().__init__(session, Room, RoomModel)

    def save(self, room: Room) -> None:
        """Save a room to the repository."""
        try:
            model = self._entity_to_model(room)
            self.session.add(model)
            self.session.flush()
        except Exception as e:
            raise RepositoryError(f"Failed to save room: {str(e)}")

    def get_by_id(self, room_id: RoomId) -> Optional[Room]:
        """Get a room by its ID."""
        try:
            model = (
                self.session.query(RoomModel)
                .filter(
                    and_(RoomModel.id == room_id.value, RoomModel.deleted_at.is_(None))
                )
                .first()
            )

            if model is None:
                return None

            return self._model_to_entity(model)
        except Exception as e:
            raise RepositoryError(f"Failed to get room by ID: {str(e)}")

    def get_by_floor_id(self, floor_id: FloorId) -> List[Room]:
        """Get all rooms for a floor."""
        try:
            models = (
                self.session.query(RoomModel)
                .filter(
                    and_(
                        RoomModel.floor_id == floor_id.value,
                        RoomModel.deleted_at.is_(None),
                    )
                )
                .order_by(RoomModel.room_number)
                .all()
            )

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find rooms by floor ID: {str(e)}")

    def get_by_building_id(self, building_id: BuildingId) -> List[Room]:
        """Get all rooms for a building."""
        try:
            # Join with floors to get rooms by building
            models = (
                self.session.query(RoomModel)
                .join(RoomModel.floor)
                .filter(
                    and_(
                        RoomModel.floor.has(building_id=building_id.value),
                        RoomModel.deleted_at.is_(None),
                    )
                )
                .order_by(RoomModel.room_number)
                .all()
            )

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find rooms by building ID: {str(e)}")

    def get_by_floor_and_number(
        self, floor_id: FloorId, room_number: str
    ) -> Optional[Room]:
        """Get a room by floor ID and room number."""
        try:
            model = (
                self.session.query(RoomModel)
                .filter(
                    and_(
                        RoomModel.floor_id == floor_id.value,
                        RoomModel.room_number == room_number,
                        RoomModel.deleted_at.is_(None),
                    )
                )
                .first()
            )

            if model is None:
                return None

            return self._model_to_entity(model)
        except Exception as e:
            raise RepositoryError(f"Failed to find room by number: {str(e)}")

    def get_by_status(self, status: RoomStatus) -> List[Room]:
        """Get rooms by status."""
        try:
            models = (
                self.session.query(RoomModel)
                .filter(
                    and_(RoomModel.status == status, RoomModel.deleted_at.is_(None))
                )
                .order_by(RoomModel.room_number)
                .all()
            )

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find rooms by status: {str(e)}")

    def delete(self, room_id: RoomId) -> None:
        """Delete a room by ID."""
        try:
            model = (
                self.session.query(RoomModel)
                .filter(
                    and_(RoomModel.id == room_id.value, RoomModel.deleted_at.is_(None))
                )
                .first()
            )

            if model is None:
                raise RepositoryError(f"Room with ID {room_id} not found")

            model.soft_delete()
            self.session.flush()
        except Exception as e:
            raise RepositoryError(f"Failed to delete room: {str(e)}")

    def exists(self, room_id: RoomId) -> bool:
        """Check if a room exists."""
        try:
            return (
                self.session.query(RoomModel)
                .filter(
                    and_(RoomModel.id == room_id.value, RoomModel.deleted_at.is_(None))
                )
                .first()
                is not None
            )
        except Exception as e:
            raise RepositoryError(f"Failed to check room existence: {str(e)}")

    def count_by_floor(self, floor_id: FloorId) -> int:
        """Get the number of rooms on a floor."""
        try:
            return (
                self.session.query(RoomModel)
                .filter(
                    and_(
                        RoomModel.floor_id == floor_id.value,
                        RoomModel.deleted_at.is_(None),
                    )
                )
                .count()
            )
        except Exception as e:
            raise RepositoryError(f"Failed to count rooms by floor: {str(e)}")

    def count_by_building(self, building_id: BuildingId) -> int:
        """Get the number of rooms in a building."""
        try:
            return (
                self.session.query(RoomModel)
                .join(RoomModel.floor)
                .filter(
                    and_(
                        RoomModel.floor.has(building_id=building_id.value),
                        RoomModel.deleted_at.is_(None),
                    )
                )
                .count()
            )
        except Exception as e:
            raise RepositoryError(f"Failed to count rooms by building: {str(e)}")

    def find_by_floor_id(self, floor_id) -> List[Room]:
        """Find rooms by floor ID."""
        try:
            models = (
                self.session.query(RoomModel)
                .filter(
                    and_(
                        RoomModel.floor_id == floor_id.value,
                        RoomModel.deleted_at.is_(None),
                    )
                )
                .order_by(RoomModel.room_number)
                .all()
            )

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find rooms by floor ID: {str(e)}")

    def _entity_to_model(self, entity: Room) -> RoomModel:
        """Convert Room entity to RoomModel."""
        model = RoomModel(
            id=entity.id.value,
            floor_id=entity.floor_id.value,
            name=entity.name,
            room_number=entity.room_number,
            room_type=entity.room_type,
            description=entity.description,
            status=entity.status,
            width=entity.dimensions.width if entity.dimensions else None,
            length=entity.dimensions.length if entity.dimensions else None,
            height=entity.dimensions.height if entity.dimensions else None,
            dimensions_unit=entity.dimensions.unit if entity.dimensions else "meters",
            created_by=entity.created_by,
            updated_by=entity.updated_by,
        )

        # Copy metadata if available
        if hasattr(entity, "metadata") and entity.metadata:
            model.metadata_json = entity.metadata

        return model

    def _model_to_entity(self, model: RoomModel) -> Room:
        """Convert RoomModel to Room entity."""
        from domain.value_objects import FloorId, Dimensions

        # Create dimensions if available
        dimensions = None
        if model.width is not None and model.length is not None:
            dimensions = Dimensions(
                width=model.width,
                length=model.length,
                height=model.height,
                unit=model.dimensions_unit or "meters",
            )

        room = Room(
            id=RoomId(model.id),
            floor_id=FloorId(model.floor_id),
            name=model.name,
            room_number=model.room_number,
            room_type=model.room_type,
            status=model.status,
            description=model.description,
            dimensions=dimensions,
            created_by=model.created_by,
            updated_by=model.updated_by,
        )

        # Copy metadata if available
        if model.metadata_json:
            room.metadata = model.metadata_json

        return room
