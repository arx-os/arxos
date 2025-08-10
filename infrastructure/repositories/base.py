"""
Base Repository Implementation

This module contains the base repository class that provides common
functionality for all repository implementations.
"""

from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from abc import ABC, abstractmethod
import logging

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from domain.exceptions import RepositoryError

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Domain entity type
M = TypeVar('M')  # Model type


class BaseRepository(ABC, Generic[T, M]):
    """Base repository with common CRUD operations."""

    def __init__(self, session: Session, entity_class: Type[T], model_class: Type[M]):
        """Initialize repository with session and classes."""
        self.session = session
        self.entity_class = entity_class
        self.model_class = model_class

    def save(self, entity: T) -> T:
        """Save an entity to the database."""
        try:
            model = self._entity_to_model(entity)
            self.session.add(model)
            self.session.flush()  # Flush to get the ID
            return self._model_to_entity(model)
        except SQLAlchemyError as e:
            logger.error(f"Error saving {self.entity_class.__name__}: {e}")
            self.session.rollback()
            raise RepositoryError(f"Failed to save {self.entity_class.__name__}: {str(e)}")

    def get_by_id(self, entity_id) -> Optional[T]:
        """Get an entity by its ID."""
        try:
            model = self.session.query(self.model_class).filter(
                self.model_class.id == entity_id,
                self.model_class.deleted_at.is_(None)
            ).first()

            if model is None:
                return None

            return self._model_to_entity(model)
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving {self.entity_class.__name__} by ID: {e}")
            raise RepositoryError(f"Failed to retrieve {self.entity_class.__name__}: {str(e)}")

    def get_by_id_or_raise(self, entity_id) -> T:
        """Get an entity by its ID or raise an exception if not found."""
        entity = self.get_by_id(entity_id)
        if entity is None:
            raise RepositoryError(f"{self.entity_class.__name__} with ID {entity_id} not found")
        return entity

    def find_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """Find all entities with optional pagination."""
        try:
            query = self.session.query(self.model_class).filter(
                self.model_class.deleted_at.is_(None)
            )
            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            models = query.all()
            return [self._model_to_entity(model) for model in models]
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving all {self.entity_class.__name__}s: {e}")
            raise RepositoryError(f"Failed to retrieve {self.entity_class.__name__}s: {str(e)}")

    def count(self) -> int:
        """Count all non-deleted entities."""
        try:
            return self.session.query(self.model_class).filter(
                self.model_class.deleted_at.is_(None)
            ).count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.entity_class.__name__}s: {e}")
            raise RepositoryError(f"Failed to count {self.entity_class.__name__}s: {str(e)}")

    def delete(self, entity_id) -> bool:
        """Soft delete an entity by its ID."""
        try:
            model = self.session.query(self.model_class).filter(
                self.model_class.id == entity_id,
                self.model_class.deleted_at.is_(None)
            ).first()

            if model is None:
                return False

            model.soft_delete()
            self.session.flush()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting {self.entity_class.__name__}: {e}")
            self.session.rollback()
            raise RepositoryError(f"Failed to delete {self.entity_class.__name__}: {str(e)}")

    def hard_delete(self, entity_id) -> bool:
        """Hard delete an entity by its ID."""
        try:
            model = self.session.query(self.model_class).filter(
                self.model_class.id == entity_id
            ).first()

            if model is None:
                return False

            self.session.delete(model)
            self.session.flush()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error hard deleting {self.entity_class.__name__}: {e}")
            self.session.rollback()
            raise RepositoryError(f"Failed to hard delete {self.entity_class.__name__}: {str(e)}")

    def exists(self, entity_id) -> bool:
        """Check if an entity exists by its ID."""
        try:
            return self.session.query(self.model_class).filter(
                self.model_class.id == entity_id,
                self.model_class.deleted_at.is_(None)
            ).first() is not None
        except SQLAlchemyError as e:
            logger.error(f"Error checking existence of {self.entity_class.__name__}: {e}")
            raise RepositoryError(f"Failed to check existence of {self.entity_class.__name__}: {str(e)}")

    @abstractmethod
    def _entity_to_model(self, entity: T) -> M:
        """Convert domain entity to database model."""
        pass

    @abstractmethod
    def _model_to_entity(self, model: M) -> T:
        """Convert database model to domain entity."""
        pass
