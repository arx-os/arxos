"""
Unified Value Objects

Minimal, self-contained value objects used by the unified domain slice.
These intentionally avoid dependencies on the legacy domain modules to
enable gradual migration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class BuildingStatus(Enum):
    PLANNED = "planned"
    UNDER_CONSTRUCTION = "under_construction"
    COMPLETED = "completed"
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    DECOMMISSIONED = "decommissioned"


class FloorStatus(Enum):
    PLANNED = "planned"
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"


class RoomStatus(Enum):
    PLANNED = "planned"
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"


@dataclass(frozen=True)
class BuildingId:
    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_string(cls, value: str) -> 'BuildingId':
        """Create a BuildingId from a string value."""
        return cls(value=value)


@dataclass(frozen=True)
class FloorId:
    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class RoomId:
    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class DeviceId:
    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Address:
    street: str
    city: str
    state: str
    postal_code: str
    country: str = "USA"
    unit: Optional[str] = None

    @property
    def full_address(self) -> str:
        parts = [self.street]
        if self.unit:
            parts.append(f"Unit {self.unit}")
        parts.extend([self.city, self.state, self.postal_code])
        if self.country and self.country != "USA":
            parts.append(self.country)
        return ", ".join(parts)

    def is_valid(self) -> bool:
        return all([self.street.strip(), self.city.strip(), self.state.strip(), self.postal_code.strip()])

    def to_dict(self) -> dict:
        return {
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
            "unit": self.unit,
        }


@dataclass(frozen=True)
class Coordinates:
    latitude: float
    longitude: float
    elevation: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "elevation": self.elevation,
        }


@dataclass(frozen=True)
class Dimensions:
    width: float
    length: float
    height: Optional[float] = None

    @property
    def area(self) -> float:
        return float(self.width) * float(self.length)

    @property
    def volume(self) -> Optional[float]:
        if self.height is None:
            return None
        return float(self.width) * float(self.length) * float(self.height)

    def to_dict(self) -> dict:
        return {
            "width": self.width,
            "length": self.length,
            "height": self.height,
        }
