"""
SVGX Engine - Animation Behavior System

Handles comprehensive animation capabilities including keyframe-based animations, easing functions, timing control, performance optimization, and event handling.
Supports smooth transitions, animation synchronization, and performance monitoring.
Integrates with all behavior systems and provides enterprise-grade animation management.
Follows Arxos engineering standards: absolute imports, global instances, modular/testable code, and comprehensive documentation.
"""

from typing import Dict, Any, List, Optional, Set, Tuple, Union, Callable
from svgx_engine.runtime.event_driven_behavior_engine import Event, EventType, EventPriority
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import threading
import json
import math
import time
from copy import deepcopy
import weakref

logger = logging.getLogger(__name__)

class AnimationType(Enum):
    """Types of animations supported by the Animation Behavior System."""
    TRANSFORM = "transform"
    OPACITY = "opacity"
    COLOR = "color"
    SIZE = "size"
    POSITION = "position"
    ROTATION = "rotation"
    SCALE = "scale"
    CUSTOM = "custom"

class EasingFunction(Enum):
    """Easing functions for smooth animation transitions."""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    BOUNCE = "bounce"
    ELASTIC = "elastic"
    BACK = "back"
    CUSTOM = "custom"

class AnimationStatus(Enum):
    """Status states for animations."""
    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"

class AnimationDirection(Enum):
    """Animation direction for playback."""
    FORWARD = "forward"
    REVERSE = "reverse"
    ALTERNATE = "alternate"
    ALTERNATE_REVERSE = "alternate_reverse"

@dataclass
class Keyframe:
    """Represents a keyframe in an animation."""
    time: float  # Time in seconds from animation start
    value: Any   # Target value at this keyframe
    easing: EasingFunction = EasingFunction.LINEAR
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AnimationState:
    """Current state of an animation."""
    current_time: float = 0.0
    current_value: Any = None
    progress: float = 0.0  # 0.0 to 1.0
    direction: AnimationDirection = AnimationDirection.FORWARD
    iteration_count: int = 0
    is_reversed: bool = False

@dataclass
class AnimationConfig:
    """Configuration for an animation."""
    duration: float = 1.0  # Duration in seconds
    delay: float = 0.0     # Delay before animation starts
    iterations: int = 1     # Number of iterations (0 = infinite)
    direction: AnimationDirection = AnimationDirection.FORWARD
    easing: EasingFunction = EasingFunction.LINEAR
    fill_mode: str = "none"  # "none", "forwards", "backwards", "both"
    auto_reverse: bool = False
    performance_mode: str = "balanced"  # "quality", "balanced", "performance"

@dataclass
class Animation:
    """Represents an animation in the Animation Behavior System."""
    id: str
    name: str
    animation_type: AnimationType
    target_element: str
    keyframes: List[Keyframe]
    config: AnimationConfig
    status: AnimationStatus = AnimationStatus.IDLE
    state: AnimationState = field(default_factory=AnimationState)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    event_handlers: Dict[str, Callable] = field(default_factory=dict)

class AnimationBehaviorSystem:
    """
    Comprehensive animation behavior system for keyframe-based animations, easing functions, timing control, and performance optimization.
    Supports smooth transitions, animation synchronization, and enterprise-grade animation management.
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
        # {animation_id: Animation}
        self.animations: Dict[str, Animation] = {}
        # {element_id: Set[animation_id]}
        self.animations_by_element: Dict[str, Set[str]] = {}
        # {animation_type: Set[animation_id]}
        self.animations_by_type: Dict[AnimationType, Set[str]] = {}
        # {status: Set[animation_id]}
        self.animations_by_status: Dict[AnimationStatus, Set[str]] = {}
        # Animation performance tracking
        self.performance_tracking: Dict[str, List[Dict[str, Any]]] = {}
        # Easing function implementations
        self.easing_functions: Dict[EasingFunction, Callable] = {}
        # Animation loop management
        self._animation_loop_running = False
        self._animation_loop_task: Optional[asyncio.Task] = None
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize easing functions
        self._initialize_easing_functions()
        # Start animation loop
        self._start_animation_loop()

    def _initialize_easing_functions(self):
        """Initialize easing function implementations."""
        self.easing_functions = {
            EasingFunction.LINEAR: lambda t: t,
            EasingFunction.EASE_IN: lambda t: t * t,
            EasingFunction.EASE_OUT: lambda t: 1 - (1 - t) * (1 - t),
            EasingFunction.EASE_IN_OUT: lambda t: t * t * (3 - 2 * t),
            EasingFunction.BOUNCE: self._bounce_easing,
            EasingFunction.ELASTIC: self._elastic_easing,
            EasingFunction.BACK: self._back_easing
        }

    def _bounce_easing(self, t: float) -> float:
        """Bounce easing function."""
        if t < 1/2.75:
            return 7.5625 * t * t
        elif t < 2/2.75:
            t = t - 1.5/2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5/2.75:
            t = t - 2.25/2.75
            return 7.5625 * t * t + 0.9375
        else:
            t = t - 2.625/2.75
            return 7.5625 * t * t + 0.984375

    def _elastic_easing(self, t: float) -> float:
        """Elastic easing function."""
        if t == 0:
            return 0
        if t == 1:
            return 1
        return math.pow(2, -10 * t) * math.sin((t - 0.075) * (2 * math.pi) / 0.3) + 1

    def _back_easing(self, t: float) -> float:
        """Back easing function."""
        s = 1.70158
        return t * t * ((s + 1) * t - s)

    def _start_animation_loop(self):
        """Start the animation loop for updating animations."""
        if not self._animation_loop_running:
            self._animation_loop_running = True
            # Start the animation loop lazily when first needed
            try:
                loop = asyncio.get_running_loop()
                self._animation_loop_task = loop.create_task(self._animation_loop())
            except RuntimeError:
                # No running loop, will start when first animation is played
                pass

    async def _ensure_animation_loop_running(self):
        """Ensure the animation loop is running."""
        if not self._animation_loop_running:
            self._animation_loop_running = True
            self._animation_loop_task = asyncio.create_task(self._animation_loop())

    async def _animation_loop(self):
        """Main animation loop for updating all active animations."""
        try:
            while self._animation_loop_running:
                with self._lock:
                    current_time = time.time()
                    active_animations = [
                        anim for anim in self.animations.values()
                        if anim.status == AnimationStatus.PLAYING
                    ]
                    
                    for animation in active_animations:
                        await self._update_animation(animation, current_time)
                
                # Update at 60 FPS
                await asyncio.sleep(1/60)
                
        except Exception as e:
            logger.error(f"Animation loop error: {e}")
            self._animation_loop_running = False

    async def _update_animation(self, animation: Animation, current_time: float):
        """Update a single animation."""
        try:
            if animation.start_time is None:
                animation.start_time = datetime.utcnow()
                animation.state.current_time = 0.0
            
            # Calculate elapsed time
            elapsed_time = current_time - animation.start_time.timestamp()
            animation.state.current_time = elapsed_time
            
            # Check if animation should start (considering delay)
            if elapsed_time < animation.config.delay:
                return
            
            # Calculate animation progress
            animation_time = elapsed_time - animation.config.delay
            if animation_time < 0:
                return
            
            # Calculate iteration progress
            iteration_duration = animation.config.duration
            if iteration_duration <= 0:
                return
            
            # Calculate total iterations completed
            total_iterations = animation_time // iteration_duration
            iteration_progress = (animation_time % iteration_duration) / iteration_duration
            
            # Handle iteration limits
            if animation.config.iterations > 0 and total_iterations >= animation.config.iterations:
                animation.status = AnimationStatus.COMPLETED
                animation.end_time = datetime.utcnow()
                await self._trigger_animation_event(animation, "completed")
                return
            
            # Handle direction changes
            if animation.config.direction == AnimationDirection.REVERSE:
                iteration_progress = 1.0 - iteration_progress
            elif animation.config.direction == AnimationDirection.ALTERNATE:
                if int(total_iterations) % 2 == 1:
                    iteration_progress = 1.0 - iteration_progress
            elif animation.config.direction == AnimationDirection.ALTERNATE_REVERSE:
                if int(total_iterations) % 2 == 0:
                    iteration_progress = 1.0 - iteration_progress
            
            # Apply easing function
            easing_func = self.easing_functions.get(animation.config.easing, self.easing_functions[EasingFunction.LINEAR])
            eased_progress = easing_func(iteration_progress)
            
            # Update animation state
            animation.state.progress = eased_progress
            animation.state.iteration_count = int(total_iterations)
            
            # Interpolate between keyframes
            current_value = self._interpolate_keyframes(animation, eased_progress)
            animation.state.current_value = current_value
            
            # Apply animation to target element
            await self._apply_animation_to_element(animation, current_value)
            
            # Trigger progress event
            await self._trigger_animation_event(animation, "progress", {"progress": eased_progress})
            
        except Exception as e:
            logger.error(f"Error updating animation {animation.id}: {e}")
            animation.status = AnimationStatus.ERROR
            await self._trigger_animation_event(animation, "error", {"error": str(e)})

    def _interpolate_keyframes(self, animation: Animation, progress: float) -> Any:
        """Interpolate between keyframes based on progress."""
        if not animation.keyframes:
            return None
        
        # Find the appropriate keyframes for interpolation
        keyframes = sorted(animation.keyframes, key=lambda k: k.time)
        
        if progress <= 0:
            return keyframes[0].value
        if progress >= 1:
            return keyframes[-1].value
        
        # Find the two keyframes to interpolate between
        current_time = progress * animation.config.duration
        prev_keyframe = None
        next_keyframe = None
        
        for i, keyframe in enumerate(keyframes):
            if keyframe.time <= current_time:
                prev_keyframe = keyframe
                if i + 1 < len(keyframes):
                    next_keyframe = keyframes[i + 1]
                else:
                    next_keyframe = keyframe
            else:
                if prev_keyframe is None:
                    prev_keyframe = keyframe
                next_keyframe = keyframe
                break
        
        if prev_keyframe is None or next_keyframe is None:
            return keyframes[0].value if keyframes else None
        
        # Interpolate between keyframes
        if prev_keyframe == next_keyframe:
            return prev_keyframe.value
        
        # Calculate interpolation factor
        total_time = next_keyframe.time - prev_keyframe.time
        if total_time == 0:
            return prev_keyframe.value
        
        factor = (current_time - prev_keyframe.time) / total_time
        
        # Apply keyframe-specific easing
        easing_func = self.easing_functions.get(prev_keyframe.easing, self.easing_functions[EasingFunction.LINEAR])
        eased_factor = easing_func(factor)
        
        # Interpolate values
        return self._interpolate_values(prev_keyframe.value, next_keyframe.value, eased_factor)

    def _interpolate_values(self, start_value: Any, end_value: Any, factor: float) -> Any:
        """Interpolate between two values based on factor."""
        if isinstance(start_value, (int, float)) and isinstance(end_value, (int, float)):
            return start_value + (end_value - start_value) * factor
        elif isinstance(start_value, dict) and isinstance(end_value, dict):
            result = {}
            all_keys = set(start_value.keys()) | set(end_value.keys())
            for key in all_keys:
                start_val = start_value.get(key, 0)
                end_val = end_value.get(key, 0)
                if isinstance(start_val, (int, float)) and isinstance(end_val, (int, float)):
                    result[key] = start_val + (end_val - start_val) * factor
                else:
                    result[key] = end_val if factor > 0.5 else start_val
            return result
        elif isinstance(start_value, list) and isinstance(end_value, list):
            # Interpolate list elements
            max_len = max(len(start_value), len(end_value))
            result = []
            for i in range(max_len):
                start_val = start_value[i] if i < len(start_value) else 0
                end_val = end_value[i] if i < len(end_value) else 0
                if isinstance(start_val, (int, float)) and isinstance(end_val, (int, float)):
                    result.append(start_val + (end_val - start_val) * factor)
                else:
                    result.append(end_val if factor > 0.5 else start_val)
            return result
        else:
            # For non-numeric types, use discrete interpolation
            return end_value if factor > 0.5 else start_value

    async def _apply_animation_to_element(self, animation: Animation, value: Any):
        """Apply animation value to target element."""
        try:
            # Import event-driven behavior engine locally to avoid circular imports
            from svgx_engine.runtime.event_driven_behavior_engine import event_driven_behavior_engine, Event, EventType
            
            # Create animation event
            event = Event(
                id=f"animation_{animation.id}",
                element_id=animation.target_element,
                type=EventType.SYSTEM,
                priority=EventPriority.NORMAL,
                data={
                    "animation_id": animation.id,
                    "target_element": animation.target_element,
                    "animation_type": animation.animation_type.value,
                    "current_value": value,
                    "progress": animation.state.progress,
                    "iteration_count": animation.state.iteration_count
                },
                timestamp=datetime.utcnow()
            )
            
            # Dispatch event to behavior engine
            await event_driven_behavior_engine.dispatch_event(event)
            
        except Exception as e:
            logger.error(f"Error applying animation to element: {e}")

    async def _trigger_animation_event(self, animation: Animation, event_type: str, additional_data: Dict[str, Any] = None):
        """Trigger animation event."""
        try:
            # Import event-driven behavior engine locally to avoid circular imports
            from svgx_engine.runtime.event_driven_behavior_engine import event_driven_behavior_engine, Event, EventType
            
            event_data = {
                "animation_id": animation.id,
                "target_element": animation.target_element,
                "animation_type": animation.animation_type.value,
                "event_type": event_type,
                "current_time": animation.state.current_time,
                "progress": animation.state.progress,
                "iteration_count": animation.state.iteration_count
            }
            
            if additional_data:
                event_data.update(additional_data)
            
            event = Event(
                id=f"animation_event_{animation.id}_{event_type}",
                element_id=animation.target_element,
                type=EventType.SYSTEM,
                priority=EventPriority.NORMAL,
                data=event_data,
                timestamp=datetime.utcnow()
            )
            
            await event_driven_behavior_engine.dispatch_event(event)
            
        except Exception as e:
            logger.error(f"Error triggering animation event: {e}")

    def create_animation(self, animation_id: str, name: str, animation_type: AnimationType, 
                        target_element: str, keyframes: List[Keyframe], config: AnimationConfig) -> Animation:
        """Create a new animation."""
        try:
            with self._lock:
                # Validate keyframes
                if not keyframes:
                    raise ValueError("Animation must have at least one keyframe")
                
                # Sort keyframes by time
                keyframes = sorted(keyframes, key=lambda k: k.time)
                
                # Create animation
                animation = Animation(
                    id=animation_id,
                    name=name,
                    animation_type=animation_type,
                    target_element=target_element,
                    keyframes=keyframes,
                    config=config
                )
                
                # Register animation
                self.animations[animation_id] = animation
                
                # Update indexes
                if target_element not in self.animations_by_element:
                    self.animations_by_element[target_element] = set()
                self.animations_by_element[target_element].add(animation_id)
                
                if animation_type not in self.animations_by_type:
                    self.animations_by_type[animation_type] = set()
                self.animations_by_type[animation_type].add(animation_id)
                
                if animation.status not in self.animations_by_status:
                    self.animations_by_status[animation.status] = set()
                self.animations_by_status[animation.status].add(animation_id)
                
                logger.info(f"Created animation: {animation_id}")
                return animation
                
        except Exception as e:
            logger.error(f"Error creating animation {animation_id}: {e}")
            raise

    async def play_animation(self, animation_id: str) -> bool:
        """Start playing an animation."""
        try:
            with self._lock:
                if animation_id not in self.animations:
                    logger.error(f"Animation {animation_id} not found")
                    return False
                
                animation = self.animations[animation_id]
                
                if animation.status == AnimationStatus.PLAYING:
                    logger.warning(f"Animation {animation_id} is already playing")
                    return True
                
                # Ensure animation loop is running
                await self._ensure_animation_loop_running()
                
                # Reset animation state
                animation.state = AnimationState()
                animation.status = AnimationStatus.PLAYING
                animation.start_time = None
                animation.end_time = None
                
                # Update status index
                old_status = animation.status
                if old_status in self.animations_by_status:
                    self.animations_by_status[old_status].discard(animation_id)
                
                if animation.status not in self.animations_by_status:
                    self.animations_by_status[animation.status] = set()
                self.animations_by_status[animation.status].add(animation_id)
                
                # Trigger start event
                await self._trigger_animation_event(animation, "start")
                
                logger.info(f"Started animation: {animation_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error playing animation {animation_id}: {e}")
            return False

    async def pause_animation(self, animation_id: str) -> bool:
        """Pause an animation."""
        try:
            with self._lock:
                if animation_id not in self.animations:
                    logger.error(f"Animation {animation_id} not found")
                    return False
                
                animation = self.animations[animation_id]
                
                if animation.status != AnimationStatus.PLAYING:
                    logger.warning(f"Animation {animation_id} is not playing")
                    return False
                
                animation.status = AnimationStatus.PAUSED
                
                # Update status index
                old_status = AnimationStatus.PLAYING
                if old_status in self.animations_by_status:
                    self.animations_by_status[old_status].discard(animation_id)
                
                if animation.status not in self.animations_by_status:
                    self.animations_by_status[animation.status] = set()
                self.animations_by_status[animation.status].add(animation_id)
                
                # Trigger pause event
                await self._trigger_animation_event(animation, "pause")
                
                logger.info(f"Paused animation: {animation_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error pausing animation {animation_id}: {e}")
            return False

    async def resume_animation(self, animation_id: str) -> bool:
        """Resume a paused animation."""
        try:
            with self._lock:
                if animation_id not in self.animations:
                    logger.error(f"Animation {animation_id} not found")
                    return False
                
                animation = self.animations[animation_id]
                
                if animation.status != AnimationStatus.PAUSED:
                    logger.warning(f"Animation {animation_id} is not paused")
                    return False
                
                animation.status = AnimationStatus.PLAYING
                
                # Update status index
                old_status = AnimationStatus.PAUSED
                if old_status in self.animations_by_status:
                    self.animations_by_status[old_status].discard(animation_id)
                
                if animation.status not in self.animations_by_status:
                    self.animations_by_status[animation.status] = set()
                self.animations_by_status[animation.status].add(animation_id)
                
                # Trigger resume event
                await self._trigger_animation_event(animation, "resume")
                
                logger.info(f"Resumed animation: {animation_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error resuming animation {animation_id}: {e}")
            return False

    async def stop_animation(self, animation_id: str) -> bool:
        """Stop an animation."""
        try:
            with self._lock:
                if animation_id not in self.animations:
                    logger.error(f"Animation {animation_id} not found")
                    return False
                
                animation = self.animations[animation_id]
                
                if animation.status == AnimationStatus.IDLE:
                    logger.warning(f"Animation {animation_id} is already stopped")
                    return True
                
                old_status = animation.status
                animation.status = AnimationStatus.IDLE
                animation.end_time = datetime.utcnow()
                
                # Update status index
                if old_status in self.animations_by_status:
                    self.animations_by_status[old_status].discard(animation_id)
                
                if animation.status not in self.animations_by_status:
                    self.animations_by_status[animation.status] = set()
                self.animations_by_status[animation.status].add(animation_id)
                
                # Trigger stop event
                await self._trigger_animation_event(animation, "stop")
                
                logger.info(f"Stopped animation: {animation_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error stopping animation {animation_id}: {e}")
            return False

    def get_animation(self, animation_id: str) -> Optional[Animation]:
        """Get an animation by ID."""
        return self.animations.get(animation_id)

    def get_animations_by_element(self, element_id: str) -> List[Animation]:
        """Get all animations for a specific element."""
        animation_ids = self.animations_by_element.get(element_id, set())
        return [self.animations[aid] for aid in animation_ids if aid in self.animations]

    def get_animations_by_type(self, animation_type: AnimationType) -> List[Animation]:
        """Get all animations of a specific type."""
        animation_ids = self.animations_by_type.get(animation_type, set())
        return [self.animations[aid] for aid in animation_ids if aid in self.animations]

    def get_animations_by_status(self, status: AnimationStatus) -> List[Animation]:
        """Get all animations with a specific status."""
        animation_ids = self.animations_by_status.get(status, set())
        return [self.animations[aid] for aid in animation_ids if aid in self.animations]

    def update_animation(self, animation_id: str, updates: Dict[str, Any]) -> bool:
        """Update an animation with new configuration."""
        try:
            with self._lock:
                if animation_id not in self.animations:
                    logger.error(f"Animation {animation_id} not found")
                    return False
                
                animation = self.animations[animation_id]
                
                # Update fields
                for field, value in updates.items():
                    if hasattr(animation, field):
                        setattr(animation, field, value)
                    elif hasattr(animation.config, field):
                        setattr(animation.config, field, value)
                
                logger.info(f"Updated animation: {animation_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating animation {animation_id}: {e}")
            return False

    def delete_animation(self, animation_id: str) -> bool:
        """Delete an animation."""
        try:
            with self._lock:
                if animation_id not in self.animations:
                    logger.error(f"Animation {animation_id} not found")
                    return False
                
                animation = self.animations[animation_id]
                
                # Remove from indexes
                if animation.target_element in self.animations_by_element:
                    self.animations_by_element[animation.target_element].discard(animation_id)
                
                if animation.animation_type in self.animations_by_type:
                    self.animations_by_type[animation.animation_type].discard(animation_id)
                
                if animation.status in self.animations_by_status:
                    self.animations_by_status[animation.status].discard(animation_id)
                
                # Remove animation
                del self.animations[animation_id]
                
                logger.info(f"Deleted animation: {animation_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting animation {animation_id}: {e}")
            return False

    def get_performance_analytics(self, animation_id: str = None) -> Dict[str, Any]:
        """Get performance analytics for animations."""
        try:
            with self._lock:
                if animation_id:
                    animation = self.animations.get(animation_id)
                    if not animation:
                        return {}
                    
                    return {
                        "animation_id": animation_id,
                        "performance_metrics": animation.performance_metrics,
                        "status": animation.status.value,
                        "current_progress": animation.state.progress,
                        "iteration_count": animation.state.iteration_count
                    }
                else:
                    # Aggregate analytics for all animations
                    total_animations = len(self.animations)
                    playing_animations = len(self.animations_by_status.get(AnimationStatus.PLAYING, set()))
                    completed_animations = len(self.animations_by_status.get(AnimationStatus.COMPLETED, set()))
                    
                    return {
                        "total_animations": total_animations,
                        "playing_animations": playing_animations,
                        "completed_animations": completed_animations,
                        "animations_by_type": {
                            at.value: len(animations)
                            for at, animations in self.animations_by_type.items()
                        },
                        "animations_by_status": {
                            as_.value: len(animations)
                            for as_, animations in self.animations_by_status.items()
                        }
                    }
                    
        except Exception as e:
            logger.error(f"Error getting performance analytics: {e}")
            return {}

    def add_easing_function(self, name: str, function: Callable[[float], float]):
        """Add a custom easing function."""
        try:
            # Create custom easing enum value
            custom_easing = EasingFunction.CUSTOM
            self.easing_functions[custom_easing] = function
            logger.info(f"Added custom easing function: {name}")
            
        except Exception as e:
            logger.error(f"Error adding easing function {name}: {e}")

    def __del__(self):
        """Cleanup when the system is destroyed."""
        self._animation_loop_running = False
        if self._animation_loop_task:
            self._animation_loop_task.cancel()

# Global instance
animation_behavior_system = AnimationBehaviorSystem()

# Register with the event-driven engine
def _register_animation_behavior_system():
    """
    Perform _register_animation_behavior_system operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = _register_animation_behavior_system(param)
        print(result)
    """
    def handler(event: Event):
        if event.type == EventType.SYSTEM and event.data.get('animation'):
            # Animation events are handled internally
            return None
        return None
    
    # Import here to avoid circular imports
    from svgx_engine.runtime.event_driven_behavior_engine import event_driven_behavior_engine
    event_driven_behavior_engine.register_handler(
        event_type=EventType.SYSTEM,
        handler_id='animation_behavior_system',
        handler=handler,
        priority=3
    )

_register_animation_behavior_system() 