"""
Base Controller - Common Controller Functionality

This module provides the base controller class that implements common
functionality for all unified controllers in the API layer.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Dict, Any, Union
from fastapi import HTTPException, status
from pydantic import BaseModel
import logging

from typing import Any
from .exceptions import ControllerError, ValidationError, NotFoundError

logger = logging.getLogger(__name__)

T = TypeVar('T')
U = TypeVar('U')


class BaseController(ABC, Generic[T, U]):
    """
    Base controller providing common CRUD operations and error handling.

    This class implements the Template Method pattern for consistent
    controller behavior across all entities.
    """

    def __init__(self, use_case: U):
        """Initialize controller with use case dependency."""
        self.use_case = use_case
        self.logger = logging.getLogger(self.__class__.__name__)

    async def create(self, request_data: Dict[str, Any]) -> T:
        """
        Create a new entity.

        Args:
            request_data: Request data dictionary

        Returns:
            Created entity DTO

        Raises:
            HTTPException: If creation fails
        """
        try:
            self.logger.info(f"Creating {self.entity_name}")

            # Validate request data
            validated_data = await self._validate_create_request(request_data)

            # Execute use case
            result = await self.use_case.create(validated_data)

            self.logger.info(f"Successfully created {self.entity_name}")
            return result

        except ValidationError as e:
            self.logger.warning(f"Validation error creating {self.entity_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except ControllerError as e:
            self.logger.error(f"Controller error creating {self.entity_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
        except Exception as e:
            # If repository factory or DB not initialized, surface as 503 to signal retry
            self.logger.error(f"Unexpected error creating {self.entity_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service unavailable"
            )

    async def get_by_id(self, entity_id: str) -> T:
        """
        Get entity by ID.

        Args:
            entity_id: Entity identifier

        Returns:
            Entity DTO

        Raises:
            HTTPException: If entity not found or retrieval fails
        """
        try:
            self.logger.info(f"Retrieving {self.entity_name} with ID: {entity_id}")

            # Validate entity ID
            validated_id = await self._validate_entity_id(entity_id)

            # Execute use case
            result = await self.use_case.get_by_id(validated_id)

            if not result:
                raise NotFoundError(f"{self.entity_name} not found")

            self.logger.info(f"Successfully retrieved {self.entity_name}")
            return result

        except NotFoundError as e:
            self.logger.warning(f"{self.entity_name} not found: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except ValidationError as e:
            self.logger.warning(f"Validation error retrieving {self.entity_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving {self.entity_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def get_all(self, filters: Optional[Dict[str, Any]] = None,
                     pagination: Optional[Dict[str, Any]] = None) -> List[T]:
        """
        Get all entities with optional filtering and pagination.

        Args:
            filters: Optional filter parameters
            pagination: Optional pagination parameters

        Returns:
            List of entity DTOs

        Raises:
            HTTPException: If retrieval fails
        """
        try:
            self.logger.info(f"Retrieving all {self.entity_name}s")

            # Validate filters and pagination
            validated_filters = await self._validate_filters(filters or {})
            validated_pagination = await self._validate_pagination(pagination or {})

            # Execute use case
            result = await self.use_case.get_all(validated_filters, validated_pagination)

            self.logger.info(f"Successfully retrieved {len(result)} {self.entity_name}s")
            return result

        except ValidationError as e:
            self.logger.warning(f"Validation error retrieving {self.entity_name}s: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving {self.entity_name}s: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def update(self, entity_id: str, request_data: Dict[str, Any]) -> T:
        """
        Update an entity.

        Args:
            entity_id: Entity identifier
            request_data: Request data dictionary

        Returns:
            Updated entity DTO

        Raises:
            HTTPException: If update fails
        """
        try:
            self.logger.info(f"Updating {self.entity_name} with ID: {entity_id}")

            # Validate request data
            validated_id = await self._validate_entity_id(entity_id)
            validated_data = await self._validate_update_request(request_data)

            # Execute use case
            result = await self.use_case.update(validated_id, validated_data)

            if not result:
                raise NotFoundError(f"{self.entity_name} not found")

            self.logger.info(f"Successfully updated {self.entity_name}")
            return result

        except NotFoundError as e:
            self.logger.warning(f"{self.entity_name} not found for update: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except ValidationError as e:
            self.logger.warning(f"Validation error updating {self.entity_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            self.logger.error(f"Unexpected error updating {self.entity_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def delete(self, entity_id: str) -> bool:
        """
        Delete an entity.

        Args:
            entity_id: Entity identifier

        Returns:
            True if deletion successful

        Raises:
            HTTPException: If deletion fails
        """
        try:
            self.logger.info(f"Deleting {self.entity_name} with ID: {entity_id}")

            # Validate entity ID
            validated_id = await self._validate_entity_id(entity_id)

            # Execute use case
            result = await self.use_case.delete(validated_id)

            if not result:
                raise NotFoundError(f"{self.entity_name} not found")

            self.logger.info(f"Successfully deleted {self.entity_name}")
            return True

        except NotFoundError as e:
            self.logger.warning(f"{self.entity_name} not found for deletion: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except ValidationError as e:
            self.logger.warning(f"Validation error deleting {self.entity_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            self.logger.error(f"Unexpected error deleting {self.entity_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    @property
    @abstractmethod
    def entity_name(self) -> str:
        """Return the entity name for logging and error messages."""
        pass

    @abstractmethod
    async def _validate_create_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate create request data."""
        pass

    @abstractmethod
    async def _validate_update_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate update request data."""
        pass

    @abstractmethod
    async def _validate_entity_id(self, entity_id: str) -> str:
        """Validate entity ID."""
        pass

    @abstractmethod
    async def _validate_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate filter parameters."""
        pass

    @abstractmethod
    async def _validate_pagination(self, pagination: Dict[str, Any]) -> Dict[str, Any]:
        """Validate pagination parameters."""
        pass
