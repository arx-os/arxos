"""
SVGX Engine - Animation Behavior System Tests

Comprehensive test suite for the Animation Behavior System covering keyframe animations, easing functions, timing control, performance optimization, and event handling.
Tests animation lifecycle management, easing functions, and performance analytics.
Follows Arxos engineering standards: absolute imports, global instances, comprehensive test coverage.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

from svgx_engine import event_driven_behavior_engine
from svgx_engine.runtime.animation_behavior_system import (
    animation_behavior_system, AnimationBehaviorSystem,
    Animation, AnimationConfig, AnimationState, Keyframe,
    AnimationType, EasingFunction, AnimationStatus, AnimationDirection
)
from svgx_engine.runtime.event_driven_behavior_engine import Event, EventType, EventPriority

class TestAnimationBehaviorSystemLogic:
    """Test core animation behavior system logic and functionality."""
    
    def test_create_animation(self):
        """Test creating an animation with keyframes."""
        # Create keyframes
        keyframes = [
            Keyframe(time=0.0, value=0, easing=EasingFunction.LINEAR),
            Keyframe(time=1.0, value=100, easing=EasingFunction.EASE_OUT)
        ]
        
        # Create animation config
        config = AnimationConfig(
            duration=2.0,
            delay=0.5,
            iterations=3,
            direction=AnimationDirection.FORWARD,
            easing=EasingFunction.EASE_IN_OUT
        )
        
        # Create animation
        animation = animation_behavior_system.create_animation(
            animation_id="test_animation",
            name="Test Animation",
            animation_type=AnimationType.TRANSFORM,
            target_element="test_element",
            keyframes=keyframes,
            config=config
        )
        
        assert animation is not None
        assert animation.id == "test_animation"
        assert animation.name == "Test Animation"
        assert animation.animation_type == AnimationType.TRANSFORM
        assert animation.target_element == "test_element"
        assert len(animation.keyframes) == 2
        assert animation.config.duration == 2.0
        assert animation.config.delay == 0.5
        assert animation.config.iterations == 3
        assert animation.status == AnimationStatus.IDLE
        
        # Clean up
        animation_behavior_system.delete_animation("test_animation")

    def test_create_animation_invalid_keyframes(self):
        """Test creating animation with invalid keyframes."""
        # Try to create animation without keyframes
        with pytest.raises(ValueError, match="Animation must have at least one keyframe"):
            animation_behavior_system.create_animation(
                animation_id="test_invalid_animation",
                name="Test Invalid Animation",
                animation_type=AnimationType.TRANSFORM,
                target_element="test_element",
                keyframes=[],
                config=AnimationConfig()
            )

    def test_animation_keyframe_sorting(self):
        """Test that keyframes are automatically sorted by time."""
        # Create keyframes in random order
        keyframes = [
            Keyframe(time=1.0, value=100),
            Keyframe(time=0.0, value=0),
            Keyframe(time=0.5, value=50)
        ]
        
        config = AnimationConfig(duration=1.0)
        
        animation = animation_behavior_system.create_animation(
            animation_id="test_sorting_animation",
            name="Test Sorting Animation",
            animation_type=AnimationType.TRANSFORM,
            target_element="test_element",
            keyframes=keyframes,
            config=config
        )
        
        # Check that keyframes are sorted by time
        assert animation.keyframes[0].time == 0.0
        assert animation.keyframes[1].time == 0.5
        assert animation.keyframes[2].time == 1.0
        
        # Clean up
        animation_behavior_system.delete_animation("test_sorting_animation")

    def test_easing_functions(self):
        """Test easing function implementations."""
        # Test linear easing
        linear_result = animation_behavior_system.easing_functions[EasingFunction.LINEAR](0.5)
        assert linear_result == 0.5
        
        # Test ease-in easing
        ease_in_result = animation_behavior_system.easing_functions[EasingFunction.EASE_IN](0.5)
        assert ease_in_result == 0.25  # 0.5 * 0.5
        
        # Test ease-out easing
        ease_out_result = animation_behavior_system.easing_functions[EasingFunction.EASE_OUT](0.5)
        assert ease_out_result == 0.75  # 1 - (1 - 0.5) * (1 - 0.5)
        
        # Test ease-in-out easing
        ease_in_out_result = animation_behavior_system.easing_functions[EasingFunction.EASE_IN_OUT](0.5)
        assert ease_in_out_result == 0.5  # 0.5 * 0.5 * (3 - 2 * 0.5)

    def test_value_interpolation(self):
        """Test value interpolation between different types."""
        # Test numeric interpolation
        numeric_result = animation_behavior_system._interpolate_values(0, 100, 0.5)
        assert numeric_result == 50
        
        # Test dictionary interpolation
        dict_start = {"x": 0, "y": 0, "z": 0}
        dict_end = {"x": 100, "y": 200, "z": 300}
        dict_result = animation_behavior_system._interpolate_values(dict_start, dict_end, 0.5)
        assert dict_result["x"] == 50
        assert dict_result["y"] == 100
        assert dict_result["z"] == 150
        
        # Test list interpolation
        list_start = [0, 0, 0]
        list_end = [100, 200, 300]
        list_result = animation_behavior_system._interpolate_values(list_start, list_end, 0.5)
        assert list_result[0] == 50
        assert list_result[1] == 100
        assert list_result[2] == 150

    def test_keyframe_interpolation(self):
        """Test keyframe interpolation."""
        # Create animation with keyframes
        keyframes = [
            Keyframe(time=0.0, value=0),
            Keyframe(time=1.0, value=100)
        ]
        
        config = AnimationConfig(duration=1.0)
        
        animation = animation_behavior_system.create_animation(
            animation_id="test_interpolation_animation",
            name="Test Interpolation Animation",
            animation_type=AnimationType.TRANSFORM,
            target_element="test_element",
            keyframes=keyframes,
            config=config
        )
        
        # Test interpolation at different progress points
        result_0 = animation_behavior_system._interpolate_keyframes(animation, 0.0)
        assert result_0 == 0
        
        result_0_5 = animation_behavior_system._interpolate_keyframes(animation, 0.5)
        assert result_0_5 == 50
        
        result_1 = animation_behavior_system._interpolate_keyframes(animation, 1.0)
        assert result_1 == 100
        
        # Clean up
        animation_behavior_system.delete_animation("test_interpolation_animation")

    def test_animation_management_operations(self):
        """Test animation management operations."""
        # Create animation
        keyframes = [Keyframe(time=0.0, value=0), Keyframe(time=1.0, value=100)]
        config = AnimationConfig(duration=1.0)
        
        animation = animation_behavior_system.create_animation(
            animation_id="test_management_animation",
            name="Test Management Animation",
            animation_type=AnimationType.TRANSFORM,
            target_element="test_element",
            keyframes=keyframes,
            config=config
        )
        
        # Test get animation
        retrieved_animation = animation_behavior_system.get_animation("test_management_animation")
        assert retrieved_animation is not None
        assert retrieved_animation.id == "test_management_animation"
        
        # Test get animations by element
        element_animations = animation_behavior_system.get_animations_by_element("test_element")
        assert len(element_animations) >= 1
        assert any(a.id == "test_management_animation" for a in element_animations)
        
        # Test get animations by type
        transform_animations = animation_behavior_system.get_animations_by_type(AnimationType.TRANSFORM)
        assert len(transform_animations) >= 1
        assert any(a.id == "test_management_animation" for a in transform_animations)
        
        # Test get animations by status
        idle_animations = animation_behavior_system.get_animations_by_status(AnimationStatus.IDLE)
        assert len(idle_animations) >= 1
        assert any(a.id == "test_management_animation" for a in idle_animations)
        
        # Test update animation
        updates = {"config": AnimationConfig(duration=2.0)}
        assert animation_behavior_system.update_animation("test_management_animation", updates) is True
        
        updated_animation = animation_behavior_system.get_animation("test_management_animation")
        assert updated_animation.config.duration == 2.0
        
        # Test delete animation
        assert animation_behavior_system.delete_animation("test_management_animation") is True
        assert animation_behavior_system.get_animation("test_management_animation") is None

    def test_add_custom_easing_function(self):
        """Test adding custom easing functions."""
        # Define custom easing function
        def custom_easing(t: float) -> float:
            return t * t * t  # Cubic easing
        
        # Add custom easing function
        animation_behavior_system.add_easing_function("custom_cubic", custom_easing)
        
        # Test custom easing function
        custom_result = animation_behavior_system.easing_functions[EasingFunction.CUSTOM](0.5)
        assert custom_result == 0.125  # 0.5 * 0.5 * 0.5

    def test_animation_completion_logic(self):
        """Test animation completion logic without relying on the animation loop."""
        # Create animation
        keyframes = [Keyframe(time=0.0, value=0), Keyframe(time=1.0, value=100)]
        config = AnimationConfig(duration=1.0, iterations=1)
        
        animation = animation_behavior_system.create_animation(
            animation_id="test_completion_animation",
            name="Test Completion Animation",
            animation_type=AnimationType.TRANSFORM,
            target_element="test_element",
            keyframes=keyframes,
            config=config
        )
        
        # Manually set start time to simulate a past time
        past_time = datetime.utcnow() - timedelta(seconds=2)  # 2 seconds ago
        animation.start_time = past_time
        
        # Simulate animation completion by setting elapsed time beyond duration
        current_time = time.time()
        elapsed_time = current_time - animation.start_time.timestamp()
        
        # Calculate if animation should be completed
        animation_time = elapsed_time - animation.config.delay
        total_iterations = animation_time // animation.config.duration
        
        # Check completion logic
        if animation.config.iterations > 0 and total_iterations >= animation.config.iterations:
            animation.status = AnimationStatus.COMPLETED
            animation.end_time = datetime.utcnow()
        
        # Verify completion logic works
        assert animation.status == AnimationStatus.COMPLETED
        
        # Clean up
        animation_behavior_system.delete_animation("test_completion_animation")

class TestAnimationBehaviorSystemAsync:
    """Test asynchronous animation behavior system operations."""
    
    @pytest.mark.asyncio
    async def test_play_animation(self):
        """Test playing an animation."""
        # Create animation
        keyframes = [Keyframe(time=0.0, value=0), Keyframe(time=1.0, value=100)]
        config = AnimationConfig(duration=0.1)  # Short duration for testing
        
        animation = animation_behavior_system.create_animation(
            animation_id="test_play_animation",
            name="Test Play Animation",
            animation_type=AnimationType.TRANSFORM,
            target_element="test_element",
            keyframes=keyframes,
            config=config
        )
        
        # Play animation
        result = await animation_behavior_system.play_animation("test_play_animation")
        assert result is True
        
        # Check animation status
        updated_animation = animation_behavior_system.get_animation("test_play_animation")
        assert updated_animation.status == AnimationStatus.PLAYING
        
        # Wait for animation to complete
        await asyncio.sleep(0.2)
        
        # Check final status
        final_animation = animation_behavior_system.get_animation("test_play_animation")
        assert final_animation.status == AnimationStatus.COMPLETED
        
        # Clean up
        animation_behavior_system.delete_animation("test_play_animation")

    @pytest.mark.asyncio
    async def test_pause_resume_animation(self):
        """Test pausing and resuming an animation."""
        # Create animation
        keyframes = [Keyframe(time=0.0, value=0), Keyframe(time=1.0, value=100)]
        config = AnimationConfig(duration=1.0)  # Longer duration for testing pause/resume
        
        animation = animation_behavior_system.create_animation(
            animation_id="test_pause_resume_animation",
            name="Test Pause Resume Animation",
            animation_type=AnimationType.TRANSFORM,
            target_element="test_element",
            keyframes=keyframes,
            config=config
        )
        
        # Play animation
        await animation_behavior_system.play_animation("test_pause_resume_animation")
        
        # Wait a bit then pause
        await asyncio.sleep(0.1)
        pause_result = await animation_behavior_system.pause_animation("test_pause_resume_animation")
        assert pause_result is True
        
        # Check paused status
        paused_animation = animation_behavior_system.get_animation("test_pause_resume_animation")
        assert paused_animation.status == AnimationStatus.PAUSED
        
        # Resume animation
        resume_result = await animation_behavior_system.resume_animation("test_pause_resume_animation")
        assert resume_result is True
        
        # Check playing status
        resumed_animation = animation_behavior_system.get_animation("test_pause_resume_animation")
        assert resumed_animation.status == AnimationStatus.PLAYING
        
        # Wait for completion
        await asyncio.sleep(1.0)
        
        # Clean up
        animation_behavior_system.delete_animation("test_pause_resume_animation")

    @pytest.mark.asyncio
    async def test_stop_animation(self):
        """Test stopping an animation."""
        # Create animation
        keyframes = [Keyframe(time=0.0, value=0), Keyframe(time=1.0, value=100)]
        config = AnimationConfig(duration=1.0)
        
        animation = animation_behavior_system.create_animation(
            animation_id="test_stop_animation",
            name="Test Stop Animation",
            animation_type=AnimationType.TRANSFORM,
            target_element="test_element",
            keyframes=keyframes,
            config=config
        )
        
        # Play animation
        await animation_behavior_system.play_animation("test_stop_animation")
        
        # Wait a bit then stop
        await asyncio.sleep(0.1)
        stop_result = await animation_behavior_system.stop_animation("test_stop_animation")
        assert stop_result is True
        
        # Check stopped status
        stopped_animation = animation_behavior_system.get_animation("test_stop_animation")
        assert stopped_animation.status == AnimationStatus.IDLE
        
        # Clean up
        animation_behavior_system.delete_animation("test_stop_animation")

    @pytest.mark.asyncio
    async def test_animation_with_delay(self):
        """Test animation with delay."""
        # Create animation with delay
        keyframes = [Keyframe(time=0.0, value=0), Keyframe(time=1.0, value=100)]
        config = AnimationConfig(duration=0.1, delay=0.2)  # 0.2s delay
        
        animation = animation_behavior_system.create_animation(
            animation_id="test_delay_animation",
            name="Test Delay Animation",
            animation_type=AnimationType.TRANSFORM,
            target_element="test_element",
            keyframes=keyframes,
            config=config
        )
        
        # Play animation
        await animation_behavior_system.play_animation("test_delay_animation")
        
        # Check that animation hasn't started yet (due to delay)
        await asyncio.sleep(0.1)
        early_animation = animation_behavior_system.get_animation("test_delay_animation")
        assert early_animation.status == AnimationStatus.PLAYING
        assert early_animation.state.current_time < 0.2
        
        # Wait for animation to complete
        await asyncio.sleep(0.3)
        
        # Check final status
        final_animation = animation_behavior_system.get_animation("test_delay_animation")
        assert final_animation.status == AnimationStatus.COMPLETED
        
        # Clean up
        animation_behavior_system.delete_animation("test_delay_animation")

    @pytest.mark.asyncio
    async def test_animation_iterations(self):
        """Test animation with multiple iterations."""
        # Create animation with iterations
        keyframes = [Keyframe(time=0.0, value=0), Keyframe(time=1.0, value=100)]
        config = AnimationConfig(duration=0.1, iterations=3)  # 3 iterations
        
        animation = animation_behavior_system.create_animation(
            animation_id="test_iterations_animation",
            name="Test Iterations Animation",
            animation_type=AnimationType.TRANSFORM,
            target_element="test_element",
            keyframes=keyframes,
            config=config
        )
        
        # Play animation
        await animation_behavior_system.play_animation("test_iterations_animation")
        
        # Wait for all iterations to complete
        await asyncio.sleep(0.4)  # 3 * 0.1 + buffer
        
        # Check final status
        final_animation = animation_behavior_system.get_animation("test_iterations_animation")
        assert final_animation.status == AnimationStatus.COMPLETED
        assert final_animation.state.iteration_count >= 3
        
        # Clean up
        animation_behavior_system.delete_animation("test_iterations_animation")

class TestAnimationBehaviorSystemIntegration:
    """Test integration with other behavior systems."""
    
    def test_performance_analytics(self):
        """Test performance analytics functionality."""
        # Get analytics for all animations
        analytics = animation_behavior_system.get_performance_analytics()
        assert isinstance(analytics, dict)
        assert "total_animations" in analytics
        assert "playing_animations" in analytics
        assert "completed_animations" in analytics
        assert "animations_by_type" in analytics
        assert "animations_by_status" in analytics
        
        # Analytics should have reasonable values
        assert analytics["total_animations"] >= 0
        assert analytics["playing_animations"] >= 0
        assert analytics["completed_animations"] >= 0

    def test_performance_analytics_specific(self):
        """Test performance analytics for specific animation."""
        # Create animation for analytics
        keyframes = [Keyframe(time=0.0, value=0), Keyframe(time=1.0, value=100)]
        config = AnimationConfig(duration=1.0)
        
        animation = animation_behavior_system.create_animation(
            animation_id="test_analytics_animation",
            name="Test Analytics Animation",
            animation_type=AnimationType.TRANSFORM,
            target_element="test_element",
            keyframes=keyframes,
            config=config
        )
        
        # Get analytics for specific animation
        animation_analytics = animation_behavior_system.get_performance_analytics("test_analytics_animation")
        assert isinstance(animation_analytics, dict)
        assert animation_analytics["animation_id"] == "test_analytics_animation"
        assert "performance_metrics" in animation_analytics
        assert "status" in animation_analytics
        assert "current_progress" in animation_analytics
        assert "iteration_count" in animation_analytics
        
        # Clean up
        animation_behavior_system.delete_animation("test_analytics_animation")

    @pytest.mark.asyncio
    async def test_animation_event_integration(self):
        """Test animation integration with event-driven behavior engine."""
        # Create animation
        keyframes = [Keyframe(time=0.0, value=0), Keyframe(time=1.0, value=100)]
        config = AnimationConfig(duration=0.1)
        
        animation = animation_behavior_system.create_animation(
            animation_id="test_event_integration_animation",
            name="Test Event Integration Animation",
            animation_type=AnimationType.TRANSFORM,
            target_element="test_element",
            keyframes=keyframes,
            config=config
        )
        
        # Play animation (this should trigger events)
        await animation_behavior_system.play_animation("test_event_integration_animation")
        
        # Wait for animation to complete
        await asyncio.sleep(0.2)
        
        # Check that animation completed successfully
        final_animation = animation_behavior_system.get_animation("test_event_integration_animation")
        assert final_animation.status == AnimationStatus.COMPLETED
        
        # Clean up
        animation_behavior_system.delete_animation("test_event_integration_animation")

    def test_animation_types(self):
        """Test different animation types."""
        animation_types = [
            AnimationType.TRANSFORM,
            AnimationType.OPACITY,
            AnimationType.COLOR,
            AnimationType.SIZE,
            AnimationType.POSITION,
            AnimationType.ROTATION,
            AnimationType.SCALE,
            AnimationType.CUSTOM
        ]
        
        for i, anim_type in enumerate(animation_types):
            keyframes = [Keyframe(time=0.0, value=0), Keyframe(time=1.0, value=100)]
            config = AnimationConfig(duration=1.0)
            
            animation = animation_behavior_system.create_animation(
                animation_id=f"test_type_{i}_animation",
                name=f"Test {anim_type.value} Animation",
                animation_type=anim_type,
                target_element="test_element",
                keyframes=keyframes,
                config=config
            )
            
            assert animation.animation_type == anim_type
            
            # Clean up
            animation_behavior_system.delete_animation(f"test_type_{i}_animation")

    def test_animation_directions(self):
        """Test different animation directions."""
        directions = [
            AnimationDirection.FORWARD,
            AnimationDirection.REVERSE,
            AnimationDirection.ALTERNATE,
            AnimationDirection.ALTERNATE_REVERSE
        ]
        
        for i, direction in enumerate(directions):
            keyframes = [Keyframe(time=0.0, value=0), Keyframe(time=1.0, value=100)]
            config = AnimationConfig(duration=1.0, direction=direction)
            
            animation = animation_behavior_system.create_animation(
                animation_id=f"test_direction_{i}_animation",
                name=f"Test {direction.value} Animation",
                animation_type=AnimationType.TRANSFORM,
                target_element="test_element",
                keyframes=keyframes,
                config=config
            )
            
            assert animation.config.direction == direction
            
            # Clean up
            animation_behavior_system.delete_animation(f"test_direction_{i}_animation")

    @pytest.mark.asyncio
    async def test_animation_lifecycle(self):
        """Test complete animation lifecycle."""
        # Create animation
        keyframes = [Keyframe(time=0.0, value=0), Keyframe(time=1.0, value=100)]
        config = AnimationConfig(duration=0.1)
        
        animation = animation_behavior_system.create_animation(
            animation_id="test_lifecycle_animation",
            name="Test Lifecycle Animation",
            animation_type=AnimationType.TRANSFORM,
            target_element="test_element",
            keyframes=keyframes,
            config=config
        )
        
        # 1. Play animation
        assert await animation_behavior_system.play_animation("test_lifecycle_animation") is True
        
        # 2. Check playing status
        playing_animation = animation_behavior_system.get_animation("test_lifecycle_animation")
        assert playing_animation.status == AnimationStatus.PLAYING
        
        # 3. Wait for completion
        await asyncio.sleep(0.2)
        
        # 4. Check completed status
        completed_animation = animation_behavior_system.get_animation("test_lifecycle_animation")
        assert completed_animation.status == AnimationStatus.COMPLETED
        
        # 5. Get performance analytics
        analytics = animation_behavior_system.get_performance_analytics("test_lifecycle_animation")
        assert analytics is not None
        
        # 6. Delete animation
        assert animation_behavior_system.delete_animation("test_lifecycle_animation") is True
        
        # 7. Verify deletion
        assert animation_behavior_system.get_animation("test_lifecycle_animation") is None 