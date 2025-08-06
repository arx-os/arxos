"""
SVGX Engine - Electrical BIM Objects

Electrical BIM objects with embedded engineering logic.
Each object has its own engineering analysis capabilities.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class ElectricalObjectType(Enum):
    """Electrical BIM object types with embedded engineering logic."""

    OUTLET = "outlet"
    SWITCH = "switch"
    PANEL = "panel"
    TRANSFORMER = "transformer"
    BREAKER = "breaker"
    FUSE = "fuse"
    RECEPTACLE = "receptacle"
    JUNCTION = "junction"
    CONDUIT = "conduit"
    CABLE = "cable"
    WIRE = "wire"
    LIGHT = "light"
    FIXTURE = "fixture"
    SENSOR = "sensor"
    CONTROLLER = "controller"
    METER = "meter"
    GENERATOR = "generator"
    UPS = "ups"
    CAPACITOR = "capacitor"
    INDUCTOR = "inductor"


@dataclass
class ElectricalBIMObject:
    """Base class for all electrical BIM objects with embedded engineering logic."""

    # Core BIM properties
    id: str
    name: str
    object_type: ElectricalObjectType
    geometry: Optional[Dict[str, Any]] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Engineering parameters
    voltage: Optional[float] = None
    current: Optional[float] = None
    power: Optional[float] = None
    power_factor: Optional[float] = None
    resistance: Optional[float] = None
    reactance: Optional[float] = None

    # Engineering analysis results (embedded)
    circuit_analysis: Dict[str, Any] = field(default_factory=dict)
    load_calculations: Dict[str, Any] = field(default_factory=dict)
    voltage_drop_analysis: Dict[str, Any] = field(default_factory=dict)
    protection_coordination: Dict[str, Any] = field(default_factory=dict)
    harmonic_analysis: Dict[str, Any] = field(default_factory=dict)
    panel_analysis: Dict[str, Any] = field(default_factory=dict)
    safety_analysis: Dict[str, Any] = field(default_factory=dict)
    code_compliance: Dict[str, Any] = field(default_factory=dict)

    # Engineering recommendations and warnings
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_analysis: Optional[datetime] = None

    def __post_init__(self):
        """Validate electrical BIM object after initialization."""
        if not self.id:
            raise ValueError("Electrical BIM object ID cannot be empty")
        if not self.name:
            raise ValueError("Electrical BIM object name cannot be empty")
        if not self.object_type:
            raise ValueError("Electrical BIM object type is required")

    async def perform_engineering_analysis(self) -> Dict[str, Any]:
        """
        Perform comprehensive engineering analysis on this electrical object.

        This method embeds real engineering calculations directly into the BIM object.

        Returns:
            Dictionary containing comprehensive engineering analysis results
        """
        try:
            # Import the electrical logic engine
            from services.electrical_logic_engine import ElectricalLogicEngine

            # Initialize electrical logic engine
            electrical_engine = ElectricalLogicEngine()

            # Convert BIM object to analysis format
            object_data = {
                "id": self.id,
                "type": self.object_type.value,
                "voltage": self.voltage,
                "current": self.current,
                "power": self.power,
                "power_factor": self.power_factor,
                "resistance": self.resistance,
                "reactance": self.reactance,
                **self.properties,
            }

            # Perform comprehensive electrical analysis
            result = await electrical_engine.analyze_object(object_data)

            # Update embedded engineering analysis results
            self.circuit_analysis = result.circuit_analysis
            self.load_calculations = result.load_calculations
            self.voltage_drop_analysis = result.voltage_drop_analysis
            self.protection_coordination = result.protection_coordination
            self.harmonic_analysis = result.harmonic_analysis
            self.panel_analysis = result.panel_analysis
            self.safety_analysis = result.safety_analysis
            self.code_compliance = result.code_compliance
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
                "circuit_analysis": self.circuit_analysis,
                "load_calculations": self.load_calculations,
                "voltage_drop_analysis": self.voltage_drop_analysis,
                "protection_coordination": self.protection_coordination,
                "harmonic_analysis": self.harmonic_analysis,
                "panel_analysis": self.panel_analysis,
                "safety_analysis": self.safety_analysis,
                "code_compliance": self.code_compliance,
                "recommendations": self.recommendations,
                "warnings": self.warnings,
                "errors": self.errors,
            }

        except Exception as e:
            # Handle analysis errors gracefully
            self.errors.append(f"Engineering analysis failed: {str(e)}")
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
            "voltage": self.voltage,
            "current": self.current,
            "power": self.power,
            "has_circuit_analysis": bool(self.circuit_analysis),
            "has_load_calculations": bool(self.load_calculations),
            "has_voltage_drop_analysis": bool(self.voltage_drop_analysis),
            "has_protection_coordination": bool(self.protection_coordination),
            "has_harmonic_analysis": bool(self.harmonic_analysis),
            "has_panel_analysis": bool(self.panel_analysis),
            "has_safety_analysis": bool(self.safety_analysis),
            "has_code_compliance": bool(self.code_compliance),
            "recommendations_count": len(self.recommendations),
            "warnings_count": len(self.warnings),
            "errors_count": len(self.errors),
            "last_analysis": (
                self.last_analysis.isoformat() if self.last_analysis else None
            ),
        }

    def is_compliant(self) -> bool:
        """Check if this electrical object meets code compliance requirements."""
        if not self.code_compliance:
            return False
        return self.code_compliance.get("overall_compliance", False)

    def get_safety_status(self) -> str:
        """Get the safety status of this electrical object."""
        if not self.safety_analysis:
            return "unknown"
        return self.safety_analysis.get("overall_safety_status", "unknown")

    def to_dict(self) -> Dict[str, Any]:
        """Convert electrical BIM object to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "object_type": self.object_type.value,
            "geometry": self.geometry,
            "properties": self.properties,
            "metadata": self.metadata,
            "voltage": self.voltage,
            "current": self.current,
            "power": self.power,
            "power_factor": self.power_factor,
            "resistance": self.resistance,
            "reactance": self.reactance,
            "circuit_analysis": self.circuit_analysis,
            "load_calculations": self.load_calculations,
            "voltage_drop_analysis": self.voltage_drop_analysis,
            "protection_coordination": self.protection_coordination,
            "harmonic_analysis": self.harmonic_analysis,
            "panel_analysis": self.panel_analysis,
            "safety_analysis": self.safety_analysis,
            "code_compliance": self.code_compliance,
            "recommendations": self.recommendations,
            "warnings": self.warnings,
            "errors": self.errors,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_analysis": (
                self.last_analysis.isoformat() if self.last_analysis else None
            ),
        }


# Specific electrical BIM object classes
@dataclass
class ElectricalOutlet(ElectricalBIMObject):
    """Electrical outlet BIM object with embedded engineering logic."""

    outlet_type: str = "duplex"
    is_gfci: bool = False
    is_afci: bool = False
    is_emergency: bool = False
    circuit_id: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        self.object_type = ElectricalObjectType.OUTLET


@dataclass
class ElectricalPanel(ElectricalBIMObject):
    """Electrical panel BIM object with embedded engineering logic."""

    panel_type: str = "distribution"
    phase: Optional[str] = None
    circuit_count: Optional[int] = None
    available_circuits: Optional[int] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        self.object_type = ElectricalObjectType.PANEL


@dataclass
class ElectricalSwitch(ElectricalBIMObject):
    """Electrical switch BIM object with embedded engineering logic."""

    switch_type: str = "single_pole"
    is_dimmer: bool = False
    is_three_way: bool = False
    is_four_way: bool = False

    def __post_init__(self):
        super().__post_init__()
        self.object_type = ElectricalObjectType.SWITCH


@dataclass
class ElectricalTransformer(ElectricalBIMObject):
    """Electrical transformer BIM object with embedded engineering logic."""

    transformer_type: str = "distribution"
    primary_voltage: Optional[float] = None
    secondary_voltage: Optional[float] = None
    kva_rating: Optional[float] = None
    efficiency: Optional[float] = None

    def __post_init__(self):
        super().__post_init__()
        self.object_type = ElectricalObjectType.TRANSFORMER


@dataclass
class ElectricalBreaker(ElectricalBIMObject):
    """Electrical breaker BIM object with embedded engineering logic."""

    breaker_type: str = "thermal_magnetic"
    trip_rating: Optional[float] = None
    frame_size: Optional[str] = None
    is_afci: bool = False
    is_gfci: bool = False

    def __post_init__(self):
        super().__post_init__()
        self.object_type = ElectricalObjectType.BREAKER


@dataclass
class ElectricalLight(ElectricalBIMObject):
    """Electrical light BIM object with embedded engineering logic."""

    light_type: str = "led"
    wattage: Optional[float] = None
    lumens: Optional[float] = None
    color_temperature: Optional[float] = None
    is_emergency: bool = False

    def __post_init__(self):
        super().__post_init__()
        self.object_type = ElectricalObjectType.LIGHT
