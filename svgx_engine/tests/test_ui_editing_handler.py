"""
Tests for SVGX Engine UI Editing Handler

Covers:
- EditingHandler logic (edit, undo, redo, history, shadow model)
- Integration with event_driven_behavior_engine
- Edge cases and invalid input
- Follows Arxos standards: absolute imports, global instances, modular tests
"""

import pytest
from svgx_engine import event_driven_behavior_engine
from svgx_engine.runtime.ui_editing_handler import editing_handler, EditingHandler
from svgx_engine.runtime.event_driven_behavior_engine import (
    Event,
    EventType,
    EventPriority,
)
from datetime import datetime
from copy import deepcopy


@pytest.fixture(autouse=True)
def clear_editing_state():
    # Clear all editing state before each test
    editing_handler.shadow_model.clear()
    editing_handler.edit_history.clear()
    editing_handler.undo_stack.clear()
    editing_handler.redo_stack.clear()
    yield
    editing_handler.shadow_model.clear()
    editing_handler.edit_history.clear()
    editing_handler.undo_stack.clear()
    editing_handler.redo_stack.clear()


class TestEditingHandlerLogic:
    def test_edit_action(self):
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={
                "canvas_id": "canvas1",
                "object_id": "obj1",
                "action": "edit",
                "edit_data": {"x": 1, "y": 2},
            },
        )
        feedback = editing_handler.handle_editing_event(event)
        assert feedback["action"] == "edit"
        assert feedback["edit_data"] == {"x": 1, "y": 2}
        assert editing_handler.get_shadow_model("canvas1", "obj1") == {"x": 1, "y": 2}
        assert len(editing_handler.get_edit_history("canvas1")) == 1

    def test_undo_action(self):
        # Edit, then undo
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={
                "canvas_id": "canvas1",
                "object_id": "obj1",
                "action": "edit",
                "edit_data": {"x": 1},
            },
        )
        editing_handler.handle_editing_event(event)
        event2 = Event(
            id="evt2",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={
                "canvas_id": "canvas1",
                "object_id": "obj1",
                "action": "edit",
                "edit_data": {"x": 2},
            },
        )
        editing_handler.handle_editing_event(event2)
        undo_event = Event(
            id="evt3",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "object_id": "obj1", "action": "undo"},
        )
        feedback = editing_handler.handle_editing_event(undo_event)
        assert feedback["action"] == "undo"
        assert feedback["restored_state"] == {"x": 1}
        assert editing_handler.get_shadow_model("canvas1", "obj1") == {"x": 1}

    def test_redo_action(self):
        # Edit, undo, redo
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={
                "canvas_id": "canvas1",
                "object_id": "obj1",
                "action": "edit",
                "edit_data": {"x": 1},
            },
        )
        editing_handler.handle_editing_event(event)
        event2 = Event(
            id="evt2",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={
                "canvas_id": "canvas1",
                "object_id": "obj1",
                "action": "edit",
                "edit_data": {"x": 2},
            },
        )
        editing_handler.handle_editing_event(event2)
        undo_event = Event(
            id="evt3",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "object_id": "obj1", "action": "undo"},
        )
        editing_handler.handle_editing_event(undo_event)
        redo_event = Event(
            id="evt4",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "object_id": "obj1", "action": "redo"},
        )
        feedback = editing_handler.handle_editing_event(redo_event)
        assert feedback["action"] == "redo"
        assert feedback["restored_state"] == {"x": 2}
        assert editing_handler.get_shadow_model("canvas1", "obj1") == {"x": 2}

    def test_undo_empty(self):
        # Undo with empty stack
        undo_event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "object_id": "obj1", "action": "undo"},
        )
        feedback = editing_handler.handle_editing_event(undo_event)
        assert feedback["action"] == "undo"
        assert feedback["result"] == "empty"

    def test_redo_empty(self):
        # Redo with empty stack
        redo_event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "object_id": "obj1", "action": "redo"},
        )
        feedback = editing_handler.handle_editing_event(redo_event)
        assert feedback["action"] == "redo"
        assert feedback["result"] == "empty"

    def test_invalid_input(self):
        # Missing canvas_id
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"object_id": "obj1", "action": "edit", "edit_data": {"x": 1}},
        )
        feedback = editing_handler.handle_editing_event(event)
        assert feedback is None
        # Missing object_id
        event2 = Event(
            id="evt2",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el2",
            data={"canvas_id": "canvas1", "action": "edit", "edit_data": {"x": 1}},
        )
        feedback2 = editing_handler.handle_editing_event(event2)
        assert feedback2 is None
        # Unknown action
        event3 = Event(
            id="evt3",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el3",
            data={"canvas_id": "canvas1", "object_id": "obj1", "action": "unknown"},
        )
        feedback3 = editing_handler.handle_editing_event(event3)
        assert feedback3 is None


class TestEditingHandlerIntegration:
    def test_dispatch_editing_event(self):
        # Dispatch an editing event through the event-driven engine
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={
                "canvas_id": "canvas1",
                "object_id": "obj1",
                "action": "edit",
                "edit_data": {"x": 1},
                "event_subtype": "editing",
            },
        )
        result = event_driven_behavior_engine.process_event(event)
        # If process_event is async, run it
        if hasattr(result, "__await__"):
            import asyncio

            feedback = asyncio.get_event_loop().run_until_complete(result)
        else:
            feedback = result
        assert feedback is not None
        assert feedback.success is True
        assert feedback.result["handler_results"][0]["result"]["edit_data"] == {"x": 1}
        # State should be updated
        assert editing_handler.get_shadow_model("canvas1", "obj1") == {"x": 1}
