"""
Arxos NLP Integration Package

This package provides natural language processing capabilities for the Arxos Platform,
enabling users to interact with building data and systems using natural language.

Key Components:
- NLP Router: Main entry point for NLP processing
- Intent Detection: Identify user intentions from natural language
- Slot Filling: Extract parameters from natural language input
- CLI Translation: Convert NLP results to ArxCLI commands
- Context Management: Handle contextual object resolution
"""

from services.nlp_router
from services.intent_mapper
from services.models.nlp_models
    NLPRequest, NLPResponse, Intent, Slot, SlotResult, CLICommand,
    NLPContext, ValidationResult, ProcessingStats,
    IntentType, SlotType
)

__version__ = "1.0.0"
__author__ = "Arxos Platform Team"
__description__ = "NLP Integration for Arxos Platform"

# Main classes for easy import
__all__ = [
    "NLPRouter",
    "IntentMapper", 
    "process_nlp_input",
    "detect_intent",
    "NLPRequest",
    "NLPResponse", 
    "Intent",
    "Slot",
    "SlotResult",
    "CLICommand",
    "NLPContext",
    "ValidationResult",
    "ProcessingStats",
    "IntentType",
    "SlotType"
] 