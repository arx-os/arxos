"""
UI Event Dispatcher - Event Routing and Processing

This module provides event dispatching and routing functionality for
UI events in the SVGX Engine behavior system.
"""

from typing import Dict, Any, Callable, Optional
import logging
from svgx_engine.runtime.behavior.ui_event_schemas import UIEvent, SelectionEvent, EditingEvent, NavigationEvent, AnnotationEvent

logger = logging.getLogger(__name__)

class UIEventDispatcher:
    """
    UI Event Dispatcher for routing and processing UI events.
    
    Provides centralized event dispatching for UI interactions
    including selection, editing, navigation, and annotation events.
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
        self.handlers: Dict[str, Callable] = {}
        self.event_history: list = []
        self.stats = {
            "total_events": 0,
            "events_by_type": {},
            "errors": 0
        }
    
    def register_handler(self, event_type: str, handler: Callable) -> None:
        """
        Register a handler for a specific event type.
        
        Args:
            event_type: Type of event to handle
            handler: Function to call when event occurs
        """
        self.handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")
    
    def dispatch_event(self, event: UIEvent) -> Optional[Dict[str, Any]]:
        """
        Dispatch an event to the appropriate handler.
        
        Args:
            event: UI event to dispatch
            
        Returns:
            Handler result or None if no handler found
        """
        try:
            self.stats["total_events"] += 1
            event_type = event.event_type
            
            # Update event type statistics
            if event_type not in self.stats["events_by_type"]:
                self.stats["events_by_type"][event_type] = 0
            self.stats["events_by_type"][event_type] += 1
            
            # Store event in history
            self.event_history.append({
                "event_type": event_type,
                "timestamp": event.timestamp,
                "payload": event.payload
            })
            
            # Find and call appropriate handler
            if event_type in self.handlers:
                handler = self.handlers[event_type]
                result = handler(event)
                logger.debug(f"Dispatched {event_type} event to handler")
                return result
            else:
                logger.warning(f"No handler registered for event type: {event_type}")
                return None
                
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Error dispatching event {event.event_type}: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get dispatcher statistics."""
        return {
            "total_events": self.stats["total_events"],
            "events_by_type": self.stats["events_by_type"],
            "errors": self.stats["errors"],
            "history_size": len(self.event_history)
        }
    
    def clear_history(self) -> None:
        """Clear event history."""
        self.event_history.clear()
        logger.info("Event history cleared")

# Version and metadata
__version__ = "1.0.0"
__description__ = "UI event dispatcher for SVGX Engine"

# Export all event types and dispatcher
__all__ = [
    "UIEventDispatcher",
    "UIEvent",
    "SelectionEvent",
    "EditingEvent", 
    "NavigationEvent",
    "AnnotationEvent"
] 