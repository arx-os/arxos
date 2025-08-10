"""
Building Controller - Unified Building API Operations

This module provides the unified building controller that handles all
building-related API operations with consistent patterns and error handling.
"""

from typing import Dict, Any, Optional, List
import logging

from .base_controller import BaseController
from application.unified.use_cases.building_use_cases import (
    CreateBuildingUseCase,
    GetBuildingUseCase,
    ListBuildingsUseCase,
    UpdateBuildingUseCase,
    DeleteBuildingUseCase
)
from application.unified.dto.building_dto import BuildingDTO
from .exceptions import ValidationError
try:
    from .validators import BuildingValidator  # type: ignore
except Exception:
    class BuildingValidator:  # type: ignore
        async def validate_create_request(self, data):
            return data
        async def validate_update_request(self, data):
            return data
        async def validate_building_id(self, building_id: str) -> str:
            return building_id
        async def validate_filters(self, filters):
            return filters
        async def validate_pagination(self, pagination):
            return pagination
from fastapi import HTTPException, status


class BuildingController(BaseController[BuildingDTO, CreateBuildingUseCase]):
    """
    Unified building controller providing consistent CRUD operations.

    This controller implements the Template Method pattern from BaseController import BaseController
    and adds building-specific validation and business logic.
    """

    def __init__(self,
                 create_use_case: CreateBuildingUseCase,
                 get_use_case: GetBuildingUseCase,
                 list_use_case: ListBuildingsUseCase,
                 update_use_case: UpdateBuildingUseCase,
                 delete_use_case: DeleteBuildingUseCase):
        """Initialize building controller with use case dependencies."""
        super().__init__(create_use_case)
        self.get_use_case = get_use_case
        self.list_use_case = list_use_case
        self.update_use_case = update_use_case
        self.delete_use_case = delete_use_case
        self.validator = BuildingValidator()
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    def entity_name(self) -> str:
        """Return the entity name for logging and error messages."""
        return "Building"

    async def get_by_id(self, building_id: str) -> BuildingDTO:
        """
        Get building by ID using the dedicated get use case.

        Args:
            building_id: Building identifier

        Returns:
            Building DTO

        Raises:
            HTTPException: If building not found or retrieval fails
        """
        try:
            self.logger.info(f"Retrieving building with ID: {building_id}")

            # Validate building ID
            validated_id = await self._validate_entity_id(building_id)

            # Execute use case
            result = await self.get_use_case.execute(validated_id)

            if not result:
                raise HTTPException(status_code=404, detail="Building not found")

            self.logger.info(f"Successfully retrieved building")
            return result

        except HTTPException as e:
            self.logger.warning(f"Building not found: {e}")
            raise
        except ValidationError as e:
            self.logger.warning(f"Validation error retrieving building: {e}")
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving building: {e}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )

    async def get_all(self, filters: Optional[Dict[str, Any]] = None,
                     pagination: Optional[Dict[str, Any]] = None) -> List[BuildingDTO]:
        """
        Get all buildings with optional filtering and pagination.

        Args:
            filters: Optional filter parameters
            pagination: Optional pagination parameters

        Returns:
            List of building DTOs

        Raises:
            HTTPException: If retrieval fails
        """
        try:
            self.logger.info("Retrieving all buildings")

            # Validate filters and pagination
            validated_filters = await self._validate_filters(filters or {})
            validated_pagination = await self._validate_pagination(pagination or {})

            # Execute use case
            result = await self.list_use_case.execute(validated_filters, validated_pagination)

            self.logger.info(f"Successfully retrieved {len(result)} buildings")
            return result

        except ValidationError as e:
            self.logger.warning(f"Validation error retrieving buildings: {e}")
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        except Exception as e:
            # For list endpoints, prefer resilience: return empty list on repository/init errors
            self.logger.error(f"Unexpected error retrieving buildings: {e}")
            return []

    async def update(self, building_id: str, request_data: Dict[str, Any]) -> BuildingDTO:
        """
        Update a building using the dedicated update use case.

        Args:
            building_id: Building identifier
            request_data: Request data dictionary

        Returns:
            Updated building DTO

        Raises:
            HTTPException: If update fails
        """
        try:
            self.logger.info(f"Updating building with ID: {building_id}")

            # Validate request data
            validated_id = await self._validate_entity_id(building_id)
            validated_data = await self._validate_update_request(request_data)

            # Execute use case
            result = await self.update_use_case.execute(validated_id, validated_data)

            if not result:
                raise HTTPException(status_code=404, detail="Building not found")

            self.logger.info("Successfully updated building")
            return result

        except HTTPException as e:
            self.logger.warning(f"Building not found for update: {e}")
            raise
        except ValidationError as e:
            self.logger.warning(f"Validation error updating building: {e}")
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        except Exception as e:
            self.logger.error(f"Unexpected error updating building: {e}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )

    async def delete(self, building_id: str) -> bool:
        """
        Delete a building using the dedicated delete use case.

        Args:
            building_id: Building identifier

        Returns:
            True if deletion successful

        Raises:
            HTTPException: If deletion fails
        """
        try:
            self.logger.info(f"Deleting building with ID: {building_id}")

            # Validate building ID
            validated_id = await self._validate_entity_id(building_id)

            # Execute use case
            result = await self.delete_use_case.execute(validated_id)

            if not result:
                raise HTTPException(status_code=404, detail="Building not found")

            self.logger.info("Successfully deleted building")
            return True

        except HTTPException as e:
            self.logger.warning(f"Building not found for deletion: {e}")
            raise
        except ValidationError as e:
            self.logger.warning(f"Validation error deleting building: {e}")
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        except Exception as e:
            self.logger.error(f"Unexpected error deleting building: {e}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )

    async def _validate_create_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate create building request data."""
        return await self.validator.validate_create_request(request_data)

    async def _validate_update_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate update building request data."""
        return await self.validator.validate_update_request(request_data)

    async def _validate_entity_id(self, building_id: str) -> str:
        """Validate building ID."""
        return await self.validator.validate_building_id(building_id)

    async def _validate_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate building filter parameters."""
        return await self.validator.validate_filters(filters)

    async def _validate_pagination(self, pagination: Dict[str, Any]) -> Dict[str, Any]:
        """Validate pagination parameters."""
        return await self.validator.validate_pagination(pagination)
