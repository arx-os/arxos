from __future__ import annotations

from typing import Dict, Any

from .exceptions import ValidationError


class BuildingValidator:
    async def validate_create_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        name = (data.get("name") or "").strip()
        address = data.get("address") or {}
        if not name:
            raise ValidationError("name is required")
        if not isinstance(address, dict) or not (address.get("street") and address.get("city") and address.get("state") and address.get("postal_code")):
            raise ValidationError("address with street, city, state, postal_code is required")
        return data

    async def validate_update_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if "name" in data and data["name"] is not None and not str(data["name"]).strip():
            raise ValidationError("name, if provided, cannot be empty")
        return data

    async def validate_building_id(self, building_id: str) -> str:
        if not building_id or not str(building_id).strip():
            raise ValidationError("building_id is required")
        return building_id

    async def validate_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        # Limit filter sizes to prevent abuse
        for k, v in list(filters.items()):
            if isinstance(v, str) and len(v) > 255:
                filters[k] = v[:255]
        return filters

    async def validate_pagination(self, pagination: Dict[str, Any]) -> Dict[str, Any]:
        page = int(pagination.get("page", 1))
        page_size = int(pagination.get("page_size", 10))
        if page < 1:
            raise ValidationError("page must be >= 1")
        if not 1 <= page_size <= 100:
            raise ValidationError("page_size must be between 1 and 100")
        return {"page": page, "page_size": page_size, "sort_by": pagination.get("sort_by"), "sort_order": pagination.get("sort_order")}
