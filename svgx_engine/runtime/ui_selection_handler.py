"""
SVGX Engine - UI Selection Handler

Handles selection events (select, deselect, toggle, clear) for SVGX canvases and objects.
Manages selection state, multi-select operations, and selection feedback.
Integrates with the event-driven behavior engine and provides feedback for selection actions.
Follows Arxos engineering standards: absolute imports, global instances, modular/testable code, and comprehensive documentation.
"""

from typing import Dict, Any, List, Optional, Set
from svgx_engine.runtime.event_driven_behavior_engine import Event, EventType
import logging

logger = logging.getLogger(__name__)

class SelectionHandler:
    """
    Handles selection state for SVGX canvases and objects.
    Supports single-select, multi-select, and deselect operations.
    """
def __init__(self):
    """
    Perform __init__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        # {canvas_id: Set[object_id]}
        self.selection_state: Dict[str, Set[str]] = {}

    def handle_selection_event(self, event: Event) -> Optional[Dict[str, Any]]:
        """
        Handle selection events (select, deselect, toggle, clear).

        Args:
            event: Selection event with action and parameters

        Returns:
            Dict with action result and feedback, or None if invalid
        """
        try:
            canvas_id = event.data.get('canvas_id')
            action = event.data.get('action')

            if not canvas_id or not action:
                logger.warning(f"Invalid selection event: missing canvas_id or action")
                return None

            # Initialize selection state if not exists
            if canvas_id not in self.selection_state:
                self.selection_state[canvas_id] = set()

            if action == 'select':
                return self._handle_select(event, canvas_id)
            elif action == 'deselect':
                return self._handle_deselect(event, canvas_id)
            elif action == 'toggle':
                return self._handle_toggle(event, canvas_id)
            elif action == 'clear':
                return self._handle_clear(event, canvas_id)
            elif action == 'select_multiple':
                return self._handle_select_multiple(event, canvas_id)
            else:
                logger.warning(f"Unknown selection action: {action}")
                return None

        except Exception as e:
            logger.error(f"Error handling selection event: {e}")
            return None

    def _handle_select(self, event: Event, canvas_id: str) -> Dict[str, Any]:
        """Handle single object selection."""
        object_id = event.data.get('object_id')
        clear_previous = event.data.get('clear_previous', True)

        if not object_id:
            logger.warning("Select action requires object_id")
            return None

        old_selection = self.selection_state[canvas_id].copy()

        if clear_previous:
            self.selection_state[canvas_id].clear()

        self.selection_state[canvas_id].add(object_id)

        return {
            'action': 'select',
            'object_id': object_id,
            'clear_previous': clear_previous,
            'old_selection': list(old_selection),
            'new_selection': list(self.selection_state[canvas_id]),
            'total_selected': len(self.selection_state[canvas_id])
        }

    def _handle_deselect(self, event: Event, canvas_id: str) -> Dict[str, Any]:
        """Handle object deselection."""
        object_id = event.data.get('object_id')

        if not object_id:
            logger.warning("Deselect action requires object_id")
            return None

        old_selection = self.selection_state[canvas_id].copy()
        was_selected = object_id in self.selection_state[canvas_id]

        self.selection_state[canvas_id].discard(object_id)

        return {
            'action': 'deselect',
            'object_id': object_id,
            'was_selected': was_selected,
            'old_selection': list(old_selection),
            'new_selection': list(self.selection_state[canvas_id]),
            'total_selected': len(self.selection_state[canvas_id])
        }

    def _handle_toggle(self, event: Event, canvas_id: str) -> Dict[str, Any]:
        """Handle selection toggle."""
        object_id = event.data.get('object_id')

        if not object_id:
            logger.warning("Toggle action requires object_id")
            return None

        old_selection = self.selection_state[canvas_id].copy()
        was_selected = object_id in self.selection_state[canvas_id]

        if was_selected:
            self.selection_state[canvas_id].discard(object_id)
        else:
            self.selection_state[canvas_id].add(object_id)

        return {
            'action': 'toggle',
            'object_id': object_id,
            'was_selected': was_selected,
            'now_selected': not was_selected,
            'old_selection': list(old_selection),
            'new_selection': list(self.selection_state[canvas_id]),
            'total_selected': len(self.selection_state[canvas_id])
        }

    def _handle_clear(self, event: Event, canvas_id: str) -> Dict[str, Any]:
        """Handle clear all selections."""
        old_selection = self.selection_state[canvas_id].copy()
        cleared_count = len(old_selection)

        self.selection_state[canvas_id].clear()

        return {
            'action': 'clear',
            'cleared_count': cleared_count,
            'old_selection': list(old_selection),
            'new_selection': [],
            'total_selected': 0
        }

    def _handle_select_multiple(self, event: Event, canvas_id: str) -> Dict[str, Any]:
        """Handle multiple object selection."""
        object_ids = event.data.get('object_ids', [])
        clear_previous = event.data.get('clear_previous', True)

        if not object_ids:
            logger.warning("Select multiple action requires object_ids")
            return None

        old_selection = self.selection_state[canvas_id].copy()

        if clear_previous:
            self.selection_state[canvas_id].clear()

        # Add all object IDs to selection
        for object_id in object_ids:
            self.selection_state[canvas_id].add(object_id)

        return {
            'action': 'select_multiple',
            'object_ids': object_ids,
            'clear_previous': clear_previous,
            'old_selection': list(old_selection),
            'new_selection': list(self.selection_state[canvas_id]),
            'total_selected': len(self.selection_state[canvas_id])
        }

    def get_selection(self, canvas_id: str) -> Set[str]:
        """Get current selection for canvas."""
        return self.selection_state.get(canvas_id, set()).copy()

    def is_selected(self, canvas_id: str, object_id: str) -> bool:
        """Check if object is selected in canvas."""
        return object_id in self.selection_state.get(canvas_id, set()
    def get_selection_count(self, canvas_id: str) -> int:
        """Get number of selected objects in canvas."""
        return len(self.selection_state.get(canvas_id, set()))

    def clear_selection(self, canvas_id: str):
        """Clear selection for canvas."""
        if canvas_id in self.selection_state:
            self.selection_state[canvas_id].clear()

# Global instance
selection_handler = SelectionHandler()

# Register with the event-driven engine
def _register_selection_handler():
    """
    Handle events or exceptions

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = _register_selection_handler(param)
        print(result)
    """
def handler(event: Event):
        if event.type == EventType.USER_INTERACTION and event.data.get('event_subtype') == 'selection':
            return selection_handler.handle_selection_event(event)
        return None

    # Import here to avoid circular imports
    from svgx_engine.runtime.event_driven_behavior_engine import event_driven_behavior_engine
    event_driven_behavior_engine.register_handler(
        event_type=EventType.USER_INTERACTION,
        handler_id='ui_selection_handler',
        handler=handler,
        priority=0
    )

_register_selection_handler()
