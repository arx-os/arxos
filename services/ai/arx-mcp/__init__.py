"""
Arxos MCP (Model Context Protocol) Package

This package provides comprehensive regulatory compliance workflows for the Arxos Platform,
enabling automated validation of building plans against jurisdictional rules.

Key Components:
- MCP Rule Validation Engine
- Report Generation (JSON + PDF)
- Compliance Analysis and Recommendations
- Multi-jurisdiction Support
"""

from .validate.rule_engine import MCPRuleEngine
from .report.generate_report import ReportGenerator
from .models.mcp_models import (
    MCPFile, MCPRule, BuildingModel, BuildingObject,
    ComplianceReport, MCPValidationReport, ValidationResult, ValidationViolation,
    RuleSeverity, RuleCategory, ConditionType, ActionType,
    serialize_mcp_file, deserialize_mcp_file
)

__version__ = "1.0.0"
__author__ = "Arxos Platform Team"

__all__ = [
    # Main classes
    'MCPRuleEngine',
    'ReportGenerator',
    
    # Data models
    'MCPFile',
    'MCPRule', 
    'BuildingModel',
    'BuildingObject',
    'ComplianceReport',
    'MCPValidationReport',
    'ValidationResult',
    'ValidationViolation',
    
    # Enums
    'RuleSeverity',
    'RuleCategory',
    'ConditionType',
    'ActionType',
    
    # Utility functions
    'serialize_mcp_file',
    'deserialize_mcp_file'
] 