"""
Unified Building Use Cases (async)

Async use cases consumed by unified controllers. These wrap repository
operations via the SQLAlchemy UnitOfWork and return DTOs.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime

from application.unified.dto.building_dto import BuildingDTO, AddressDTO, CoordinatesDTO, DimensionsDTO
from infrastructure.repository_factory import get_repository_factory, initialize_repository_factory
# Use legacy value objects for repository compatibility
from domain.value_objects import BuildingId, Address, Coordinates, Dimensions, BuildingStatus


def _now() -> datetime:
    return datetime.utcnow()


def _ensure_factory():
    """Get a repository factory, initializing from application container if needed."""
    try:
        return get_repository_factory()
    except Exception:
        try:
            from application.config import get_config
            from application.container import container  # local import to avoid cycles
            # Initialize container if not already; it's idempotent
            container.initialize(get_config())
            db_session = container.get_database_session()
            initialize_repository_factory(db_session.session_factory)
            return get_repository_factory()
        except Exception as e:
            raise


def _dto_from_entity(entity) -> BuildingDTO:
    address_dto = AddressDTO(
        street=entity.address.street,
        city=entity.address.city,
        state=entity.address.state,
        postal_code=entity.address.postal_code,
        country=entity.address.country,
    ) if getattr(entity, "address", None) else None

    coordinates_dto = CoordinatesDTO(
        latitude=entity.coordinates.latitude,
        longitude=entity.coordinates.longitude,
        elevation=getattr(entity.coordinates, "elevation", None),
    ) if getattr(entity, "coordinates", None) else None

    dimensions_dto = DimensionsDTO(
        length=getattr(entity.dimensions, "length", None) or getattr(entity.dimensions, "width", None) or 0.0,
        width=getattr(entity.dimensions, "width", None) or getattr(entity.dimensions, "length", None) or 0.0,
        height=getattr(entity.dimensions, "height", None) or 0.0,
        area=getattr(entity, "area", None),
        volume=getattr(entity, "volume", None),
    ) if getattr(entity, "dimensions", None) else None

    # Map domain status values to unified API enum values
    raw_status = getattr(entity.status, "value", str(entity.status))
    status_map = {
        "planned": "active",
        "under_construction": "construction",
        "completed": "active",
        "operational": "active",
        "maintenance": "maintenance",
        "decommissioned": "inactive",
    }
    unified_status = status_map.get(str(raw_status).lower(), "active")

    return BuildingDTO(
        id=str(entity.id),
        name=entity.name,
        building_type=getattr(entity, "building_type", "other"),
        status=unified_status,
        address=address_dto,
        coordinates=coordinates_dto,
        dimensions=dimensions_dto,
        description=getattr(entity, "description", None),
        year_built=getattr(entity, "year_built", None),
        total_floors=getattr(entity, "total_floors", None),
        owner_id=getattr(entity, "owner_id", None),
        tags=getattr(entity, "tags", None),
        metadata=getattr(entity, "metadata", None),
        created_at=getattr(entity, "created_at", None),
        updated_at=getattr(entity, "updated_at", None),
    )


class CreateBuildingUseCase:
    async def create(self, data: Dict[str, Any]) -> BuildingDTO:
        factory = _ensure_factory()
        uow = factory.create_unit_of_work()
        with uow:
            # Build domain entity
            addr = data.get("address", {})
            address_vo = Address(
                street=addr.get("street", ""),
                city=addr.get("city", ""),
                state=addr.get("state", ""),
                postal_code=addr.get("postal_code", ""),
                country=addr.get("country", "USA"),
            )
            coords = data.get("coordinates") or None
            coordinates_vo = Coordinates(**coords) if coords else None
            dims = data.get("dimensions") or None
            # Dimensions in domain are (width, length, height)
            dimensions_vo = None
            if dims:
                dimensions_vo = Dimensions(
                    width=float(dims.get("width", dims.get("length", 0.0))),
                    length=float(dims.get("length", dims.get("width", 0.0))),
                    height=dims.get("height"),
                )

            # Create entity
            # Persist using legacy entity for maximum repository compatibility
            from domain.entities import Building  # type: ignore
            status_value = data.get("status", "planned").lower()
            try:
                status_vo = BuildingStatus(status_value)
            except Exception:
                status_vo = BuildingStatus.PLANNED

            entity = Building(
                id=BuildingId(),
                name=data.get("name", ""),
                address=address_vo,
                status=status_vo,
                coordinates=coordinates_vo,
                dimensions=dimensions_vo,
                description=data.get("description"),
                created_by=data.get("created_by"),
                metadata=data.get("metadata", {}) or {},
            )

            # Persist
            uow.buildings.save(entity)
            # Return DTO
            return _dto_from_entity(entity)


class GetBuildingUseCase:
    async def execute(self, building_id: str) -> Optional[BuildingDTO]:
        print(f"DEBUG: GetBuildingUseCase.execute called with building_id: '{building_id}' (type: {type(building_id)})")
        if not building_id or not str(building_id).strip():
            print(f"DEBUG: building_id is empty or whitespace: '{building_id}'")
            raise ValueError(f"Building ID cannot be empty: '{building_id}'")

        factory = _ensure_factory()
        uow = factory.create_unit_of_work()
        with uow:
            print(f"DEBUG: About to create BuildingId with: '{building_id}'")
            building_id_vo = BuildingId.from_string(building_id)
            print(f"DEBUG: BuildingId created successfully: {building_id_vo}")
            entity = uow.buildings.get_by_id(building_id_vo)
            return _dto_from_entity(entity) if entity else None


class ListBuildingsUseCase:
    async def execute(self, filters: Dict[str, Any], pagination: Dict[str, Any]) -> List[BuildingDTO]:
        factory = _ensure_factory()
        uow = factory.create_unit_of_work()
        with uow:
            entities = uow.buildings.get_all()
            # Basic filtering (status, name contains, city)
            status = (filters.get("status") or "").lower()
            name = (filters.get("name") or "").lower()
            city = (filters.get("city") or "").lower()

            def _match(e) -> bool:
                ok = True
                if status:
                    try:
                        ok = ok and getattr(e.status, "value", str(e.status)).lower() == status
                    except Exception:
                        ok = False
                if name:
                    ok = ok and name in e.name.lower()
                if city:
                    ok = ok and e.address and city in e.address.city.lower()
                return ok

            filtered = [e for e in entities if _match(e)]

            page = int(pagination.get("page", 1))
            page_size = int(pagination.get("page_size", 10))
            start = (page - 1) * page_size
            end = start + page_size
            return [_dto_from_entity(e) for e in filtered[start:end]]

    async def count(self, filters: Dict[str, Any]) -> int:
        factory = _ensure_factory()
        uow = factory.create_unit_of_work()
        with uow:
            entities = uow.buildings.get_all()
            status = (filters.get("status") or "").lower()
            name = (filters.get("name") or "").lower()
            city = (filters.get("city") or "").lower()

            def _match(e) -> bool:
                ok = True
                if status:
                    try:
                        ok = ok and getattr(e.status, "value", str(e.status)).lower() == status
                    except Exception:
                        ok = False
                if name:
                    ok = ok and name in e.name.lower()
                if city:
                    ok = ok and e.address and city in e.address.city.lower()
                return ok

            return sum(1 for e in entities if _match(e))


class UpdateBuildingUseCase:
    async def execute(self, building_id: str, data: Dict[str, Any]) -> Optional[BuildingDTO]:
        factory = get_repository_factory()
        uow = factory.create_unit_of_work()
        with uow:
            entity = uow.buildings.get_by_id(BuildingId.from_string(building_id))
            if not entity:
                return None
            # Apply updates
            if "name" in data and data["name"] is not None:
                entity.update_name(str(data["name"]), updated_by=str(data.get("updated_by", "system")))
            if "status" in data and data["status"] is not None:
                try:
                    new_status = BuildingStatus(str(data["status"]).lower())
                    entity.update_status(new_status, updated_by=str(data.get("updated_by", "system")))
                except Exception:
                    pass
            if "dimensions" in data and data["dimensions"]:
                dims = data["dimensions"]
                dims_vo = Dimensions(
                    width=float(dims.get("width", dims.get("length", 0.0))),
                    length=float(dims.get("length", dims.get("width", 0.0))),
                    height=dims.get("height"),
                )
                entity.update_dimensions(dims_vo, updated_by=str(data.get("updated_by", "system")))

            # Direct field updates for description/metadata
            if "description" in data and data["description"] is not None:
                entity.description = data["description"]
                entity.updated_at = _now()
            if "metadata" in data and data["metadata"] is not None:
                entity.metadata = data["metadata"]
                entity.updated_at = _now()

            # Persist
            uow.buildings.save(entity)
            return _dto_from_entity(entity)


class DeleteBuildingUseCase:
    async def execute(self, building_id: str) -> bool:
        factory = get_repository_factory()
        uow = factory.create_unit_of_work()
        with uow:
            try:
                uow.buildings.delete(BuildingId.from_string(building_id))
                return True
            except Exception:
                return False
