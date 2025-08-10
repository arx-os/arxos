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


def get_unified_repository_factory():
    """Provide a unified repository factory with adapters."""
    from infrastructure.repository_factory import get_repository_factory
    from infrastructure.unified.repositories.adapters import (
        BuildingRepositoryAdapter,
        FloorRepositoryAdapter,
        RoomRepositoryAdapter,
        DeviceRepositoryAdapter,
    )

    factory = get_repository_factory()

    def _create_unified_repositories():
        with factory.create_unit_of_work() as uow:
            # Wrap the legacy repos with unified adapters
            adapted_buildings = BuildingRepositoryAdapter(uow.buildings)
            adapted_floors = FloorRepositoryAdapter(uow.floors)
            adapted_rooms = RoomRepositoryAdapter(uow.rooms)
            adapted_devices = DeviceRepositoryAdapter(uow.devices)
            return {
                'buildings': adapted_buildings,
                'floors': adapted_floors,
                'rooms': adapted_rooms,
                'devices': adapted_devices,
                'projects': uow.projects,
            }

    return _create_unified_repositories


def get_building_controller() -> BuildingController:
    """Provide a BuildingController instance.

    Note: This currently constructs a controller with placeholder use cases.
    Replace with real unified use case instances once they are available.
    """
    try:
        # Lazy import to avoid import errors if modules are not ready
        # Prefer unified use cases if available; fall back to async unified impl wiring to legacy repos
        try:
            from application.unified.use_cases.building_use_case import UnifiedBuildingUseCase  # type: ignore

            def _unified_uc():
                unified_factory = get_unified_repository_factory()
                repos = unified_factory()
                return UnifiedBuildingUseCase(
                    building_repository=repos['buildings'],
                    floor_repository=repos['floors'],
                    room_repository=repos['rooms'],
                    device_repository=repos['devices'],
                    project_repository=repos['projects'],
                )

            class _CreateUC:
                async def create(self, data):
                    uc = _unified_uc()
                    # Map and create via unified use case (no floors by default)
                    from domain.unified.value_objects import Address, Dimensions, BuildingStatus
                    addr = data.get("address") or {}
                    address = Address(
                        street=addr.get("street", ""),
                        city=addr.get("city", ""),
                        state=addr.get("state", ""),
                        postal_code=addr.get("postal_code", ""),
                        country=addr.get("country", "USA"),
                    )
                    dims = data.get("dimensions") or None
                    dimensions = None
                    if dims:
                        dimensions = Dimensions(
                            width=float(dims.get("width", dims.get("length", 0.0))),
                            length=float(dims.get("length", dims.get("width", 0.0))),
                            height=dims.get("height"),
                        )
                    status = str(data.get("status", "planned")).lower()
                    try:
                        status_vo = BuildingStatus(status)
                    except Exception:
                        status_vo = BuildingStatus.PLANNED
                    entity = uc.create_building_with_floors(
                        name=data.get("name", ""),
                        address=address,
                        floor_data=[],
                        status=status_vo,
                        dimensions=dimensions,
                        description=data.get("description"),
                        created_by=data.get("created_by"),
                        metadata=data.get("metadata", {}),
                    )
                    from application.unified.use_cases.building_use_cases import _dto_from_entity
                    return _dto_from_entity(entity)

            class _GetUC:
                async def execute(self, building_id: str):
                    # Use the dedicated GetBuildingUseCase for getting just the building
                    from application.unified.use_cases.building_use_cases import GetBuildingUseCase
                    uc = GetBuildingUseCase()
                    return await uc.execute(building_id)

            class _ListUC:
                async def execute(self, filters, pagination):
                    from application.unified.use_cases.building_use_cases import ListBuildingsUseCase as _LB
                    tmp = _LB()
                    return await tmp.execute(filters, pagination)
                async def count(self, filters):
                    from application.unified.use_cases.building_use_cases import ListBuildingsUseCase as _LB
                    tmp = _LB()
                    return await tmp.count(filters)

            class _UpdateUC:
                async def execute(self, building_id: str, data):
                    from application.unified.use_cases.building_use_cases import UpdateBuildingUseCase as _UB
                    tmp = _UB()
                    return await tmp.execute(building_id, data)

            class _DeleteUC:
                async def execute(self, building_id: str) -> bool:
                    from application.unified.use_cases.building_use_cases import DeleteBuildingUseCase as _DB
                    tmp = _DB()
                    return await tmp.execute(building_id)

            create_uc = _CreateUC()
            get_uc = _GetUC()
            list_uc = _ListUC()
            update_uc = _UpdateUC()
            delete_uc = _DeleteUC()

        except Exception:
            from application.unified.use_cases.building_use_cases import (
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

        # Attach list use case for providers that need it
        _providers_state["building_list_uc"] = list_uc

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


# Simple internal state to share singletons between providers
_providers_state: dict = {}


def get_building_list_use_case():
    """Provide the ListBuildingsUseCase used by the controller."""
    try:
        uc = _providers_state.get("building_list_uc")
        if uc is not None:
            return uc
        from application.unified.use_cases.building_use_cases import ListBuildingsUseCase  # type: ignore
        uc = ListBuildingsUseCase()
        _providers_state["building_list_uc"] = uc
        return uc
    except Exception:
        class _StubListUC:
            async def execute(self, filters, pagination):
                return []
            async def count(self, filters):
                return 0
        return _StubListUC()


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


def get_unified_building_use_case():
    """Provide a fully wired UnifiedBuildingUseCase with adapters."""
    try:
        from infrastructure.repository_factory import get_repository_factory  # type: ignore
        from infrastructure.unified.repositories.adapters import (
            BuildingRepositoryAdapter,
            FloorRepositoryAdapter,
            RoomRepositoryAdapter,
            DeviceRepositoryAdapter,
        )  # type: ignore
        from application.unified.use_cases.building_use_case import UnifiedBuildingUseCase  # type: ignore

        factory = get_repository_factory()
        # Use repository factory methods to obtain session-backed repos
        legacy_buildings = factory.create_building_repository()
        legacy_floors = factory.create_floor_repository()
        legacy_rooms = factory.create_room_repository()
        legacy_devices = factory.create_device_repository()

        adapted_buildings = BuildingRepositoryAdapter(legacy_buildings)
        adapted_floors = FloorRepositoryAdapter(legacy_floors)
        adapted_rooms = RoomRepositoryAdapter(legacy_rooms)
        adapted_devices = DeviceRepositoryAdapter(legacy_devices)
        return UnifiedBuildingUseCase(
            building_repository=adapted_buildings,
            floor_repository=adapted_floors,
            room_repository=adapted_rooms,
            device_repository=adapted_devices,
            project_repository=factory.create_project_repository(),
        )
    except Exception:
        # Minimal stub to keep router importable
        class _StubUC:
            def get_building_hierarchy(self, building_id: str):
                return {"building": {}, "floors": []}
        return _StubUC()
