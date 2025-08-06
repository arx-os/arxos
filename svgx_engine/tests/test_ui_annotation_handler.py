"""
Tests for SVGX Engine UI Annotation Handler

Covers:
- AnnotationHandler logic (create, update, delete, show, hide, toggle, move)
- Integration with event_driven_behavior_engine
- Edge cases and invalid input
- Follows Arxos standards: absolute imports, global instances, modular tests
"""

import pytest
from svgx_engine import event_driven_behavior_engine
from svgx_engine.runtime.ui_annotation_handler import (
    annotation_handler,
    AnnotationHandler,
    Annotation,
    AnnotationType,
    AnnotationVisibility,
)
from svgx_engine.runtime.event_driven_behavior_engine import (
    Event,
    EventType,
    EventPriority,
)
from datetime import datetime


@pytest.fixture(autouse=True)
def clear_annotation_state():
    # Clear all annotation state before each test
    annotation_handler.annotations.clear()
    annotation_handler.annotation_history.clear()
    annotation_handler.visibility_states.clear()
    yield
    annotation_handler.annotations.clear()
    annotation_handler.annotation_history.clear()
    annotation_handler.visibility_states.clear()


class TestAnnotationHandlerLogic:
    def test_create_annotation(self):
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={
                "canvas_id": "canvas1",
                "action": "create",
                "annotation_id": "ann1",
                "target_id": "obj1",
                "type": "text",
                "content": "Test annotation",
                "position": (100.0, 200.0),
                "metadata": {"color": "red", "size": 12},
            },
        )
        feedback = annotation_handler.handle_annotation_event(event)
        assert feedback["action"] == "create"
        assert feedback["annotation_id"] == "ann1"
        assert feedback["annotation"]["content"] == "Test annotation"
        assert feedback["annotation"]["position"] == (100.0, 200.0)
        assert feedback["annotation"]["type"] == "text"
        assert feedback["annotation"]["metadata"]["color"] == "red"
        assert feedback["total_annotations"] == 1
        assert len(annotation_handler.get_annotation_history("canvas1")) == 1

    def test_create_annotation_duplicate_id(self):
        # Create first annotation
        event1 = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={
                "canvas_id": "canvas1",
                "action": "create",
                "annotation_id": "ann1",
                "content": "First annotation",
            },
        )
        annotation_handler.handle_annotation_event(event1)

        # Try to create duplicate
        event2 = Event(
            id="evt2",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={
                "canvas_id": "canvas1",
                "action": "create",
                "annotation_id": "ann1",
                "content": "Duplicate annotation",
            },
        )
        feedback = annotation_handler.handle_annotation_event(event2)
        assert feedback is None

    def test_update_annotation(self):
        # Create annotation first
        create_event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={
                "canvas_id": "canvas1",
                "action": "create",
                "annotation_id": "ann1",
                "content": "Original content",
                "position": (100.0, 200.0),
            },
        )
        annotation_handler.handle_annotation_event(create_event)

        # Update annotation
        update_event = Event(
            id="evt2",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={
                "canvas_id": "canvas1",
                "action": "update",
                "annotation_id": "ann1",
                "content": "Updated content",
                "position": (150.0, 250.0),
                "metadata": {"color": "blue"},
            },
        )
        feedback = annotation_handler.handle_annotation_event(update_event)
        assert feedback["action"] == "update"
        assert feedback["annotation_id"] == "ann1"
        assert feedback["annotation"]["content"] == "Updated content"
        assert feedback["annotation"]["position"] == (150.0, 250.0)
        assert feedback["annotation"]["metadata"]["color"] == "blue"
        assert feedback["changes"]["content"] == True
        assert feedback["changes"]["position"] == True
        assert feedback["changes"]["metadata"] == True

    def test_update_nonexistent_annotation(self):
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={
                "canvas_id": "canvas1",
                "action": "update",
                "annotation_id": "nonexistent",
                "content": "Updated content",
            },
        )
        feedback = annotation_handler.handle_annotation_event(event)
        assert feedback is None

    def test_delete_annotation(self):
        # Create annotation first
        create_event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={
                "canvas_id": "canvas1",
                "action": "create",
                "annotation_id": "ann1",
                "content": "Test annotation",
            },
        )
        annotation_handler.handle_annotation_event(create_event)

        # Delete annotation
        delete_event = Event(
            id="evt2",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "delete", "annotation_id": "ann1"},
        )
        feedback = annotation_handler.handle_annotation_event(delete_event)
        assert feedback["action"] == "delete"
        assert feedback["annotation_id"] == "ann1"
        assert feedback["deleted_annotation"]["content"] == "Test annotation"
        assert feedback["total_annotations"] == 0
        assert annotation_handler.get_annotation("canvas1", "ann1") is None

    def test_delete_nonexistent_annotation(self):
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={
                "canvas_id": "canvas1",
                "action": "delete",
                "annotation_id": "nonexistent",
            },
        )
        feedback = annotation_handler.handle_annotation_event(event)
        assert feedback is None

    def test_show_annotation(self):
        # Create annotation first
        create_event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={
                "canvas_id": "canvas1",
                "action": "create",
                "annotation_id": "ann1",
                "content": "Test annotation",
            },
        )
        annotation_handler.handle_annotation_event(create_event)

        # Hide it first
        hide_event = Event(
            id="evt2",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "hide", "annotation_id": "ann1"},
        )
        annotation_handler.handle_annotation_event(hide_event)

        # Show annotation
        show_event = Event(
            id="evt3",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "show", "annotation_id": "ann1"},
        )
        feedback = annotation_handler.handle_annotation_event(show_event)
        assert feedback["action"] == "show"
        assert feedback["annotation_id"] == "ann1"
        assert feedback["old_visibility"] == "hidden"
        assert feedback["new_visibility"] == "visible"
        assert (
            annotation_handler.get_visibility_state("canvas1", "ann1")
            == AnnotationVisibility.VISIBLE
        )

    def test_hide_annotation(self):
        # Create annotation first
        create_event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={
                "canvas_id": "canvas1",
                "action": "create",
                "annotation_id": "ann1",
                "content": "Test annotation",
            },
        )
        annotation_handler.handle_annotation_event(create_event)

        # Hide annotation
        hide_event = Event(
            id="evt2",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "hide", "annotation_id": "ann1"},
        )
        feedback = annotation_handler.handle_annotation_event(hide_event)
        assert feedback["action"] == "hide"
        assert feedback["annotation_id"] == "ann1"
        assert feedback["old_visibility"] == "visible"
        assert feedback["new_visibility"] == "hidden"
        assert (
            annotation_handler.get_visibility_state("canvas1", "ann1")
            == AnnotationVisibility.HIDDEN
        )

    def test_toggle_annotation(self):
        # Create annotation first
        create_event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={
                "canvas_id": "canvas1",
                "action": "create",
                "annotation_id": "ann1",
                "content": "Test annotation",
            },
        )
        annotation_handler.handle_annotation_event(create_event)

        # Toggle to hidden
        toggle_event1 = Event(
            id="evt2",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "toggle", "annotation_id": "ann1"},
        )
        feedback1 = annotation_handler.handle_annotation_event(toggle_event1)
        assert feedback1["action"] == "toggle"
        assert feedback1["old_visibility"] == "visible"
        assert feedback1["new_visibility"] == "hidden"

        # Toggle back to visible
        toggle_event2 = Event(
            id="evt3",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "toggle", "annotation_id": "ann1"},
        )
        feedback2 = annotation_handler.handle_annotation_event(toggle_event2)
        assert feedback2["action"] == "toggle"
        assert feedback2["old_visibility"] == "hidden"
        assert feedback2["new_visibility"] == "visible"

    def test_move_annotation(self):
        # Create annotation first
        create_event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={
                "canvas_id": "canvas1",
                "action": "create",
                "annotation_id": "ann1",
                "content": "Test annotation",
                "position": (100.0, 200.0),
            },
        )
        annotation_handler.handle_annotation_event(create_event)

        # Move annotation
        move_event = Event(
            id="evt2",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={
                "canvas_id": "canvas1",
                "action": "move",
                "annotation_id": "ann1",
                "position": (150.0, 250.0),
            },
        )
        feedback = annotation_handler.handle_annotation_event(move_event)
        assert feedback["action"] == "move"
        assert feedback["annotation_id"] == "ann1"
        assert feedback["old_position"] == (100.0, 200.0)
        assert feedback["new_position"] == (150.0, 250.0)

        # Verify annotation was moved
        annotation = annotation_handler.get_annotation("canvas1", "ann1")
        assert annotation.position == (150.0, 250.0)

    def test_invalid_input(self):
        # Missing canvas_id
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"action": "create", "annotation_id": "ann1"},
        )
        feedback = annotation_handler.handle_annotation_event(event)
        assert feedback is None

        # Missing action
        event2 = Event(
            id="evt2",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1"},
        )
        feedback2 = annotation_handler.handle_annotation_event(event2)
        assert feedback2 is None

        # Unknown action
        event3 = Event(
            id="evt3",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "unknown"},
        )
        feedback3 = annotation_handler.handle_annotation_event(event3)
        assert feedback3 is None

    def test_annotation_types(self):
        # Test different annotation types
        types = ["text", "marker", "highlight", "note", "measurement", "custom"]

        for i, annotation_type in enumerate(types):
            event = Event(
                id=f"evt{i}",
                type=EventType.USER_INTERACTION,
                priority=EventPriority.NORMAL,
                timestamp=datetime.utcnow(),
                element_id="el1",
                data={
                    "canvas_id": "canvas1",
                    "action": "create",
                    "annotation_id": f"ann{i}",
                    "type": annotation_type,
                    "content": f"Test {annotation_type}",
                },
            )
            feedback = annotation_handler.handle_annotation_event(event)
            assert feedback["annotation"]["type"] == annotation_type

    def test_get_annotations_visible_only(self):
        # Create multiple annotations
        for i in range(3):
            create_event = Event(
                id=f"evt{i}",
                type=EventType.USER_INTERACTION,
                priority=EventPriority.NORMAL,
                timestamp=datetime.utcnow(),
                element_id="el1",
                data={
                    "canvas_id": "canvas1",
                    "action": "create",
                    "annotation_id": f"ann{i}",
                    "content": f"Test annotation {i}",
                },
            )
            annotation_handler.handle_annotation_event(create_event)

        # Hide one annotation
        hide_event = Event(
            id="evt3",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "hide", "annotation_id": "ann1"},
        )
        annotation_handler.handle_annotation_event(hide_event)

        # Get all annotations
        all_annotations = annotation_handler.get_annotations(
            "canvas1", visible_only=False
        )
        assert len(all_annotations) == 3

        # Get visible annotations only
        visible_annotations = annotation_handler.get_annotations(
            "canvas1", visible_only=True
        )
        assert len(visible_annotations) == 2
        assert all(ann.id != "ann1" for ann in visible_annotations)

    def test_get_annotations_by_target(self):
        # Create annotations for different targets
        for i in range(3):
            create_event = Event(
                id=f"evt{i}",
                type=EventType.USER_INTERACTION,
                priority=EventPriority.NORMAL,
                timestamp=datetime.utcnow(),
                element_id="el1",
                data={
                    "canvas_id": "canvas1",
                    "action": "create",
                    "annotation_id": f"ann{i}",
                    "target_id": f"obj{i % 2}",  # Alternate between obj0 and obj1
                    "content": f"Test annotation {i}",
                },
            )
            annotation_handler.handle_annotation_event(create_event)

        # Get annotations for obj0
        obj0_annotations = annotation_handler.get_annotations_by_target(
            "canvas1", "obj0"
        )
        assert len(obj0_annotations) == 2
        assert all(ann.target_id == "obj0" for ann in obj0_annotations)

        # Get annotations for obj1
        obj1_annotations = annotation_handler.get_annotations_by_target(
            "canvas1", "obj1"
        )
        assert len(obj1_annotations) == 1
        assert all(ann.target_id == "obj1" for ann in obj1_annotations)


class TestAnnotationHandlerIntegration:
    def test_dispatch_annotation_event(self):
        # Dispatch an annotation event through the event-driven engine
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={
                "canvas_id": "canvas1",
                "action": "create",
                "annotation_id": "ann1",
                "content": "Test annotation",
                "event_subtype": "annotation",
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
        assert feedback.result["handler_results"][0]["result"]["action"] == "create"
        assert (
            feedback.result["handler_results"][0]["result"]["annotation_id"] == "ann1"
        )
        # State should be updated
        annotation = annotation_handler.get_annotation("canvas1", "ann1")
        assert annotation is not None
        assert annotation.content == "Test annotation"

    def test_annotation_history(self):
        # Perform multiple annotation actions
        actions = [
            {
                "action": "create",
                "annotation_id": "ann1",
                "content": "First annotation",
            },
            {
                "action": "create",
                "annotation_id": "ann2",
                "content": "Second annotation",
            },
            {
                "action": "update",
                "annotation_id": "ann1",
                "content": "Updated annotation",
            },
            {"action": "delete", "annotation_id": "ann2"},
        ]

        for i, action_data in enumerate(actions):
            event = Event(
                id=f"evt{i}",
                type=EventType.USER_INTERACTION,
                priority=EventPriority.NORMAL,
                timestamp=datetime.utcnow(),
                element_id="el1",
                data={"canvas_id": "canvas1", **action_data},
            )
            annotation_handler.handle_annotation_event(event)

        history = annotation_handler.get_annotation_history("canvas1")
        assert len(history) == 4
        assert history[0]["action"] == "create"
        assert history[1]["action"] == "create"
        assert history[2]["action"] == "update"
        assert history[3]["action"] == "delete"

    def test_clear_history(self):
        # Add some history
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={
                "canvas_id": "canvas1",
                "action": "create",
                "annotation_id": "ann1",
                "content": "Test annotation",
            },
        )
        annotation_handler.handle_annotation_event(event)
        assert len(annotation_handler.get_annotation_history("canvas1")) == 1

        # Clear history
        annotation_handler.clear_history("canvas1")
        assert len(annotation_handler.get_annotation_history("canvas1")) == 0
