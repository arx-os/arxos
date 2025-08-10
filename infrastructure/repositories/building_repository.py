"""
Building Repository Implementation

This module contains the SQLAlchemy implementation of the BuildingRepository
interface defined in the domain layer.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import uuid
from sqlalchemy.exc import SQLAlchemyError

from domain.entities import Building
from domain.value_objects import BuildingId, BuildingStatus, Address, Coordinates, Dimensions
from domain.repositories import BuildingRepository
from domain.exceptions import BuildingNotFoundError, DuplicateBuildingError, RepositoryError, DatabaseError

from .base import BaseRepository
from infrastructure.database.models.building import BuildingModel


class SQLAlchemyBuildingRepository(BaseRepository[Building, BuildingModel], BuildingRepository):
    """SQLAlchemy implementation of BuildingRepository."""

    def __init__(self, session: Session):
        """Initialize building repository."""
        super().__init__(session, Building, BuildingModel)

    def save(self, building: Building) -> None:
        """Save a building to the repository."""
        try:
            model = self._entity_to_model(building)
            self.session.add(model)
            self.session.flush()
        except Exception as e:
            raise RepositoryError(f"Failed to save building: {str(e)}")

    def get_by_id(self, building_id: BuildingId) -> Optional[Building]:
        """Get a building by its ID."""
        try:
            # Convert string UUID to UUID object for SQLAlchemy
            uuid_obj = uuid.UUID(building_id.value)

            model = self.session.query(BuildingModel).filter(
                and_(
                    BuildingModel.id == uuid_obj,
                    BuildingModel.deleted_at.is_(None)
                )
            ).first()

            if model is None:
                return None

            return self._model_to_entity(model)
        except Exception as e:
            raise RepositoryError(f"Failed to get building by ID: {str(e)}")

    def get_all(self) -> List[Building]:
        """Get all buildings."""
        try:
            models = self.session.query(BuildingModel).filter(
                BuildingModel.deleted_at.is_(None)
            ).order_by(BuildingModel.name).all()

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to get all buildings: {str(e)}")

    def get_by_status(self, status: BuildingStatus) -> List[Building]:
        """Get buildings by status."""
        try:
            models = self.session.query(BuildingModel).filter(
                and_(
                    BuildingModel.status == status,
                    BuildingModel.deleted_at.is_(None)
                )
            ).order_by(BuildingModel.name).all()

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find buildings by status: {str(e)}")

    def get_by_address(self, address: str) -> List[Building]:
        """Get buildings by address."""
        try:
            models = self.session.query(BuildingModel).filter(
                and_(
                    or_(
                        BuildingModel.address_street.ilike(f"%{address}%"),
                        BuildingModel.address_city.ilike(f"%{address}%"),
                        BuildingModel.address_state.ilike(f"%{address}%"),
                        BuildingModel.address_postal_code.ilike(f"%{address}%")
                    ),
                    BuildingModel.deleted_at.is_(None)
                )
            ).order_by(BuildingModel.name).all()

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find buildings by address: {str(e)}")

    def delete(self, building_id: BuildingId) -> None:
        """Delete a building by ID."""
        try:
            # Convert string UUID to UUID object for SQLAlchemy
            uuid_obj = uuid.UUID(building_id.value)

            model = self.session.query(BuildingModel).filter(
                and_(
                    BuildingModel.id == uuid_obj,
                    BuildingModel.deleted_at.is_(None)
                )
            ).first()

            if model is None:
                raise BuildingNotFoundError(f"Building with ID {building_id} not found")

            model.soft_delete()
            self.session.flush()
        except Exception as e:
            raise RepositoryError(f"Failed to delete building: {str(e)}")

    def exists(self, building_id: BuildingId) -> bool:
        """Check if a building exists."""
        try:
            # Convert string UUID to UUID object for SQLAlchemy
            uuid_obj = uuid.UUID(building_id.value)

            return self.session.query(BuildingModel).filter(
                and_(
                    BuildingModel.id == uuid_obj,
                    BuildingModel.deleted_at.is_(None)
                )
            ).first() is not None
        except Exception as e:
            raise RepositoryError(f"Failed to check building existence: {str(e)}")

    def find_by_name(self, name: str) -> Optional[Building]:
        """Find building by name."""
        try:
            building_model = self.session.query(BuildingModel).filter(
                BuildingModel.name == name
            ).first()

            if building_model:
                return self._model_to_entity(building_model)
            return None

        except SQLAlchemyError as e:
            self.logger.error(f"Database error finding building by name '{name}': {e}")
            raise DatabaseError(f"Failed to find building by name: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error finding building by name '{name}': {e}")
            raise RepositoryError(f"Unexpected error finding building by name: {e}")

    def find_by_status(self, status: str) -> List[Building]:
        """Find buildings by status."""
        try:
            building_models = self.session.query(BuildingModel).filter(
                BuildingModel.status == status
            ).all()

            return [self._model_to_entity(model) for model in building_models]

        except SQLAlchemyError as e:
            self.logger.error(f"Database error finding buildings by status '{status}': {e}")
            raise DatabaseError(f"Failed to find buildings by status: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error finding buildings by status '{status}': {e}")
            raise RepositoryError(f"Unexpected error finding buildings by status: {e}")

    def count(self) -> int:
        """Get total count of buildings."""
        try:
            return self.session.query(BuildingModel).count()
        except SQLAlchemyError as e:
            self.logger.error(f"Database error counting buildings: {e}")
            raise DatabaseError(f"Failed to count buildings: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error counting buildings: {e}")
            raise RepositoryError(f"Unexpected error counting buildings: {e}")

    def count_by_status(self, status: str) -> int:
        """Get count of buildings by status."""
        try:
            return self.session.query(BuildingModel).filter(
                BuildingModel.status == status
            ).count()
        except SQLAlchemyError as e:
            self.logger.error(f"Database error counting buildings by status '{status}': {e}")
            raise DatabaseError(f"Failed to count buildings by status: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error counting buildings by status '{status}': {e}")
            raise RepositoryError(f"Unexpected error counting buildings by status: {e}")

    def find_by_city(self, city: str) -> List[Building]:
        """Find buildings by city."""
        try:
            building_models = self.session.query(BuildingModel).filter(
                BuildingModel.address_city == city
            ).all()

            return [self._model_to_entity(model) for model in building_models]

        except SQLAlchemyError as e:
            self.logger.error(f"Database error finding buildings by city '{city}': {e}")
            raise DatabaseError(f"Failed to find buildings by city: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error finding buildings by city '{city}': {e}")
            raise RepositoryError(f"Unexpected error finding buildings by city: {e}")

    def find_by_building_type(self, building_type: str) -> List[Building]:
        """Find buildings by building type."""
        try:
            building_models = self.session.query(BuildingModel).filter(
                BuildingModel.building_type == building_type
            ).all()

            return [self._model_to_entity(model) for model in building_models]

        except SQLAlchemyError as e:
            self.logger.error(f"Database error finding buildings by type '{building_type}': {e}")
            raise DatabaseError(f"Failed to find buildings by type: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error finding buildings by type '{building_type}': {e}")
            raise RepositoryError(f"Unexpected error finding buildings by type: {e}")

    def search_buildings(self, query: str) -> List[Building]:
        """Search buildings by name, address, or description."""
        try:
            search_term = f"%{query}%"
            building_models = self.session.query(BuildingModel).filter(
                or_(
                    BuildingModel.name.ilike(search_term),
                    BuildingModel.address_street.ilike(search_term),
                    BuildingModel.description.ilike(search_term)
                )
            ).all()

            return [self._model_to_entity(model) for model in building_models]

        except SQLAlchemyError as e:
            self.logger.error(f"Database error searching buildings with query '{query}': {e}")
            raise DatabaseError(f"Failed to search buildings: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error searching buildings with query '{query}': {e}")
            raise RepositoryError(f"Unexpected error searching buildings: {e}")

    def get_building_statistics(self) -> Dict[str, Any]:
        """Get building statistics."""
        try:
            total_buildings = self.session.query(BuildingModel).count()
            active_buildings = self.session.query(BuildingModel).filter(
                BuildingModel.status == "active"
            ).count()
            inactive_buildings = self.session.query(BuildingModel).filter(
                BuildingModel.status == "inactive"
            ).count()

            # Get building types distribution
            type_counts = self.session.query(
                BuildingModel.building_type,
                func.count(BuildingModel.id)
            ).group_by(BuildingModel.building_type).all()

            # Get cities distribution
            city_counts = self.session.query(
                BuildingModel.address_city,
                func.count(BuildingModel.id)
            ).group_by(BuildingModel.address_city).all()

            return {
                "total_buildings": total_buildings,
                "active_buildings": active_buildings,
                "inactive_buildings": inactive_buildings,
                "building_types": dict(type_counts),
                "cities": dict(city_counts)
            }

        except SQLAlchemyError as e:
            self.logger.error(f"Database error getting building statistics: {e}")
            raise DatabaseError(f"Failed to get building statistics: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error getting building statistics: {e}")
            raise RepositoryError(f"Unexpected error getting building statistics: {e}")

    def _entity_to_model(self, entity: Building) -> BuildingModel:
        """Convert Building entity to BuildingModel."""
        model = BuildingModel(
            id=uuid.UUID(entity.id.value),
            name=entity.name,
            address_street=entity.address.street,
            address_city=entity.address.city,
            address_state=entity.address.state,
            address_postal_code=entity.address.postal_code,
            address_country=entity.address.country,
            status=entity.status,
            description=entity.description,
            created_by=entity.created_by,
            updated_by=getattr(entity, 'updated_by', None)
        )

        # Set coordinates if available
        if entity.coordinates:
            model.latitude = entity.coordinates.latitude
            model.longitude = entity.coordinates.longitude

        # Set dimensions if available
        if entity.dimensions:
            model.width = entity.dimensions.width
            model.length = entity.dimensions.length
            model.height = entity.dimensions.height

        # Copy metadata if available
        if hasattr(entity, 'metadata') and entity.metadata:
            model.metadata_json = entity.metadata

        return model

    def _model_to_entity(self, model: BuildingModel) -> Building:
        """Convert BuildingModel to Building entity."""
        from domain.value_objects import Address, Coordinates, Dimensions

        # Create address
        address = Address(
            street=model.address_street,
            city=model.address_city,
            state=model.address_state,
            postal_code=model.address_postal_code,
            country=model.address_country
        )

        # Create coordinates if available
        coordinates = None
        if model.latitude is not None and model.longitude is not None:
            coordinates = Coordinates(
                latitude=model.latitude,
                longitude=model.longitude
            )

        # Create dimensions if available
        dimensions = None
        if model.width is not None and model.length is not None:
            dimensions = Dimensions(
                width=model.width,
                length=model.length,
                height=model.height
            )

        building = Building(
            id=BuildingId.from_string(str(model.id)),
            name=model.name,
            address=address,
            status=model.status,
            coordinates=coordinates,
            dimensions=dimensions,
            description=model.description,
            created_by=model.created_by,
        )

        # Copy metadata if available
        if model.metadata_json:
            building.metadata = model.metadata_json

        return building
