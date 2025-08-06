#!/usr/bin/env python3
"""
MCP Intelligence Layer

This module provides intelligent context analysis, suggestions, and proactive monitoring
for the MCP (Model Context Protocol) service. It serves as the "smart assistant" layer
that provides real-time guidance and validation for building design.
"""

from .intelligence_service import MCPIntelligenceService
from .context_analyzer import ContextAnalyzer
from .suggestion_engine import SuggestionEngine
from .proactive_monitor import ProactiveMonitor
from .models import (
    IntelligenceContext,
    UserIntent,
    ModelContext,
    Suggestion,
    Alert,
    Improvement,
    Conflict,
    ValidationResult,
    CodeReference,
)

__all__ = [
    "MCPIntelligenceService",
    "ContextAnalyzer",
    "SuggestionEngine",
    "ProactiveMonitor",
    "IntelligenceContext",
    "UserIntent",
    "ModelContext",
    "Suggestion",
    "Alert",
    "Improvement",
    "Conflict",
    "ValidationResult",
    "CodeReference",
]

__version__ = "1.0.0"
