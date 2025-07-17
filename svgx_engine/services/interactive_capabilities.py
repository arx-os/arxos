"""
SVGX Engine - Interactive Capabilities Service

Implements interactive capabilities including:
- Click/drag handlers with <16ms response time
- Hover effects and tooltips
- Snap-to constraint system
- Selection and multi-select
- Undo/redo functionality

CTO Directives:
- <16ms interaction response time
- Batch processing for non-critical updates
- Defer assembly-wide parametrics

Author: SVGX Engineering Team
Date: 2024
"""

import asyncio
import time
import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import threading
import numpy as np

logger = logging.getLogger(__name__)

class InteractionType(Enum):
    """Types of interactions supported."""
    CLICK = "click"
    DRAG_START = "drag_start"
    DRAG_MOVE = "drag_move"
    DRAG_END = "drag_end"
    HOVER = "hover"
    SELECT = "select"
    DESELECT = "deselect"
    SNAP = "snap"
    UNDO = "undo"
    REDO = "redo"

class SelectionMode(Enum):
    """Selection modes."""
    SINGLE = "single"
    MULTI = "multi"
    RECTANGLE = "rectangle"
    POLYGON = "polygon"

@dataclass
class InteractionEvent:
    """Interaction event data."""
    event_type: InteractionType
    element_id: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    modifiers: Optional[Dict[str, bool]] = None
    timestamp: float = field(default_factory=time.time)
    session_id: Optional[str] = None

@dataclass
class SelectionState:
    """Selection state management."""
    selected_elements: Set[str] = field(default_factory=set)
    hovered_element: Optional[str] = None
    selection_mode: SelectionMode = SelectionMode.SINGLE
    selection_rectangle: Optional[Dict[str, float]] = None

@dataclass
class DragState:
    """Drag operation state."""
    is_dragging: bool = False
    element_id: Optional[str] = None
    start_position: Optional[Dict[str, float]] = None
    current_position: Optional[Dict[str, float]] = None
    start_time: float = 0.0

@dataclass
class Constraint:
    """Geometric constraint."""
    constraint_id: str
    constraint_type: str  # snap, align, distance, angle
    target_element: str
    reference_element: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    active: bool = True

class ClickHandler:
    """Handles click interactions with <16ms response time."""
    
    def __init__(self):
        self.click_threshold_ms = 16.0
        self.double_click_threshold_ms = 300.0
        self.last_click_time = 0.0
        self.last_click_element = None
        
    async def handle_click(self, event: InteractionEvent, selection_state: SelectionState) -> Dict[str, Any]:
        """Handle click interaction."""
        start_time = time.time()
        
        try:
            # Check for double click
            is_double_click = (
                event.element_id == self.last_click_element and
                (event.timestamp - self.last_click_time) < self.double_click_threshold_ms
            )
            
            # Update click tracking
            self.last_click_time = event.timestamp
            self.last_click_element = event.element_id
            
            # Process click based on modifiers
            modifiers = event.modifiers or {}
            
            if modifiers.get("ctrl") or modifiers.get("meta"):
                # Multi-select mode
                await self._handle_multi_select_click(event, selection_state)
            else:
                # Single select mode
                await self._handle_single_select_click(event, selection_state)
            
            # Handle double click
            if is_double_click:
                await self._handle_double_click(event, selection_state)
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "element_id": event.element_id,
                "coordinates": event.coordinates,
                "is_double_click": is_double_click,
                "selection_updated": True,
                "response_time_ms": duration,
                "performance_target_met": duration <= self.click_threshold_ms
            }
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"Click handling failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": duration
            }
    
    async def _handle_single_select_click(self, event: InteractionEvent, selection_state: SelectionState):
        """Handle single select click."""
        if event.element_id:
            # Clear previous selection and select new element
            selection_state.selected_elements.clear()
            selection_state.selected_elements.add(event.element_id)
            selection_state.selection_mode = SelectionMode.SINGLE
    
    async def _handle_multi_select_click(self, event: InteractionEvent, selection_state: SelectionState):
        """Handle multi-select click."""
        if event.element_id:
            if event.element_id in selection_state.selected_elements:
                # Deselect if already selected
                selection_state.selected_elements.remove(event.element_id)
            else:
                # Add to selection
                selection_state.selected_elements.add(event.element_id)
            selection_state.selection_mode = SelectionMode.MULTI
    
    async def _handle_double_click(self, event: InteractionEvent, selection_state: SelectionState):
        """Handle double click (e.g., edit mode)."""
        # In real implementation, this would trigger edit mode
        logger.info(f"Double click on element {event.element_id}")

class DragHandler:
    """Handles drag interactions with performance optimization."""
    
    def __init__(self):
        self.drag_threshold_pixels = 5.0
        self.drag_start_time = 0.0
        self.current_drag_state = DragState()
        
    async def handle_drag_start(self, event: InteractionEvent) -> Dict[str, Any]:
        """Handle drag start interaction."""
        start_time = time.time()
        
        try:
            # Initialize drag state
            self.current_drag_state = DragState(
                is_dragging=True,
                element_id=event.element_id,
                start_position=event.coordinates,
                current_position=event.coordinates,
                start_time=event.timestamp
            )
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "drag_started": True,
                "element_id": event.element_id,
                "start_position": event.coordinates,
                "response_time_ms": duration
            }
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"Drag start failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": duration
            }
    
    async def handle_drag_move(self, event: InteractionEvent) -> Dict[str, Any]:
        """Handle drag move interaction."""
        start_time = time.time()
        
        try:
            if not self.current_drag_state.is_dragging:
                return {"success": False, "error": "No active drag operation"}
            
            # Update current position
            self.current_drag_state.current_position = event.coordinates
            
            # Calculate movement
            if self.current_drag_state.start_position:
                movement = {
                    "dx": event.coordinates["x"] - self.current_drag_state.start_position["x"],
                    "dy": event.coordinates["y"] - self.current_drag_state.start_position["y"],
                    "dz": event.coordinates.get("z", 0) - self.current_drag_state.start_position.get("z", 0)
                }
            else:
                movement = {"dx": 0, "dy": 0, "dz": 0}
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "is_dragging": True,
                "element_id": self.current_drag_state.element_id,
                "current_position": event.coordinates,
                "movement": movement,
                "response_time_ms": duration
            }
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"Drag move failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": duration
            }
    
    async def handle_drag_end(self, event: InteractionEvent) -> Dict[str, Any]:
        """Handle drag end interaction."""
        start_time = time.time()
        
        try:
            if not self.current_drag_state.is_dragging:
                return {"success": False, "error": "No active drag operation"}
            
            # Calculate final movement
            final_position = event.coordinates
            if self.current_drag_state.start_position:
                total_movement = {
                    "dx": final_position["x"] - self.current_drag_state.start_position["x"],
                    "dy": final_position["y"] - self.current_drag_state.start_position["y"],
                    "dz": final_position.get("z", 0) - self.current_drag_state.start_position.get("z", 0)
                }
            else:
                total_movement = {"dx": 0, "dy": 0, "dz": 0}
            
            # Reset drag state
            drag_duration = event.timestamp - self.current_drag_state.start_time
            self.current_drag_state = DragState()
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "drag_ended": True,
                "element_id": event.element_id,
                "final_position": final_position,
                "total_movement": total_movement,
                "drag_duration_ms": drag_duration * 1000,
                "response_time_ms": duration
            }
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"Drag end failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": duration
            }

class HoverHandler:
    """Handles hover interactions with tooltip support."""
    
    def __init__(self):
        self.hover_threshold_ms = 500.0  # Time to show tooltip
        self.hover_start_time = 0.0
        self.current_hover_element = None
        
    async def handle_hover(self, event: InteractionEvent) -> Dict[str, Any]:
        """Handle hover interaction."""
        start_time = time.time()
        
        try:
            # Update hover state
            if event.element_id != self.current_hover_element:
                self.current_hover_element = event.element_id
                self.hover_start_time = event.timestamp
            
            # Check if tooltip should be shown
            hover_duration = event.timestamp - self.hover_start_time
            show_tooltip = hover_duration >= self.hover_threshold_ms
            
            # Generate tooltip content
            tooltip_content = None
            if show_tooltip and event.element_id:
                tooltip_content = await self._generate_tooltip(event.element_id)
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "element_id": event.element_id,
                "coordinates": event.coordinates,
                "hover_duration_ms": hover_duration * 1000,
                "show_tooltip": show_tooltip,
                "tooltip_content": tooltip_content,
                "response_time_ms": duration
            }
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"Hover handling failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": duration
            }
    
    async def _generate_tooltip(self, element_id: str) -> Dict[str, Any]:
        """Generate tooltip content for element."""
        # In real implementation, this would fetch element properties
        return {
            "element_id": element_id,
            "type": "unknown",
            "properties": {},
            "actions": ["select", "edit", "delete"]
        }

class SnapToConstraintSystem:
    """Snap-to constraint system for precise positioning."""
    
    def __init__(self):
        self.grid_size = 1.0  # 1mm grid
        self.snap_threshold = 5.0  # pixels
        self.active_constraints: List[Constraint] = []
        
    async def apply_snap_constraints(self, coordinates: Dict[str, float], 
                                   nearby_elements: List[Dict]) -> Dict[str, float]:
        """Apply snap constraints to coordinates."""
        start_time = time.time()
        
        try:
            snapped_coordinates = coordinates.copy()
            
            # Grid snapping
            snapped_coordinates = self._snap_to_grid(snapped_coordinates)
            
            # Element snapping
            if nearby_elements:
                snapped_coordinates = await self._snap_to_elements(
                    snapped_coordinates, nearby_elements
                )
            
            # Constraint snapping
            if self.active_constraints:
                snapped_coordinates = await self._apply_constraints(
                    snapped_coordinates
                )
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "original_coordinates": coordinates,
                "snapped_coordinates": snapped_coordinates,
                "snap_applied": coordinates != snapped_coordinates,
                "response_time_ms": duration
            }
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"Snap constraint application failed: {e}")
            return {
                "original_coordinates": coordinates,
                "snapped_coordinates": coordinates,
                "snap_applied": False,
                "error": str(e),
                "response_time_ms": duration
            }
    
    def _snap_to_grid(self, coordinates: Dict[str, float]) -> Dict[str, float]:
        """Snap coordinates to grid."""
        return {
            "x": round(coordinates["x"] / self.grid_size) * self.grid_size,
            "y": round(coordinates["y"] / self.grid_size) * self.grid_size,
            "z": round(coordinates.get("z", 0) / self.grid_size) * self.grid_size
        }
    
    async def _snap_to_elements(self, coordinates: Dict[str, float], 
                               elements: List[Dict]) -> Dict[str, float]:
        """Snap to nearby elements."""
        best_snap = coordinates.copy()
        min_distance = float('inf')
        
        for element in elements:
            element_pos = element.get("position", {})
            if not element_pos:
                continue
            
            distance = np.sqrt(
                (coordinates["x"] - element_pos["x"]) ** 2 +
                (coordinates["y"] - element_pos["y"]) ** 2
            )
            
            if distance < self.snap_threshold and distance < min_distance:
                best_snap = element_pos.copy()
                min_distance = distance
        
        return best_snap
    
    async def _apply_constraints(self, coordinates: Dict[str, float]) -> Dict[str, float]:
        """Apply active constraints."""
        constrained_coordinates = coordinates.copy()
        
        for constraint in self.active_constraints:
            if not constraint.active:
                continue
            
            if constraint.constraint_type == "snap":
                # Apply snap constraint
                target_pos = constraint.parameters.get("target_position", {})
                if target_pos:
                    constrained_coordinates.update(target_pos)
            
            elif constraint.constraint_type == "align":
                # Apply alignment constraint
                axis = constraint.parameters.get("axis", "x")
                reference_value = constraint.parameters.get("reference_value", 0)
                constrained_coordinates[axis] = reference_value
        
        return constrained_coordinates
    
    def add_constraint(self, constraint: Constraint):
        """Add a new constraint."""
        self.active_constraints.append(constraint)
    
    def remove_constraint(self, constraint_id: str):
        """Remove a constraint."""
        self.active_constraints = [
            c for c in self.active_constraints if c.constraint_id != constraint_id
        ]

class UndoRedoManager:
    """Manages undo/redo functionality."""
    
    def __init__(self, max_history_size: int = 100):
        self.undo_stack: deque = deque(maxlen=max_history_size)
        self.redo_stack: deque = deque(maxlen=max_history_size)
        self.current_state = {}
        self.lock = threading.Lock()
        
    def save_state(self, state: Dict[str, Any], action_name: str):
        """Save current state for undo."""
        with self.lock:
            # Save current state to undo stack
            self.undo_stack.append({
                "state": self.current_state.copy(),
                "action_name": action_name,
                "timestamp": time.time()
            })
            
            # Update current state
            self.current_state = state.copy()
            
            # Clear redo stack when new action is performed
            self.redo_stack.clear()
    
    def undo(self) -> Optional[Dict[str, Any]]:
        """Undo last action."""
        with self.lock:
            if not self.undo_stack:
                return None
            
            # Get last state from undo stack
            last_action = self.undo_stack.pop()
            
            # Save current state to redo stack
            self.redo_stack.append({
                "state": self.current_state.copy(),
                "action_name": "redo",
                "timestamp": time.time()
            })
            
            # Restore previous state
            self.current_state = last_action["state"]
            
            return {
                "success": True,
                "restored_state": self.current_state,
                "action_name": last_action["action_name"],
                "can_undo": len(self.undo_stack) > 0,
                "can_redo": len(self.redo_stack) > 0
            }
    
    def redo(self) -> Optional[Dict[str, Any]]:
        """Redo last undone action."""
        with self.lock:
            if not self.redo_stack:
                return None
            
            # Get next state from redo stack
            next_action = self.redo_stack.pop()
            
            # Save current state to undo stack
            self.undo_stack.append({
                "state": self.current_state.copy(),
                "action_name": "undo",
                "timestamp": time.time()
            })
            
            # Restore next state
            self.current_state = next_action["state"]
            
            return {
                "success": True,
                "restored_state": self.current_state,
                "action_name": next_action["action_name"],
                "can_undo": len(self.undo_stack) > 0,
                "can_redo": len(self.redo_stack) > 0
            }
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self.redo_stack) > 0
    
    def get_history_info(self) -> Dict[str, Any]:
        """Get undo/redo history information."""
        return {
            "undo_stack_size": len(self.undo_stack),
            "redo_stack_size": len(self.redo_stack),
            "can_undo": self.can_undo(),
            "can_redo": self.can_redo()
        }

class InteractiveCapabilitiesService:
    """Main interactive capabilities service."""
    
    def __init__(self):
        self.click_handler = ClickHandler()
        self.drag_handler = DragHandler()
        self.hover_handler = HoverHandler()
        self.snap_system = SnapToConstraintSystem()
        self.undo_redo_manager = UndoRedoManager()
        
        # State management
        self.selection_state = SelectionState()
        self.performance_target_ms = 16.0
        
        # Performance monitoring
        self.performance_stats = {
            "total_interactions": 0,
            "successful_interactions": 0,
            "performance_target_met": 0,
            "average_response_time_ms": 0.0
        }
        
    async def handle_interaction(self, event: InteractionEvent) -> Dict[str, Any]:
        """Handle interaction event with performance monitoring."""
        start_time = time.time()
        
        try:
            # Route to appropriate handler
            if event.event_type == InteractionType.CLICK:
                result = await self.click_handler.handle_click(event, self.selection_state)
            elif event.event_type == InteractionType.DRAG_START:
                result = await self.drag_handler.handle_drag_start(event)
            elif event.event_type == InteractionType.DRAG_MOVE:
                result = await self.drag_handler.handle_drag_move(event)
            elif event.event_type == InteractionType.DRAG_END:
                result = await self.drag_handler.handle_drag_end(event)
            elif event.event_type == InteractionType.HOVER:
                result = await self.hover_handler.handle_hover(event)
            elif event.event_type == InteractionType.SELECT:
                result = await self._handle_select(event)
            elif event.event_type == InteractionType.DESELECT:
                result = await self._handle_deselect(event)
            elif event.event_type == InteractionType.SNAP:
                result = await self._handle_snap(event)
            elif event.event_type == InteractionType.UNDO:
                result = await self._handle_undo()
            elif event.event_type == InteractionType.REDO:
                result = await self._handle_redo()
            else:
                result = {"success": False, "error": f"Unknown interaction type: {event.event_type}"}
            
            # Update performance statistics
            await self._update_performance_stats(result, start_time)
            
            return result
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"Interaction handling failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": duration
            }
    
    async def _handle_select(self, event: InteractionEvent) -> Dict[str, Any]:
        """Handle select interaction."""
        start_time = time.time()
        
        try:
            if event.element_id:
                self.selection_state.selected_elements.add(event.element_id)
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "element_id": event.element_id,
                "selected_elements": list(self.selection_state.selected_elements),
                "response_time_ms": duration
            }
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": duration
            }
    
    async def _handle_deselect(self, event: InteractionEvent) -> Dict[str, Any]:
        """Handle deselect interaction."""
        start_time = time.time()
        
        try:
            if event.element_id and event.element_id in self.selection_state.selected_elements:
                self.selection_state.selected_elements.remove(event.element_id)
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "element_id": event.element_id,
                "selected_elements": list(self.selection_state.selected_elements),
                "response_time_ms": duration
            }
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": duration
            }
    
    async def _handle_snap(self, event: InteractionEvent) -> Dict[str, Any]:
        """Handle snap interaction."""
        start_time = time.time()
        
        try:
            if not event.coordinates:
                return {"success": False, "error": "No coordinates provided"}
            
            # Get nearby elements (in real implementation, this would query the scene)
            nearby_elements = []  # Placeholder
            
            result = await self.snap_system.apply_snap_constraints(
                event.coordinates, nearby_elements
            )
            
            duration = (time.time() - start_time) * 1000
            result["response_time_ms"] = duration
            
            return result
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": duration
            }
    
    async def _handle_undo(self) -> Dict[str, Any]:
        """Handle undo interaction."""
        start_time = time.time()
        
        try:
            result = self.undo_redo_manager.undo()
            
            duration = (time.time() - start_time) * 1000
            
            if result:
                result["response_time_ms"] = duration
                return result
            else:
                return {
                    "success": False,
                    "error": "Nothing to undo",
                    "response_time_ms": duration
                }
                
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": duration
            }
    
    async def _handle_redo(self) -> Dict[str, Any]:
        """Handle redo interaction."""
        start_time = time.time()
        
        try:
            result = self.undo_redo_manager.redo()
            
            duration = (time.time() - start_time) * 1000
            
            if result:
                result["response_time_ms"] = duration
                return result
            else:
                return {
                    "success": False,
                    "error": "Nothing to redo",
                    "response_time_ms": duration
                }
                
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": duration
            }
    
    async def _update_performance_stats(self, result: Dict[str, Any], start_time: float):
        """Update performance statistics."""
        duration = (time.time() - start_time) * 1000
        
        self.performance_stats["total_interactions"] += 1
        
        if result.get("success", False):
            self.performance_stats["successful_interactions"] += 1
            
            # Update average response time
            current_avg = self.performance_stats["average_response_time_ms"]
            total_interactions = self.performance_stats["successful_interactions"]
            new_avg = (current_avg * (total_interactions - 1) + duration) / total_interactions
            self.performance_stats["average_response_time_ms"] = new_avg
            
            # Check if performance target met
            if duration <= self.performance_target_ms:
                self.performance_stats["performance_target_met"] += 1
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = self.performance_stats.copy()
        if stats["total_interactions"] > 0:
            stats["success_rate"] = stats["successful_interactions"] / stats["total_interactions"]
            stats["performance_target_rate"] = stats["performance_target_met"] / stats["successful_interactions"]
        else:
            stats["success_rate"] = 0.0
            stats["performance_target_rate"] = 0.0
        return stats
    
    def get_selection_state(self) -> Dict[str, Any]:
        """Get current selection state."""
        return {
            "selected_elements": list(self.selection_state.selected_elements),
            "hovered_element": self.selection_state.hovered_element,
            "selection_mode": self.selection_state.selection_mode.value,
            "selection_rectangle": self.selection_state.selection_rectangle
        }
    
    def get_undo_redo_info(self) -> Dict[str, Any]:
        """Get undo/redo information."""
        return self.undo_redo_manager.get_history_info()

# Global instance
interactive_service = InteractiveCapabilitiesService()

async def handle_interaction_event(event_type: str, element_id: Optional[str] = None,
                                coordinates: Optional[Dict[str, float]] = None,
                                modifiers: Optional[Dict[str, bool]] = None,
                                session_id: Optional[str] = None) -> Dict[str, Any]:
    """Handle interaction event."""
    try:
        event = InteractionEvent(
            event_type=InteractionType(event_type),
            element_id=element_id,
            coordinates=coordinates,
            modifiers=modifiers,
            session_id=session_id
        )
        
        result = await interactive_service.handle_interaction(event)
        return result
        
    except Exception as e:
        logger.error(f"Interaction event handling failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def get_interaction_performance_stats() -> Dict[str, Any]:
    """Get interaction performance statistics."""
    return interactive_service.get_performance_stats()

def get_selection_state() -> Dict[str, Any]:
    """Get current selection state."""
    return interactive_service.get_selection_state()

def get_undo_redo_info() -> Dict[str, Any]:
    """Get undo/redo information."""
    return interactive_service.get_undo_redo_info() 