"""
Tests for SVGX Engine UI Navigation Handler

Covers:
- NavigationHandler logic (pan, zoom, focus, reset, fit_to_view)
- Integration with event_driven_behavior_engine
- Edge cases and invalid input
- Follows Arxos standards: absolute imports, global instances, modular tests
"""

import pytest
from svgx_engine import event_driven_behavior_engine
from svgx_engine.runtime.ui_navigation_handler import navigation_handler, NavigationHandler, ViewportState
from svgx_engine.runtime.event_driven_behavior_engine import Event, EventType, EventPriority
from datetime import datetime

@pytest.fixture(autouse=True)
def clear_navigation_state():
    # Clear all navigation state before each test
    navigation_handler.viewport_states.clear()
    navigation_handler.navigation_history.clear()
    navigation_handler.focus_targets.clear()
    yield
    navigation_handler.viewport_states.clear()
    navigation_handler.navigation_history.clear()
    navigation_handler.focus_targets.clear()

class TestNavigationHandlerLogic:
    def test_pan_action(self):
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "pan", "dx": 10.0, "dy": 20.0}
        )
        feedback = navigation_handler.handle_navigation_event(event)
        assert feedback['action'] == 'pan'
        assert feedback['dx'] == 10.0
        assert feedback['dy'] == 20.0
        assert feedback['old_position'] == (0.0, 0.0)
        assert feedback['new_position'] == (10.0, 20.0)
        assert len(navigation_handler.get_navigation_history("canvas1")) == 1

    def test_zoom_action(self):
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "zoom", "zoom_factor": 2.0, "center_x": 100.0, "center_y": 100.0}
        )
        feedback = navigation_handler.handle_navigation_event(event)
        assert feedback['action'] == 'zoom'
        assert feedback['zoom_factor'] == 2.0
        assert feedback['center'] == (100.0, 100.0)
        assert feedback['old_zoom'] == 1.0
        assert feedback['new_zoom'] == 2.0
        assert len(navigation_handler.get_navigation_history("canvas1")) == 1

    def test_zoom_bounds_checking(self):
        # Test zoom below minimum
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "zoom", "zoom_factor": 0.05}
        )
        feedback = navigation_handler.handle_navigation_event(event)
        assert feedback['new_zoom'] == 0.1  # min_zoom

        # Test zoom above maximum
        event2 = Event(
            id="evt2",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "zoom", "zoom_factor": 20.0}
        )
        feedback2 = navigation_handler.handle_navigation_event(event2)
        assert feedback2['new_zoom'] == 10.0  # max_zoom

    def test_focus_action(self):
        # Add focus target first
        navigation_handler.add_focus_target("canvas1", "target1", 200.0, 300.0, 2.0)

        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "focus", "target_id": "target1", "smooth": True}
        )
        feedback = navigation_handler.handle_navigation_event(event)
        assert feedback['action'] == 'focus'
        assert feedback['target_id'] == 'target1'
        assert feedback['smooth'] == True
        assert feedback['old_focus'] == None
        assert feedback['new_focus'] == 'target1'
        assert feedback['target_position'] == (200.0, 300.0)
        assert len(navigation_handler.get_navigation_history("canvas1")) == 1

    def test_focus_target_not_found(self):
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "focus", "target_id": "nonexistent"}
        )
        feedback = navigation_handler.handle_navigation_event(event)
        assert feedback is None

    def test_reset_action(self):
        # First set some state
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "pan", "dx": 100.0, "dy": 200.0}
        )
        navigation_handler.handle_navigation_event(event)

        # Then reset
        reset_event = Event(
            id="evt2",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "reset"}
        )
        feedback = navigation_handler.handle_navigation_event(reset_event)
        assert feedback['action'] == 'reset'
        assert feedback['old_state']['x'] == 100.0
        assert feedback['new_state']['x'] == 0.0
        assert feedback['new_state']['y'] == 0.0
        assert feedback['new_state']['zoom'] == 1.0
        assert feedback['new_state']['focus_target'] == None

    def test_fit_to_view_action(self):
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "fit_to_view", "bounds": (0.0, 0.0, 100.0, 200.0), "padding": 0.1}
        )
        feedback = navigation_handler.handle_navigation_event(event)
        assert feedback['action'] == 'fit_to_view'
        assert feedback['bounds'] == (0.0, 0.0, 100.0, 200.0)
        assert feedback['padding'] == 0.1
        assert feedback['old_state']['x'] == 0.0
        assert feedback['new_state']['x'] != 0.0  # Should be adjusted to center content
        assert len(navigation_handler.get_navigation_history("canvas1")) == 1

    def test_fit_to_view_invalid_bounds(self):
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "fit_to_view", "bounds": (100.0, 200.0, 50.0, 100.0)}  # Invalid bounds
        )
        feedback = navigation_handler.handle_navigation_event(event)
        assert feedback is None

    def test_invalid_input(self):
        # Missing canvas_id
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"action": "pan", "dx": 10.0}
        )
        feedback = navigation_handler.handle_navigation_event(event)
        assert feedback is None

        # Missing action
        event2 = Event(
            id="evt2",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1"}
        )
        feedback2 = navigation_handler.handle_navigation_event(event2)
        assert feedback2 is None

        # Unknown action
        event3 = Event(
            id="evt3",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "unknown"}
        )
        feedback3 = navigation_handler.handle_navigation_event(event3)
        assert feedback3 is None

    def test_viewport_state_initialization(self):
        # Access viewport state for new canvas
        viewport = navigation_handler.get_viewport_state("new_canvas")
        assert viewport is None

        # Trigger navigation to initialize
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "new_canvas", "action": "pan", "dx": 10.0}
        )
        navigation_handler.handle_navigation_event(event)

        # Now viewport should be initialized
        viewport = navigation_handler.get_viewport_state("new_canvas")
        assert viewport is not None
        assert viewport.x == 10.0
        assert viewport.y == 0.0
        assert viewport.zoom == 1.0

    def test_focus_target_management(self):
        # Add focus targets
        navigation_handler.add_focus_target("canvas1", "target1", 100.0, 200.0, 1.5)
        navigation_handler.add_focus_target("canvas1", "target2", 300.0, 400.0)

        # Focus on target1
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "focus", "target_id": "target1"}
        )
        feedback = navigation_handler.handle_navigation_event(event)
        assert feedback['target_position'] == (100.0, 200.0)
        assert feedback['viewport_state']['zoom'] == 1.5

        # Focus on target2 (should use current zoom since none specified)
        event2 = Event(
            id="evt2",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "focus", "target_id": "target2"}
        )
        feedback2 = navigation_handler.handle_navigation_event(event2)
        assert feedback2['target_position'] == (300.0, 400.0)
        assert feedback2['viewport_state']['zoom'] == 1.5  # Should maintain previous zoom

class TestNavigationHandlerIntegration:
    def test_dispatch_navigation_event(self):
        # Dispatch a navigation event through the event-driven engine
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "pan", "dx": 50.0, "dy": 100.0, "event_subtype": "navigation"}
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
        assert feedback.result['handler_results'][0]['result']['action'] == 'pan'
        assert feedback.result['handler_results'][0]['result']['dx'] == 50.0
        assert feedback.result['handler_results'][0]['result']['dy'] == 100.0
        # State should be updated
        viewport = navigation_handler.get_viewport_state("canvas1")
        assert viewport.x == 50.0
        assert viewport.y == 100.0

    def test_navigation_history(self):
        # Perform multiple navigation actions
        actions = [
            {"action": "pan", "dx": 10.0, "dy": 20.0},
            {"action": "zoom", "zoom_factor": 2.0},
            {"action": "reset"}
        ]

        for i, action_data in enumerate(actions):
            event = Event(
                id=f"evt{i}",
                type=EventType.USER_INTERACTION,
                priority=EventPriority.NORMAL,
                timestamp=datetime.utcnow(),
                element_id="el1",
                data={"canvas_id": "canvas1", **action_data}
            )
            navigation_handler.handle_navigation_event(event)

        history = navigation_handler.get_navigation_history("canvas1")
        assert len(history) == 3
        assert history[0]['action'] == 'pan'
        assert history[1]['action'] == 'zoom'
        assert history[2]['action'] == 'reset'

    def test_clear_history(self):
        # Add some history
        event = Event(
            id="evt1",
            type=EventType.USER_INTERACTION,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="el1",
            data={"canvas_id": "canvas1", "action": "pan", "dx": 10.0}
        )
        navigation_handler.handle_navigation_event(event)
        assert len(navigation_handler.get_navigation_history("canvas1")) == 1

        # Clear history
        navigation_handler.clear_history("canvas1")
        assert len(navigation_handler.get_navigation_history("canvas1")) == 0
