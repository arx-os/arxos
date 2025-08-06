"""
SVGX Engine - HVAC BIM Objects

HVAC BIM objects with embedded engineering logic.
Each object has its own engineering analysis capabilities.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class HVACObjectType(Enum):
    """HVAC BIM object types with embedded engineering logic."""

    DUCT = "duct"
    DAMPER = "damper"
    DIFFUSER = "diffuser"
    GRILLE = "grille"
    COIL = "coil"
    FAN = "fan"
    PUMP = "pump"
    VALVE = "valve"
    FILTER = "filter"
    HEATER = "heater"
    COOLER = "cooler"
    THERMOSTAT = "thermostat"
    ACTUATOR = "actuator"
    COMPRESSOR = "compressor"
    CONDENSER = "condenser"
    EVAPORATOR = "evaporator"
    CHILLER = "chiller"
    BOILER = "boiler"
    HEAT_EXCHANGER = "heat_exchanger"


@dataclass
class HVACBIMObject:
    """Base class for all HVAC BIM objects with embedded engineering logic."""

    # Core BIM properties
    id: str
    name: str
    object_type: HVACObjectType
    geometry: Optional[Dict[str, Any]] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # HVAC engineering parameters
    capacity: Optional[float] = None
    airflow: Optional[float] = None
    efficiency: Optional[float] = None
    temperature_setpoint: Optional[float] = None
    humidity_setpoint: Optional[float] = None
    pressure_drop: Optional[float] = None

    # Engineering analysis results (embedded)
    thermal_analysis: Dict[str, Any] = field(default_factory=dict)
    airflow_analysis: Dict[str, Any] = field(default_factory=dict)
    energy_analysis: Dict[str, Any] = field(default_factory=dict)
    equipment_analysis: Dict[str, Any] = field(default_factory=dict)
    ashrae_compliance: Dict[str, Any] = field(default_factory=dict)

    # Engineering recommendations and warnings
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_analysis: Optional[datetime] = None

    def __post_init__(self):
        """Validate HVAC BIM object after initialization."""
        if not self.id:
            raise ValueError("HVAC BIM object ID cannot be empty")
        if not self.name:
            raise ValueError("HVAC BIM object name cannot be empty")
        if not self.object_type:
            raise ValueError("HVAC BIM object type is required")

    async def perform_engineering_analysis(self) -> Dict[str, Any]:
        """
        Perform comprehensive HVAC engineering analysis on this object.

        This method embeds real HVAC engineering calculations directly into the BIM object.

        Returns:
            Dictionary containing comprehensive HVAC engineering analysis results
        """
        try:
            # Import the HVAC logic engine
            from services.hvac_logic_engine import HVACLogicEngine

            # Initialize HVAC logic engine
            hvac_engine = HVACLogicEngine()

            # Convert BIM object to analysis format
            object_data = {
                "id": self.id,
                "type": self.object_type.value,
                "capacity": self.capacity,
                "airflow": self.airflow,
                "efficiency": self.efficiency,
                "temperature_setpoint": self.temperature_setpoint,
                "humidity_setpoint": self.humidity_setpoint,
                "pressure_drop": self.pressure_drop,
                "area": getattr(self, "area", 1000),
                "height": getattr(self, "height", 10),
                "space_type": getattr(self, "space_type", "office_space"),
                "occupancy": getattr(self, "occupancy", 1),
                "diameter": getattr(self, "diameter", 12),
                "length": getattr(self, "length", 50),
                "material": getattr(self, "material", "galvanized_steel"),
                "equipment_type": getattr(self, "equipment_type", "hvac"),
                "power_input": getattr(self, "power_input", 5000),
                **self.properties,
            }

            # Perform comprehensive HVAC analysis
            result = await hvac_engine.analyze_object(object_data)

            # Update embedded engineering analysis results
            self.thermal_analysis = result.thermal_analysis
            self.airflow_analysis = result.airflow_analysis
            self.energy_analysis = result.energy_analysis
            self.equipment_analysis = result.equipment_analysis
            self.ashrae_compliance = result.ashrae_compliance
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
                "thermal_analysis": self.thermal_analysis,
                "airflow_analysis": self.airflow_analysis,
                "energy_analysis": self.energy_analysis,
                "equipment_analysis": self.equipment_analysis,
                "ashrae_compliance": self.ashrae_compliance,
                "recommendations": self.recommendations,
                "warnings": self.warnings,
                "errors": self.errors,
            }

        except Exception as e:
            # Handle analysis errors gracefully
            self.errors.append(f"HVAC engineering analysis failed: {str(e)}")
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
            "capacity": self.capacity,
            "airflow": self.airflow,
            "efficiency": self.efficiency,
            "has_thermal_analysis": bool(self.thermal_analysis),
            "has_airflow_analysis": bool(self.airflow_analysis),
            "has_energy_analysis": bool(self.energy_analysis),
            "has_equipment_analysis": bool(self.equipment_analysis),
            "has_ashrae_compliance": bool(self.ashrae_compliance),
            "recommendations_count": len(self.recommendations),
            "warnings_count": len(self.warnings),
            "errors_count": len(self.errors),
            "last_analysis": (
                self.last_analysis.isoformat() if self.last_analysis else None
            ),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert HVAC BIM object to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "object_type": self.object_type.value,
            "geometry": self.geometry,
            "properties": self.properties,
            "metadata": self.metadata,
            "capacity": self.capacity,
            "airflow": self.airflow,
            "efficiency": self.efficiency,
            "temperature_setpoint": self.temperature_setpoint,
            "humidity_setpoint": self.humidity_setpoint,
            "pressure_drop": self.pressure_drop,
            "thermal_analysis": self.thermal_analysis,
            "airflow_analysis": self.airflow_analysis,
            "energy_analysis": self.energy_analysis,
            "equipment_analysis": self.equipment_analysis,
            "ashrae_compliance": self.ashrae_compliance,
            "recommendations": self.recommendations,
            "warnings": self.warnings,
            "errors": self.errors,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_analysis": (
                self.last_analysis.isoformat() if self.last_analysis else None
            ),
        }


# Specific HVAC BIM object classes
@dataclass
class HVACDuct(HVACBIMObject):
    """HVAC duct BIM object with embedded engineering logic."""

    duct_type: str = "supply"
    diameter: Optional[float] = None
    length: Optional[float] = None
    material: Optional[str] = None
    insulation: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        self.object_type = HVACObjectType.DUCT


@dataclass
class HVACDamper(HVACBIMObject):
    """HVAC damper BIM object with embedded engineering logic."""

    damper_type: str = "volume"
    position: Optional[float] = None  # 0.0 to 1.0
    is_automatic: bool = False
    actuator_type: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        self.object_type = HVACObjectType.DAMPER


@dataclass
class HVACDiffuser(HVACBIMObject):
    """HVAC diffuser BIM object with embedded engineering logic."""

    diffuser_type: str = "ceiling"
    throw_distance: Optional[float] = None
    spread_pattern: Optional[str] = None
    noise_criteria: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        self.object_type = HVACObjectType.DIFFUSER


@dataclass
class HVACFan(HVACBIMObject):
    """HVAC fan BIM object with embedded engineering logic."""

    fan_type: str = "centrifugal"
    static_pressure: Optional[float] = None
    motor_horsepower: Optional[float] = None
    fan_efficiency: Optional[float] = None

    def __post_init__(self):
        super().__post_init__()
        self.object_type = HVACObjectType.FAN


@dataclass
class HVACThermostat(HVACBIMObject):
    """HVAC thermostat BIM object with embedded engineering logic."""

    thermostat_type: str = "digital"
    setpoint: Optional[float] = None
    deadband: Optional[float] = None
    is_programmable: bool = False

    def __post_init__(self):
        super().__post_init__()
        self.object_type = HVACObjectType.THERMOSTAT
