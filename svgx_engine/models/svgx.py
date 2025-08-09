"""
SVGX data models for SVGX Engine.

This module defines the core data structures for SVGX documents,
objects, behaviors, and physics.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class SVGXDocument:
    """SVGX document model."""

    version: str = "1.0"
    elements: List['SVGXElement'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        pass
    """
    Perform __post_init__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __post_init__(param)
        print(result)
    """
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    def add_element(self, element: 'SVGXElement'):
        """Add an element to the document."""
        self.elements.append(element)
        self.updated_at = datetime.utcnow()

    def get_elements_by_type(self, element_type: str) -> List['SVGXElement']:
        """Get elements by type."""
        return [elem for elem in self.elements if elem.tag == element_type]

    def get_elements_with_arx_object(self) -> List['SVGXElement']:
        """Get elements that have arx:object data."""
        return [elem for elem in self.elements if elem.arx_object is not None]


@dataclass
class SVGXElement:
    """SVGX element model."""

    tag: str
    attributes: Dict[str, str] = field(default_factory=dict)
    content: str = ""
    position: List[float] = field(default_factory=lambda: [0, 0])
    children: List['SVGXElement'] = field(default_factory=list)
    arx_object: Optional['ArxObject'] = None
    arx_behavior: Optional['ArxBehavior'] = None
    arx_physics: Optional['ArxPhysics'] = None

    def add_child(self, child: 'SVGXElement'):
        """Add a child element."""
        self.children.append(child)

    def get_arx_attribute(self, name: str) -> Optional[str]:
        """Get an arx: namespace attribute."""
        return self.attributes.get(f"arx:{name}")

    def has_arx_object(self) -> bool:
        """Check if element has arx:object data."""
        return any(key.startswith("arx:") for key in self.attributes.keys()
@dataclass
class ArxObject:
    """ArxObject model for SVGX."""

    object_id: str
    object_type: str
    system: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    geometry: Optional[Dict[str, Any]] = None
    behavior: Optional['ArxBehavior'] = None
    physics: Optional['ArxPhysics'] = None

    def add_property(self, key: str, value: Any):
        """Add a property to the object."""
        self.properties[key] = value

    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a property from the object."""
        return self.properties.get(key, default)


@dataclass
class ArxBehavior:
    """ArxBehavior model for SVGX."""

    variables: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    calculations: Dict[str, str] = field(default_factory=dict)
    triggers: List[Dict[str, str]] = field(default_factory=list)

    def add_variable(self, name: str, value: float, unit: str = None):
        """Add a variable to the behavior."""
        self.variables[name] = {"value": value, "unit": unit}

    def add_calculation(self, name: str, formula: str):
        """Add a calculation to the behavior."""
        self.calculations[name] = formula

    def add_trigger(self, event: str, action: str):
        """Add a trigger to the behavior."""
        self.triggers.append({"event": event, "action": action})

    def get_variable(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a variable from the behavior."""
        return self.variables.get(name)

    def get_calculation(self, name: str) -> Optional[str]:
        """Get a calculation from the behavior."""
        return self.calculations.get(name)


@dataclass
class ArxPhysics:
    """ArxPhysics model for SVGX."""

    mass: Optional[Dict[str, Any]] = None
    anchor: Optional[str] = None
    forces: List[Dict[str, Any]] = field(default_factory=list)

    def set_mass(self, mass: float, unit: str = "kg"):
        """Set the mass of the object."""
        self.mass = {"value": mass, "unit": unit}

    def set_anchor(self, anchor: str):
        """Set the anchor point."""
        self.anchor = anchor

    def add_force(self, force_type: str, direction: str = None, value: float = None):
        """Add a force to the physics."""
        self.forces.append({
            "type": force_type,
            "direction": direction,
            "value": value
        })

    def get_mass(self) -> Optional[float]:
        """Get the mass value."""
        return self.mass["value"] if self.mass else None

    def get_mass_unit(self) -> Optional[str]:
        """Get the mass unit."""
        return self.mass["unit"] if self.mass else None


@dataclass
class SVGXObject:
    """SVGX object model for database storage."""

    object_id: str
    object_type: str
    system: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    geometry: Optional[Dict[str, Any]] = None
    behavior: Optional[ArxBehavior] = None
    physics: Optional[ArxPhysics] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'object_id': self.object_id,
            'object_type': self.object_type,
            'system': self.system,
            'properties': self.properties,
            'geometry': self.geometry,
            'behavior': self.behavior.__dict__ if self.behavior else None,
            'physics': self.physics.__dict__ if self.physics else None
        }

    @classmethod
def from_dict(cls, data: Dict[str, Any]) -> 'SVGXObject':
        """Create from dictionary."""
        behavior = None
        if data.get('behavior'):
            behavior = ArxBehavior(**data['behavior'])

        physics = None
        if data.get('physics'):
            physics = ArxPhysics(**data['physics'])

        return cls(
            object_id=data['object_id'],
            object_type=data['object_type'],
            system=data.get('system'),
            properties=data.get('properties', {}),
            geometry=data.get('geometry'),
            behavior=behavior,
            physics=physics
        )


@dataclass
class SVGXSymbol:
    """SVGX symbol model for symbol management."""

    symbol_id: str
    symbol_name: str
    symbol_type: str
    content: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    def add_property(self, key: str, value: Any):
        """Add a property to the symbol."""
        self.properties[key] = value
        self.updated_at = datetime.utcnow()

    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a property from the symbol."""
        return self.properties.get(key, default)

    def add_metadata(self, key: str, value: Any):
        """Add metadata to the symbol."""
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata from the symbol."""
        return self.metadata.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'symbol_id': self.symbol_id,
            'symbol_name': self.symbol_name,
            'symbol_type': self.symbol_type,
            'content': self.content,
            'properties': self.properties,
            'metadata': self.metadata,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
def from_dict(cls, data: Dict[str, Any]) -> 'SVGXSymbol':
        """Create from dictionary."""
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])

        updated_at = None
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'])

        return cls(
            symbol_id=data['symbol_id'],
            symbol_name=data['symbol_name'],
            symbol_type=data['symbol_type'],
            content=data.get('content', ''),
            properties=data.get('properties', {}),
            metadata=data.get('metadata', {}),
            version=data.get('version', '1.0'),
            created_at=created_at,
            updated_at=updated_at
        )
