"""
NLP Data Models for Arxos Platform

This module defines the data models used throughout the NLP system for
request/response handling, intent detection, slot filling, and CLI command generation.
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class IntentType(Enum):
    """Supported intent types for building operations"""
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    MOVE = "move"
    QUERY = "query"
    EXPORT = "export"
    IMPORT = "import"
    VALIDATE = "validate"
    SYNC = "sync"
    ANNOTATE = "annotate"
    INSPECT = "inspect"
    REPORT = "report"


class SlotType(Enum):
    """Slot types for parameter extraction"""
    OBJECT_TYPE = "object_type"
    OBJECT_ID = "object_id"
    LOCATION = "location"
    PROPERTY = "property"
    VALUE = "value"
    UNIT = "unit"
    FORMAT = "format"
    TARGET = "target"
    SOURCE = "source"
    CONDITION = "condition"


@dataclass
class Intent:
    """Intent detection result"""
    intent_type: IntentType
    confidence: float
    raw_text: str
    required_slots: List[SlotType] = field(default_factory=list)
    optional_slots: List[SlotType] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'intent_type': self.intent_type.value,
            'confidence': self.confidence,
            'raw_text': self.raw_text,
            'required_slots': [slot.value for slot in self.required_slots],
            'optional_slots': [slot.value for slot in self.optional_slots],
            'metadata': self.metadata
        }


@dataclass
class Slot:
    """Slot extraction result"""
    slot_type: SlotType
    value: str
    value_type: str = "string"
    confidence: float = 0.0
    start_pos: int = -1
    end_pos: int = -1
    original_value: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'slot_type': self.slot_type.value,
            'value': self.value,
            'value_type': self.value_type,
            'confidence': self.confidence,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos,
            'original_value': self.original_value,
            'metadata': self.metadata
        }


@dataclass
class SlotResult:
    """Result of slot extraction"""
    slots: List[Slot]
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'slots': [slot.to_dict() for slot in self.slots],
            'confidence': self.confidence,
            'metadata': self.metadata
        }


@dataclass
class CLICommand:
    """Generated CLI command"""
    command: str
    arguments: List[str] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)
    subcommand: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'command': self.command,
            'arguments': self.arguments,
            'options': self.options,
            'subcommand': self.subcommand,
            'metadata': self.metadata
        }

    def to_string(self) -> str:
        """Convert to command string"""
        cmd_parts = [self.command]

        if self.subcommand:
            cmd_parts.append(self.subcommand)

        cmd_parts.extend(self.arguments)

        for key, value in self.options.items():
            if isinstance(value, bool):
                if value:
                    cmd_parts.append(f"--{key}")
            else:
                cmd_parts.append(f"--{key}")
                cmd_parts.append(str(value))

        return " ".join(cmd_parts)


@dataclass
class NLPContext:
    """Context information for NLP processing"""
    user_id: Optional[str] = None
    building_id: Optional[str] = None
    floor_id: Optional[str] = None
    session_id: Optional[str] = None
    previous_commands: List[str] = field(default_factory=list)
    object_context: Dict[str, Any] = field(default_factory=dict)
    permissions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'building_id': self.building_id,
            'floor_id': self.floor_id,
            'session_id': self.session_id,
            'previous_commands': self.previous_commands,
            'object_context': self.object_context,
            'permissions': self.permissions,
            'metadata': self.metadata
        }


@dataclass
class NLPRequest:
    """NLP processing request"""
    text: str
    context: Optional[NLPContext] = None
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'text': self.text,
            'context': self.context.to_dict() if self.context else None,
            'config': self.config,
            'metadata': self.metadata
        }


@dataclass
class NLPResponse:
    """NLP processing response"""
    original_text: str
    intent: Intent
    slots: List[Slot]
    cli_command: CLICommand
    confidence: float
    context: NLPContext
    timestamp: datetime
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'original_text': self.original_text,
            'intent': self.intent.to_dict(),
            'slots': [slot.to_dict() for slot in self.slots],
            'cli_command': self.cli_command.to_dict(),
            'confidence': self.confidence,
            'context': self.context.to_dict(),
            'timestamp': self.timestamp.isoformat(),
            'error': self.error,
            'metadata': self.metadata
        }

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class ValidationResult:
    """Validation result for NLP processing"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'suggestions': self.suggestions,
            'metadata': self.metadata
        }


@dataclass
class ProcessingStats:
    """Statistics for NLP processing"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_confidence: float = 0.0
    average_processing_time: float = 0.0
    intent_distribution: Dict[str, int] = field(default_factory=dict)
    slot_distribution: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'average_confidence': self.average_confidence,
            'average_processing_time': self.average_processing_time,
            'intent_distribution': self.intent_distribution,
            'slot_distribution': self.slot_distribution,
            'metadata': self.metadata
        }


# Utility functions for model serialization
def intent_from_dict(data: Dict[str, Any]) -> Intent:
    """Create Intent from dictionary"""
    return Intent(
        intent_type=IntentType(data['intent_type']),
        confidence=data['confidence'],
        raw_text=data['raw_text'],
        required_slots=[SlotType(slot) for slot in data.get('required_slots', [])],
        optional_slots=[SlotType(slot) for slot in data.get('optional_slots', [])],
        metadata=data.get('metadata', {})
    )


def slot_from_dict(data: Dict[str, Any]) -> Slot:
    """Create Slot from dictionary"""
    return Slot(
        slot_type=SlotType(data['slot_type']),
        value=data['value'],
        value_type=data.get('value_type', 'string'),
        confidence=data.get('confidence', 0.0),
        start_pos=data.get('start_pos', -1),
        end_pos=data.get('end_pos', -1),
        original_value=data.get('original_value'),
        metadata=data.get('metadata', {})
    )


def cli_command_from_dict(data: Dict[str, Any]) -> CLICommand:
    """Create CLICommand from dictionary"""
    return CLICommand(
        command=data['command'],
        arguments=data.get('arguments', []),
        options=data.get('options', {}),
        subcommand=data.get('subcommand'),
        metadata=data.get('metadata', {})
    )


def nlp_context_from_dict(data: Dict[str, Any]) -> NLPContext:
    """Create NLPContext from dictionary"""
    return NLPContext(
        user_id=data.get('user_id'),
        building_id=data.get('building_id'),
        floor_id=data.get('floor_id'),
        session_id=data.get('session_id'),
        previous_commands=data.get('previous_commands', []),
        object_context=data.get('object_context', {}),
        permissions=data.get('permissions', []),
        metadata=data.get('metadata', {})
    )


def nlp_response_from_dict(data: Dict[str, Any]) -> NLPResponse:
    """Create NLPResponse from dictionary"""
    return NLPResponse(
        original_text=data['original_text'],
        intent=intent_from_dict(data['intent']),
        slots=[slot_from_dict(slot) for slot in data['slots']],
        cli_command=cli_command_from_dict(data['cli_command']),
        confidence=data['confidence'],
        context=nlp_context_from_dict(data['context']),
        timestamp=datetime.fromisoformat(data['timestamp']),
        error=data.get('error'),
        metadata=data.get('metadata', {})
    )


def nlp_response_from_json(json_str: str) -> NLPResponse:
    """Create NLPResponse from JSON string"""
    data = json.loads(json_str)
    return nlp_response_from_dict(data)
