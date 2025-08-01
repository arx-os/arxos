"""
Building Repository Implementation

This module contains the SQLAlchemy implementation of the BuildingRepository
interface defined in the domain layer.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from domain.entities import Building
from domain.value_objects import BuildingId, BuildingStatus, Address, Coordinates, Dimensions
from domain.repositories import BuildingRepository
from domain.exceptions import BuildingNotFoundError, DuplicateBuildingError, RepositoryError

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
            model = self.session.query(BuildingModel).filter(
                and_(
                    BuildingModel.id == building_id.value,
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
            model = self.session.query(BuildingModel).filter(
                and_(
                    BuildingModel.id == building_id.value,
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
            return self.session.query(BuildingModel).filter(
                and_(
                    BuildingModel.id == building_id.value,
                    BuildingModel.deleted_at.is_(None)
                )
            ).first() is not None
        except Exception as e:
            raise RepositoryError(f"Failed to check building existence: {str(e)}")
    
    def count(self) -> int:
        """Get the total number of buildings."""
        try:
            return self.session.query(BuildingModel).filter(
                BuildingModel.deleted_at.is_(None)
            ).count()
        except Exception as e:
            raise RepositoryError(f"Failed to count buildings: {str(e)}")
    
    def get_with_floors(self, building_id: BuildingId) -> Optional[Building]:
        """Get a building with all its floors."""
        try:
            model = self.session.query(BuildingModel).filter(
                and_(
                    BuildingModel.id == building_id.value,
                    BuildingModel.deleted_at.is_(None)
                )
            ).first()
            
            if model is None:
                return None
            
            # Load floors relationship
            building = self._model_to_entity(model)
            # Note: This would need to be implemented based on the actual relationship structure
            # For now, we return the building without floors
            return building
        except Exception as e:
            raise RepositoryError(f"Failed to get building with floors: {str(e)}")
    
    def find_by_name(self, name: str) -> Optional[Building]:
        """Find a building by name."""
        try:
            model = self.session.query(BuildingModel).filter(
                and_(
                    BuildingModel.name == name,
                    BuildingModel.deleted_at.is_(None)
                )
            ).first()
            
            if model is None:
                return None
                
            return self._model_to_entity(model)
        except Exception as e:
            raise RepositoryError(f"Failed to find building by name: {str(e)}")
    
    def find_by_address(self, address: Address) -> List[Building]:
        """Find buildings by address."""
        try:
            models = self.session.query(BuildingModel).filter(
                and_(
                    BuildingModel.address_street == address.street,
                    BuildingModel.address_city == address.city,
                    BuildingModel.address_state == address.state,
                    BuildingModel.address_postal_code == address.postal_code,
                    BuildingModel.deleted_at.is_(None)
                )
            ).all()
            
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find buildings by address: {str(e)}")
    
    def search_buildings(self, search_term: str) -> List[Building]:
        """Search buildings by name or description."""
        try:
            search_pattern = f"%{search_term}%"
            models = self.session.query(BuildingModel).filter(
                and_(
                    or_(
                        BuildingModel.name.ilike(search_pattern),
                        BuildingModel.description.ilike(search_pattern)
                    ),
                    BuildingModel.deleted_at.is_(None)
                )
            ).all()
            
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to search buildings: {str(e)}")
    
    def get_building_statistics(self) -> dict:
        """Get building statistics."""
        try:
            total_buildings = self.session.query(BuildingModel).filter(
                BuildingModel.deleted_at.is_(None)
            ).count()
            
            # Count by status
            status_counts = {}
            for status in BuildingStatus:
                count = self.session.query(BuildingModel).filter(
                    and_(
                        BuildingModel.status == status,
                        BuildingModel.deleted_at.is_(None)
                    )
                ).count()
                status_counts[status.value] = count
            
            return {
                'total_buildings': total_buildings,
                'status_counts': status_counts
            }
        except Exception as e:
            raise RepositoryError(f"Failed to get building statistics: {str(e)}")
    
    def _entity_to_model(self, entity: Building) -> BuildingModel:
        """Convert Building entity to BuildingModel."""
        model = BuildingModel(
            id=entity.id.value,
            name=entity.name,
            address_street=entity.address.street,
            address_city=entity.address.city,
            address_state=entity.address.state,
            address_postal_code=entity.address.postal_code,
            address_country=entity.address.country,
            status=entity.status,
            description=entity.description,
            created_by=entity.created_by,
            updated_by=entity.updated_by
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
            id=BuildingId(model.id),
            name=model.name,
            address=address,
            status=model.status,
            coordinates=coordinates,
            dimensions=dimensions,
            description=model.description,
            created_by=model.created_by,
            updated_by=model.updated_by
        )
        
        # Copy metadata if available
        if model.metadata_json:
            building.metadata = model.metadata_json
        
        return building 