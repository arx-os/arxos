"""
Unified API Dependencies

Provides dependency providers for unified API routes, wiring controllers and
middleware with the application layer and infrastructure.
"""

from typing import Callable
import logging

from api.unified.controllers.building_controller import BuildingController
from api.unified.middleware.auth_middleware import AuthMiddleware

# Placeholders for use cases and services until unified application layer is wired
# These should be replaced with real implementations when available.

logger = logging.getLogger(__name__)


def get_building_controller() -> BuildingController:
    """Provide a BuildingController instance.

    Note: This currently constructs a controller with placeholder use cases.
    Replace with real unified use case instances once they are available.
    """
    try:
        # Lazy import to avoid import errors if modules are not ready
        from application.unified.use_cases.building_controller_use_cases import (
            CreateBuildingUseCase,
            GetBuildingUseCase,
            ListBuildingsUseCase,
            UpdateBuildingUseCase,
            DeleteBuildingUseCase,
        )  # type: ignore

        create_uc = CreateBuildingUseCase()
        get_uc = GetBuildingUseCase()
        list_uc = ListBuildingsUseCase()
        update_uc = UpdateBuildingUseCase()
        delete_uc = DeleteBuildingUseCase()

        return BuildingController(
            create_use_case=create_uc,
            get_use_case=get_uc,
            list_use_case=list_uc,
            update_use_case=update_uc,
            delete_use_case=delete_uc,
        )
    except Exception:
        # Fallback minimal stub to keep router importable without enabling flag
        class _StubUseCase:
            async def create(self, data):
                raise NotImplementedError("Unified use cases not wired")

            async def get_by_id(self, entity_id):
                raise NotImplementedError("Unified use cases not wired")

            async def get_all(self, filters, pagination):
                raise NotImplementedError("Unified use cases not wired")

            async def update(self, entity_id, data):
                raise NotImplementedError("Unified use cases not wired")

            async def delete(self, entity_id):
                raise NotImplementedError("Unified use cases not wired")

        stub = _StubUseCase()
        return BuildingController(
            create_use_case=stub,  # type: ignore[arg-type]
            get_use_case=stub,     # type: ignore[arg-type]
            list_use_case=stub,    # type: ignore[arg-type]
            update_use_case=stub,  # type: ignore[arg-type]
            delete_use_case=stub,  # type: ignore[arg-type]
        )


def get_auth_middleware() -> AuthMiddleware:
    """Provide an AuthMiddleware instance."""
    try:
        from application.unified.services.auth_service import AuthService  # type: ignore

        auth_service = AuthService()
        return AuthMiddleware(auth_service=auth_service)
    except Exception:
        # Minimal stub to avoid import-time errors; real enforcement happens when flag is enabled
        class _StubAuthService:
            async def validate_token(self, token):
                raise NotImplementedError("Unified auth service not wired")

            async def get_user_by_id(self, user_id):
                raise NotImplementedError("Unified auth service not wired")

        return AuthMiddleware(auth_service=_StubAuthService())  # type: ignore[arg-type]
