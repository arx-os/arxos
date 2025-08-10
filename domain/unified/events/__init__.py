"""
Unified Domain Events (minimal stubs)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BuildingCreated:
    building_id: str
    building_name: str
    address: str
    created_by: str


@dataclass
class BuildingUpdated:
    building_id: str
    updated_fields: list[str]
    updated_by: str


@dataclass
class BuildingStatusChanged:
    building_id: str
    old_status: str
    new_status: str
    changed_by: str
