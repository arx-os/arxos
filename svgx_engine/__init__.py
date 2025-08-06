"""
SVGX Engine - Advanced Behavior Engine for SVG Processing and Collaboration

This package provides a comprehensive behavior engine for SVG processing,
including event-driven behavior, state management, conditional logic,
performance optimization, UI interactions, time-based triggers, rule engines,
behavior management, animation systems, and custom plugin support.
"""

# Core Behavior Systems
from svgx_engine.runtime.event_driven_behavior_engine import (
    event_driven_behavior_engine,
    EventDrivenBehaviorEngine,
)
from svgx_engine.runtime.advanced_state_machine import (
    advanced_state_machine,
    AdvancedStateMachine,
)
from svgx_engine.runtime.conditional_logic_engine import (
    conditional_logic_engine,
    ConditionalLogicEngine,
)
from svgx_engine.runtime.performance_optimization_engine import (
    performance_optimization_engine,
    PerformanceOptimizationEngine,
)

# UI Behavior Systems
from svgx_engine.runtime.ui_selection_handler import selection_handler, SelectionHandler
from svgx_engine.runtime.ui_editing_handler import editing_handler, EditingHandler
from svgx_engine.runtime.ui_navigation_handler import (
    navigation_handler,
    NavigationHandler,
)
from svgx_engine.runtime.ui_annotation_handler import (
    annotation_handler,
    AnnotationHandler,
)

# Time-based and Rule Systems
from svgx_engine.runtime.time_based_trigger_system import (
    time_based_trigger_system,
    TimeBasedTriggerSystem,
)
from svgx_engine.runtime.advanced_rule_engine import (
    advanced_rule_engine,
    AdvancedRuleEngine,
)

# Behavior Management and Animation
from svgx_engine.runtime.behavior_management_system import (
    behavior_management_system,
    BehaviorManagementSystem,
)
from svgx_engine.runtime.animation_behavior_system import (
    animation_behavior_system,
    AnimationBehaviorSystem,
)

# Custom Behavior Plugin System
from svgx_engine.runtime.custom_behavior_plugin_system import (
    custom_behavior_plugin_system,
    CustomBehaviorPluginSystem,
)

# Services
try:
    from svgx_engine.services import (
        CurveSystem,
        BezierCurve,
        BSplineCurve,
        CurveFitter,
        ControlPoint,
        CurvePoint,
        KnotVector,
        CurveType,
        CurveDegree,
        create_curve_system,
        create_bezier_curve,
        create_bspline_curve,
        ConstraintSystem,
        ConstraintSolver,
        ConstraintType,
        ConstraintStatus,
        DistanceConstraint,
        AngleConstraint,
        ParallelConstraint,
        PerpendicularConstraint,
        HorizontalConstraint,
        VerticalConstraint,
        CoincidentConstraint,
        TangentConstraint,
        SymmetricConstraint,
        CurveTangentConstraint,
        CurvatureContinuousConstraint,
        CurvePositionConstraint,
        CurveLengthConstraint,
        create_constraint_system,
        create_constraint_solver,
    )
except ImportError:
    # Services not available
    pass

# Core Classes and Types
from svgx_engine.runtime.event_driven_behavior_engine import (
    Event,
    EventType,
    EventPriority,
)
from svgx_engine.runtime.advanced_state_machine import (
    State,
    StateType,
    StatePriority,
    StateTransition,
)
from svgx_engine.runtime.conditional_logic_engine import (
    Condition,
    LogicType,
    ComparisonOperator,
)
from svgx_engine.runtime.performance_optimization_engine import (
    CacheEntry,
    CacheStrategy,
)
from svgx_engine.runtime.ui_navigation_handler import ViewportState
from svgx_engine.runtime.ui_annotation_handler import (
    Annotation,
    AnnotationType,
    AnnotationVisibility,
)
from svgx_engine.runtime.time_based_trigger_system import (
    Trigger,
    TriggerType,
    TriggerStatus,
)
from svgx_engine.runtime.advanced_rule_engine import (
    Rule,
    RuleCondition,
    RuleAction,
    RuleResult,
    RuleType,
    RulePriority,
    RuleStatus,
)
from svgx_engine.runtime.behavior_management_system import (
    Behavior,
    BehaviorMetadata,
    BehaviorValidation,
    BehaviorVersion,
    BehaviorType,
    BehaviorStatus,
    ValidationLevel,
)
from svgx_engine.runtime.animation_behavior_system import (
    Animation,
    AnimationConfig,
    AnimationState,
    Keyframe,
    AnimationType,
    EasingFunction,
    AnimationStatus,
    AnimationDirection,
)

# Error Classes
from svgx_engine.utils.errors import (
    SVGXError,
    ValidationError,
    BehaviorError,
    StateError,
    OptimizationError,
    MemoryError,
)

# Version and Metadata
__version__ = "1.0.0"
__author__ = "Arxos Development Team"
__description__ = "Advanced behavior engine for SVG processing and collaboration"

# Package-level configuration
DEFAULT_CONFIG = {
    "event_processing": {
        "max_events_per_batch": 100,
        "event_timeout_seconds": 30,
        "enable_async_processing": True,
    },
    "state_management": {
        "max_states_per_machine": 1000,
        "state_transition_timeout": 60,
        "enable_state_persistence": True,
    },
    "performance": {
        "cache_size": 1000,
        "cache_ttl_seconds": 3600,
        "enable_lazy_evaluation": True,
        "max_parallel_operations": 10,
    },
    "ui_behavior": {
        "selection_timeout_ms": 5000,
        "editing_lock_timeout_seconds": 300,
        "navigation_smoothness": 0.8,
        "annotation_visibility_default": "visible",
    },
    "time_triggers": {
        "max_scheduled_triggers": 100,
        "trigger_check_interval_seconds": 60,
        "enable_cron_triggers": True,
    },
    "rule_engine": {
        "max_rules_per_context": 100,
        "rule_evaluation_timeout_ms": 5000,
        "enable_rule_caching": True,
    },
    "behavior_management": {
        "max_behaviors_per_type": 50,
        "behavior_validation_level": "strict",
        "enable_behavior_versioning": True,
    },
    "animation": {
        "max_animations_per_element": 10,
        "animation_frame_rate": 60,
        "enable_animation_caching": True,
    },
    "plugin_system": {
        "max_plugins_per_type": 20,
        "plugin_validation_level": "strict",
        "enable_plugin_sandboxing": True,
        "plugin_timeout_seconds": 30,
    },
}

# Global instances for easy access
_instances = {}


def get_instance(instance_type: str):
    """
    Get a global instance by type.

    Args:
        instance_type: Type of instance to retrieve

    Returns:
        The requested instance or None if not found
    """
    return _instances.get(instance_type)


def register_instance(instance_type: str, instance):
    """
    Register a global instance.

    Args:
        instance_type: Type of instance
        instance: Instance to register
    """
    _instances[instance_type] = instance


def initialize_core_systems():
    """
    Initialize all core SVGX Engine systems.

    This function sets up all the core behavior systems and registers
    them as global instances for easy access throughout the application.
    """
    try:
        # Initialize core behavior systems
        from svgx_engine.runtime.event_driven_behavior_engine import (
            event_driven_behavior_engine,
        )
        from svgx_engine.runtime.advanced_state_machine import advanced_state_machine
        from svgx_engine.runtime.conditional_logic_engine import (
            conditional_logic_engine,
        )
        from svgx_engine.runtime.performance_optimization_engine import (
            performance_optimization_engine,
        )

        # Initialize UI behavior systems
        from svgx_engine.runtime.ui_selection_handler import selection_handler
        from svgx_engine.runtime.ui_editing_handler import editing_handler
        from svgx_engine.runtime.ui_navigation_handler import navigation_handler
        from svgx_engine.runtime.ui_annotation_handler import annotation_handler

        # Initialize time-based and rule systems
        from svgx_engine.runtime.time_based_trigger_system import (
            time_based_trigger_system,
        )
        from svgx_engine.runtime.advanced_rule_engine import advanced_rule_engine

        # Initialize behavior management and animation
        from svgx_engine.runtime.behavior_management_system import (
            behavior_management_system,
        )
        from svgx_engine.runtime.animation_behavior_system import (
            animation_behavior_system,
        )

        # Initialize custom behavior plugin system
        from svgx_engine.runtime.custom_behavior_plugin_system import (
            custom_behavior_plugin_system,
        )

        # Register all instances
        register_instance("event_driven_behavior_engine", event_driven_behavior_engine)
        register_instance("advanced_state_machine", advanced_state_machine)
        register_instance("conditional_logic_engine", conditional_logic_engine)
        register_instance(
            "performance_optimization_engine", performance_optimization_engine
        )
        register_instance("selection_handler", selection_handler)
        register_instance("editing_handler", editing_handler)
        register_instance("navigation_handler", navigation_handler)
        register_instance("annotation_handler", annotation_handler)
        register_instance("time_based_trigger_system", time_based_trigger_system)
        register_instance("advanced_rule_engine", advanced_rule_engine)
        register_instance("behavior_management_system", behavior_management_system)
        register_instance("animation_behavior_system", animation_behavior_system)
        register_instance(
            "custom_behavior_plugin_system", custom_behavior_plugin_system
        )

        print("All core SVGX Engine systems initialized successfully")
        return True

    except Exception as e:
        print(f"Error initializing core systems: {e}")
        return False


def get_system_status():
    """
    Get the status of all core systems.

    Returns:
        Dictionary containing the status of all systems
    """
    status = {}

    for system_name in [
        "event_driven_behavior_engine",
        "advanced_state_machine",
        "conditional_logic_engine",
        "performance_optimization_engine",
        "selection_handler",
        "editing_handler",
        "navigation_handler",
        "annotation_handler",
        "time_based_trigger_system",
        "advanced_rule_engine",
        "behavior_management_system",
        "animation_behavior_system",
        "custom_behavior_plugin_system",
    ]:
        instance = get_instance(system_name)
        status[system_name] = {
            "initialized": instance is not None,
            "type": type(instance).__name__ if instance else None,
        }

    return status


# Export all public classes and instances
__all__ = [
    # Core Behavior Systems (global instances)
    "event_driven_behavior_engine",
    "EventDrivenBehaviorEngine",
    "advanced_state_machine",
    "AdvancedStateMachine",
    "conditional_logic_engine",
    "ConditionalLogicEngine",
    "performance_optimization_engine",
    "PerformanceOptimizationEngine",
    # UI Behavior Systems (global instances)
    "selection_handler",
    "SelectionHandler",
    "editing_handler",
    "EditingHandler",
    "navigation_handler",
    "NavigationHandler",
    "annotation_handler",
    "AnnotationHandler",
    # Time-based and Rule Systems (global instances)
    "time_based_trigger_system",
    "TimeBasedTriggerSystem",
    "advanced_rule_engine",
    "AdvancedRuleEngine",
    # Behavior Management and Animation (global instances)
    "behavior_management_system",
    "BehaviorManagementSystem",
    "animation_behavior_system",
    "AnimationBehaviorSystem",
    # Custom Behavior Plugin System (global instance)
    "custom_behavior_plugin_system",
    "CustomBehaviorPluginSystem",
    # Core Classes and Types
    "Event",
    "EventType",
    "EventPriority",
    "State",
    "StateType",
    "StatePriority",
    "StateTransition",
    "Condition",
    "LogicType",
    "ComparisonOperator",
    "CacheEntry",
    "CacheStrategy",
    "ViewportState",
    "Annotation",
    "AnnotationType",
    "AnnotationVisibility",
    "Trigger",
    "TriggerType",
    "TriggerStatus",
    "Rule",
    "RuleCondition",
    "RuleAction",
    "RuleResult",
    "RuleType",
    "RulePriority",
    "RuleStatus",
    "Behavior",
    "BehaviorMetadata",
    "BehaviorValidation",
    "BehaviorVersion",
    "BehaviorType",
    "BehaviorStatus",
    "ValidationLevel",
    "Animation",
    "AnimationConfig",
    "AnimationState",
    "Keyframe",
    "AnimationType",
    "EasingFunction",
    "AnimationStatus",
    "AnimationDirection",
    # Error Classes
    "SVGXError",
    "ValidationError",
    "BehaviorError",
    "StateError",
    "OptimizationError",
    "MemoryError",
    # Utility Functions
    "get_instance",
    "register_instance",
    "initialize_core_systems",
    "get_system_status",
    # Configuration
    "DEFAULT_CONFIG",
]

# Auto-initialize core systems when package is imported
if __name__ != "__main__":
    initialize_core_systems()
