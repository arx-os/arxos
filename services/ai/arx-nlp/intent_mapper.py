"""
Intent Mapper for Arxos NLP System

This module provides intent detection and slot-filling functionality to translate
natural language user input into structured ArxCLI commands with contextual
object resolution.

Key Features:
- Intent detection with confidence scoring
- Slot filling for command parameters
- Contextual object resolution
- Command validation and suggestion
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from services.models.nlp_models import services.models.nlp_models
from services.utils.context_manager import services.utils.context_manager
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
class IntentPattern:
    """Pattern for intent detection"""
    pattern: str
    intent_type: IntentType
    confidence_boost: float = 0.0
    required_slots: List[SlotType] = field(default_factory=list)
    optional_slots: List[SlotType] = field(default_factory=list)


@dataclass
class SlotPattern:
    """Pattern for slot extraction"""
    pattern: str
    slot_type: SlotType
    value_type: str = "string"
    validation_rules: Dict[str, Any] = field(default_factory=dict)


class IntentMapper:
    """
    Intent Mapper for detecting intents and extracting slots from natural language

    This class provides:
    - Intent detection with confidence scoring
    - Slot filling for command parameters
    - Contextual object resolution
    - Command validation and suggestion
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Intent Mapper

        Args:
            config: Configuration dictionary for intent mapping
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Initialize context manager
        self.context_manager = ContextManager(config.get('context', {})

        # Load patterns and rules
        self._load_intent_patterns()
        self._load_slot_patterns()
        self._load_object_mappings()

    def _load_intent_patterns(self):
        """Load intent detection patterns"""
        self.intent_patterns = [
            # Create patterns
            IntentPattern(r'create\s+(\w+)', IntentType.CREATE, 0.1, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'add\s+(\w+)', IntentType.CREATE, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'new\s+(\w+)', IntentType.CREATE, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'build\s+(\w+)', IntentType.CREATE, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'generate\s+(\w+)', IntentType.CREATE, 0.05, [SlotType.OBJECT_TYPE]),

            # Modify patterns
            IntentPattern(r'modify\s+(\w+)', IntentType.MODIFY, 0.1, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'change\s+(\w+)', IntentType.MODIFY, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'update\s+(\w+)', IntentType.MODIFY, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'edit\s+(\w+)', IntentType.MODIFY, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'adjust\s+(\w+)', IntentType.MODIFY, 0.05, [SlotType.OBJECT_TYPE]),

            # Delete patterns
            IntentPattern(r'delete\s+(\w+)', IntentType.DELETE, 0.1, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'remove\s+(\w+)', IntentType.DELETE, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'destroy\s+(\w+)', IntentType.DELETE, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'eliminate\s+(\w+)', IntentType.DELETE, 0.05, [SlotType.OBJECT_TYPE]),

            # Move patterns
            IntentPattern(r'move\s+(\w+)', IntentType.MOVE, 0.1, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'relocate\s+(\w+)', IntentType.MOVE, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'transfer\s+(\w+)', IntentType.MOVE, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'reposition\s+(\w+)', IntentType.MOVE, 0.05, [SlotType.OBJECT_TYPE]),

            # Query patterns
            IntentPattern(r'find\s+(\w+)', IntentType.QUERY, 0.1, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'search\s+for\s+(\w+)', IntentType.QUERY, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'locate\s+(\w+)', IntentType.QUERY, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'where\s+is\s+(\w+)', IntentType.QUERY, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'what\s+(\w+)', IntentType.QUERY, 0.05, [SlotType.OBJECT_TYPE]),

            # Export patterns
            IntentPattern(r'export\s+(\w+)', IntentType.EXPORT, 0.1, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'save\s+(\w+)', IntentType.EXPORT, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'download\s+(\w+)', IntentType.EXPORT, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'backup\s+(\w+)', IntentType.EXPORT, 0.05, [SlotType.OBJECT_TYPE]),

            # Import patterns
            IntentPattern(r'import\s+(\w+)', IntentType.IMPORT, 0.1, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'load\s+(\w+)', IntentType.IMPORT, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'upload\s+(\w+)', IntentType.IMPORT, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'bring\s+in\s+(\w+)', IntentType.IMPORT, 0.05, [SlotType.OBJECT_TYPE]),

            # Validate patterns
            IntentPattern(r'validate\s+(\w+)', IntentType.VALIDATE, 0.1, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'check\s+(\w+)', IntentType.VALIDATE, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'verify\s+(\w+)', IntentType.VALIDATE, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'test\s+(\w+)', IntentType.VALIDATE, 0.05, [SlotType.OBJECT_TYPE]),

            # Sync patterns
            IntentPattern(r'sync\s+(\w+)', IntentType.SYNC, 0.1, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'synchronize\s+(\w+)', IntentType.SYNC, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'push\s+(\w+)', IntentType.SYNC, 0.05, [SlotType.OBJECT_TYPE]),

            # Annotate patterns
            IntentPattern(r'annotate\s+(\w+)', IntentType.ANNOTATE, 0.1, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'note\s+(\w+)', IntentType.ANNOTATE, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'comment\s+on\s+(\w+)', IntentType.ANNOTATE, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'mark\s+(\w+)', IntentType.ANNOTATE, 0.05, [SlotType.OBJECT_TYPE]),

            # Inspect patterns
            IntentPattern(r'inspect\s+(\w+)', IntentType.INSPECT, 0.1, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'examine\s+(\w+)', IntentType.INSPECT, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'review\s+(\w+)', IntentType.INSPECT, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'look\s+at\s+(\w+)', IntentType.INSPECT, 0.05, [SlotType.OBJECT_TYPE]),

            # Report patterns
            IntentPattern(r'report\s+(\w+)', IntentType.REPORT, 0.1, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'generate\s+report\s+(\w+)', IntentType.REPORT, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'summary\s+(\w+)', IntentType.REPORT, 0.05, [SlotType.OBJECT_TYPE]),
            IntentPattern(r'status\s+(\w+)', IntentType.REPORT, 0.05, [SlotType.OBJECT_TYPE])
        ]

    def _load_slot_patterns(self):
        """Load slot extraction patterns"""
        self.slot_patterns = [
            # Object type patterns
            SlotPattern(r'\b(room|bedroom|bathroom|kitchen|living|office)\b', SlotType.OBJECT_TYPE, "room"),
            SlotPattern(r'\b(wall|door|window|fixture|equipment|system)\b', SlotType.OBJECT_TYPE, "building_element"),
            SlotPattern(r'\b(floor|building|site)\b', SlotType.OBJECT_TYPE, "structure"),

            # Location patterns
            SlotPattern(r'on\s+floor\s+(\d+)', SlotType.LOCATION, "floor_number"),
            SlotPattern(r'in\s+(\w+)', SlotType.LOCATION, "room_name"),
            SlotPattern(r'at\s+(\w+)', SlotType.LOCATION, "position"),

            # Property patterns
            SlotPattern(r'color\s+(\w+)', SlotType.PROPERTY, "color"),
            SlotPattern(r'size\s+(\w+)', SlotType.PROPERTY, "size"),
            SlotPattern(r'type\s+(\w+)', SlotType.PROPERTY, "type"),
            SlotPattern(r'width\s+(\d+)', SlotType.PROPERTY, "width"),
            SlotPattern(r'height\s+(\d+)', SlotType.PROPERTY, "height"),
            SlotPattern(r'length\s+(\d+)', SlotType.PROPERTY, "length"),

            # Value patterns
            SlotPattern(r'(\d+)\s*(?:x|by)\s*(\d+)', SlotType.VALUE, "dimensions"),
            SlotPattern(r'(\d+)\s*(?:feet|ft)', SlotType.VALUE, "distance"),
            SlotPattern(r'(\d+)\s*(?:inches|in)', SlotType.VALUE, "distance"),

            # Format patterns
            SlotPattern(r'format\s+(\w+)', SlotType.FORMAT, "format"),
            SlotPattern(r'as\s+(\w+)', SlotType.FORMAT, "format"),

            # Target patterns
            SlotPattern(r'to\s+(\w+)', SlotType.TARGET, "target"),
            SlotPattern(r'target\s+(\w+)', SlotType.TARGET, "target"),

            # Source patterns
            SlotPattern(r'from\s+(\w+)', SlotType.SOURCE, "source"),
            SlotPattern(r'source\s+(\w+)', SlotType.SOURCE, "source"),

            # Condition patterns
            SlotPattern(r'if\s+(\w+)', SlotType.CONDITION, "condition"),
            SlotPattern(r'when\s+(\w+)', SlotType.CONDITION, "condition"),
            SlotPattern(r'where\s+(\w+)', SlotType.CONDITION, "condition")
        ]

    def _load_object_mappings(self):
        """Load object type mappings for contextual resolution"""
        self.object_mappings = {
            'room': 'room',
            'bedroom': 'room',
            'bathroom': 'room',
            'kitchen': 'room',
            'living': 'room',
            'office': 'room',
            'wall': 'wall',
            'door': 'door',
            'window': 'window',
            'fixture': 'fixture',
            'equipment': 'equipment',
            'system': 'system',
            'floor': 'floor',
            'building': 'building',
            'site': 'site'
        }

    def detect_intent(self, text: str) -> Intent:
        """
        Detect intent from natural language text

        Args:
            text: Natural language input text

        Returns:
            Intent with detected type and confidence
        """
        text_lower = text.lower().strip()
        best_match = None
        highest_confidence = 0.0

        for pattern in self.intent_patterns:
            match = re.search(pattern.pattern, text_lower)
            if match:
                # Calculate confidence based on pattern match
                confidence = 0.5  # Base confidence

                # Boost confidence for exact matches
                if match.group(0) == text_lower:
                    confidence += 0.3

                # Add pattern-specific boost
                confidence += pattern.confidence_boost

                # Boost for longer matches
                confidence += min(0.2, len(match.group(0) / len(text_lower) * 0.2)

                if confidence > highest_confidence:
                    highest_confidence = confidence
                    best_match = pattern

        if best_match:
            return Intent(
                intent_type=best_match.intent_type,
                confidence=min(1.0, highest_confidence),
                raw_text=text,
                required_slots=best_match.required_slots,
                optional_slots=best_match.optional_slots
            )
        else:
            # Default to query intent with low confidence
            return Intent(
                intent_type=IntentType.QUERY,
                confidence=0.1,
                raw_text=text,
                required_slots=[],
                optional_slots=[]
            )

    def extract_slots(self, text: str, intent_type: IntentType) -> SlotResult:
        """
        Extract slots from natural language text

        Args:
            text: Natural language input text
            intent_type: Detected intent type

        Returns:
            SlotResult with extracted slots
        """
        text_lower = text.lower().strip()
        slots = []

        # Extract slots using patterns
        for pattern in self.slot_patterns:
            matches = re.finditer(pattern.pattern, text_lower)
            for match in matches:
                slot_value = match.group(1) if match.groups() else match.group(0)

                # Validate slot value
                if self._validate_slot_value(slot_value, pattern):
                    slot = Slot(
                        slot_type=pattern.slot_type,
                        value=slot_value,
                        value_type=pattern.value_type,
                        confidence=0.8,  # Base confidence for pattern matches
                        start_pos=match.start(),
                        end_pos=match.end()
                    slots.append(slot)

        # Extract additional slots based on intent type
        additional_slots = self._extract_intent_specific_slots(text_lower, intent_type)
        slots.extend(additional_slots)

        # Resolve object references
        resolved_slots = self._resolve_object_references(slots)

        return SlotResult(
            slots=resolved_slots,
            confidence=min(1.0, len(slots) * 0.1 + 0.5)

    def _validate_slot_value(self, value: str, pattern: SlotPattern) -> bool:
        """Validate slot value against pattern rules"""
        if not value or value.strip() == '':
            return False

        # Apply validation rules
        rules = pattern.validation_rules

        # Check minimum length
        if 'min_length' in rules and len(value) < rules['min_length']:
            return False

        # Check maximum length
        if 'max_length' in rules and len(value) > rules['max_length']:
            return False

        # Check pattern match
        if 'pattern' in rules and not re.match(rules['pattern'], value):
            return False

        # Check allowed values
        if 'allowed_values' in rules and value not in rules['allowed_values']:
            return False

        return True

    def _extract_intent_specific_slots(self, text: str, intent_type: IntentType) -> List[Slot]:
        """Extract slots specific to intent type"""
        slots = []

        if intent_type == IntentType.CREATE:
            # Extract object properties for creation
            size_match = re.search(r'(\d+)\s*(?:x|by)\s*(\d+)', text)
            if size_match:
                slots.append(Slot(
                    slot_type=SlotType.VALUE,
                    value=f"{size_match.group(1)}x{size_match.group(2)}",
                    value_type="dimensions",
                    confidence=0.9
                )

            color_match = re.search(r'(red|green|blue|yellow|black|white|gray|grey)', text)
            if color_match:
                slots.append(Slot(
                    slot_type=SlotType.PROPERTY,
                    value=color_match.group(1),
                    value_type="color",
                    confidence=0.9
                )

        elif intent_type == IntentType.MODIFY:
            # Extract property changes
            property_match = re.search(r'(\w+)\s+to\s+(\w+)', text)
            if property_match:
                slots.append(Slot(
                    slot_type=SlotType.PROPERTY,
                    value=property_match.group(1),
                    value_type="property_name",
                    confidence=0.8
                )
                slots.append(Slot(
                    slot_type=SlotType.VALUE,
                    value=property_match.group(2),
                    value_type="new_value",
                    confidence=0.8
                )

        elif intent_type == IntentType.QUERY:
            # Extract query filters
            filter_match = re.search(r'(\w+)\s+(\w+)', text)
            if filter_match:
                slots.append(Slot(
                    slot_type=SlotType.CONDITION,
                    value=f"{filter_match.group(1)} {filter_match.group(2)}",
                    value_type="filter",
                    confidence=0.7
                )

        return slots

    def _resolve_object_references(self, slots: List[Slot]) -> List[Slot]:
        """Resolve object references using context"""
        resolved_slots = []

        for slot in slots:
            if slot.slot_type == SlotType.OBJECT_TYPE:
                # Map object names to standard types
                mapped_value = self.object_mappings.get(slot.value, slot.value)
                resolved_slot = Slot(
                    slot_type=slot.slot_type,
                    value=mapped_value,
                    value_type=slot.value_type,
                    confidence=slot.confidence,
                    start_pos=slot.start_pos,
                    end_pos=slot.end_pos,
                    original_value=slot.value
                )
                resolved_slots.append(resolved_slot)
            else:
                resolved_slots.append(slot)

        return resolved_slots

    def get_suggestions(self, partial_text: str) -> List[str]:
        """
        Get intent suggestions based on partial text

        Args:
            partial_text: Partial natural language input

        Returns:
            List of suggested completions
        """
        suggestions = []
        partial_lower = partial_text.lower().strip()

        # Get intent suggestions
        for pattern in self.intent_patterns:
            if partial_lower in pattern.pattern.lower():
                suggestions.append(pattern.pattern.replace(r'(\w+)', '<object>')

        # Get object suggestions
        for obj_name in self.object_mappings.keys():
            if partial_lower in obj_name or obj_name.startswith(partial_lower):
                suggestions.append(f"create {obj_name}")
                suggestions.append(f"modify {obj_name}")
                suggestions.append(f"delete {obj_name}")

        return list(set(suggestions)[:10]  # Limit to 10 unique suggestions

    def validate_intent(self, intent: Intent) -> bool:
        """
        Validate detected intent

        Args:
            intent: Intent to validate

        Returns:
            True if intent is valid, False otherwise
        """
        # Check if intent type is supported
        if intent.intent_type not in [e.value for e in IntentType]:
            return False

        # Check confidence threshold
        if intent.confidence < 0.1:
            return False

        # Check required slots
        if hasattr(intent, 'required_slots'):
            # This would be validated during slot extraction
            pass

        return True

    def get_intent_help(self, intent_type: IntentType) -> str:
        """
        Get help information for specific intent type

        Args:
            intent_type: Intent type for help

        Returns:
            Help text for the intent type
        """
        help_texts = {
            IntentType.CREATE: "Create commands: create <object_type> [properties]",
            IntentType.MODIFY: "Modify commands: modify <object> [property=value]",
            IntentType.DELETE: "Delete commands: delete <object> [conditions]",
            IntentType.MOVE: "Move commands: move <object> to <location>",
            IntentType.QUERY: "Query commands: query <object> [filters]",
            IntentType.EXPORT: "Export commands: export <object> [format]",
            IntentType.IMPORT: "Import commands: import <object> from <source>",
            IntentType.VALIDATE: "Validate commands: validate <object> [rules]",
            IntentType.SYNC: "Sync commands: sync <object> [target]",
            IntentType.ANNOTATE: "Annotate commands: annotate <object> [note]",
            IntentType.INSPECT: "Inspect commands: inspect <object> [details]",
            IntentType.REPORT: "Report commands: report <object> [type]"
        }

        return help_texts.get(intent_type, f"No help available for intent: {intent_type}")


# Convenience function for quick intent detection
def detect_intent(text: str, config: Optional[Dict[str, Any]] = None) -> Intent:
    """
    Convenience function for quick intent detection

    Args:
        text: Natural language input
        config: Optional configuration

    Returns:
        Intent with detected type and confidence
    """
    mapper = IntentMapper(config)
    return mapper.detect_intent(text)


if __name__ == "__main__":
    # Example usage
    mapper = IntentMapper()

    # Test intent detection
    test_inputs = [
        "create a bedroom",
        "modify the kitchen layout",
        "find all doors on floor 2",
        "export the building plan",
        "validate electrical systems"
    ]

    for text in test_inputs:
        intent = mapper.detect_intent(text)
        slots = mapper.extract_slots(text, intent.intent_type)

        print(f"Input: {text}")
        print(f"Intent: {intent.intent_type}")
        print(f"Confidence: {intent.confidence}")
        print(f"Slots: {[f'{s.slot_type}={s.value}' for s in slots.slots]}")
        print("-" * 50) )))))))))))
