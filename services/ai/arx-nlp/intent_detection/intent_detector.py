"""
Intent Detector for Arxos NLP System

This module provides intent detection functionality with confidence scoring
and pattern matching for building operations.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from services.models.nlp_models import services.models.nlp_models
@dataclass
class IntentPattern:
    """Pattern for intent detection"""
    pattern: str
    intent_type: IntentType
    confidence_boost: float = 0.0
    required_slots: List[str] = None
    optional_slots: List[str] = None

    def __post_init__(self):
        if self.required_slots is None:
            self.required_slots = []
        if self.optional_slots is None:
            self.optional_slots = []


class IntentDetector:
    """
    Intent Detector for identifying user intentions from natural language

    This class provides:
    - Pattern-based intent detection
    - Confidence scoring
    - Intent validation
    - Suggestion generation
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Intent Detector

        Args:
            config: Configuration dictionary for intent detection
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Load patterns
        self._load_patterns()

    def _load_patterns(self):
        """Load intent detection patterns"""
        self.intent_patterns = [
            # Create patterns
            IntentPattern(r'create\s+(\w+)', IntentType.CREATE, 0.1),
            IntentPattern(r'add\s+(\w+)', IntentType.CREATE, 0.05),
            IntentPattern(r'new\s+(\w+)', IntentType.CREATE, 0.05),
            IntentPattern(r'build\s+(\w+)', IntentType.CREATE, 0.05),
            IntentPattern(r'generate\s+(\w+)', IntentType.CREATE, 0.05),

            # Modify patterns
            IntentPattern(r'modify\s+(\w+)', IntentType.MODIFY, 0.1),
            IntentPattern(r'change\s+(\w+)', IntentType.MODIFY, 0.05),
            IntentPattern(r'update\s+(\w+)', IntentType.MODIFY, 0.05),
            IntentPattern(r'edit\s+(\w+)', IntentType.MODIFY, 0.05),
            IntentPattern(r'adjust\s+(\w+)', IntentType.MODIFY, 0.05),

            # Delete patterns
            IntentPattern(r'delete\s+(\w+)', IntentType.DELETE, 0.1),
            IntentPattern(r'remove\s+(\w+)', IntentType.DELETE, 0.05),
            IntentPattern(r'destroy\s+(\w+)', IntentType.DELETE, 0.05),
            IntentPattern(r'eliminate\s+(\w+)', IntentType.DELETE, 0.05),

            # Move patterns
            IntentPattern(r'move\s+(\w+)', IntentType.MOVE, 0.1),
            IntentPattern(r'relocate\s+(\w+)', IntentType.MOVE, 0.05),
            IntentPattern(r'transfer\s+(\w+)', IntentType.MOVE, 0.05),
            IntentPattern(r'reposition\s+(\w+)', IntentType.MOVE, 0.05),

            # Query patterns
            IntentPattern(r'find\s+(\w+)', IntentType.QUERY, 0.1),
            IntentPattern(r'search\s+for\s+(\w+)', IntentType.QUERY, 0.05),
            IntentPattern(r'locate\s+(\w+)', IntentType.QUERY, 0.05),
            IntentPattern(r'where\s+is\s+(\w+)', IntentType.QUERY, 0.05),
            IntentPattern(r'what\s+(\w+)', IntentType.QUERY, 0.05),

            # Export patterns
            IntentPattern(r'export\s+(\w+)', IntentType.EXPORT, 0.1),
            IntentPattern(r'save\s+(\w+)', IntentType.EXPORT, 0.05),
            IntentPattern(r'download\s+(\w+)', IntentType.EXPORT, 0.05),
            IntentPattern(r'backup\s+(\w+)', IntentType.EXPORT, 0.05),

            # Import patterns
            IntentPattern(r'import\s+(\w+)', IntentType.IMPORT, 0.1),
            IntentPattern(r'load\s+(\w+)', IntentType.IMPORT, 0.05),
            IntentPattern(r'upload\s+(\w+)', IntentType.IMPORT, 0.05),
            IntentPattern(r'bring\s+in\s+(\w+)', IntentType.IMPORT, 0.05),

            # Validate patterns
            IntentPattern(r'validate\s+(\w+)', IntentType.VALIDATE, 0.1),
            IntentPattern(r'check\s+(\w+)', IntentType.VALIDATE, 0.05),
            IntentPattern(r'verify\s+(\w+)', IntentType.VALIDATE, 0.05),
            IntentPattern(r'test\s+(\w+)', IntentType.VALIDATE, 0.05),

            # Sync patterns
            IntentPattern(r'sync\s+(\w+)', IntentType.SYNC, 0.1),
            IntentPattern(r'synchronize\s+(\w+)', IntentType.SYNC, 0.05),
            IntentPattern(r'push\s+(\w+)', IntentType.SYNC, 0.05),

            # Annotate patterns
            IntentPattern(r'annotate\s+(\w+)', IntentType.ANNOTATE, 0.1),
            IntentPattern(r'note\s+(\w+)', IntentType.ANNOTATE, 0.05),
            IntentPattern(r'comment\s+on\s+(\w+)', IntentType.ANNOTATE, 0.05),
            IntentPattern(r'mark\s+(\w+)', IntentType.ANNOTATE, 0.05),

            # Inspect patterns
            IntentPattern(r'inspect\s+(\w+)', IntentType.INSPECT, 0.1),
            IntentPattern(r'examine\s+(\w+)', IntentType.INSPECT, 0.05),
            IntentPattern(r'review\s+(\w+)', IntentType.INSPECT, 0.05),
            IntentPattern(r'look\s+at\s+(\w+)', IntentType.INSPECT, 0.05),

            # Report patterns
            IntentPattern(r'report\s+(\w+)', IntentType.REPORT, 0.1),
            IntentPattern(r'generate\s+report\s+(\w+)', IntentType.REPORT, 0.05),
            IntentPattern(r'summary\s+(\w+)', IntentType.REPORT, 0.05),
            IntentPattern(r'status\s+(\w+)', IntentType.REPORT, 0.05)
        ]

    def detect_intent(self, text: str, patterns: Optional[Dict] = None) -> Intent:
        """
        Detect intent from natural language text

        Args:
            text: Natural language input text
            patterns: Optional custom patterns to use

        Returns:
            Intent with detected type and confidence
        """
        text_lower = text.lower().strip()
        best_match = None
        highest_confidence = 0.0

        # Use provided patterns or default patterns
        patterns_to_use = patterns or self.intent_patterns

        for pattern in patterns_to_use:
            if isinstance(pattern, dict):
                # Handle dictionary pattern format
                pattern_obj = IntentPattern(
                    pattern=pattern['pattern'],
                    intent_type=IntentType(pattern['intent_type']),
                    confidence_boost=pattern.get('confidence_boost', 0.0)
            else:
                pattern_obj = pattern

            match = re.search(pattern_obj.pattern, text_lower)
            if match:
                # Calculate confidence based on pattern match
                confidence = 0.5  # Base confidence

                # Boost confidence for exact matches
                if match.group(0) == text_lower:
                    confidence += 0.3

                # Add pattern-specific boost
                confidence += pattern_obj.confidence_boost

                # Boost for longer matches
                confidence += min(0.2, len(match.group(0) / len(text_lower) * 0.2)

                if confidence > highest_confidence:
                    highest_confidence = confidence
                    best_match = pattern_obj

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

        # Get common object suggestions
        common_objects = [
            'room', 'bedroom', 'bathroom', 'kitchen', 'living', 'office',
            'wall', 'door', 'window', 'fixture', 'equipment', 'system',
            'floor', 'building', 'site'
        ]

        for obj in common_objects:
            if partial_lower in obj or obj.startswith(partial_lower):
                suggestions.append(f"create {obj}")
                suggestions.append(f"modify {obj}")
                suggestions.append(f"delete {obj}")

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
    detector = IntentDetector(config)
    return detector.detect_intent(text) ))))
