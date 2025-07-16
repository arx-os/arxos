"""
SVGX Engine - BIM Models

This module defines the data models for Building Information Modeling (BIM)
elements and structures used in the SVGX Engine.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime


class GeometryType(Enum):
    """Types of geometry supported in SVGX Engine."""
    POINT = "point"
    LINESTRING = "linestring"
    POLYGON = "polygon"
    MULTIPOINT = "multipoint"
    MULTILINESTRING = "multilinestring"
    MULTIPOLYGON = "multipolygon"
    GEOMETRYCOLLECTION = "geometrycollection"


class SystemType(Enum):
    """Types of BIM systems."""
    ELECTRICAL = "electrical"
    MECHANICAL = "mechanical"
    PLUMBING = "plumbing"
    HVAC = "hvac"
    FIRE_PROTECTION = "fire_protection"
    SECURITY = "security"
    TELECOMMUNICATIONS = "telecommunications"
    STRUCTURAL = "structural"
    ARCHITECTURAL = "architectural"


class RoomType(Enum):
    """Types of rooms in BIM models."""
    OFFICE = "office"
    CONFERENCE = "conference"
    LOBBY = "lobby"
    RESTROOM = "restroom"
    KITCHEN = "kitchen"
    STORAGE = "storage"
    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    CORRIDOR = "corridor"
    STAIRWELL = "stairwell"
    ELEVATOR = "elevator"
    EXIT = "exit"
    ENTRANCE = "entrance"
    OTHER = "other"


class DeviceCategory(Enum):
    """Categories of devices in BIM models."""
    ELECTRICAL = "electrical"
    MECHANICAL = "mechanical"
    PLUMBING = "plumbing"
    HVAC = "hvac"
    FIRE_PROTECTION = "fire_protection"
    SECURITY = "security"
    TELECOMMUNICATIONS = "telecommunications"
    LIGHTING = "lighting"
    OTHER = "other"


class ElementCategory(Enum):
    """Categories of BIM elements."""
    HVAC = "hvac"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    FIRE_SAFETY = "fire_safety"
    SECURITY = "security"
    STRUCTURAL = "structural"
    LIGHTING = "lighting"
    OTHER = "other"


@dataclass
class Geometry:
    """Geometry representation for BIM elements."""
    geometry_type: GeometryType
    coordinates: Union[List, List[List], List[List[List]]]
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate geometry after initialization."""
        if not isinstance(self.coordinates, (list, tuple)):
            raise ValueError("Coordinates must be a list or tuple")
        
        if self.geometry_type == GeometryType.POINT:
            if not isinstance(self.coordinates, (list, tuple)) or len(self.coordinates) < 2:
                raise ValueError("Point geometry must have at least 2 coordinates")
        elif self.geometry_type == GeometryType.LINESTRING:
            if not isinstance(self.coordinates, (list, tuple)) or len(self.coordinates) < 2:
                raise ValueError("LineString geometry must have at least 2 points")
        elif self.geometry_type == GeometryType.POLYGON:
            if not isinstance(self.coordinates, (list, tuple)) or len(self.coordinates) < 3:
                raise ValueError("Polygon geometry must have at least 3 points")


@dataclass
class BIMElementBase:
    """Base class for all BIM elements."""
    id: str
    name: str
    geometry: Optional[Geometry] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate element after initialization."""
        if not self.id:
            raise ValueError("Element ID cannot be empty")
        if not self.name:
            raise ValueError("Element name cannot be empty")


@dataclass
class BIMElement(BIMElementBase):
    """Generic BIM element."""
    element_type: str = "generic"
    system_type: Optional[SystemType] = None
    
    def __post_init__(self):
        """Validate BIM element after initialization."""
        super().__post_init__()
        if not self.element_type:
            raise ValueError("Element type cannot be empty")


@dataclass
class Room(BIMElementBase):
    """Room element in BIM model."""
    room_type: RoomType = RoomType.OTHER
    floor_number: Optional[int] = None
    area: Optional[float] = None
    height: Optional[float] = None
    occupancy: Optional[int] = None
    
    def __post_init__(self):
        """Validate room after initialization."""
        super().__post_init__()
        if self.area is not None and self.area <= 0:
            raise ValueError("Room area must be positive")
        if self.height is not None and self.height <= 0:
            raise ValueError("Room height must be positive")
        if self.occupancy is not None and self.occupancy < 0:
            raise ValueError("Room occupancy cannot be negative")


@dataclass
class Wall(BIMElementBase):
    """Wall element in BIM model."""
    wall_type: str = "standard"
    thickness: Optional[float] = None
    height: Optional[float] = None
    material: Optional[str] = None
    fire_rating: Optional[str] = None
    
    def __post_init__(self):
        """Validate wall after initialization."""
        super().__post_init__()
        if self.thickness is not None and self.thickness <= 0:
            raise ValueError("Wall thickness must be positive")
        if self.height is not None and self.height <= 0:
            raise ValueError("Wall height must be positive")


@dataclass
class Door(BIMElementBase):
    """Door element in BIM model."""
    door_type: str = "standard"
    width: Optional[float] = None
    height: Optional[float] = None
    material: Optional[str] = None
    fire_rating: Optional[str] = None
    swing_direction: Optional[str] = None
    
    def __post_init__(self):
        """Validate door after initialization."""
        super().__post_init__()
        if self.width is not None and self.width <= 0:
            raise ValueError("Door width must be positive")
        if self.height is not None and self.height <= 0:
            raise ValueError("Door height must be positive")


@dataclass
class Window(BIMElementBase):
    """Window element in BIM model."""
    window_type: str = "standard"
    width: Optional[float] = None
    height: Optional[float] = None
    material: Optional[str] = None
    glazing_type: Optional[str] = None
    
    def __post_init__(self):
        """Validate window after initialization."""
        super().__post_init__()
        if self.width is not None and self.width <= 0:
            raise ValueError("Window width must be positive")
        if self.height is not None and self.height <= 0:
            raise ValueError("Window height must be positive")


@dataclass
class Device(BIMElementBase):
    """Device element in BIM model."""
    category: DeviceCategory = DeviceCategory.OTHER
    device_type: str = "generic"
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    power_rating: Optional[float] = None
    voltage: Optional[float] = None
    
    def __post_init__(self):
        """Validate device after initialization."""
        super().__post_init__()
        if self.power_rating is not None and self.power_rating < 0:
            raise ValueError("Device power rating cannot be negative")
        if self.voltage is not None and self.voltage <= 0:
            raise ValueError("Device voltage must be positive")


@dataclass
class BIMSystem:
    """BIM system containing related elements."""
    id: str
    name: str
    system_type: SystemType
    elements: List[BIMElement] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate system after initialization."""
        if not self.id:
            raise ValueError("System ID cannot be empty")
        if not self.name:
            raise ValueError("System name cannot be empty")
    
    def add_element(self, element: BIMElement):
        """Add an element to the system."""
        self.elements.append(element)
        self.updated_at = datetime.now()
    
    def remove_element(self, element_id: str):
        """Remove an element from the system."""
        self.elements = [e for e in self.elements if e.id != element_id]
        self.updated_at = datetime.now()


@dataclass
class BIMSpace:
    """BIM space containing related elements."""
    id: str
    name: str
    space_type: str = "generic"
    elements: List[BIMElement] = field(default_factory=list)
    geometry: Optional[Geometry] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate space after initialization."""
        if not self.id:
            raise ValueError("Space ID cannot be empty")
        if not self.name:
            raise ValueError("Space name cannot be empty")
    
    def add_element(self, element: BIMElement):
        """Add an element to the space."""
        self.elements.append(element)
        self.updated_at = datetime.now()
    
    def remove_element(self, element_id: str):
        """Remove an element from the space."""
        self.elements = [e for e in self.elements if e.id != element_id]
        self.updated_at = datetime.now()


@dataclass
class BIMRelationship:
    """Relationship between BIM elements."""
    id: str
    source_element_id: str
    target_element_id: str
    relationship_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate relationship after initialization."""
        if not self.id:
            raise ValueError("Relationship ID cannot be empty")
        if not self.source_element_id:
            raise ValueError("Source element ID cannot be empty")
        if not self.target_element_id:
            raise ValueError("Target element ID cannot be empty")
        if not self.relationship_type:
            raise ValueError("Relationship type cannot be empty")


@dataclass
class BIMModel:
    """Complete BIM model containing all elements and systems."""
    id: str
    name: str
    description: Optional[str] = None
    elements: List[BIMElement] = field(default_factory=list)
    systems: List[BIMSystem] = field(default_factory=list)
    relationships: List[BIMRelationship] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate model after initialization."""
        if not self.id:
            raise ValueError("Model ID cannot be empty")
        if not self.name:
            raise ValueError("Model name cannot be empty")
    
    def add_element(self, element: BIMElement):
        """Add an element to the model."""
        self.elements.append(element)
        self.updated_at = datetime.now()
    
    def remove_element(self, element_id: str):
        """Remove an element from the model."""
        self.elements = [e for e in self.elements if e.id != element_id]
        self.updated_at = datetime.now()
    
    def add_system(self, system: BIMSystem):
        """Add a system to the model."""
        self.systems.append(system)
        self.updated_at = datetime.now()
    
    def remove_system(self, system_id: str):
        """Remove a system from the model."""
        self.systems = [s for s in self.systems if s.id != system_id]
        self.updated_at = datetime.now()
    
    def add_relationship(self, relationship: BIMRelationship):
        """Add a relationship to the model."""
        self.relationships.append(relationship)
        self.updated_at = datetime.now()
    
    def remove_relationship(self, relationship_id: str):
        """Remove a relationship from the model."""
        self.relationships = [r for r in self.relationships if r.id != relationship_id]
        self.updated_at = datetime.now()
    
    def get_element_by_id(self, element_id: str) -> Optional[BIMElement]:
        """Get an element by its ID."""
        for element in self.elements:
            if element.id == element_id:
                return element
        return None
    
    def get_system_by_id(self, system_id: str) -> Optional[BIMSystem]:
        """Get a system by its ID."""
        for system in self.systems:
            if system.id == system_id:
                return system
        return None
    
    def get_elements_by_type(self, element_type: str) -> List[BIMElement]:
        """Get all elements of a specific type."""
        return [e for e in self.elements if e.element_type == element_type]
    
    def get_elements_by_system(self, system_type: SystemType) -> List[BIMElement]:
        """Get all elements of a specific system type."""
        return [e for e in self.elements if e.system_type == system_type]
    
    def get_relationships_by_type(self, relationship_type: str) -> List[BIMRelationship]:
        """Get all relationships of a specific type."""
        return [r for r in self.relationships if r.relationship_type == relationship_type]
    
    def validate(self) -> bool:
        """Validate the BIM model."""
        # Check for duplicate element IDs
        element_ids = [e.id for e in self.elements]
        if len(element_ids) != len(set(element_ids)):
            return False
        
        # Check for duplicate system IDs
        system_ids = [s.id for s in self.systems]
        if len(system_ids) != len(set(system_ids)):
            return False
        
        # Check for duplicate relationship IDs
        relationship_ids = [r.id for r in self.relationships]
        if len(relationship_ids) != len(set(relationship_ids)):
            return False
        
        # Check that relationship references exist
        for relationship in self.relationships:
            if not self.get_element_by_id(relationship.source_element_id):
                return False
            if not self.get_element_by_id(relationship.target_element_id):
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the BIM model to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'elements': [self._element_to_dict(e) for e in self.elements],
            'systems': [self._system_to_dict(s) for s in self.systems],
            'relationships': [self._relationship_to_dict(r) for r in self.relationships],
            'properties': self.properties,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def _element_to_dict(self, element: BIMElement) -> Dict[str, Any]:
        """Convert an element to a dictionary."""
        return {
            'id': element.id,
            'name': element.name,
            'element_type': getattr(element, 'element_type', type(element).__name__.lower()),
            'geometry': self._geometry_to_dict(element.geometry) if element.geometry else None,
            'properties': element.properties,
            'metadata': element.metadata,
            'created_at': element.created_at.isoformat(),
            'updated_at': element.updated_at.isoformat()
        }
    
    def _geometry_to_dict(self, geometry: Geometry) -> Dict[str, Any]:
        """Convert geometry to a dictionary."""
        return {
            'type': geometry.geometry_type.value,
            'coordinates': geometry.coordinates,
            'properties': geometry.properties
        }
    
    def _system_to_dict(self, system: BIMSystem) -> Dict[str, Any]:
        """Convert a system to a dictionary."""
        return {
            'id': system.id,
            'name': system.name,
            'system_type': system.system_type.value,
            'elements': [e.id for e in system.elements],
            'properties': system.properties,
            'metadata': system.metadata,
            'created_at': system.created_at.isoformat(),
            'updated_at': system.updated_at.isoformat()
        }
    
    def _relationship_to_dict(self, relationship: BIMRelationship) -> Dict[str, Any]:
        """Convert a relationship to a dictionary."""
        return {
            'id': relationship.id,
            'source_element_id': relationship.source_element_id,
            'target_element_id': relationship.target_element_id,
            'relationship_type': relationship.relationship_type,
            'properties': relationship.properties,
            'metadata': relationship.metadata,
            'created_at': relationship.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BIMModel':
        """Create a BIM model from a dictionary."""
        # This would need more complex implementation to handle all element types
        # For now, return a basic model
        return cls(
            id=data['id'],
            name=data['name'],
            description=data.get('description'),
            properties=data.get('properties', {}),
            metadata=data.get('metadata', {})
        ) 