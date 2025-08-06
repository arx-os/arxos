"""
MCP Data Models Package

This package contains all data models for the MCP (Model Context Protocol) system,
including models for MCP files, rules, validation results, and compliance reports.
"""

from .mcp_models import (
    # Enums
    RuleSeverity,
    RuleCategory,
    ConditionType,
    ActionType,
    # Core models
    Jurisdiction,
    RuleCondition,
    RuleAction,
    MCPRule,
    MCPMetadata,
    MCPFile,
    # Validation models
    ValidationViolation,
    ValidationResult,
    MCPValidationReport,
    ComplianceReport,
    # Building models
    BuildingObject,
    BuildingModel,
    # Utility functions
    serialize_mcp_file,
    deserialize_mcp_file,
)

__all__ = [
    "RuleSeverity",
    "RuleCategory",
    "ConditionType",
    "ActionType",
    "Jurisdiction",
    "RuleCondition",
    "RuleAction",
    "MCPRule",
    "MCPMetadata",
    "MCPFile",
    "ValidationViolation",
    "ValidationResult",
    "MCPValidationReport",
    "ComplianceReport",
    "BuildingObject",
    "BuildingModel",
    "serialize_mcp_file",
    "deserialize_mcp_file",
]
