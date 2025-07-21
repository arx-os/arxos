from typing import Callable, Dict, Any, Optional
from .ui_event_schemas import UIEvent, SelectionEvent, EditingEvent, NavigationEvent, AnnotationEvent
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)

class UIEventDispatcher:
    """
    Dispatches validated UI events to registered handlers and emits feedback.
    Extensible for new event types and feedback mechanisms.
    """
    def __init__(self):
        self.handlers: Dict[str, Callable[[Any], Optional[dict]]] = {}
        self._register_default_handlers()

    def _register_default_handlers(self):
        self.handlers = {
            "selection": self.handle_selection,
            "editing": self.handle_editing,
            "navigation": self.handle_navigation,
            "annotation": self.handle_annotation,
        }

    def register_handler(self, event_type: str, handler: Callable[[Any], Optional[dict]]):
        self.handlers[event_type] = handler

    def dispatch(self, event_data: dict) -> Optional[dict]:
        """
        Validate and dispatch a UI event. Returns feedback if any.
        """
        try:
            event = self._validate_event(event_data)
            handler = self.handlers.get(event.event_type)
            if handler:
                logger.info(f"Dispatching {event.event_type} event to handler.")
                return handler(event)
            else:
                logger.warning(f"No handler registered for event type: {event.event_type}")
        except ValidationError as ve:
            logger.error(f"UI event validation failed: {ve}")
        except Exception as e:
            logger.error(f"Error dispatching UI event: {e}")
        return None

    def _validate_event(self, event_data: dict) -> UIEvent:
        etype = event_data.get("event_type")
        if etype == "selection":
            return SelectionEvent.parse_obj(event_data)
        elif etype == "editing":
            return EditingEvent.parse_obj(event_data)
        elif etype == "navigation":
            return NavigationEvent.parse_obj(event_data)
        elif etype == "annotation":
            return AnnotationEvent.parse_obj(event_data)
        else:
            raise ValidationError(f"Unknown event_type: {etype}")

    # Default handler stubs (to be extended)
    def handle_selection(self, event: SelectionEvent) -> Optional[dict]:
        logger.info(f"[Dispatcher] Handling selection event: {event}")
        # TODO: Integrate with runtime, emit feedback
        return None

    def handle_editing(self, event: EditingEvent) -> Optional[dict]:
        logger.info(f"[Dispatcher] Handling editing event: {event}")
        # TODO: Integrate with runtime, emit feedback
        return None

    def handle_navigation(self, event: NavigationEvent) -> Optional[dict]:
        logger.info(f"[Dispatcher] Handling navigation event: {event}")
        # TODO: Integrate with runtime, emit feedback
        return None

    def handle_annotation(self, event: AnnotationEvent) -> Optional[dict]:
        logger.info(f"[Dispatcher] Handling annotation event: {event}")
        # TODO: Integrate with runtime, emit feedback
        return None 