"""
MCP Data Models for Arxos Platform

This module defines the data models used throughout the MCP system for
rule validation, compliance checking, and report generation.
"""

import json
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class RuleSeverity(Enum):
    """Rule severity levels"""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class RuleCategory(Enum):
    """Rule categories for building codes"""

    ELECTRICAL_SAFETY = "electrical_safety"
    ELECTRICAL_DESIGN = "electrical_design"
    PLUMBING_WATER_SUPPLY = "plumbing_water_supply"
    PLUMBING_DRAINAGE = "plumbing_drainage"
    MECHANICAL_HVAC = "mechanical_hvac"
    MECHANICAL_VENTILATION = "mechanical_ventilation"
    STRUCTURAL_LOADS = "structural_loads"
    STRUCTURAL_MATERIALS = "structural_materials"
    FIRE_SAFETY_EGRESS = "fire_safety_egress"
    FIRE_SAFETY_RESISTANCE = "fire_safety_resistance"
    ACCESSIBILITY = "accessibility"
    ENERGY_EFFICIENCY = "energy_efficiency"
    ENVIRONMENTAL = "environmental"
    GENERAL = "general"


class ConditionType(Enum):
    """Condition types for rule evaluation"""

    PROPERTY = "property"
    SPATIAL = "spatial"
    RELATIONSHIP = "relationship"
    SYSTEM = "system"
    COMPOSITE = "composite"


class ActionType(Enum):
    """Action types for rule execution"""

    VALIDATION = "validation"
    CALCULATION = "calculation"
    WARNING = "warning"
    ERROR = "error"
    MODIFICATION = "modification"
    NOTIFICATION = "notification"


@dataclass
class Jurisdiction:
    """Jurisdiction information for MCP files"""

    country: str
    state: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "country": self.country,
            "state": self.state,
            "city": self.city,
            "county": self.county,
        }


@dataclass
class RuleCondition:
    """Rule condition for evaluation"""

    type: ConditionType
    element_type: Optional[str] = None
    property: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[Any] = None
    relationship: Optional[str] = None
    target_type: Optional[str] = None
    conditions: Optional[List["RuleCondition"]] = None
    composite_operator: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "type": self.type.value,
            "element_type": self.element_type,
            "property": self.property,
            "operator": self.operator,
            "value": self.value,
            "relationship": self.relationship,
            "target_type": self.target_type,
            "composite_operator": self.composite_operator,
        }

        if self.conditions:
            result["conditions"] = [c.to_dict() for c in self.conditions]

        return result


@dataclass
class RuleAction:
    """Rule action for execution"""

    type: ActionType
    message: Optional[str] = None
    severity: Optional[RuleSeverity] = None
    code_reference: Optional[str] = None
    formula: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "type": self.type.value,
            "message": self.message,
            "severity": self.severity.value if self.severity else None,
            "code_reference": self.code_reference,
            "formula": self.formula,
            "unit": self.unit,
            "description": self.description,
            "parameters": self.parameters,
        }
        return {k: v for k, v in result.items() if v is not None}


@dataclass
class MCPRule:
    """MCP rule definition"""

    rule_id: str
    name: str
    description: str
    category: RuleCategory
    priority: int = 1
    conditions: List[RuleCondition] = field(default_factory=list)
    actions: List[RuleAction] = field(default_factory=list)
    enabled: bool = True
    version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "priority": self.priority,
            "conditions": [c.to_dict() for c in self.conditions],
            "actions": [a.to_dict() for a in self.actions],
            "enabled": self.enabled,
            "version": self.version,
            "metadata": self.metadata,
        }


@dataclass
class MCPMetadata:
    """MCP file metadata"""

    source: str
    website: Optional[str] = None
    contact: Optional[str] = None
    notes: Optional[str] = None
    last_updated: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "source": self.source,
            "website": self.website,
            "contact": self.contact,
            "notes": self.notes,
        }

        if self.last_updated:
            result["last_updated"] = self.last_updated.isoformat()

        return {k: v for k, v in result.items() if v is not None}


@dataclass
class MCPFile:
    """MCP file definition"""

    mcp_id: str
    name: str
    description: str
    jurisdiction: Jurisdiction
    version: str
    effective_date: str
    rules: List[MCPRule] = field(default_factory=list)
    metadata: Optional[MCPMetadata] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "mcp_id": self.mcp_id,
            "name": self.name,
            "description": self.description,
            "jurisdiction": self.jurisdiction.to_dict(),
            "version": self.version,
            "effective_date": self.effective_date,
            "rules": [r.to_dict() for r in self.rules],
        }

        if self.metadata:
            result["metadata"] = self.metadata.to_dict()

        return result


@dataclass
class ValidationViolation:
    """Validation violation result"""

    rule_id: str
    rule_name: str
    category: RuleCategory
    severity: RuleSeverity
    message: str
    code_reference: Optional[str] = None
    element_id: Optional[str] = None
    element_type: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    calculated_value: Optional[Any] = None
    expected_value: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "code_reference": self.code_reference,
            "element_id": self.element_id,
            "element_type": self.element_type,
            "location": self.location,
            "calculated_value": self.calculated_value,
            "expected_value": self.expected_value,
            "timestamp": self.timestamp.isoformat(),
        }
        return {k: v for k, v in result.items() if v is not None}


@dataclass
class ValidationResult:
    """Validation result for a single rule"""

    rule_id: str
    rule_name: str
    category: RuleCategory
    passed: bool
    violations: List[ValidationViolation] = field(default_factory=list)
    warnings: List[ValidationViolation] = field(default_factory=list)
    calculations: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "category": self.category.value,
            "passed": self.passed,
            "violations": [v.to_dict() for v in self.violations],
            "warnings": [w.to_dict() for w in self.warnings],
            "calculations": self.calculations,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class MCPValidationReport:
    """Complete MCP validation report"""

    mcp_id: str
    mcp_name: str
    jurisdiction: Jurisdiction
    validation_date: datetime
    total_rules: int
    passed_rules: int
    failed_rules: int
    total_violations: int
    total_warnings: int
    results: List[ValidationResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "mcp_id": self.mcp_id,
            "mcp_name": self.mcp_name,
            "jurisdiction": self.jurisdiction.to_dict(),
            "validation_date": self.validation_date.isoformat(),
            "total_rules": self.total_rules,
            "passed_rules": self.passed_rules,
            "failed_rules": self.failed_rules,
            "total_violations": self.total_violations,
            "total_warnings": self.total_warnings,
            "results": [r.to_dict() for r in self.results],
            "summary": self.summary,
            "metadata": self.metadata,
        }


@dataclass
class ComplianceReport:
    """Comprehensive compliance report"""

    building_id: str
    building_name: str
    validation_reports: List[MCPValidationReport] = field(default_factory=list)
    overall_compliance_score: float = 0.0
    critical_violations: int = 0
    total_violations: int = 0
    total_warnings: int = 0
    recommendations: List[str] = field(default_factory=list)
    generated_date: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "building_id": self.building_id,
            "building_name": self.building_name,
            "validation_reports": [r.to_dict() for r in self.validation_reports],
            "overall_compliance_score": self.overall_compliance_score,
            "critical_violations": self.critical_violations,
            "total_violations": self.total_violations,
            "total_warnings": self.total_warnings,
            "recommendations": self.recommendations,
            "generated_date": self.generated_date.isoformat(),
        }


@dataclass
class BuildingObject:
    """Building object for validation"""

    object_id: str
    object_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    location: Optional[Dict[str, Any]] = None
    connections: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "object_id": self.object_id,
            "object_type": self.object_type,
            "properties": self.properties,
            "location": self.location,
            "connections": self.connections,
            "metadata": self.metadata,
        }


@dataclass
class BuildingModel:
    """Building model for validation"""

    building_id: str
    building_name: str
    objects: List[BuildingObject] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "building_id": self.building_id,
            "building_name": self.building_name,
            "objects": [o.to_dict() for o in self.objects],
            "metadata": self.metadata,
        }


@dataclass
class ValidationRequest:
    """Validation request for building model"""

    building_model: BuildingModel
    jurisdiction: Optional[str] = None
    include_suggestions: bool = True
    confidence_threshold: float = 0.7
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "building_model": self.building_model.to_dict(),
            "jurisdiction": self.jurisdiction,
            "include_suggestions": self.include_suggestions,
            "confidence_threshold": self.confidence_threshold,
            "metadata": self.metadata,
        }


@dataclass
class ValidationResponse:
    """Validation response for building model"""

    building_id: str
    validation_date: datetime
    overall_compliance_score: float
    total_violations: int
    total_warnings: int
    critical_violations: int
    results: List[ValidationResult] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "building_id": self.building_id,
            "validation_date": self.validation_date.isoformat(),
            "overall_compliance_score": self.overall_compliance_score,
            "total_violations": self.total_violations,
            "total_warnings": self.total_warnings,
            "critical_violations": self.critical_violations,
            "results": [r.to_dict() for r in self.results],
            "recommendations": self.recommendations,
            "metadata": self.metadata,
        }


# Utility functions for model serialization
def serialize_mcp_file(mcp_file: MCPFile) -> str:
    """Serialize MCP file to JSON string"""
    return json.dumps(mcp_file.to_dict(), indent=2)


def deserialize_mcp_file(json_str: str) -> MCPFile:
    """Deserialize JSON string to MCP file"""
    data = json.loads(json_str)
    return _dict_to_mcp_file(data)


def _dict_to_mcp_file(data: Dict[str, Any]) -> MCPFile:
    """Convert dictionary to MCP file"""
    jurisdiction = Jurisdiction(**data["jurisdiction"])

    rules = []
    for rule_data in data.get("rules", []):
        rules.append(_dict_to_mcp_rule(rule_data))

    metadata = None
    if "metadata" in data:
        metadata = MCPMetadata(**data["metadata"])

    return MCPFile(
        mcp_id=data["mcp_id"],
        name=data["name"],
        description=data["description"],
        jurisdiction=jurisdiction,
        version=data["version"],
        effective_date=data["effective_date"],
        rules=rules,
        metadata=metadata,
    )


def _dict_to_mcp_rule(data: Dict[str, Any]) -> MCPRule:
    """Convert dictionary to MCP rule"""
    category = RuleCategory(data["category"])

    conditions = []
    for condition_data in data.get("conditions", []):
        conditions.append(_dict_to_rule_condition(condition_data))

    actions = []
    for action_data in data.get("actions", []):
        actions.append(_dict_to_rule_action(action_data))

    return MCPRule(
        rule_id=data["rule_id"],
        name=data["name"],
        description=data["description"],
        category=category,
        priority=data.get("priority", 1),
        conditions=conditions,
        actions=actions,
        enabled=data.get("enabled", True),
        version=data.get("version", "1.0"),
        metadata=data.get("metadata", {}),
    )


def _dict_to_rule_condition(data: Dict[str, Any]) -> RuleCondition:
    """Convert dictionary to rule condition"""
    condition_type = ConditionType(data["type"])

    conditions = None
    if "conditions" in data:
        conditions = [_dict_to_rule_condition(c) for c in data["conditions"]]

    return RuleCondition(
        type=condition_type,
        element_type=data.get("element_type"),
        property=data.get("property"),
        operator=data.get("operator"),
        value=data.get("value"),
        relationship=data.get("relationship"),
        target_type=data.get("target_type"),
        conditions=conditions,
        composite_operator=data.get("composite_operator"),
    )


def _dict_to_rule_action(data: Dict[str, Any]) -> RuleAction:
    """Convert dictionary to rule action"""
    action_type = ActionType(data["type"])

    severity = None
    if "severity" in data:
        severity = RuleSeverity(data["severity"])

    return RuleAction(
        type=action_type,
        message=data.get("message"),
        severity=severity,
        code_reference=data.get("code_reference"),
        formula=data.get("formula"),
        unit=data.get("unit"),
        description=data.get("description"),
        parameters=data.get("parameters"),
    )
