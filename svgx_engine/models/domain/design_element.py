#!/usr/bin/env python3
"""
Design Element Domain Model

Domain model for engineering design elements.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SystemType(Enum):
    """Engineering system types."""

    ELECTRICAL = "electrical"
    HVAC = "hvac"
    PLUMBING = "plumbing"
    STRUCTURAL = "structural"
    MULTI_SYSTEM = "multi_system"


class ElementType(Enum):
    """Design element types."""

    # Electrical elements
    CIRCUIT_BREAKER = "circuit_breaker"
    WIRE = "wire"
    OUTLET = "outlet"
    LIGHTING_FIXTURE = "lighting_fixture"
    PANEL = "panel"

    # HVAC elements
    AIR_HANDLER = "air_handler"
    DUCT = "duct"
    VAV_BOX = "vav_box"
    THERMOSTAT = "thermostat"
    DIFFUSER = "diffuser"

    # Plumbing elements
    PIPE = "pipe"
    VALVE = "valve"
    FIXTURE = "fixture"
    PUMP = "pump"
    TANK = "tank"

    # Structural elements
    BEAM = "beam"
    COLUMN = "column"
    WALL = "wall"
    SLAB = "slab"
    FOUNDATION = "foundation"


@dataclass
class Geometry:
    """Geometry information for design elements."""

    type: str
    coordinates: List[float]
    dimensions: Optional[Dict[str, float]] = None
    properties: Optional[Dict[str, Any]] = None


@dataclass
class Location:
    """Location information for design elements."""

    x: float
    y: float
    z: float
    floor: Optional[str] = None
    room: Optional[str] = None
    building: Optional[str] = None


@dataclass
class DesignElement:
    """Engineering design element."""

    id: str
    system_type: SystemType
    element_type: ElementType
    properties: Dict[str, Any] = field(default_factory=dict)
    geometry: Optional[Geometry] = None
    location: Optional[Location] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Post-initialization validation."""
        if isinstance(self.system_type, str):
            self.system_type = SystemType(self.system_type)
        if isinstance(self.element_type, str):
            self.element_type = ElementType(self.element_type)

    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a property value."""
        return self.properties.get(key, default)

    def set_property(self, key: str, value: Any) -> None:
        """Set a property value."""
        self.properties[key] = value

    def has_property(self, key: str) -> bool:
        """Check if element has a specific property."""
        return key in self.properties

    def get_required_properties(self) -> List[str]:
        """Get list of required properties based on system type."""
        if self.system_type == SystemType.ELECTRICAL:
            return ["current_rating", "voltage", "wire_size"]
        elif self.system_type == SystemType.HVAC:
            return ["airflow", "temperature", "pressure"]
        elif self.system_type == SystemType.PLUMBING:
            return ["flow_rate", "pressure", "pipe_size"]
        elif self.system_type == SystemType.STRUCTURAL:
            return ["load", "material", "dimensions"]
        else:
            return []

    def validate_required_properties(self) -> List[str]:
        """Validate that all required properties are present."""
        missing_properties = []
        required_properties = self.get_required_properties()

        for prop in required_properties:
            if not self.has_property(prop):
                missing_properties.append(prop)

        return missing_properties

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "system_type": self.system_type.value,
            "element_type": self.element_type.value,
            "properties": self.properties,
            "geometry": self.geometry.__dict__ if self.geometry else None,
            "location": self.location.__dict__ if self.location else None,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DesignElement":
        """Create DesignElement from dictionary."""
        geometry_data = data.get("geometry")
        geometry = Geometry(**geometry_data) if geometry_data else None

        location_data = data.get("location")
        location = Location(**location_data) if location_data else None

        return cls(
            id=data["id"],
            system_type=data["system_type"],
            element_type=data["element_type"],
            properties=data.get("properties", {}),
            geometry=geometry,
            location=location,
            metadata=data.get("metadata", {}),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if "timestamp" in data
                else datetime.utcnow()
            ),
        )
