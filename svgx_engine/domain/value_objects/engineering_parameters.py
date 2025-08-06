"""
SVGX Engine - Engineering Parameters Value Objects

Value objects for engineering parameters across all building systems.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum


class ParameterType(Enum):
    """Types of engineering parameters."""

    ELECTRICAL = "electrical"
    HVAC = "hvac"
    PLUMBING = "plumbing"
    STRUCTURAL = "structural"


@dataclass
class EngineeringParameter:
    """Base class for engineering parameters."""

    name: str
    value: float
    unit: str
    parameter_type: ParameterType
    description: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    is_required: bool = True

    def __post_init__(self):
        """Validate engineering parameter after initialization."""
        if not self.name:
            raise ValueError("Parameter name cannot be empty")
        if not self.unit:
            raise ValueError("Parameter unit cannot be empty")
        if self.min_value is not None and self.value < self.min_value:
            raise ValueError(
                f"Parameter value {self.value} is below minimum {self.min_value}"
            )
        if self.max_value is not None and self.value > self.max_value:
            raise ValueError(
                f"Parameter value {self.value} is above maximum {self.max_value}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert parameter to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "parameter_type": self.parameter_type.value,
            "description": self.description,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "is_required": self.is_required,
        }


@dataclass
class ElectricalParameter(EngineeringParameter):
    """Electrical engineering parameter."""

    def __post_init__(self):
        self.parameter_type = ParameterType.ELECTRICAL
        super().__post_init__()


@dataclass
class HVACParameter(EngineeringParameter):
    """HVAC engineering parameter."""

    def __post_init__(self):
        self.parameter_type = ParameterType.HVAC
        super().__post_init__()


@dataclass
class PlumbingParameter(EngineeringParameter):
    """Plumbing engineering parameter."""

    def __post_init__(self):
        self.parameter_type = ParameterType.PLUMBING
        super().__post_init__()


@dataclass
class StructuralParameter(EngineeringParameter):
    """Structural engineering parameter."""

    def __post_init__(self):
        self.parameter_type = ParameterType.STRUCTURAL
        super().__post_init__()


# Common electrical parameters
@dataclass
class VoltageParameter(ElectricalParameter):
    """Voltage parameter for electrical systems."""

    def __post_init__(self):
        self.name = "voltage"
        self.unit = "V"
        self.min_value = 0
        self.max_value = 1000000
        super().__post_init__()


@dataclass
class CurrentParameter(ElectricalParameter):
    """Current parameter for electrical systems."""

    def __post_init__(self):
        self.name = "current"
        self.unit = "A"
        self.min_value = 0
        self.max_value = 100000
        super().__post_init__()


@dataclass
class PowerParameter(ElectricalParameter):
    """Power parameter for electrical systems."""

    def __post_init__(self):
        self.name = "power"
        self.unit = "W"
        self.min_value = 0
        self.max_value = 10000000
        super().__post_init__()


# Common HVAC parameters
@dataclass
class CapacityParameter(HVACParameter):
    """Capacity parameter for HVAC systems."""

    def __post_init__(self):
        self.name = "capacity"
        self.unit = "BTU/h"
        self.min_value = 0
        self.max_value = 1000000
        super().__post_init__()


@dataclass
class AirflowParameter(HVACParameter):
    """Airflow parameter for HVAC systems."""

    def __post_init__(self):
        self.name = "airflow"
        self.unit = "CFM"
        self.min_value = 0
        self.max_value = 100000
        super().__post_init__()


# Common plumbing parameters
@dataclass
class FlowRateParameter(PlumbingParameter):
    """Flow rate parameter for plumbing systems."""

    def __post_init__(self):
        self.name = "flow_rate"
        self.unit = "GPM"
        self.min_value = 0
        self.max_value = 10000
        super().__post_init__()


@dataclass
class PressureParameter(PlumbingParameter):
    """Pressure parameter for plumbing systems."""

    def __post_init__(self):
        self.name = "pressure"
        self.unit = "PSI"
        self.min_value = 0
        self.max_value = 1000
        super().__post_init__()


# Common structural parameters
@dataclass
class LoadParameter(StructuralParameter):
    """Load parameter for structural systems."""

    def __post_init__(self):
        self.name = "load"
        self.unit = "lb"
        self.min_value = 0
        self.max_value = 1000000
        super().__post_init__()


@dataclass
class LengthParameter(StructuralParameter):
    """Length parameter for structural systems."""

    def __post_init__(self):
        self.name = "length"
        self.unit = "ft"
        self.min_value = 0
        self.max_value = 10000
        super().__post_init__()
