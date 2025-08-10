"""
ArxObject Core Data Structure.

Granular building components with 1'x1' to sub-micron precision for the Arxos BIM system.
Implements Building-Infrastructure-as-Code paradigm with spatial awareness.
"""

import uuid
import time
import math
from typing import Dict, Any, List, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timezone
import json
import hashlib

from .octree_index import BoundingBox3D
from .rtree_index import BoundingBox2D

logger = logging.getLogger(__name__)


class ArxObjectType(Enum):
    """ArxObject type enumeration for different building systems."""
    
    # Structural System (Highest Priority)
    STRUCTURAL_BEAM = "structural_beam"
    STRUCTURAL_COLUMN = "structural_column"
    STRUCTURAL_WALL = "structural_wall"
    STRUCTURAL_SLAB = "structural_slab"
    STRUCTURAL_FOUNDATION = "structural_foundation"
    
    # Life Safety System (Second Priority)
    FIRE_SPRINKLER = "fire_sprinkler"
    FIRE_ALARM = "fire_alarm"
    FIRE_EXTINGUISHER = "fire_extinguisher" 
    EMERGENCY_EXIT = "emergency_exit"
    SMOKE_DETECTOR = "smoke_detector"
    
    # MEP Systems (Third Priority)
    ELECTRICAL_OUTLET = "electrical_outlet"
    ELECTRICAL_PANEL = "electrical_panel"
    ELECTRICAL_CONDUIT = "electrical_conduit"
    ELECTRICAL_FIXTURE = "electrical_fixture"
    HVAC_DUCT = "hvac_duct"
    HVAC_UNIT = "hvac_unit"
    HVAC_DIFFUSER = "hvac_diffuser"
    PLUMBING_PIPE = "plumbing_pipe"
    PLUMBING_FIXTURE = "plumbing_fixture"
    PLUMBING_VALVE = "plumbing_valve"
    
    # Distribution Systems (Fourth Priority)
    TELECOMMUNICATIONS = "telecommunications"
    DATA_CABLE = "data_cable"
    SECURITY_CAMERA = "security_camera"
    ACCESS_CONTROL = "access_control"
    
    # Finishes (Lowest Priority)
    CEILING_TILE = "ceiling_tile"
    FLOORING = "flooring"
    PAINT = "paint"
    FURNITURE = "furniture"
    DECORATION = "decoration"
    
    def get_system_priority(self) -> int:
        """Get system priority for conflict resolution."""
        if self.value.startswith('structural_'):
            return 1  # Highest priority
        elif self.value.startswith('fire_') or self.value in ['emergency_exit', 'smoke_detector']:
            return 2  # Life safety
        elif self.value.startswith(('electrical_', 'hvac_', 'plumbing_')):
            return 3  # MEP systems
        elif self.value.startswith(('telecommunications', 'data_', 'security_', 'access_')):
            return 4  # Distribution
        else:
            return 5  # Finishes (lowest priority)
    
    def get_system_type(self) -> str:
        """Get general system type."""
        if self.value.startswith('structural_'):
            return 'structural'
        elif self.value.startswith('fire_') or self.value in ['emergency_exit', 'smoke_detector']:
            return 'life_safety'
        elif self.value.startswith('electrical_'):
            return 'electrical'
        elif self.value.startswith('hvac_'):
            return 'hvac'
        elif self.value.startswith('plumbing_'):
            return 'plumbing'
        elif self.value.startswith(('telecommunications', 'data_')):
            return 'telecommunications'
        elif self.value.startswith(('security_', 'access_')):
            return 'security'
        else:
            return 'finishes'


class ArxObjectPrecision(Enum):
    """Precision levels for ArxObjects."""
    
    COARSE = "coarse"          # 1 foot precision
    STANDARD = "standard"      # 1 inch precision  
    FINE = "fine"             # 1/16 inch precision
    ULTRA_FINE = "ultra_fine"  # 1/64 inch precision
    MICRO = "micro"           # 1/1000 inch precision
    NANO = "nano"             # Sub-micron precision
    
    def get_tolerance(self) -> float:
        """Get precision tolerance in feet."""
        tolerances = {
            ArxObjectPrecision.COARSE: 1.0,        # 1 foot
            ArxObjectPrecision.STANDARD: 1/12,     # 1 inch
            ArxObjectPrecision.FINE: 1/192,        # 1/16 inch
            ArxObjectPrecision.ULTRA_FINE: 1/768,  # 1/64 inch
            ArxObjectPrecision.MICRO: 1/12000,     # 1/1000 inch
            ArxObjectPrecision.NANO: 1/12000000    # Sub-micron
        }
        return tolerances[self]


@dataclass
class ArxObjectGeometry:
    """Geometric representation of ArxObject."""
    
    # 3D coordinates (in feet, relative to building origin)
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    # Dimensions (in feet)
    length: float = 1.0
    width: float = 1.0
    height: float = 1.0
    
    # Rotation (in radians)
    rotation_x: float = 0.0
    rotation_y: float = 0.0
    rotation_z: float = 0.0
    
    # Additional geometric properties
    shape_type: str = "box"  # box, cylinder, sphere, custom
    custom_geometry: Optional[Dict[str, Any]] = None
    
    def get_bounding_box_3d(self) -> BoundingBox3D:
        """Get 3D bounding box."""
        # TODO: Account for rotation in bounding box calculation
        half_length = self.length / 2
        half_width = self.width / 2
        half_height = self.height / 2
        
        return BoundingBox3D(
            min_x=self.x - half_length,
            min_y=self.y - half_width,
            min_z=self.z - half_height,
            max_x=self.x + half_length,
            max_y=self.y + half_width,
            max_z=self.z + half_height
        )
    
    def get_bounding_box_2d(self) -> BoundingBox2D:
        """Get 2D bounding box (plan view projection)."""
        half_length = self.length / 2
        half_width = self.width / 2
        
        return BoundingBox2D(
            min_x=self.x - half_length,
            min_y=self.y - half_width,
            max_x=self.x + half_length,
            max_y=self.y + half_width
        )
    
    def get_center(self) -> Tuple[float, float, float]:
        """Get geometric center point."""
        return (self.x, self.y, self.z)
    
    def get_volume(self) -> float:
        """Calculate volume of ArxObject."""
        if self.shape_type == "box":
            return self.length * self.width * self.height
        elif self.shape_type == "cylinder":
            radius = self.width / 2  # Assume width is diameter
            return math.pi * radius * radius * self.height
        elif self.shape_type == "sphere":
            radius = self.width / 2  # Assume width is diameter
            return (4/3) * math.pi * radius * radius * radius
        else:
            # Custom geometry volume calculation
            if self.custom_geometry and 'volume' in self.custom_geometry:
                return self.custom_geometry['volume']
            return self.length * self.width * self.height
    
    def distance_to_point(self, x: float, y: float, z: float) -> float:
        """Calculate distance from ArxObject center to point."""
        dx = self.x - x
        dy = self.y - y
        dz = self.z - z
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def distance_to_point_2d(self, x: float, y: float) -> float:
        """Calculate 2D distance from ArxObject center to point."""
        dx = self.x - x
        dy = self.y - y
        return math.sqrt(dx*dx + dy*dy)
    
    def contains_point(self, x: float, y: float, z: float) -> bool:
        """Check if point is contained within ArxObject."""
        bbox = self.get_bounding_box_3d()
        return bbox.contains_point(x, y, z)
    
    def contains_point_2d(self, x: float, y: float) -> bool:
        """Check if 2D point is contained within ArxObject plan projection."""
        bbox = self.get_bounding_box_2d()
        return bbox.contains_point(x, y)


@dataclass 
class ArxObjectMetadata:
    """Metadata for ArxObject properties and attributes."""
    
    # Identity and classification
    name: str = ""
    description: str = ""
    manufacturer: str = ""
    model_number: str = ""
    specification: str = ""
    
    # Material properties
    material: str = ""
    material_properties: Dict[str, Any] = field(default_factory=dict)
    
    # Installation information
    installed_by: str = ""
    installation_date: Optional[datetime] = None
    warranty_expiration: Optional[datetime] = None
    
    # Maintenance information
    maintenance_schedule: Dict[str, Any] = field(default_factory=dict)
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    
    # Cost information
    unit_cost: float = 0.0
    installation_cost: float = 0.0
    maintenance_cost_annual: float = 0.0
    
    # Compliance and certification
    certifications: List[str] = field(default_factory=list)
    compliance_codes: List[str] = field(default_factory=list)
    
    # Custom attributes
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    
    # Performance data
    performance_data: Dict[str, Any] = field(default_factory=dict)
    
    # Relationships to other objects
    connected_to: List[str] = field(default_factory=list)  # Connected ArxObject IDs
    depends_on: List[str] = field(default_factory=list)    # Dependency ArxObject IDs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArxObjectMetadata':
        """Create metadata from dictionary."""
        # Handle datetime fields
        datetime_fields = ['installation_date', 'warranty_expiration', 
                          'last_maintenance', 'next_maintenance']
        
        for field_name in datetime_fields:
            if field_name in data and data[field_name]:
                if isinstance(data[field_name], str):
                    data[field_name] = datetime.fromisoformat(data[field_name])
        
        return cls(**data)


class ArxObject:
    """
    Core ArxObject implementation.
    
    Granular building component with 1'x1' to sub-micron precision,
    supporting Building-Infrastructure-as-Code paradigm.
    """
    
    def __init__(self, 
                 arxobject_type: ArxObjectType,
                 geometry: ArxObjectGeometry,
                 metadata: Optional[ArxObjectMetadata] = None,
                 precision: ArxObjectPrecision = ArxObjectPrecision.STANDARD,
                 building_id: Optional[str] = None,
                 floor_id: Optional[str] = None,
                 room_id: Optional[str] = None,
                 arxobject_id: Optional[str] = None):
        """
        Initialize ArxObject.
        
        Args:
            arxobject_type: Type of building component
            geometry: 3D geometric representation
            metadata: Additional object metadata
            precision: Precision level for geometric operations
            building_id: Parent building identifier
            floor_id: Parent floor identifier  
            room_id: Parent room identifier
            arxobject_id: Unique object identifier (generated if not provided)
        """
        self.id = arxobject_id or self._generate_id()
        self.type = arxobject_type
        self.geometry = geometry
        self.metadata = metadata or ArxObjectMetadata()
        self.precision = precision
        
        # Hierarchical relationships
        self.building_id = building_id
        self.floor_id = floor_id
        self.room_id = room_id
        
        # Versioning and change tracking
        self.version = 1
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
        self.created_by = ""
        self.updated_by = ""
        
        # State tracking
        self.is_active = True
        self.is_locked = False
        self.lock_owner = ""
        self.lock_timestamp: Optional[datetime] = None
        
        # Spatial indexing support
        self._spatial_hash: Optional[str] = None
        self._last_geometry_update = self.updated_at
        
        # Performance tracking
        self._access_count = 0
        self._last_accessed = self.created_at
        
        logger.debug(f"Created ArxObject {self.id} of type {arxobject_type.value}")
    
    def _generate_id(self) -> str:
        """Generate unique ArxObject ID."""
        timestamp = int(time.time() * 1000000)  # Microsecond timestamp
        random_component = uuid.uuid4().hex[:8]
        return f"arx_{timestamp}_{random_component}"
    
    def get_system_priority(self) -> int:
        """Get system priority for conflict resolution."""
        return self.type.get_system_priority()
    
    def get_system_type(self) -> str:
        """Get general system type."""
        return self.type.get_system_type()
    
    def get_bounding_box(self) -> BoundingBox3D:
        """Get 3D bounding box for spatial indexing."""
        return self.geometry.get_bounding_box_3d()
    
    def get_plan_view_bounds(self) -> BoundingBox2D:
        """Get 2D plan view bounding box."""
        return self.geometry.get_bounding_box_2d()
    
    def get_center(self) -> Tuple[float, float, float]:
        """Get geometric center point."""
        self._access_count += 1
        self._last_accessed = datetime.now(timezone.utc)
        return self.geometry.get_center()
    
    def contains_point(self, x: float, y: float, z: float) -> bool:
        """Check if 3D point is contained within ArxObject."""
        return self.geometry.contains_point(x, y, z)
    
    def contains_point_2d(self, x: float, y: float) -> bool:
        """Check if 2D point is contained within ArxObject plan projection."""
        return self.geometry.contains_point_2d(x, y)
    
    def distance_to_point(self, x: float, y: float, z: float) -> float:
        """Calculate distance to 3D point."""
        return self.geometry.distance_to_point(x, y, z)
    
    def distance_to_point_2d(self, x: float, y: float) -> float:
        """Calculate distance to 2D point."""
        return self.geometry.distance_to_point_2d(x, y)
    
    def get_volume(self) -> float:
        """Get ArxObject volume."""
        return self.geometry.get_volume()
    
    def get_tolerance(self) -> float:
        """Get precision tolerance."""
        return self.precision.get_tolerance()
    
    def update_geometry(self, new_geometry: ArxObjectGeometry) -> None:
        """Update ArxObject geometry."""
        if self.is_locked:
            raise ValueError(f"Cannot update geometry: ArxObject {self.id} is locked by {self.lock_owner}")
        
        old_geometry = self.geometry
        self.geometry = new_geometry
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)
        self._last_geometry_update = self.updated_at
        self._spatial_hash = None  # Invalidate spatial hash
        
        logger.info(f"Updated geometry for ArxObject {self.id} (version {self.version})")
    
    def update_metadata(self, new_metadata: ArxObjectMetadata) -> None:
        """Update ArxObject metadata."""
        if self.is_locked:
            raise ValueError(f"Cannot update metadata: ArxObject {self.id} is locked by {self.lock_owner}")
        
        self.metadata = new_metadata
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Updated metadata for ArxObject {self.id} (version {self.version})")
    
    def lock(self, owner: str, duration_minutes: int = 30) -> bool:
        """Lock ArxObject for exclusive editing."""
        if self.is_locked and self._is_lock_expired():
            self.unlock()
        
        if self.is_locked:
            return False
        
        self.is_locked = True
        self.lock_owner = owner
        self.lock_timestamp = datetime.now(timezone.utc)
        
        logger.info(f"Locked ArxObject {self.id} for {owner}")
        return True
    
    def unlock(self, owner: Optional[str] = None) -> bool:
        """Unlock ArxObject."""
        if not self.is_locked:
            return True
        
        if owner and self.lock_owner != owner:
            return False
        
        self.is_locked = False
        self.lock_owner = ""
        self.lock_timestamp = None
        
        logger.info(f"Unlocked ArxObject {self.id}")
        return True
    
    def _is_lock_expired(self, duration_minutes: int = 30) -> bool:
        """Check if lock has expired."""
        if not self.lock_timestamp:
            return True
        
        expiry_time = self.lock_timestamp.timestamp() + (duration_minutes * 60)
        return time.time() > expiry_time
    
    def get_spatial_hash(self) -> str:
        """Get spatial hash for efficient conflict detection."""
        if self._spatial_hash is None:
            # Create hash based on geometry and precision
            geometry_data = {
                'x': round(self.geometry.x / self.get_tolerance()),
                'y': round(self.geometry.y / self.get_tolerance()),
                'z': round(self.geometry.z / self.get_tolerance()),
                'length': round(self.geometry.length / self.get_tolerance()),
                'width': round(self.geometry.width / self.get_tolerance()),
                'height': round(self.geometry.height / self.get_tolerance()),
                'type': self.type.value,
                'precision': self.precision.value
            }
            
            hash_input = json.dumps(geometry_data, sort_keys=True)
            self._spatial_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        
        return self._spatial_hash
    
    def clone(self, new_id: Optional[str] = None) -> 'ArxObject':
        """Create copy of ArxObject with new ID."""
        clone = ArxObject(
            arxobject_type=self.type,
            geometry=ArxObjectGeometry(**self.geometry.__dict__),
            metadata=ArxObjectMetadata.from_dict(self.metadata.to_dict()),
            precision=self.precision,
            building_id=self.building_id,
            floor_id=self.floor_id,
            room_id=self.room_id,
            arxobject_id=new_id
        )
        
        logger.info(f"Cloned ArxObject {self.id} to {clone.id}")
        return clone
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ArxObject to dictionary representation."""
        return {
            'id': self.id,
            'type': self.type.value,
            'geometry': self.geometry.__dict__,
            'metadata': self.metadata.to_dict(),
            'precision': self.precision.value,
            'building_id': self.building_id,
            'floor_id': self.floor_id,
            'room_id': self.room_id,
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'is_active': self.is_active,
            'is_locked': self.is_locked,
            'lock_owner': self.lock_owner,
            'lock_timestamp': self.lock_timestamp.isoformat() if self.lock_timestamp else None,
            'spatial_hash': self.get_spatial_hash(),
            'access_count': self._access_count,
            'last_accessed': self._last_accessed.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArxObject':
        """Create ArxObject from dictionary representation."""
        # Parse geometry
        geometry_data = data['geometry']
        geometry = ArxObjectGeometry(**geometry_data)
        
        # Parse metadata
        metadata_data = data['metadata']
        metadata = ArxObjectMetadata.from_dict(metadata_data)
        
        # Create ArxObject
        arxobject = cls(
            arxobject_type=ArxObjectType(data['type']),
            geometry=geometry,
            metadata=metadata,
            precision=ArxObjectPrecision(data['precision']),
            building_id=data['building_id'],
            floor_id=data['floor_id'], 
            room_id=data['room_id'],
            arxobject_id=data['id']
        )
        
        # Set additional fields
        arxobject.version = data['version']
        arxobject.created_at = datetime.fromisoformat(data['created_at'])
        arxobject.updated_at = datetime.fromisoformat(data['updated_at'])
        arxobject.created_by = data['created_by']
        arxobject.updated_by = data['updated_by']
        arxobject.is_active = data['is_active']
        arxobject.is_locked = data['is_locked']
        arxobject.lock_owner = data['lock_owner']
        
        if data['lock_timestamp']:
            arxobject.lock_timestamp = datetime.fromisoformat(data['lock_timestamp'])
        
        arxobject._access_count = data.get('access_count', 0)
        arxobject._last_accessed = datetime.fromisoformat(data['last_accessed'])
        
        return arxobject
    
    def to_ifc(self) -> Dict[str, Any]:
        """Export ArxObject to IFC-compatible representation."""
        # Basic IFC entity structure
        ifc_data = {
            'GlobalId': self.id,
            'Name': self.metadata.name or f"{self.type.value}_{self.id[-8:]}",
            'Description': self.metadata.description,
            'ObjectType': self.type.value,
            'ObjectPlacement': {
                'Location': {
                    'Coordinates': [self.geometry.x, self.geometry.y, self.geometry.z]
                },
                'Axis': [0, 0, 1],  # Z-axis
                'RefDirection': [1, 0, 0]  # X-axis
            },
            'Representation': {
                'RepresentationType': 'BoundingBox',
                'Items': [{
                    'Dimensions': [self.geometry.length, self.geometry.width, self.geometry.height],
                    'Position': [self.geometry.x, self.geometry.y, self.geometry.z]
                }]
            },
            'Properties': {
                'Material': self.metadata.material,
                'Manufacturer': self.metadata.manufacturer,
                'ModelNumber': self.metadata.model_number,
                'SystemType': self.get_system_type(),
                'SystemPriority': self.get_system_priority(),
                'Precision': self.precision.value,
                'Volume': self.get_volume(),
                'Version': self.version,
                'CustomAttributes': self.metadata.custom_attributes
            }
        }
        
        return ifc_data
    
    def __str__(self) -> str:
        """String representation of ArxObject."""
        return (f"ArxObject(id={self.id}, type={self.type.value}, "
                f"center=({self.geometry.x:.3f}, {self.geometry.y:.3f}, {self.geometry.z:.3f}), "
                f"dims=({self.geometry.length:.3f}x{self.geometry.width:.3f}x{self.geometry.height:.3f}), "
                f"precision={self.precision.value})")
    
    def __repr__(self) -> str:
        """Detailed representation of ArxObject."""
        return self.__str__()
    
    def __eq__(self, other) -> bool:
        """Check equality based on ID."""
        if not isinstance(other, ArxObject):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash based on ID for use in sets and dictionaries."""
        return hash(self.id)
    
    def __lt__(self, other) -> bool:
        """Compare ArxObjects for sorting (by system priority, then by ID)."""
        if not isinstance(other, ArxObject):
            return NotImplemented
        
        # Primary sort: system priority (lower number = higher priority)
        if self.get_system_priority() != other.get_system_priority():
            return self.get_system_priority() < other.get_system_priority()
        
        # Secondary sort: by ID for consistency
        return self.id < other.id