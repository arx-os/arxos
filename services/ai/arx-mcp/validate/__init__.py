"""
MCP Validation Package

This package contains the rule validation engine for checking building designs
against MCP (Model Context Protocol) rules and generating compliance reports.
"""

from services.rule_engine import services.rule_engine
__all__ = [
    'MCPRuleEngine',
    'ConditionEvaluator',
    'ActionExecutor'
]
