"""
SVGX Engine - Plumbing BIM Objects

Plumbing BIM objects with embedded engineering logic.
Each object has its own engineering analysis capabilities.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class PlumbingObjectType(Enum):
    """Plumbing BIM object types with embedded engineering logic."""

    PIPE = "pipe"
    VALVE = "valve"
    FITTING = "fitting"
    FIXTURE = "fixture"
    PUMP = "pump"
    TANK = "tank"
    METER = "meter"
    DRAIN = "drain"
    VENT = "vent"
    TRAP = "trap"
    BACKFLOW = "backflow"
    PRESSURE_REDUCER = "pressure_reducer"
    EXPANSION_JOINT = "expansion_joint"
    STRAINER = "strainer"
    CHECK_VALVE = "check_valve"
    RELIEF_VALVE = "relief_valve"
    BALL_VALVE = "ball_valve"
    GATE_VALVE = "gate_valve"
    BUTTERFLY_VALVE = "butterfly_valve"


@dataclass
class PlumbingBIMObject:
    """Base class for all plumbing BIM objects with embedded engineering logic."""

    # Core BIM properties
    id: str
    name: str
    object_type: PlumbingObjectType
    geometry: Optional[Dict[str, Any]] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Plumbing engineering parameters
    flow_rate: Optional[float] = None
    pressure: Optional[float] = None
    temperature: Optional[float] = None
    pipe_diameter: Optional[float] = None
    pipe_material: Optional[str] = None
    fixture_units: Optional[float] = None

    # Engineering analysis results (embedded)
    flow_analysis: Dict[str, Any] = field(default_factory=dict)
    pressure_analysis: Dict[str, Any] = field(default_factory=dict)
    pipe_sizing: Dict[str, Any] = field(default_factory=dict)
    fixture_analysis: Dict[str, Any] = field(default_factory=dict)
    ipc_compliance: Dict[str, Any] = field(default_factory=dict)

    # Engineering recommendations and warnings
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_analysis: Optional[datetime] = None

    def __post_init__(self):
        """Validate plumbing BIM object after initialization."""
        if not self.id:
            raise ValueError("Plumbing BIM object ID cannot be empty")
        if not self.name:
            raise ValueError("Plumbing BIM object name cannot be empty")
        if not self.object_type:
            raise ValueError("Plumbing BIM object type is required")

    async def perform_engineering_analysis(self) -> Dict[str, Any]:
        """
        Perform comprehensive plumbing engineering analysis on this object.

        This method embeds real plumbing engineering calculations directly into the BIM object.

        Returns:
            Dictionary containing comprehensive plumbing engineering analysis results
        """
        try:
            # Import the plumbing logic engine
            from services.plumbing_logic_engine import PlumbingLogicEngine

            # Initialize plumbing logic engine
            plumbing_engine = PlumbingLogicEngine()

            # Convert BIM object to analysis format
            object_data = {
                "id": self.id,
                "type": self.object_type.value,
                "flow_rate": self.flow_rate,
                "pressure": self.pressure,
                "diameter": self.pipe_diameter,
                "length": getattr(self, "length", 100),
                "material": self.pipe_material,
                "fixture_type": getattr(self, "fixture_type", "unknown"),
                "fixture_count": getattr(self, "fixture_count", 1),
                "occupancy": getattr(self, "occupancy", 1),
                "elevation": getattr(self, "elevation", 0),
                "supply_pressure": getattr(self, "supply_pressure", 60),
                "equipment_type": getattr(self, "equipment_type", "plumbing"),
                "capacity": getattr(self, "capacity", 100),
                **self.properties,
            }

            # Perform comprehensive plumbing analysis
            result = await plumbing_engine.analyze_object(object_data)

            # Update embedded engineering analysis results
            self.flow_analysis = result.flow_analysis
            self.fixture_analysis = result.fixture_analysis
            self.pressure_analysis = result.pressure_analysis
            self.equipment_analysis = result.equipment_analysis
            self.ipc_compliance = result.ipc_compliance
            self.recommendations = result.recommendations
            self.warnings = result.warnings
            self.errors = result.errors

            # Update timestamp
            self.last_analysis = datetime.utcnow()
            self.updated_at = datetime.utcnow()

            return {
                "object_id": self.id,
                "object_type": self.object_type.value,
                "analysis_completed": True,
                "analysis_timestamp": self.last_analysis.isoformat(),
                "flow_analysis": self.flow_analysis,
                "fixture_analysis": self.fixture_analysis,
                "pressure_analysis": self.pressure_analysis,
                "equipment_analysis": self.equipment_analysis,
                "ipc_compliance": self.ipc_compliance,
                "recommendations": self.recommendations,
                "warnings": self.warnings,
                "errors": self.errors,
            }

        except Exception as e:
            # Handle analysis errors gracefully
            self.errors.append(f"Plumbing engineering analysis failed: {str(e)}")
            self.last_analysis = datetime.utcnow()
            self.updated_at = datetime.utcnow()

            return {
                "object_id": self.id,
                "object_type": self.object_type.value,
                "analysis_completed": False,
                "error": str(e),
                "analysis_timestamp": self.last_analysis.isoformat(),
            }

    def get_engineering_summary(self) -> Dict[str, Any]:
        """Get a summary of engineering analysis results."""
        return {
            "object_id": self.id,
            "object_type": self.object_type.value,
            "name": self.name,
            "flow_rate": self.flow_rate,
            "pressure": self.pressure,
            "pipe_diameter": self.pipe_diameter,
            "has_flow_analysis": bool(self.flow_analysis),
            "has_pressure_analysis": bool(self.pressure_analysis),
            "has_pipe_sizing": bool(self.pipe_sizing),
            "has_fixture_analysis": bool(self.fixture_analysis),
            "has_ipc_compliance": bool(self.ipc_compliance),
            "recommendations_count": len(self.recommendations),
            "warnings_count": len(self.warnings),
            "errors_count": len(self.errors),
            "last_analysis": (
                self.last_analysis.isoformat() if self.last_analysis else None
            ),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert plumbing BIM object to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "object_type": self.object_type.value,
            "geometry": self.geometry,
            "properties": self.properties,
            "metadata": self.metadata,
            "flow_rate": self.flow_rate,
            "pressure": self.pressure,
            "temperature": self.temperature,
            "pipe_diameter": self.pipe_diameter,
            "pipe_material": self.pipe_material,
            "fixture_units": self.fixture_units,
            "flow_analysis": self.flow_analysis,
            "pressure_analysis": self.pressure_analysis,
            "pipe_sizing": self.pipe_sizing,
            "fixture_analysis": self.fixture_analysis,
            "ipc_compliance": self.ipc_compliance,
            "recommendations": self.recommendations,
            "warnings": self.warnings,
            "errors": self.errors,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_analysis": (
                self.last_analysis.isoformat() if self.last_analysis else None
            ),
        }


# Specific plumbing BIM object classes
@dataclass
class PlumbingPipe(PlumbingBIMObject):
    """Plumbing pipe BIM object with embedded engineering logic."""

    pipe_type: str = "water"
    length: Optional[float] = None
    slope: Optional[float] = None
    roughness: Optional[float] = None

    def __post_init__(self):
        super().__post_init__()
        self.object_type = PlumbingObjectType.PIPE


@dataclass
class PlumbingValve(PlumbingBIMObject):
    """Plumbing valve BIM object with embedded engineering logic."""

    valve_type: str = "ball"
    position: Optional[float] = None  # 0.0 to 1.0
    is_automatic: bool = False
    actuator_type: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        self.object_type = PlumbingObjectType.VALVE


@dataclass
class PlumbingFixture(PlumbingBIMObject):
    """Plumbing fixture BIM object with embedded engineering logic."""

    fixture_type: str = "sink"
    water_consumption: Optional[float] = None
    waste_flow_rate: Optional[float] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        self.object_type = PlumbingObjectType.FIXTURE


@dataclass
class PlumbingPump(PlumbingBIMObject):
    """Plumbing pump BIM object with embedded engineering logic."""

    pump_type: str = "centrifugal"
    head: Optional[float] = None
    efficiency: Optional[float] = None
    motor_horsepower: Optional[float] = None

    def __post_init__(self):
        super().__post_init__()
        self.object_type = PlumbingObjectType.PUMP


@dataclass
class PlumbingDrain(PlumbingBIMObject):
    """Plumbing drain BIM object with embedded engineering logic."""

    drain_type: str = "floor"
    slope: Optional[float] = None
    material: Optional[str] = None
    size: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        self.object_type = PlumbingObjectType.DRAIN
