"""
SVGX Engine - UI Annotation Handler

Handles annotation events (create, update, delete, show, hide) for SVGX canvases and objects.
Manages annotation state, metadata, visibility, and positioning.
Integrates with the event-driven behavior engine and provides feedback for annotation actions.
Follows Arxos engineering standards: absolute imports, global instances, modular/testable code, and comprehensive documentation.
"""

from typing import Dict, Any, List, Optional, Tuple
from svgx_engine.runtime.event_driven_behavior_engine import Event, EventType
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class AnnotationType(Enum):
    """Types of annotations supported by the system."""
    TEXT = "text"
    MARKER = "marker"
    HIGHLIGHT = "highlight"
    NOTE = "note"
    MEASUREMENT = "measurement"
    CUSTOM = "custom"

class AnnotationVisibility(Enum):
    """Visibility states for annotations."""
    VISIBLE = "visible"
    HIDDEN = "hidden"
    COLLAPSED = "collapsed"

@dataclass
class Annotation:
    """Represents an annotation on an SVGX canvas."""
    id: str
    canvas_id: str
    target_id: Optional[str]  # Object being annotated, if any
    type: AnnotationType
    content: str
    position: Tuple[float, float]  # (x, y)
    metadata: Dict[str, Any]
    visibility: AnnotationVisibility = AnnotationVisibility.VISIBLE
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
    """
    Perform __post_init__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __post_init__(param)
        print(result)
    """
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = self.created_at

class AnnotationHandler:
    """
    Handles annotation state, CRUD operations, and visibility management for SVGX canvases.
    Supports various annotation types with metadata and positioning.
    """
    def __init__(self):
        # {canvas_id: {annotation_id: Annotation}}
        self.annotations: Dict[str, Dict[str, Annotation]] = {}
        # {canvas_id: list of annotation actions}
        self.annotation_history: Dict[str, List[Dict[str, Any]]] = {}
        # {canvas_id: {annotation_id: visibility_state}}
        self.visibility_states: Dict[str, Dict[str, AnnotationVisibility]] = {}

    def handle_annotation_event(self, event: Event) -> Optional[Dict[str, Any]]:
        """
        Handle annotation events (create, update, delete, show, hide).
        
        Args:
            event: Annotation event with action and parameters
            
        Returns:
            Dict with action result and feedback, or None if invalid
        """
        try:
            canvas_id = event.data.get('canvas_id')
            action = event.data.get('action')
            
            if not canvas_id or not action:
                logger.warning(f"Invalid annotation event: missing canvas_id or action")
                return None
            
            # Initialize canvas annotations if not exists
            if canvas_id not in self.annotations:
                self.annotations[canvas_id] = {}
                self.annotation_history[canvas_id] = []
                self.visibility_states[canvas_id] = {}
            
            if action == 'create':
                return self._handle_create(event, canvas_id)
            elif action == 'update':
                return self._handle_update(event, canvas_id)
            elif action == 'delete':
                return self._handle_delete(event, canvas_id)
            elif action == 'show':
                return self._handle_show(event, canvas_id)
            elif action == 'hide':
                return self._handle_hide(event, canvas_id)
            elif action == 'toggle':
                return self._handle_toggle(event, canvas_id)
            elif action == 'move':
                return self._handle_move(event, canvas_id)
            else:
                logger.warning(f"Unknown annotation action: {action}")
                return None
                
        except Exception as e:
            logger.error(f"Error handling annotation event: {e}")
            return None

    def _handle_create(self, event: Event, canvas_id: str) -> Dict[str, Any]:
        """Handle create annotation action."""
        annotation_id = event.data.get('annotation_id')
        target_id = event.data.get('target_id')
        annotation_type = AnnotationType(event.data.get('type', 'text'))
        content = event.data.get('content', '')
        position = event.data.get('position', (0.0, 0.0))
        metadata = event.data.get('metadata', {})
        
        if not annotation_id:
            logger.warning("Create annotation requires annotation_id")
            return None
        
        if annotation_id in self.annotations[canvas_id]:
            logger.warning(f"Annotation {annotation_id} already exists")
            return None
        
        # Create annotation
        annotation = Annotation(
            id=annotation_id,
            canvas_id=canvas_id,
            target_id=target_id,
            type=annotation_type,
            content=content,
            position=position,
            metadata=metadata
        )
        
        self.annotations[canvas_id][annotation_id] = annotation
        self.visibility_states[canvas_id][annotation_id] = AnnotationVisibility.VISIBLE
        
        # Record in history
        self._record_annotation_action(canvas_id, 'create', {
            'annotation_id': annotation_id,
            'target_id': target_id,
            'type': annotation_type.value,
            'content': content,
            'position': position,
            'metadata': metadata
        })
        
        return {
            'action': 'create',
            'annotation_id': annotation_id,
            'annotation': self._annotation_to_dict(annotation),
            'total_annotations': len(self.annotations[canvas_id])
        }

    def _handle_update(self, event: Event, canvas_id: str) -> Dict[str, Any]:
        """Handle update annotation action."""
        annotation_id = event.data.get('annotation_id')
        content = event.data.get('content')
        position = event.data.get('position')
        metadata = event.data.get('metadata')
        
        if not annotation_id:
            logger.warning("Update annotation requires annotation_id")
            return None
        
        annotation = self.annotations[canvas_id].get(annotation_id)
        if not annotation:
            logger.warning(f"Annotation {annotation_id} not found")
            return None
        
        # Update fields
        old_content = annotation.content
        old_position = annotation.position
        old_metadata = annotation.metadata.copy()
        
        if content is not None:
            annotation.content = content
        if position is not None:
            annotation.position = position
        if metadata is not None:
            annotation.metadata.update(metadata)
        
        annotation.updated_at = datetime.utcnow()
        
        # Record in history
        self._record_annotation_action(canvas_id, 'update', {
            'annotation_id': annotation_id,
            'old_content': old_content,
            'new_content': annotation.content,
            'old_position': old_position,
            'new_position': annotation.position,
            'old_metadata': old_metadata,
            'new_metadata': annotation.metadata
        })
        
        return {
            'action': 'update',
            'annotation_id': annotation_id,
            'annotation': self._annotation_to_dict(annotation),
            'changes': {
                'content': content is not None,
                'position': position is not None,
                'metadata': metadata is not None
            }
        }

    def _handle_delete(self, event: Event, canvas_id: str) -> Dict[str, Any]:
        """Handle delete annotation action."""
        annotation_id = event.data.get('annotation_id')
        
        if not annotation_id:
            logger.warning("Delete annotation requires annotation_id")
            return None
        
        annotation = self.annotations[canvas_id].get(annotation_id)
        if not annotation:
            logger.warning(f"Annotation {annotation_id} not found")
            return None
        
        # Store annotation data for history
        deleted_annotation = self._annotation_to_dict(annotation)
        
        # Delete annotation
        del self.annotations[canvas_id][annotation_id]
        if annotation_id in self.visibility_states[canvas_id]:
            del self.visibility_states[canvas_id][annotation_id]
        
        # Record in history
        self._record_annotation_action(canvas_id, 'delete', {
            'annotation_id': annotation_id,
            'deleted_annotation': deleted_annotation
        })
        
        return {
            'action': 'delete',
            'annotation_id': annotation_id,
            'deleted_annotation': deleted_annotation,
            'total_annotations': len(self.annotations[canvas_id])
        }

    def _handle_show(self, event: Event, canvas_id: str) -> Dict[str, Any]:
        """Handle show annotation action."""
        annotation_id = event.data.get('annotation_id')
        
        if not annotation_id:
            logger.warning("Show annotation requires annotation_id")
            return None
        
        if annotation_id not in self.annotations[canvas_id]:
            logger.warning(f"Annotation {annotation_id} not found")
            return None
        
        old_visibility = self.visibility_states[canvas_id].get(annotation_id, AnnotationVisibility.HIDDEN)
        self.visibility_states[canvas_id][annotation_id] = AnnotationVisibility.VISIBLE
        
        # Record in history
        self._record_annotation_action(canvas_id, 'show', {
            'annotation_id': annotation_id,
            'old_visibility': old_visibility.value,
            'new_visibility': AnnotationVisibility.VISIBLE.value
        })
        
        return {
            'action': 'show',
            'annotation_id': annotation_id,
            'old_visibility': old_visibility.value,
            'new_visibility': AnnotationVisibility.VISIBLE.value
        }

    def _handle_hide(self, event: Event, canvas_id: str) -> Dict[str, Any]:
        """Handle hide annotation action."""
        annotation_id = event.data.get('annotation_id')
        
        if not annotation_id:
            logger.warning("Hide annotation requires annotation_id")
            return None
        
        if annotation_id not in self.annotations[canvas_id]:
            logger.warning(f"Annotation {annotation_id} not found")
            return None
        
        old_visibility = self.visibility_states[canvas_id].get(annotation_id, AnnotationVisibility.VISIBLE)
        self.visibility_states[canvas_id][annotation_id] = AnnotationVisibility.HIDDEN
        
        # Record in history
        self._record_annotation_action(canvas_id, 'hide', {
            'annotation_id': annotation_id,
            'old_visibility': old_visibility.value,
            'new_visibility': AnnotationVisibility.HIDDEN.value
        })
        
        return {
            'action': 'hide',
            'annotation_id': annotation_id,
            'old_visibility': old_visibility.value,
            'new_visibility': AnnotationVisibility.HIDDEN.value
        }

    def _handle_toggle(self, event: Event, canvas_id: str) -> Dict[str, Any]:
        """Handle toggle annotation visibility action."""
        annotation_id = event.data.get('annotation_id')
        
        if not annotation_id:
            logger.warning("Toggle annotation requires annotation_id")
            return None
        
        if annotation_id not in self.annotations[canvas_id]:
            logger.warning(f"Annotation {annotation_id} not found")
            return None
        
        current_visibility = self.visibility_states[canvas_id].get(annotation_id, AnnotationVisibility.VISIBLE)
        new_visibility = AnnotationVisibility.HIDDEN if current_visibility == AnnotationVisibility.VISIBLE else AnnotationVisibility.VISIBLE
        
        self.visibility_states[canvas_id][annotation_id] = new_visibility
        
        # Record in history
        self._record_annotation_action(canvas_id, 'toggle', {
            'annotation_id': annotation_id,
            'old_visibility': current_visibility.value,
            'new_visibility': new_visibility.value
        })
        
        return {
            'action': 'toggle',
            'annotation_id': annotation_id,
            'old_visibility': current_visibility.value,
            'new_visibility': new_visibility.value
        }

    def _handle_move(self, event: Event, canvas_id: str) -> Dict[str, Any]:
        """Handle move annotation action."""
        annotation_id = event.data.get('annotation_id')
        new_position = event.data.get('position')
        
        if not annotation_id or new_position is None:
            logger.warning("Move annotation requires annotation_id and position")
            return None
        
        annotation = self.annotations[canvas_id].get(annotation_id)
        if not annotation:
            logger.warning(f"Annotation {annotation_id} not found")
            return None
        
        old_position = annotation.position
        annotation.position = new_position
        annotation.updated_at = datetime.utcnow()
        
        # Record in history
        self._record_annotation_action(canvas_id, 'move', {
            'annotation_id': annotation_id,
            'old_position': old_position,
            'new_position': new_position
        })
        
        return {
            'action': 'move',
            'annotation_id': annotation_id,
            'old_position': old_position,
            'new_position': new_position
        }

    def _record_annotation_action(self, canvas_id: str, action: str, data: Dict[str, Any]):
        """Record annotation action in history."""
        self.annotation_history[canvas_id].append({
            'action': action,
            'timestamp': datetime.utcnow(),
            'data': data
        })

    def _annotation_to_dict(self, annotation: Annotation) -> Dict[str, Any]:
        """Convert annotation to dictionary."""
        return {
            'id': annotation.id,
            'canvas_id': annotation.canvas_id,
            'target_id': annotation.target_id,
            'type': annotation.type.value,
            'content': annotation.content,
            'position': annotation.position,
            'metadata': annotation.metadata,
            'visibility': annotation.visibility.value,
            'created_at': annotation.created_at.isoformat(),
            'updated_at': annotation.updated_at.isoformat()
        }

    def get_annotation(self, canvas_id: str, annotation_id: str) -> Optional[Annotation]:
        """Get annotation by ID."""
        return self.annotations.get(canvas_id, {}).get(annotation_id)

    def get_annotations(self, canvas_id: str, visible_only: bool = False) -> List[Annotation]:
        """Get all annotations for canvas."""
        annotations = list(self.annotations.get(canvas_id, {}).values())
        if visible_only:
            annotations = [
                ann for ann in annotations
                if self.visibility_states.get(canvas_id, {}).get(ann.id, AnnotationVisibility.VISIBLE) == AnnotationVisibility.VISIBLE
            ]
        return annotations

    def get_annotations_by_target(self, canvas_id: str, target_id: str) -> List[Annotation]:
        """Get annotations for a specific target object."""
        return [
            ann for ann in self.annotations.get(canvas_id, {}).values()
            if ann.target_id == target_id
        ]

    def get_annotation_history(self, canvas_id: str) -> List[Dict[str, Any]]:
        """Get annotation history for canvas."""
        return self.annotation_history.get(canvas_id, [])

    def get_visibility_state(self, canvas_id: str, annotation_id: str) -> Optional[AnnotationVisibility]:
        """Get visibility state for annotation."""
        return self.visibility_states.get(canvas_id, {}).get(annotation_id)

    def clear_history(self, canvas_id: str):
        """Clear annotation history for canvas."""
        if canvas_id in self.annotation_history:
            self.annotation_history[canvas_id].clear()

# Global instance
annotation_handler = AnnotationHandler()

# Register with the event-driven engine
def _register_annotation_handler():
    """
    Handle events or exceptions

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = _register_annotation_handler(param)
        print(result)
    """
    def handler(event: Event):
        if event.type == EventType.USER_INTERACTION and event.data.get('event_subtype') == 'annotation':
            return annotation_handler.handle_annotation_event(event)
        return None
    
    # Import here to avoid circular imports
    from svgx_engine.runtime.event_driven_behavior_engine import event_driven_behavior_engine
    event_driven_behavior_engine.register_handler(
        event_type=EventType.USER_INTERACTION,
        handler_id='ui_annotation_handler',
        handler=handler,
        priority=3
    )

_register_annotation_handler() 