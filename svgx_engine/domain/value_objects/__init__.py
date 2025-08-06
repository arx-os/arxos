"""
SVGX Engine - Value Objects Package

This package contains value objects for engineering parameters and code compliance.
"""

from .engineering_parameters import (
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
)

from .code_compliance import (
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

__all__ = [
    # Engineering parameters
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
    # Code compliance
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
