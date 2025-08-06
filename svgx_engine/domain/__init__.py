"""
Domain Layer - Core Domain Models and Business Logic

This module contains the core domain models, entities, value objects,
aggregates, repositories, services, and events that implement the
business logic and rules of the SVGX Engine.
"""

# Domain Entities - BIM Objects with Embedded Engineering Logic
from domain.entities.bim_objects import (
    # Electrical BIM Objects
    ElectricalObjectType,
    ElectricalBIMObject,
    ElectricalOutlet,
    ElectricalPanel,
    ElectricalSwitch,
    ElectricalTransformer,
    ElectricalBreaker,
    ElectricalLight,
    # HVAC BIM Objects
    HVACObjectType,
    HVACBIMObject,
    HVACDuct,
    HVACDamper,
    HVACDiffuser,
    HVACFan,
    HVACThermostat,
    # Plumbing BIM Objects
    PlumbingObjectType,
    PlumbingBIMObject,
    PlumbingPipe,
    PlumbingValve,
    PlumbingFixture,
    PlumbingPump,
    PlumbingDrain,
    # Structural BIM Objects
    StructuralObjectType,
    StructuralBIMObject,
    StructuralBeam,
    StructuralColumn,
    StructuralWall,
    StructuralSlab,
    StructuralFoundation,
)

# Domain Value Objects - Engineering Parameters and Code Compliance
from domain.value_objects import (
    # Engineering Parameters
    ParameterType,
    EngineeringParameter,
    ElectricalParameter,
    HVACParameter,
    PlumbingParameter,
    StructuralParameter,
    VoltageParameter,
    CurrentParameter,
    PowerParameter,
    CapacityParameter,
    AirflowParameter,
    FlowRateParameter,
    PressureParameter,
    LoadParameter,
    LengthParameter,
    # Code Compliance
    CodeStandard,
    ComplianceStatus,
    CodeRequirement,
    ComplianceCheck,
    CodeCompliance,
    NECRequirement,
    ASHRAERequirement,
    IPCRequirement,
    IBCRequirement,
    NECOutletRequirement,
    ASHRAEThermostatRequirement,
    IPCFixtureRequirement,
    IBCStructuralRequirement,
)

# Version and metadata
__version__ = "2.0.0"
__description__ = "Domain layer for SVGX Engine with embedded engineering logic"

# Export all domain components
__all__ = [
    # Electrical BIM Objects
    "ElectricalObjectType",
    "ElectricalBIMObject",
    "ElectricalOutlet",
    "ElectricalPanel",
    "ElectricalSwitch",
    "ElectricalTransformer",
    "ElectricalBreaker",
    "ElectricalLight",
    # HVAC BIM Objects
    "HVACObjectType",
    "HVACBIMObject",
    "HVACDuct",
    "HVACDamper",
    "HVACDiffuser",
    "HVACFan",
    "HVACThermostat",
    # Plumbing BIM Objects
    "PlumbingObjectType",
    "PlumbingBIMObject",
    "PlumbingPipe",
    "PlumbingValve",
    "PlumbingFixture",
    "PlumbingPump",
    "PlumbingDrain",
    # Structural BIM Objects
    "StructuralObjectType",
    "StructuralBIMObject",
    "StructuralBeam",
    "StructuralColumn",
    "StructuralWall",
    "StructuralSlab",
    "StructuralFoundation",
    # Engineering Parameters
    "ParameterType",
    "EngineeringParameter",
    "ElectricalParameter",
    "HVACParameter",
    "PlumbingParameter",
    "StructuralParameter",
    "VoltageParameter",
    "CurrentParameter",
    "PowerParameter",
    "CapacityParameter",
    "AirflowParameter",
    "FlowRateParameter",
    "PressureParameter",
    "LoadParameter",
    "LengthParameter",
    # Code Compliance
    "CodeStandard",
    "ComplianceStatus",
    "CodeRequirement",
    "ComplianceCheck",
    "CodeCompliance",
    "NECRequirement",
    "ASHRAERequirement",
    "IPCRequirement",
    "IBCRequirement",
    "NECOutletRequirement",
    "ASHRAEThermostatRequirement",
    "IPCFixtureRequirement",
    "IBCStructuralRequirement",
]
