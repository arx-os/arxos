"""
Tests for SVGX Engine UI Selection Handler

Covers:
- SelectionHandler logic (single, multi-select, deselect, toggle, clear)
- Integration with event_driven_behavior_engine
- Edge cases and invalid input
- Follows Arxos standards: absolute imports, global instances, modular tests
"""

import pytest
from svgx_engine import event_driven_behavior_engine
from svgx_engine.runtime.ui_selection_handler import selection_handler, SelectionHandler
from svgx_engine.runtime.event_driven_behavior_engine import Event, EventType, EventPriority
from datetime import datetime

@pytest.fixture(autouse=True)
def clear_selection_state():
    # Clear all selection state before each test
    selection_handler.selection_state.clear()
    yield
    selection_handler.selection_state.clear()

class TestSelectionHandlerLogic:
    def test_single_select(self):
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "object_id": "obj1", "action": "select"}
        )
        feedback = selection_handler.handle_selection_event(event)
        assert feedback['selected'] == ["obj1"]
        assert selection_handler.get_selection("canvas1") == ["obj1"]

    def test_multi_select(self):
        # Select first object
        event1 = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "object_id": "obj1", "action": "select", "multi": True}
        )
        selection_handler.handle_selection_event(event1)
        # Select second object with multi
        event2 = Event(
            id="evt2",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el2",
            data={"canvas_id": "canvas1", "object_id": "obj2", "action": "select", "multi": True}
        )
        feedback = selection_handler.handle_selection_event(event2)
        assert set(feedback['selected']) == {"obj1", "obj2"}
        assert set(selection_handler.get_selection("canvas1")) == {"obj1", "obj2"}

    def test_deselect(self):
        # Select then deselect
        event1 = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "object_id": "obj1", "action": "select"}
        )
        selection_handler.handle_selection_event(event1)
        event2 = Event(
            id="evt2",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el2",
            data={"canvas_id": "canvas1", "object_id": "obj1", "action": "deselect"}
        )
        feedback = selection_handler.handle_selection_event(event2)
        assert feedback['selected'] == []
        assert selection_handler.get_selection("canvas1") == []

    def test_toggle(self):
        # Toggle select (should add), then toggle again (should remove)
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "object_id": "obj1", "action": "toggle"}
        )
        feedback1 = selection_handler.handle_selection_event(event)
        assert feedback1['selected'] == ["obj1"]
        feedback2 = selection_handler.handle_selection_event(event)
        assert feedback2['selected'] == []

    def test_clear(self):
        # Select two, then clear
        event1 = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "object_id": "obj1", "action": "select", "multi": True}
        )
        event2 = Event(
            id="evt2",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el2",
            data={"canvas_id": "canvas1", "object_id": "obj2", "action": "select", "multi": True}
        )
        selection_handler.handle_selection_event(event1)
        selection_handler.handle_selection_event(event2)
        clear_event = Event(
            id="evt3",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el3",
            data={"canvas_id": "canvas1", "object_id": "obj1", "action": "clear"}
        )
        feedback = selection_handler.handle_selection_event(clear_event)
        assert feedback['selected'] == []
        assert selection_handler.get_selection("canvas1") == []

    def test_invalid_input(self):
        # Missing canvas_id
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"object_id": "obj1", "action": "select"}
        )
        feedback = selection_handler.handle_selection_event(event)
        assert feedback is None
        # Missing object_id
        event2 = Event(
            id="evt2",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el2",
            data={"canvas_id": "canvas1", "action": "select"}
        )
        feedback2 = selection_handler.handle_selection_event(event2)
        assert feedback2 is None
        # Unknown action
        event3 = Event(
            id="evt3",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el3",
            data={"canvas_id": "canvas1", "object_id": "obj1", "action": "unknown"}
        )
        feedback3 = selection_handler.handle_selection_event(event3)
        assert feedback3 is None

class TestSelectionHandlerIntegration:
    def test_dispatch_selection_event(self):
        # Dispatch a selection event through the event-driven engine
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "object_id": "obj1", "action": "select", "event_subtype": "selection"}
        )
        result = event_driven_behavior_engine.process_event(event)
        # If process_event is async, run it
        if hasattr(result, '__await__'):
            import asyncio
            feedback = asyncio.get_event_loop().run_until_complete(result)
        else:
            feedback = result
        assert feedback is not None
        assert feedback.success is True
        assert feedback.result['handler_results'][0]['result']['selected'] == ["obj1"]
        # State should be updated
        assert selection_handler.get_selection("canvas1") == ["obj1"]
