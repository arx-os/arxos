"""
SVGX Engine - Code Compliance Value Objects

Value objects for building code compliance across all systems.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum


class CodeStandard(Enum):
    """Building code standards."""

    NEC = "nec"  # National Electrical Code
    ASHRAE = "ashrae"  # ASHRAE Standards
    IPC = "ipc"  # International Plumbing Code
    IBC = "ibc"  # International Building Code


class ComplianceStatus(Enum):
    """Code compliance status."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    CONDITIONAL = "conditional"
    UNKNOWN = "unknown"


@dataclass
class CodeRequirement:
    """Building code requirement."""

    code_standard: CodeStandard
    section: str
    requirement: str
    description: str
    is_mandatory: bool = True

    def __post_init__(self):
        """Validate code requirement after initialization."""
        if not self.section:
            raise ValueError("Code section cannot be empty")
        if not self.requirement:
            raise ValueError("Code requirement cannot be empty")
        if not self.description:
            raise ValueError("Code description cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert code requirement to dictionary."""
        return {
            "code_standard": self.code_standard.value,
            "section": self.section,
            "requirement": self.requirement,
            "description": self.description,
            "is_mandatory": self.is_mandatory,
        }


@dataclass
class ComplianceCheck:
    """Code compliance check result."""

    requirement: CodeRequirement
    status: ComplianceStatus
    details: str
    violations: List[str] = None
    recommendations: List[str] = None

    def __post_init__(self):
        if self.violations is None:
            self.violations = []
        if self.recommendations is None:
            self.recommendations = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert compliance check to dictionary."""
        return {
            "requirement": self.requirement.to_dict(),
            "status": self.status.value,
            "details": self.details,
            "violations": self.violations,
            "recommendations": self.recommendations,
        }


@dataclass
class CodeCompliance:
    """Complete code compliance assessment."""

    object_id: str
    object_type: str
    code_standard: CodeStandard
    overall_status: ComplianceStatus
    checks: List[ComplianceCheck]
    violations_count: int
    recommendations_count: int
    assessment_date: str

    def __post_init__(self):
        """Validate code compliance after initialization."""
        if not self.object_id:
            raise ValueError("Object ID cannot be empty")
        if not self.object_type:
            raise ValueError("Object type cannot be empty")
        if not self.checks:
            raise ValueError("Compliance checks cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert code compliance to dictionary."""
        return {
            "object_id": self.object_id,
            "object_type": self.object_type,
            "code_standard": self.code_standard.value,
            "overall_status": self.overall_status.value,
            "checks": [check.to_dict() for check in self.checks],
            "violations_count": self.violations_count,
            "recommendations_count": self.recommendations_count,
            "assessment_date": self.assessment_date,
        }


# Common code requirements
@dataclass
class NECRequirement(CodeRequirement):
    """NEC (National Electrical Code) requirement."""

    def __post_init__(self):
        self.code_standard = CodeStandard.NEC
        super().__post_init__()


@dataclass
class ASHRAERequirement(CodeRequirement):
    """ASHRAE requirement."""

    def __post_init__(self):
        self.code_standard = CodeStandard.ASHRAE
        super().__post_init__()


@dataclass
class IPCRequirement(CodeRequirement):
    """IPC (International Plumbing Code) requirement."""

    def __post_init__(self):
        self.code_standard = CodeStandard.IPC
        super().__post_init__()


@dataclass
class IBCRequirement(CodeRequirement):
    """IBC (International Building Code) requirement."""

    def __post_init__(self):
        self.code_standard = CodeStandard.IBC
        super().__post_init__()


# Specific code requirements
@dataclass
class NECOutletRequirement(NECRequirement):
    """NEC requirement for electrical outlets."""

    def __post_init__(self):
        self.section = "210.52"
        self.requirement = "Receptacle Outlets Required"
        self.description = "Receptacle outlets shall be installed in every kitchen, family room, dining room, living room, parlor, library, den, sunroom, bedroom, recreation room, or similar room or area."
        super().__post_init__()


@dataclass
class ASHRAEThermostatRequirement(ASHRAERequirement):
    """ASHRAE requirement for thermostats."""

    def __post_init__(self):
        self.section = "5.4.1"
        self.requirement = "Thermostat Control"
        self.description = "Each zone shall be provided with a thermostat to control the heating and cooling equipment."
        super().__post_init__()


@dataclass
class IPCFixtureRequirement(IPCRequirement):
    """IPC requirement for plumbing fixtures."""

    def __post_init__(self):
        self.section = "709.1"
        self.requirement = "Fixture Requirements"
        self.description = "Plumbing fixtures shall be installed in accordance with the manufacturer's instructions and this code."
        super().__post_init__()


@dataclass
class IBCStructuralRequirement(IBCRequirement):
    """IBC requirement for structural elements."""

    def __post_init__(self):
        self.section = "1604.1"
        self.requirement = "Structural Design"
        self.description = "Structural systems and members thereof shall be designed to have adequate stiffness, strength and stability."
        super().__post_init__()
