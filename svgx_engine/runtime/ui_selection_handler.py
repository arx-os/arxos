"""
SVGX Engine - UI Selection Handler

Handles selection events (select, deselect, toggle, clear) for SVGX canvases and objects.
Manages selection state, multi-select operations, and selection feedback.
Integrates with the event-driven behavior engine and provides feedback for selection actions.
Follows Arxos engineering standards: absolute imports, global instances, modular/testable code, and comprehensive documentation.
"""

from typing import Dict, Any, List, Optional, Set, Union
from svgx_engine.runtime.event_driven_behavior_engine import Event, EventType
import logging
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SelectionEventData:
    """Structured data for selection events."""

    canvas_id: str
    action: str
    object_id: Optional[str] = None
    object_ids: Optional[List[str]] = None
    clear_previous: bool = True
    timestamp: Optional[float] = None


class SelectionHandler:
    """
    Handles selection state for SVGX canvases and objects.
    Supports single-select, multi-select, and deselect operations.
    """

    def __init__(self):
        # {canvas_id: Set[object_id]}
        self.selection_state: Dict[str, Set[str]] = {}
        self.event_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000

    def handle_selection_event(self, event: Event) -> Optional[Dict[str, Any]]:
        """
        Handle selection events (select, deselect, toggle, clear).

        Args:
            event: Selection event with action and parameters

        Returns:
            Dict with action result and feedback, or None if invalid
        """
        try:
            # Validate event structure
            if not self._validate_event(event):
                logger.warning(f"Invalid selection event structure: {event}")
                return None

            # Extract and validate event data
            event_data = self._extract_event_data(event)
            if not event_data:
                logger.warning(f"Failed to extract event data from: {event}")
                return None

            # Initialize selection state if not exists
            if event_data.canvas_id not in self.selection_state:
                self.selection_state[event_data.canvas_id] = set()

            # Process the selection action
            result = self._process_selection_action(event_data)

            # Log event for debugging
            self._log_event(event_data, result)

            return result

        except Exception as e:
            logger.error(f"Error handling selection event: {e}", exc_info=True)
            return {"action": "error", "error": str(e), "timestamp": time.time()}

    def _validate_event(self, event: Event) -> bool:
        """Validate event structure and required fields."""
        try:
            if not event or not hasattr(event, "data"):
                return False

            data = event.data
            if not isinstance(data, dict):
                return False

            required_fields = ["canvas_id", "action"]
            return all(field in data for field in required_fields)

        except Exception as e:
            logger.error(f"Event validation error: {e}")
            return False

    def _extract_event_data(self, event: Event) -> Optional[SelectionEventData]:
        """Extract and validate event data."""
        try:
            data = event.data

            # Extract required fields
            canvas_id = data.get("canvas_id")
            action = data.get("action")

            if not canvas_id or not action:
                logger.warning(
                    f"Missing required fields: canvas_id={canvas_id}, action={action}"
                )
                return None

            # Extract optional fields with validation
            object_id = data.get("object_id")
            object_ids = data.get("object_ids")
            clear_previous = data.get("clear_previous", True)
            timestamp = data.get("timestamp", time.time())

            # Validate object_id/object_ids based on action
            if action in ["select", "deselect", "toggle"] and not object_id:
                logger.warning(f"Action {action} requires object_id")
                return None

            if action == "select_multiple" and not object_ids:
                logger.warning("Action select_multiple requires object_ids")
                return None

            return SelectionEventData(
                canvas_id=canvas_id,
                action=action,
                object_id=object_id,
                object_ids=object_ids,
                clear_previous=clear_previous,
                timestamp=timestamp,
            )

        except Exception as e:
            logger.error(f"Error extracting event data: {e}")
            return None

    def _process_selection_action(
        self, event_data: SelectionEventData
    ) -> Dict[str, Any]:
        """Process the selection action based on type."""
        try:
            if event_data.action == "select":
                return self._handle_select(event_data)
            elif event_data.action == "deselect":
                return self._handle_deselect(event_data)
            elif event_data.action == "toggle":
                return self._handle_toggle(event_data)
            elif event_data.action == "clear":
                return self._handle_clear(event_data)
            elif event_data.action == "select_multiple":
                return self._handle_select_multiple(event_data)
            else:
                logger.warning(f"Unknown selection action: {event_data.action}")
                return {
                    "action": "error",
                    "error": f"Unknown action: {event_data.action}",
                    "timestamp": event_data.timestamp,
                }

        except Exception as e:
            logger.error(f"Error processing selection action: {e}")
            return {
                "action": "error",
                "error": str(e),
                "timestamp": event_data.timestamp,
            }

    def _handle_select(self, event_data: SelectionEventData) -> Dict[str, Any]:
        """Handle single object selection."""
        old_selection = self.selection_state[event_data.canvas_id].copy()

        if event_data.clear_previous:
            self.selection_state[event_data.canvas_id].clear()

        self.selection_state[event_data.canvas_id].add(event_data.object_id)

        return {
            "action": "select",
            "object_id": event_data.object_id,
            "clear_previous": event_data.clear_previous,
            "old_selection": list(old_selection),
            "new_selection": list(self.selection_state[event_data.canvas_id]),
            "total_selected": len(self.selection_state[event_data.canvas_id]),
            "timestamp": event_data.timestamp,
        }

    def _handle_deselect(self, event_data: SelectionEventData) -> Dict[str, Any]:
        """Handle object deselection."""
        old_selection = self.selection_state[event_data.canvas_id].copy()
        was_selected = (
            event_data.object_id in self.selection_state[event_data.canvas_id]
        )

        self.selection_state[event_data.canvas_id].discard(event_data.object_id)

        return {
            "action": "deselect",
            "object_id": event_data.object_id,
            "was_selected": was_selected,
            "old_selection": list(old_selection),
            "new_selection": list(self.selection_state[event_data.canvas_id]),
            "total_selected": len(self.selection_state[event_data.canvas_id]),
            "timestamp": event_data.timestamp,
        }

    def _handle_toggle(self, event_data: SelectionEventData) -> Dict[str, Any]:
        """Handle selection toggle."""
        old_selection = self.selection_state[event_data.canvas_id].copy()
        was_selected = (
            event_data.object_id in self.selection_state[event_data.canvas_id]
        )

        if was_selected:
            self.selection_state[event_data.canvas_id].discard(event_data.object_id)
        else:
            self.selection_state[event_data.canvas_id].add(event_data.object_id)

        return {
            "action": "toggle",
            "object_id": event_data.object_id,
            "was_selected": was_selected,
            "now_selected": not was_selected,
            "old_selection": list(old_selection),
            "new_selection": list(self.selection_state[event_data.canvas_id]),
            "total_selected": len(self.selection_state[event_data.canvas_id]),
            "timestamp": event_data.timestamp,
        }

    def _handle_clear(self, event_data: SelectionEventData) -> Dict[str, Any]:
        """Handle clear all selections."""
        old_selection = self.selection_state[event_data.canvas_id].copy()
        cleared_count = len(old_selection)

        self.selection_state[event_data.canvas_id].clear()

        return {
            "action": "clear",
            "cleared_count": cleared_count,
            "old_selection": list(old_selection),
            "new_selection": [],
            "total_selected": 0,
            "timestamp": event_data.timestamp,
        }

    def _handle_select_multiple(self, event_data: SelectionEventData) -> Dict[str, Any]:
        """Handle multiple object selection."""
        old_selection = self.selection_state[event_data.canvas_id].copy()

        if event_data.clear_previous:
            self.selection_state[event_data.canvas_id].clear()

        # Add all object IDs to selection
        for object_id in event_data.object_ids:
            self.selection_state[event_data.canvas_id].add(object_id)

        return {
            "action": "select_multiple",
            "object_ids": event_data.object_ids,
            "clear_previous": event_data.clear_previous,
            "old_selection": list(old_selection),
            "new_selection": list(self.selection_state[event_data.canvas_id]),
            "total_selected": len(self.selection_state[event_data.canvas_id]),
            "timestamp": event_data.timestamp,
        }

    def _log_event(self, event_data: SelectionEventData, result: Dict[str, Any]):
        """Log event for debugging and monitoring."""
        try:
            log_entry = {
                "timestamp": event_data.timestamp,
                "canvas_id": event_data.canvas_id,
                "action": event_data.action,
                "result": result,
                "success": result.get("action") != "error",
            }

            self.event_history.append(log_entry)

            # Maintain history size
            if len(self.event_history) > self.max_history_size:
                self.event_history = self.event_history[-self.max_history_size :]

        except Exception as e:
            logger.error(f"Error logging event: {e}")

    def get_selection(self, canvas_id: str) -> Set[str]:
        """Get current selection for canvas."""
        return self.selection_state.get(canvas_id, set()).copy()

    def is_selected(self, canvas_id: str, object_id: str) -> bool:
        """Check if object is selected in canvas."""
        return object_id in self.selection_state.get(canvas_id, set())

    def get_selection_count(self, canvas_id: str) -> int:
        """Get number of selected objects in canvas."""
        return len(self.selection_state.get(canvas_id, set()))

    def clear_selection(self, canvas_id: str):
        """Clear selection for canvas."""
        if canvas_id in self.selection_state:
            self.selection_state[canvas_id].clear()

    def get_event_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent event history for debugging."""
        return self.event_history[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get selection handler statistics."""
        total_canvases = len(self.selection_state)
        total_selected = sum(
            len(selection) for selection in self.selection_state.values()
        )

        return {
            "total_canvases": total_canvases,
            "total_selected_objects": total_selected,
            "event_history_size": len(self.event_history),
            "successful_events": len(
                [e for e in self.event_history if e.get("success", False)]
            ),
            "failed_events": len(
                [e for e in self.event_history if not e.get("success", True)]
            ),
        }


# Global instance
selection_handler = SelectionHandler()


# Register with the event-driven engine
def _register_selection_handler():
    """Register the selection handler with the event-driven behavior engine."""
    try:

        def handler(event: Event):
            try:
                if (
                    event.type == EventType.USER_INTERACTION
                    and event.data.get("event_subtype") == "selection"
                ):
                    return selection_handler.handle_selection_event(event)
                return None
            except Exception as e:
                logger.error(f"Error in selection handler: {e}")
                return None

        # Import here to avoid circular imports
        from svgx_engine.runtime.event_driven_behavior_engine import (
            event_driven_behavior_engine,
        )

        event_driven_behavior_engine.register_handler(
            event_type=EventType.USER_INTERACTION,
            handler_id="ui_selection_handler",
            handler=handler,
            priority=0,
        )
        logger.info("Selection handler registered successfully")

    except Exception as e:
        logger.error(f"Failed to register selection handler: {e}")


_register_selection_handler()
