"""
Context Manager for Arxos NLP System

This module provides context management functionality for NLP processing,
including contextual object resolution and context tracking.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from ..models.nlp_models import NLPContext, Intent, SlotResult


@dataclass
class ObjectReference:
    """Object reference for contextual resolution"""

    object_id: str
    object_type: str
    location: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextManager:
    """
    Context Manager for NLP processing context

    This class provides:
    - Context tracking and management
    - Object reference resolution
    - Context-aware slot filling
    - Session management
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Context Manager

        Args:
            config: Configuration dictionary for context management
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Initialize context storage
        self.contexts: Dict[str, NLPContext] = {}
        self.object_references: Dict[str, ObjectReference] = {}

        # Load default context
        self._load_default_context()

    def _load_default_context(self):
        """Load default context information"""
        # Default object references
        default_objects = {
            "bedroom": ObjectReference(
                "room_001", "room", "floor_1", {"type": "bedroom"}
            ),
            "bathroom": ObjectReference(
                "room_002", "room", "floor_1", {"type": "bathroom"}
            ),
            "kitchen": ObjectReference(
                "room_003", "room", "floor_1", {"type": "kitchen"}
            ),
            "living": ObjectReference(
                "room_004", "room", "floor_1", {"type": "living"}
            ),
            "office": ObjectReference(
                "room_005", "room", "floor_1", {"type": "office"}
            ),
            "wall": ObjectReference(
                "wall_001", "wall", "floor_1", {"type": "interior"}
            ),
            "door": ObjectReference(
                "door_001", "door", "floor_1", {"type": "interior"}
            ),
            "window": ObjectReference(
                "window_001", "window", "floor_1", {"type": "standard"}
            ),
            "fixture": ObjectReference(
                "fixture_001", "fixture", "floor_1", {"type": "generic"}
            ),
            "equipment": ObjectReference(
                "equipment_001", "equipment", "floor_1", {"type": "generic"}
            ),
            "system": ObjectReference(
                "system_001", "system", "building", {"type": "generic"}
            ),
        }

        for name, obj_ref in default_objects.items():
            self.object_references[name] = obj_ref

    def resolve_context(
        self, intent: Intent, slot_result: SlotResult, context: NLPContext
    ) -> NLPContext:
        """
        Resolve context for NLP processing

        Args:
            intent: Detected intent
            slot_result: Extracted slots
            context: Input context

        Returns:
            Resolved context with additional information
        """
        resolved_context = context

        # Resolve object references
        object_context = self._resolve_object_references(slot_result.slots)
        resolved_context.object_context.update(object_context)

        # Update context with intent information
        resolved_context.metadata["intent_type"] = intent.intent_type.value
        resolved_context.metadata["confidence"] = intent.confidence

        # Add session tracking
        if not resolved_context.session_id:
            resolved_context.session_id = self._generate_session_id()

        # Store context for future reference
        self.contexts[resolved_context.session_id] = resolved_context

        return resolved_context

    def _resolve_object_references(self, slots: List) -> Dict[str, Any]:
        """Resolve object references from slots"""
        object_context = {}

        for slot in slots:
            if hasattr(slot, "slot_type") and hasattr(slot, "value"):
                if slot.slot_type.value == "object_type":
                    # Look up object reference
                    obj_ref = self.object_references.get(slot.value)
                    if obj_ref:
                        object_context[slot.value] = {
                            "object_id": obj_ref.object_id,
                            "object_type": obj_ref.object_type,
                            "location": obj_ref.location,
                            "properties": obj_ref.properties,
                        }
                elif slot.slot_type.value == "location":
                    # Add location context
                    object_context["current_location"] = slot.value
                elif slot.slot_type.value == "target":
                    # Add target context
                    object_context["target"] = slot.value

        return object_context

    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        import uuid

        return str(uuid.uuid4())

    def get_context(self, session_id: str) -> Optional[NLPContext]:
        """
        Get context for session

        Args:
            session_id: Session identifier

        Returns:
            Context for the session, or None if not found
        """
        return self.contexts.get(session_id)

    def update_context(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update context for session

        Args:
            session_id: Session identifier
            updates: Context updates

        Returns:
            True if context was updated, False otherwise
        """
        if session_id not in self.contexts:
            return False

        context = self.contexts[session_id]

        # Update context fields
        for key, value in updates.items():
            if hasattr(context, key):
                setattr(context, key, value)
            else:
                context.metadata[key] = value

        return True

    def clear_context(self, session_id: str) -> bool:
        """
        Clear context for session

        Args:
            session_id: Session identifier

        Returns:
            True if context was cleared, False otherwise
        """
        if session_id in self.contexts:
            del self.contexts[session_id]
            return True
        return False

    def add_object_reference(self, name: str, obj_ref: ObjectReference) -> None:
        """
        Add object reference to context

        Args:
            name: Object name
            obj_ref: Object reference
        """
        self.object_references[name] = obj_ref

    def get_object_reference(self, name: str) -> Optional[ObjectReference]:
        """
        Get object reference by name

        Args:
            name: Object name

        Returns:
            Object reference, or None if not found
        """
        return self.object_references.get(name)

    def resolve_object_name(self, name: str) -> Optional[str]:
        """
        Resolve object name to object ID

        Args:
            name: Object name

        Returns:
            Object ID, or None if not found
        """
        obj_ref = self.object_references.get(name)
        return obj_ref.object_id if obj_ref else None

    def get_context_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get context summary for session

        Args:
            session_id: Session identifier

        Returns:
            Context summary
        """
        context = self.contexts.get(session_id)
        if not context:
            return {}

        return {
            "session_id": context.session_id,
            "user_id": context.user_id,
            "building_id": context.building_id,
            "floor_id": context.floor_id,
            "object_context": context.object_context,
            "permissions": context.permissions,
            "metadata": context.metadata,
        }

    def get_all_contexts(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all contexts

        Returns:
            Dictionary of all contexts
        """
        return {
            session_id: self.get_context_summary(session_id)
            for session_id in self.contexts.keys()
        }

    def cleanup_expired_contexts(self, max_age_hours: int = 24) -> int:
        """
        Clean up expired contexts

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            Number of contexts cleaned up
        """
        import time

        current_time = time.time()
        expired_sessions = []

        for session_id, context in self.contexts.items():
            # Check if context has timestamp and is expired
            if hasattr(context, "timestamp"):
                age_hours = (current_time - context.timestamp.timestamp()) / 3600
                if age_hours > max_age_hours:
                    expired_sessions.append(session_id)

        # Remove expired contexts
        for session_id in expired_sessions:
            del self.contexts[session_id]

        return len(expired_sessions)

    def get_context_stats(self) -> Dict[str, Any]:
        """
        Get context statistics

        Returns:
            Context statistics
        """
        return {
            "total_contexts": len(self.contexts),
            "total_object_references": len(self.object_references),
            "active_sessions": len([c for c in self.contexts.values() if c.session_id]),
            "contexts_by_user": self._group_contexts_by_user(),
        }

    def _group_contexts_by_user(self) -> Dict[str, int]:
        """Group contexts by user ID"""
        user_counts = {}
        for context in self.contexts.values():
            user_id = context.user_id or "anonymous"
            user_counts[user_id] = user_counts.get(user_id, 0) + 1
        return user_counts


# Convenience function for quick context resolution
def resolve_context(
    intent: Intent,
    slot_result: SlotResult,
    context: NLPContext,
    config: Optional[Dict[str, Any]] = None,
) -> NLPContext:
    """
    Convenience function for quick context resolution

    Args:
        intent: Detected intent
        slot_result: Extracted slots
        context: Input context
        config: Optional configuration

    Returns:
        Resolved context
    """
    manager = ContextManager(config)
    return manager.resolve_context(intent, slot_result, context)
