"""
SVGX Engine - UI Editing Handler

Handles editing events (edit, undo, redo) for SVGX canvases and objects.
Maintains edit history, undo/redo stack, and a shadow model for each canvas/object.
Integrates with the event-driven behavior engine and provides feedback for editing actions.
Follows Arxos engineering standards: absolute imports, global instances, modular/testable code, and comprehensive documentation.
"""

from typing import Dict, Any, List, Optional
from svgx_engine.runtime.event_driven_behavior_engine import Event, EventType
import logging
from copy import deepcopy

logger = logging.getLogger(__name__)

class EditingHandler:
    """
    Handles editing state, edit history, undo/redo, and shadow model for SVGX canvases.
    Supports modular editing actions and feedback.
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
        # {canvas_id: {object_id: shadow_model}}
        self.shadow_model: Dict[str, Dict[str, Any]] = {}
        # {canvas_id: list of edit actions}
        self.edit_history: Dict[str, List[Dict[str, Any]]] = {}
        # {canvas_id: undo stack}
        self.undo_stack: Dict[str, List[Dict[str, Any]]] = {}
        # {canvas_id: redo stack}
        self.redo_stack: Dict[str, List[Dict[str, Any]]] = {}

    def handle_editing_event(self, event: Event) -> Optional[Dict[str, Any]]:
        """
        Handle editing events (edit, undo, redo).

        Args:
            event: Editing event with action and parameters

        Returns:
            Dict with action result and feedback, or None if invalid
        """
        try:
            canvas_id = event.data.get('canvas_id')
            action = event.data.get('action')

            if not canvas_id or not action:
                logger.warning(f"Invalid editing event: missing canvas_id or action")
                return None

            # Initialize editing state if not exists
            if canvas_id not in self.shadow_model:
                self.shadow_model[canvas_id] = {}
                self.edit_history[canvas_id] = []
                self.undo_stack[canvas_id] = []
                self.redo_stack[canvas_id] = []

            if action == 'edit':
                return self._handle_edit(event, canvas_id)
            elif action == 'undo':
                return self._handle_undo(event, canvas_id)
            elif action == 'redo':
                return self._handle_redo(event, canvas_id)
            else:
                logger.warning(f"Unknown editing action: {action}")
                return None

        except Exception as e:
            logger.error(f"Error handling editing event: {e}")
            return None

    def _handle_edit(self, event: Event, canvas_id: str) -> Dict[str, Any]:
        """Handle edit action."""
        object_id = event.data.get('object_id')
        edit_data = event.data.get('edit_data', {})

        if not object_id:
            logger.warning("Edit action requires object_id")
            return None

        # Store current state for undo
        current_state = self.shadow_model[canvas_id].get(object_id, {})
        if current_state:
            self.undo_stack[canvas_id].append({
                'object_id': object_id,
                'state': deepcopy(current_state),
                'timestamp': event.timestamp
            })

        # Apply edit to shadow model
        if object_id not in self.shadow_model[canvas_id]:
            self.shadow_model[canvas_id][object_id] = {}

        self.shadow_model[canvas_id][object_id].update(edit_data)

        # Clear redo stack when new edit is made
        self.redo_stack[canvas_id].clear()

        # Record in history
        self.edit_history[canvas_id].append({
            'action': 'edit',
            'object_id': object_id,
            'edit_data': edit_data,
            'timestamp': event.timestamp
        })

        return {
            'action': 'edit',
            'object_id': object_id,
            'edit_data': edit_data,
            'shadow_model': deepcopy(self.shadow_model[canvas_id][object_id])
        }

    def _handle_undo(self, event: Event, canvas_id: str) -> Dict[str, Any]:
        """Handle undo action."""
        if not self.undo_stack[canvas_id]:
            return {
                'action': 'undo',
                'result': 'empty'
            }

        # Pop last edit from undo stack
        last_edit = self.undo_stack[canvas_id].pop()
        object_id = last_edit['object_id']

        # Store current state for redo
        current_state = self.shadow_model[canvas_id].get(object_id, {})
        if current_state:
            self.redo_stack[canvas_id].append({
                'object_id': object_id,
                'state': deepcopy(current_state),
                'timestamp': event.timestamp
            })

        # Restore previous state
        self.shadow_model[canvas_id][object_id] = last_edit['state']

        # Record in history
        self.edit_history[canvas_id].append({
            'action': 'undo',
            'object_id': object_id,
            'restored_state': last_edit['state'],
            'timestamp': event.timestamp
        })

        return {
            'action': 'undo',
            'object_id': object_id,
            'restored_state': last_edit['state']
        }

    def _handle_redo(self, event: Event, canvas_id: str) -> Dict[str, Any]:
        """Handle redo action."""
        if not self.redo_stack[canvas_id]:
            return {
                'action': 'redo',
                'result': 'empty'
            }

        # Pop last edit from redo stack
        last_edit = self.redo_stack[canvas_id].pop()
        object_id = last_edit['object_id']

        # Store current state for undo
        current_state = self.shadow_model[canvas_id].get(object_id, {})
        if current_state:
            self.undo_stack[canvas_id].append({
                'object_id': object_id,
                'state': deepcopy(current_state),
                'timestamp': event.timestamp
            })

        # Restore redo state
        self.shadow_model[canvas_id][object_id] = last_edit['state']

        # Record in history
        self.edit_history[canvas_id].append({
            'action': 'redo',
            'object_id': object_id,
            'restored_state': last_edit['state'],
            'timestamp': event.timestamp
        })

        return {
            'action': 'redo',
            'object_id': object_id,
            'restored_state': last_edit['state']
        }

    def get_shadow_model(self, canvas_id: str, object_id: str) -> Any:
        """Get shadow model for object."""
        return deepcopy(self.shadow_model.get(canvas_id, {}).get(object_id, {})
    def get_edit_history(self, canvas_id: str) -> List[Dict[str, Any]]:
        """Get edit history for canvas."""
        return self.edit_history.get(canvas_id, [])

    def clear_history(self, canvas_id: str):
        """Clear edit history for canvas."""
        if canvas_id in self.edit_history:
            self.edit_history[canvas_id].clear()
        if canvas_id in self.undo_stack:
            self.undo_stack[canvas_id].clear()
        if canvas_id in self.redo_stack:
            self.redo_stack[canvas_id].clear()

# Global instance
editing_handler = EditingHandler()

# Register with the event-driven engine
def _register_editing_handler():
    """
    Handle events or exceptions

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = _register_editing_handler(param)
        print(result)
    """
def handler(event: Event):
        if event.type == EventType.USER_INTERACTION and event.data.get('event_subtype') == 'editing':
            return editing_handler.handle_editing_event(event)
        return None

    # Import here to avoid circular imports
    from svgx_engine.runtime.event_driven_behavior_engine import event_driven_behavior_engine
    event_driven_behavior_engine.register_handler(
        event_type=EventType.USER_INTERACTION,
        handler_id='ui_editing_handler',
        handler=handler,
        priority=1
    )

_register_editing_handler()
