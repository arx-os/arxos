"""
Floor Repository Implementation

This module contains the SQLAlchemy implementation of the FloorRepository
interface defined in the domain layer.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from domain.entities import Floor
from domain.value_objects import FloorId, FloorStatus, BuildingId
from domain.repositories import FloorRepository
from domain.exceptions import RepositoryError

from .base import BaseRepository
from infrastructure.database.models.floor import FloorModel


class SQLAlchemyFloorRepository(BaseRepository[Floor, FloorModel], FloorRepository):
    """SQLAlchemy implementation of FloorRepository."""

    def __init__(self, session: Session):
        """Initialize floor repository."""
        super().__init__(session, Floor, FloorModel)

    def save(self, floor: Floor) -> None:
        """Save a floor to the repository."""
        try:
            model = self._entity_to_model(floor)
            self.session.add(model)
            self.session.flush()
        except Exception as e:
            raise RepositoryError(f"Failed to save floor: {str(e)}")

    def get_by_id(self, floor_id: FloorId) -> Optional[Floor]:
        """Get a floor by its ID."""
        try:
            model = self.session.query(FloorModel).filter(
                and_(
                    FloorModel.id == floor_id.value,
                    FloorModel.deleted_at.is_(None)
                )
            ).first()

            if model is None:
                return None

            return self._model_to_entity(model)
        except Exception as e:
            raise RepositoryError(f"Failed to get floor by ID: {str(e)}")

    def get_by_building_id(self, building_id: BuildingId) -> List[Floor]:
        """Get all floors for a building."""
        try:
            models = self.session.query(FloorModel).filter(
                and_(
                    FloorModel.building_id == building_id.value,
                    FloorModel.deleted_at.is_(None)
                )
            ).order_by(FloorModel.floor_number).all()

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find floors by building ID: {str(e)}")

    def get_by_building_and_number(self, building_id: BuildingId, floor_number: int) -> Optional[Floor]:
        """Get a floor by building ID and floor number."""
        try:
            model = self.session.query(FloorModel).filter(
                and_(
                    FloorModel.building_id == building_id.value,
                    FloorModel.floor_number == floor_number,
                    FloorModel.deleted_at.is_(None)
                )
            ).first()

            if model is None:
                return None

            return self._model_to_entity(model)
        except Exception as e:
            raise RepositoryError(f"Failed to find floor by number: {str(e)}")

    def get_by_status(self, status: FloorStatus) -> List[Floor]:
        """Get floors by status."""
        try:
            models = self.session.query(FloorModel).filter(
                and_(
                    FloorModel.status == status,
                    FloorModel.deleted_at.is_(None)
                )
            ).order_by(FloorModel.floor_number).all()

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find floors by status: {str(e)}")

    def delete(self, floor_id: FloorId) -> None:
        """Delete a floor by ID."""
        try:
            model = self.session.query(FloorModel).filter(
                and_(
                    FloorModel.id == floor_id.value,
                    FloorModel.deleted_at.is_(None)
                )
            ).first()

            if model is None:
                raise RepositoryError(f"Floor with ID {floor_id} not found")

            model.soft_delete()
            self.session.flush()
        except Exception as e:
            raise RepositoryError(f"Failed to delete floor: {str(e)}")

    def exists(self, floor_id: FloorId) -> bool:
        """Check if a floor exists."""
        try:
            return self.session.query(FloorModel).filter(
                and_(
                    FloorModel.id == floor_id.value,
                    FloorModel.deleted_at.is_(None)
                )
            ).first() is not None
        except Exception as e:
            raise RepositoryError(f"Failed to check floor existence: {str(e)}")

    def count_by_building(self, building_id: BuildingId) -> int:
        """Get the number of floors in a building."""
        try:
            return self.session.query(FloorModel).filter(
                and_(
                    FloorModel.building_id == building_id.value,
                    FloorModel.deleted_at.is_(None)
                )
            ).count()
        except Exception as e:
            raise RepositoryError(f"Failed to count floors by building: {str(e)}")

    def find_by_building_id(self, building_id) -> List[Floor]:
        """Find floors by building ID."""
        try:
            models = self.session.query(FloorModel).filter(
                and_(
                    FloorModel.building_id == building_id.value,
                    FloorModel.deleted_at.is_(None)
                )
            ).order_by(FloorModel.floor_number).all()

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find floors by building ID: {str(e)}")

    def find_by_floor_number(self, building_id, floor_number: int) -> Optional[Floor]:
        """Find a floor by building ID and floor number."""
        try:
            model = self.session.query(FloorModel).filter(
                and_(
                    FloorModel.building_id == building_id.value,
                    FloorModel.floor_number == floor_number,
                    FloorModel.deleted_at.is_(None)
                )
            ).first()

            if model is None:
                return None

            return self._model_to_entity(model)
        except Exception as e:
            raise RepositoryError(f"Failed to find floor by number: {str(e)}")

    def _entity_to_model(self, entity: Floor) -> FloorModel:
        """Convert Floor entity to FloorModel."""
        model = FloorModel(
            id=entity.id.value,
            building_id=entity.building_id.value,
            name=entity.name,
            floor_number=entity.floor_number,
            description=entity.description,
            status=entity.status,
            created_by=entity.created_by,
            updated_by=entity.updated_by
        )

        # Copy metadata if available
        if hasattr(entity, 'metadata') and entity.metadata:
            model.metadata_json = entity.metadata

        return model

    def _model_to_entity(self, model: FloorModel) -> Floor:
        """Convert FloorModel to Floor entity."""
        from domain.value_objects import BuildingId

        floor = Floor(
            id=FloorId(model.id),
            building_id=BuildingId(model.building_id),
            name=model.name,
            floor_number=model.floor_number,
            status=model.status,
            description=model.description,
            created_by=model.created_by,
            updated_by=model.updated_by
        )

        # Copy metadata if available
        if model.metadata_json:
            floor.metadata = model.metadata_json

        return floor
