"""
Unified Repository Adapters

Wrap legacy SQLAlchemy repositories to present domain.unified repository
interfaces. This enables unified use cases/services without duplicating
data access logic.
"""

from __future__ import annotations

from typing import Optional, List

from domain.unified.entities import Building as UnifiedBuilding
from domain.unified.value_objects import (
    BuildingId as UnifiedBuildingId,
    Address as UnifiedAddress,
    Coordinates as UnifiedCoordinates,
    Dimensions as UnifiedDimensions,
    BuildingStatus as UnifiedBuildingStatus,
)
from domain.unified.repositories.building_repository import BuildingRepository as UnifiedBuildingRepository
from domain.unified.value_objects import FloorId as UnifiedFloorId, RoomId as UnifiedRoomId

from typing import Protocol


class FloorRepositoryProtocol(Protocol):
    def save(self, entity): ...
    def get_by_id(self, entity_id: str): ...
    def get_all(self): ...
    def delete(self, entity_id: str) -> bool: ...
    def get_by_building_id(self, building_id: str): ...
    def get_by_floor_number(self, building_id: str, floor_number: int): ...


class RoomRepositoryProtocol(Protocol):
    def save(self, entity): ...
    def get_by_id(self, entity_id: str): ...
    def get_all(self): ...
    def delete(self, entity_id: str) -> bool: ...
    def get_by_floor_id(self, floor_id: str): ...
    def get_by_room_number(self, floor_id: str, room_number: str): ...


class DeviceRepositoryProtocol(Protocol):
    def save(self, entity): ...
    def get_by_id(self, entity_id: str): ...
    def get_all(self): ...
    def delete(self, entity_id: str) -> bool: ...
    def get_by_room_id(self, room_id: str): ...
    def get_by_device_type(self, device_type: str): ...


class FloorRepositoryAdapter:
    """Adapter around legacy Floor repository with a unified-like interface."""

    def __init__(self, legacy_repo: FloorRepositoryProtocol):
        self._legacy = legacy_repo

    def save(self, entity):
        return self._legacy.save(entity)

    def get_by_id(self, entity_id: str):
        return self._legacy.get_by_id(entity_id)

    def get_all(self):
        return self._legacy.get_all()

    def delete(self, entity_id: str) -> bool:
        return self._legacy.delete(entity_id)

    def exists(self, entity_id: str) -> bool:
        return bool(self.get_by_id(entity_id))

    def get_by_building_id(self, building_id: str):
        return self._legacy.get_by_building_id(building_id)

    def get_by_floor_number(self, building_id: str, floor_number: int):
        return self._legacy.get_by_floor_number(building_id, floor_number)


class RoomRepositoryAdapter:
    """Adapter around legacy Room repository with a unified-like interface."""

    def __init__(self, legacy_repo: RoomRepositoryProtocol):
        self._legacy = legacy_repo

    def save(self, entity):
        return self._legacy.save(entity)

    def get_by_id(self, entity_id: str):
        return self._legacy.get_by_id(entity_id)

    def get_all(self):
        return self._legacy.get_all()

    def delete(self, entity_id: str) -> bool:
        return self._legacy.delete(entity_id)

    def exists(self, entity_id: str) -> bool:
        return bool(self.get_by_id(entity_id))

    def get_by_floor_id(self, floor_id: str):
        return self._legacy.get_by_floor_id(floor_id)

    def get_by_room_number(self, floor_id: str, room_number: str):
        return self._legacy.get_by_room_number(floor_id, room_number)


class DeviceRepositoryAdapter:
    """Adapter around legacy Device repository with a unified-like interface."""

    def __init__(self, legacy_repo: DeviceRepositoryProtocol):
        self._legacy = legacy_repo

    def save(self, entity):
        return self._legacy.save(entity)

    def get_by_id(self, entity_id: str):
        return self._legacy.get_by_id(entity_id)

    def get_all(self):
        return self._legacy.get_all()

    def delete(self, entity_id: str) -> bool:
        return self._legacy.delete(entity_id)

    def exists(self, entity_id: str) -> bool:
        return bool(self.get_by_id(entity_id))

    def get_by_room_id(self, room_id: str):
        return self._legacy.get_by_room_id(room_id)

    def get_by_device_type(self, device_type: str):
        return self._legacy.get_by_device_type(device_type)


class BuildingRepositoryAdapter(UnifiedBuildingRepository):
    """Adapter around legacy SQLAlchemyBuildingRepository."""

    def __init__(self, legacy_repo):
        self._legacy = legacy_repo

    def save(self, entity: UnifiedBuilding) -> UnifiedBuilding:
        legacy_entity = self._map_unified_to_legacy(entity)
        self._legacy.save(legacy_entity)
        return entity

    def get_by_id(self, entity_id: str) -> Optional[UnifiedBuilding]:
        from domain.value_objects import BuildingId
        legacy = self._legacy.get_by_id(BuildingId.from_string(entity_id))
        return self._map_legacy_to_unified(legacy) if legacy else None

    def get_all(self) -> List[UnifiedBuilding]:
        legacy_list = self._legacy.get_all()
        return [self._map_legacy_to_unified(e) for e in legacy_list]

    def delete(self, entity_id: str) -> bool:
        from domain.value_objects import BuildingId
        try:
            self._legacy.delete(BuildingId.from_string(entity_id))
            return True
        except Exception:
            return False

    # Optional optimized queries when supported by legacy repo
    def get_by_status(self, status: str) -> List[UnifiedBuilding]:  # type: ignore[override]
        if hasattr(self._legacy, "get_by_status"):
            legacy_list = self._legacy.get_by_status(self._map_unified_status_to_legacy(status))  # type: ignore
            return [self._map_legacy_to_unified(e) for e in legacy_list]
        return self.get_all()

    def find_by_name(self, name: str) -> Optional[UnifiedBuilding]:  # type: ignore[override]
        if hasattr(self._legacy, "find_by_name"):
            legacy = self._legacy.find_by_name(name)  # type: ignore
            return self._map_legacy_to_unified(legacy) if legacy else None
        for b in self.get_all():
            if b.name == name:
                return b
        return None

    # Mapping helpers
    def _map_unified_to_legacy(self, entity: UnifiedBuilding):
        from domain.entities import Building as LegacyBuilding
        from domain.value_objects import Address, Coordinates, Dimensions

        address = Address(
            street=entity.address.street,
            city=entity.address.city,
            state=entity.address.state,
            postal_code=entity.address.postal_code,
            country=entity.address.country,
        )
        coordinates = None
        if entity.coordinates:
            coordinates = Coordinates(
                latitude=entity.coordinates.latitude,
                longitude=entity.coordinates.longitude,
                elevation=entity.coordinates.elevation,
            )
        dimensions = None
        if entity.dimensions:
            dimensions = Dimensions(
                width=entity.dimensions.width,
                length=entity.dimensions.length,
                height=entity.dimensions.height,
            )
        return LegacyBuilding(
            id=self._map_unified_id_to_legacy(entity.id),
            name=entity.name,
            address=address,
            status=self._map_unified_status_to_legacy(entity.status),
            coordinates=coordinates,
            dimensions=dimensions,
            description=entity.description,
            created_by=entity.created_by,
            metadata=entity.metadata,
        )

    # Optionally expose wrapped legacy repo for advanced operations
    @property
    def legacy(self):
        return self._legacy

    def _map_legacy_to_unified(self, legacy) -> UnifiedBuilding:
        address = UnifiedAddress(
            street=legacy.address.street,
            city=legacy.address.city,
            state=legacy.address.state,
            postal_code=legacy.address.postal_code,
            country=legacy.address.country,
        )
        coordinates = None
        if getattr(legacy, "coordinates", None):
            coordinates = UnifiedCoordinates(
                latitude=legacy.coordinates.latitude,
                longitude=legacy.coordinates.longitude,
                elevation=getattr(legacy.coordinates, "elevation", None),
            )
        dimensions = None
        if getattr(legacy, "dimensions", None):
            dimensions = UnifiedDimensions(
                width=legacy.dimensions.width,
                length=legacy.dimensions.length,
                height=getattr(legacy.dimensions, "height", None),
            )
        return UnifiedBuilding(
            id=UnifiedBuildingId(str(legacy.id)),
            name=legacy.name,
            address=address,
            status=self._map_legacy_status_to_unified(legacy.status),
            coordinates=coordinates,
            dimensions=dimensions,
            description=getattr(legacy, "description", None),
            created_by=getattr(legacy, "created_by", None),
            metadata=getattr(legacy, "metadata", {}),
        )

    @staticmethod
    def _map_unified_id_to_legacy(unified_id: UnifiedBuildingId):
        from domain.value_objects import BuildingId
        return BuildingId.from_string(str(unified_id))

    @staticmethod
    def _map_unified_status_to_legacy(status: UnifiedBuildingStatus):
        from domain.value_objects import BuildingStatus
        try:
            return BuildingStatus(status.value)
        except Exception:
            return BuildingStatus.PLANNED

    @staticmethod
    def _map_legacy_status_to_unified(status) -> UnifiedBuildingStatus:
        try:
            return UnifiedBuildingStatus(getattr(status, "value", str(status)))
        except Exception:
            return UnifiedBuildingStatus.PLANNED
