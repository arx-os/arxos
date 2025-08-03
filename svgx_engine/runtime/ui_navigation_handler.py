"""
SVGX Engine - UI Navigation Handler

Handles navigation events (pan, zoom, focus, reset) for SVGX canvases and viewports.
Manages viewport state, camera position, zoom levels, and focus targets.
Integrates with the event-driven behavior engine and provides feedback for navigation actions.
Follows Arxos engineering standards: absolute imports, global instances, modular/testable code, and comprehensive documentation.
"""

from typing import Dict, Any, List, Optional, Tuple
from svgx_engine.runtime.event_driven_behavior_engine import Event, EventType
import logging
from dataclasses import dataclass
from math import sqrt

logger = logging.getLogger(__name__)

@dataclass
class ViewportState:
    """Represents the current state of a viewport/camera."""
    x: float = 0.0
    y: float = 0.0
    zoom: float = 1.0
    min_zoom: float = 0.1
    max_zoom: float = 10.0
    focus_target: Optional[str] = None
    viewport_width: float = 800.0
    viewport_height: float = 600.0

class NavigationHandler:
    """
    Handles navigation state, viewport management, and camera controls for SVGX canvases.
    Supports pan, zoom, focus, and reset operations with smooth transitions.
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
        # {canvas_id: ViewportState}
        self.viewport_states: Dict[str, ViewportState] = {}
        # {canvas_id: list of navigation actions}
        self.navigation_history: Dict[str, List[Dict[str, Any]]] = {}
        # {canvas_id: focus targets}
        self.focus_targets: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def handle_navigation_event(self, event: Event) -> Optional[Dict[str, Any]]:
        """
        Handle navigation events (pan, zoom, focus, reset).
        
        Args:
            event: Navigation event with action and parameters
            
        Returns:
            Dict with action result and feedback, or None if invalid
        """
        try:
            canvas_id = event.data.get('canvas_id')
            action = event.data.get('action')
            
            if not canvas_id or not action:
                logger.warning(f"Invalid navigation event: missing canvas_id or action")
                return None
            
            # Initialize viewport state if not exists
            if canvas_id not in self.viewport_states:
                self.viewport_states[canvas_id] = ViewportState()
            
            if action == 'pan':
                return self._handle_pan(event, canvas_id)
            elif action == 'zoom':
                return self._handle_zoom(event, canvas_id)
            elif action == 'focus':
                return self._handle_focus(event, canvas_id)
            elif action == 'reset':
                return self._handle_reset(event, canvas_id)
            elif action == 'fit_to_view':
                return self._handle_fit_to_view(event, canvas_id)
            else:
                logger.warning(f"Unknown navigation action: {action}")
                return None
                
        except Exception as e:
            logger.error(f"Error handling navigation event: {e}")
            return None

    def _handle_pan(self, event: Event, canvas_id: str) -> Dict[str, Any]:
        """Handle pan navigation action."""
        dx = event.data.get('dx', 0.0)
        dy = event.data.get('dy', 0.0)
        
        viewport = self.viewport_states[canvas_id]
        old_x, old_y = viewport.x, viewport.y
        
        # Apply pan with zoom scaling
        viewport.x += dx / viewport.zoom
        viewport.y += dy / viewport.zoom
        
        # Record in history
        self._record_navigation_action(canvas_id, 'pan', {
            'dx': dx, 'dy': dy, 'old_x': old_x, 'old_y': old_y,
            'new_x': viewport.x, 'new_y': viewport.y
        })
        
        return {
            'action': 'pan',
            'dx': dx,
            'dy': dy,
            'old_position': (old_x, old_y),
            'new_position': (viewport.x, viewport.y),
            'viewport_state': self._get_viewport_state_dict(viewport)
        }

    def _handle_zoom(self, event: Event, canvas_id: str) -> Dict[str, Any]:
        """Handle zoom navigation action."""
        zoom_factor = event.data.get('zoom_factor', 1.0)
        center_x = event.data.get('center_x', 0.0)
        center_y = event.data.get('center_y', 0.0)
        
        viewport = self.viewport_states[canvas_id]
        old_zoom = viewport.zoom
        
        # Calculate new zoom with bounds checking
        new_zoom = old_zoom * zoom_factor
        new_zoom = max(viewport.min_zoom, min(viewport.max_zoom, new_zoom))
        
        # Apply zoom centered on specified point
        if center_x is not None and center_y is not None:
            # Adjust position to keep center point fixed
            scale_change = new_zoom / old_zoom
            viewport.x = center_x - (center_x - viewport.x) * scale_change
            viewport.y = center_y - (center_y - viewport.y) * scale_change
        
        viewport.zoom = new_zoom
        
        # Record in history
        self._record_navigation_action(canvas_id, 'zoom', {
            'zoom_factor': zoom_factor, 'center_x': center_x, 'center_y': center_y,
            'old_zoom': old_zoom, 'new_zoom': new_zoom
        })
        
        return {
            'action': 'zoom',
            'zoom_factor': zoom_factor,
            'center': (center_x, center_y),
            'old_zoom': old_zoom,
            'new_zoom': new_zoom,
            'viewport_state': self._get_viewport_state_dict(viewport)
        }

    def _handle_focus(self, event: Event, canvas_id: str) -> Dict[str, Any]:
        """Handle focus navigation action."""
        target_id = event.data.get('target_id')
        smooth = event.data.get('smooth', True)
        
        if not target_id:
            logger.warning("Focus action requires target_id")
            return None
        
        viewport = self.viewport_states[canvas_id]
        old_focus = viewport.focus_target
        
        # Get target position from focus targets
        target_info = self.focus_targets.get(canvas_id, {}).get(target_id)
        if not target_info:
            logger.warning(f"Focus target not found: {target_id}")
            return None
        
        target_x = target_info.get('x', 0.0)
        target_y = target_info.get('y', 0.0)
        target_zoom = target_info.get('zoom', viewport.zoom)
        
        # Update viewport to focus on target
        viewport.x = target_x - viewport.viewport_width / (2 * viewport.zoom)
        viewport.y = target_y - viewport.viewport_height / (2 * viewport.zoom)
        viewport.zoom = max(viewport.min_zoom, min(viewport.max_zoom, target_zoom))
        viewport.focus_target = target_id
        
        # Record in history
        self._record_navigation_action(canvas_id, 'focus', {
            'target_id': target_id, 'smooth': smooth,
            'old_focus': old_focus, 'new_focus': target_id,
            'target_position': (target_x, target_y), 'target_zoom': target_zoom
        })
        
        return {
            'action': 'focus',
            'target_id': target_id,
            'smooth': smooth,
            'old_focus': old_focus,
            'new_focus': target_id,
            'target_position': (target_x, target_y),
            'viewport_state': self._get_viewport_state_dict(viewport)
        }

    def _handle_reset(self, event: Event, canvas_id: str) -> Dict[str, Any]:
        """Handle reset navigation action."""
        viewport = self.viewport_states[canvas_id]
        old_state = self._get_viewport_state_dict(viewport)
        
        # Reset to default state
        viewport.x = 0.0
        viewport.y = 0.0
        viewport.zoom = 1.0
        viewport.focus_target = None
        
        # Record in history
        self._record_navigation_action(canvas_id, 'reset', {
            'old_state': old_state, 'new_state': self._get_viewport_state_dict(viewport)
        })
        
        return {
            'action': 'reset',
            'old_state': old_state,
            'new_state': self._get_viewport_state_dict(viewport)
        }

    def _handle_fit_to_view(self, event: Event, canvas_id: str) -> Dict[str, Any]:
        """Handle fit to view navigation action."""
        bounds = event.data.get('bounds')  # (min_x, min_y, max_x, max_y)
        padding = event.data.get('padding', 0.1)
        
        if not bounds or len(bounds) != 4:
            logger.warning("Fit to view requires bounds (min_x, min_y, max_x, max_y)")
            return None
        
        min_x, min_y, max_x, max_y = bounds
        viewport = self.viewport_states[canvas_id]
        old_state = self._get_viewport_state_dict(viewport)
        
        # Calculate fit parameters
        content_width = max_x - min_x
        content_height = max_y - min_y
        
        if content_width <= 0 or content_height <= 0:
            logger.warning("Invalid bounds for fit to view")
            return None
        
        # Calculate zoom to fit content with padding
        zoom_x = (viewport.viewport_width * (1 - padding)) / content_width
        zoom_y = (viewport.viewport_height * (1 - padding)) / content_height
        new_zoom = min(zoom_x, zoom_y, viewport.max_zoom)
        
        # Center the content
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        viewport.zoom = new_zoom
        viewport.x = center_x - viewport.viewport_width / (2 * new_zoom)
        viewport.y = center_y - viewport.viewport_height / (2 * new_zoom)
        
        # Record in history
        self._record_navigation_action(canvas_id, 'fit_to_view', {
            'bounds': bounds, 'padding': padding,
            'old_state': old_state, 'new_state': self._get_viewport_state_dict(viewport)
        })
        
        return {
            'action': 'fit_to_view',
            'bounds': bounds,
            'padding': padding,
            'old_state': old_state,
            'new_state': self._get_viewport_state_dict(viewport)
        }

    def _record_navigation_action(self, canvas_id: str, action: str, data: Dict[str, Any]):
        """Record navigation action in history."""
        if canvas_id not in self.navigation_history:
            self.navigation_history[canvas_id] = []
        
        self.navigation_history[canvas_id].append({
            'action': action,
            'timestamp': event.timestamp,
            'data': data
        })

    def _get_viewport_state_dict(self, viewport: ViewportState) -> Dict[str, Any]:
        """Convert viewport state to dictionary."""
        return {
            'x': viewport.x,
            'y': viewport.y,
            'zoom': viewport.zoom,
            'focus_target': viewport.focus_target,
            'viewport_width': viewport.viewport_width,
            'viewport_height': viewport.viewport_height
        }

    def get_viewport_state(self, canvas_id: str) -> Optional[ViewportState]:
        """Get current viewport state for canvas."""
        return self.viewport_states.get(canvas_id)

    def get_navigation_history(self, canvas_id: str) -> List[Dict[str, Any]]:
        """Get navigation history for canvas."""
        return self.navigation_history.get(canvas_id, [])

    def add_focus_target(self, canvas_id: str, target_id: str, x: float, y: float, zoom: Optional[float] = None):
        """Add a focus target for navigation."""
        if canvas_id not in self.focus_targets:
            self.focus_targets[canvas_id] = {}
        
        self.focus_targets[canvas_id][target_id] = {
            'x': x,
            'y': y,
            'zoom': zoom
        }

    def clear_history(self, canvas_id: str):
        """Clear navigation history for canvas."""
        if canvas_id in self.navigation_history:
            self.navigation_history[canvas_id].clear()

# Global instance
navigation_handler = NavigationHandler()

# Register with the event-driven engine
def _register_navigation_handler():
    """
    Handle events or exceptions

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = _register_navigation_handler(param)
        print(result)
    """
    def handler(event: Event):
        if event.type == EventType.USER_INTERACTION and event.data.get('event_subtype') == 'navigation':
            return navigation_handler.handle_navigation_event(event)
        return None
    
    # Import here to avoid circular imports
    from svgx_engine.runtime.event_driven_behavior_engine import event_driven_behavior_engine
    event_driven_behavior_engine.register_handler(
        event_type=EventType.USER_INTERACTION,
        handler_id='ui_navigation_handler',
        handler=handler,
        priority=2
    )

_register_navigation_handler() 