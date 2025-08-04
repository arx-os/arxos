"""
NLP Models Package

This package contains data models for NLP processing including
request/response handling, intent detection, slot filling, and CLI command generation.
"""

from .nlp_models import (
    NLPRequest, NLPResponse, Intent, Slot, SlotResult, CLICommand,
    NLPContext, ValidationResult, ProcessingStats,
    IntentType, SlotType,
    intent_from_dict, slot_from_dict, cli_command_from_dict,
    nlp_context_from_dict, nlp_response_from_dict, nlp_response_from_json
)

__all__ = [
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
    "SlotType",
    "intent_from_dict",
    "slot_from_dict",
    "cli_command_from_dict",
    "nlp_context_from_dict",
    "nlp_response_from_dict",
    "nlp_response_from_json"
] 