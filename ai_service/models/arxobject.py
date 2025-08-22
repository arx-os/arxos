"""
ArxObject models with confidence scoring
Follows the documented specification with Pydantic for validation
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from .coordinate_system import Point3D, BoundingBox, Transform, Dimensions


class ConfidenceScore(BaseModel):
    """Multi-dimensional confidence scoring"""
    classification: float = Field(ge=0, le=1, description="Object type certainty")
    position: float = Field(ge=0, le=1, description="Spatial accuracy")
    properties: float = Field(ge=0, le=1, description="Data accuracy")
    relationships: float = Field(ge=0, le=1, description="Connection validity")
    overall: float = Field(ge=0, le=1, description="Weighted average")
    
    @validator('overall', always=True)
    def calculate_overall(cls, v, values):
        """Calculate weighted overall confidence if not provided"""
        if v is None or v == 0:
            weights = {
                'classification': 0.35,
                'position': 0.30,
                'properties': 0.20,
                'relationships': 0.15
            }
            
            overall = sum(
                values.get(key, 0) * weight
                for key, weight in weights.items()
            )
            return min(1.0, max(0.0, overall))
        return v


class RelationshipType(str, Enum):
    """Standard relationship types between ArxObjects"""
    # Spatial relationships
    CONTAINS = "contains"
    CONTAINED_BY = "contained_by"
    ADJACENT_TO = "adjacent_to"
    ABOVE = "above"
    BELOW = "below"
    CONNECTED_TO = "connected_to"
    
    # Functional relationships
    POWERS = "powers"
    CONTROLS = "controls"
    SERVES = "serves"
    MONITORS = "monitors"
    PART_OF = "part_of"
    
    # System relationships
    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"
    PRIMARY = "primary"
    BACKUP = "backup"
    GROUPED_WITH = "grouped_with"


class Relationship(BaseModel):
    """Relationship between ArxObjects"""
    type: RelationshipType
    target_id: str
    confidence: float = Field(ge=0, le=1)
    properties: Optional[Dict[str, Any]] = {}
    metadata: Optional[Dict[str, Any]] = {}


class Metadata(BaseModel):
    """ArxObject metadata for tracking provenance"""
    source: str = Field(description="Origin (pdf, field, inference)")
    source_detail: Optional[str] = None
    created: datetime = Field(default_factory=datetime.now)
    last_modified: datetime = Field(default_factory=datetime.now)
    modified_by: Optional[str] = None
    version: int = 1
    validated: bool = False
    validated_by: Optional[str] = None
    validated_at: Optional[datetime] = None


class ArxObjectType(str, Enum):
    """Building element types"""
    # Structural
    WALL = "wall"
    COLUMN = "column"
    BEAM = "beam"
    SLAB = "slab"
    FOUNDATION = "foundation"
    ROOF = "roof"
    
    # Openings
    DOOR = "door"
    WINDOW = "window"
    OPENING = "opening"
    
    # Spatial
    BUILDING = "building"
    FLOOR = "floor"
    ROOM = "room"
    ZONE = "zone"
    AREA = "area"
    
    # Annotations
    TEXT = "text"
    DIMENSION = "dimension"
    SYMBOL = "symbol"
    CORRIDOR = "corridor"
    STAIRWELL = "stairwell"
    ELEVATOR_SHAFT = "elevator_shaft"
    
    # MEP - Electrical
    ELECTRICAL_OUTLET = "electrical_outlet"
    ELECTRICAL_SWITCH = "electrical_switch"
    ELECTRICAL_PANEL = "electrical_panel"
    ELECTRICAL_CONDUIT = "electrical_conduit"
    LIGHT_FIXTURE = "light_fixture"
    
    # MEP - HVAC
    HVAC_DUCT = "hvac_duct"
    HVAC_VENT = "hvac_vent"
    HVAC_UNIT = "hvac_unit"
    THERMOSTAT = "thermostat"
    
    # MEP - Plumbing
    PLUMBING_PIPE = "plumbing_pipe"
    PLUMBING_FIXTURE = "plumbing_fixture"
    VALVE = "valve"
    PUMP = "pump"
    
    # Equipment
    EQUIPMENT = "equipment"
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    CONTROLLER = "controller"


class ValidationState(str, Enum):
    """Validation states for ArxObjects"""
    PENDING = "pending"
    PARTIAL = "partial"
    COMPLETE = "complete"
    CONFLICT = "conflict"


class ArxObject(BaseModel):
    """Core ArxObject with confidence-aware intelligence and nanometer precision"""
    id: str
    type: ArxObjectType
    
    # Spatial properties with nanometer precision
    position: Optional[Point3D] = None  # Position in world space
    dimensions: Optional[Dimensions] = None  # Real-world dimensions
    bounds: Optional[BoundingBox] = None  # Axis-aligned bounding box
    transform: Optional[Transform] = None  # Rotation/scale transform
    
    # Legacy/compatibility fields
    data: Dict[str, Any] = {}
    geometry: Optional[Dict[str, Any]] = None  # GeoJSON format
    
    # Rendering and visualization
    render_hints: Optional[Dict[str, Any]] = None
    
    # Intelligence and relationships
    confidence: ConfidenceScore
    relationships: List[Relationship] = []
    metadata: Metadata
    validation_state: ValidationState = ValidationState.PENDING
    
    # Hierarchy
    parent_id: Optional[str] = None
    children_ids: List[str] = []
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Uncertainty(BaseModel):
    """Uncertainty information for low-confidence objects"""
    object_id: str
    confidence: float
    reason: str
    validation_priority: float
    suggested_validation: str
    impact_score: float


class ValidationStrategy(BaseModel):
    """Strategic validation plan"""
    critical_validations: List[Dict[str, Any]]
    high_impact_validations: List[Dict[str, Any]]
    normal_validations: List[Dict[str, Any]]
    optional_validations: List[Dict[str, Any]]
    estimated_time: int  # minutes
    expected_confidence_gain: float


class ConversionResult(BaseModel):
    """Result of PDF to ArxObject conversion"""
    arxobjects: List[ArxObject]
    overall_confidence: float
    uncertainties: List[Uncertainty]
    validation_strategy: Optional[ValidationStrategy]
    processing_time: float  # seconds
    metadata: Dict[str, Any] = {}
    
    @validator('overall_confidence', always=True)
    def calculate_overall_confidence(cls, v, values):
        """Calculate overall confidence from ArxObjects"""
        if v == 0 and 'arxobjects' in values:
            objects = values['arxobjects']
            if objects:
                total = sum(obj.confidence.overall for obj in objects)
                return total / len(objects)
        return v


class ValidationData(BaseModel):
    """Field validation submission"""
    object_id: str
    validation_type: str  # dimension, visual, count, etc.
    measured_value: Any
    units: Optional[str] = None
    validator: str
    confidence: float = Field(ge=0, le=1)
    evidence: Optional[Dict[str, Any]] = {}  # photos, notes, etc.
    timestamp: datetime = Field(default_factory=datetime.now)


class ValidationImpact(BaseModel):
    """Impact of a validation on the system"""
    object_id: str
    old_confidence: float
    new_confidence: float
    confidence_improvement: float
    cascaded_objects: List[str]
    cascaded_count: int
    pattern_learned: bool = False
    total_confidence_gain: float
    time_saved: float  # minutes saved through propagation