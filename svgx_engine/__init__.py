"""
SVGX Engine - SVGX Processing and Behavior Engine

A comprehensive engine for processing SVGX files, managing behaviors,
and providing advanced functionality for SVGX-based applications.

This package provides:
- SVGX file parsing and processing
- Behavior engine with event-driven architecture
- State machine management
- Conditional logic evaluation
- Performance optimization
- UI behavior systems (selection, editing, navigation, annotation)
- Time-based trigger system
- Advanced rule engine
- Comprehensive testing and validation
"""

# Behavior system components
from .runtime.event_driven_behavior_engine import event_driven_behavior_engine, EventDrivenBehaviorEngine
from .runtime.advanced_state_machine import advanced_state_machine, AdvancedStateMachine
from .runtime.conditional_logic_engine import conditional_logic_engine, ConditionalLogicEngine
from .runtime.performance_optimization_engine import performance_optimization_engine, PerformanceOptimizationEngine

# UI behavior system components
from .runtime.ui_selection_handler import selection_handler, SelectionHandler
from .runtime.ui_editing_handler import editing_handler, EditingHandler
from .runtime.ui_navigation_handler import navigation_handler, NavigationHandler
from .runtime.ui_annotation_handler import annotation_handler, AnnotationHandler

# Time-based trigger system
from .runtime.time_based_trigger_system import time_based_trigger_system, TimeBasedTriggerSystem

# Advanced Rule Engine
from .runtime.advanced_rule_engine import advanced_rule_engine, AdvancedRuleEngine

# Behavior Management System
from .runtime.behavior_management_system import behavior_management_system, BehaviorManagementSystem

# Animation Behavior System
from .runtime.animation_behavior_system import animation_behavior_system, AnimationBehaviorSystem

# Custom Behavior Plugin System
from .runtime.custom_behavior_plugin_system import custom_behavior_plugin_system, CustomBehaviorPluginSystem

# Data structures and enums
from .runtime.event_driven_behavior_engine import Event, EventType, EventPriority
from .runtime.advanced_state_machine import State, StateType, StatePriority, StateTransition
from .runtime.conditional_logic_engine import Condition, LogicType, ComparisonOperator
from .runtime.performance_optimization_engine import CacheEntry, CacheStrategy
from .runtime.ui_navigation_handler import ViewportState
from .runtime.ui_annotation_handler import Annotation, AnnotationType, AnnotationVisibility
from .runtime.time_based_trigger_system import Trigger, TriggerType, TriggerStatus
from .runtime.advanced_rule_engine import Rule, RuleCondition, RuleAction, RuleResult, RuleType, RulePriority, RuleStatus
from .runtime.behavior_management_system import Behavior, BehaviorMetadata, BehaviorValidation, BehaviorVersion, BehaviorType, BehaviorStatus, ValidationLevel
from .runtime.animation_behavior_system import Animation, AnimationConfig, AnimationState, Keyframe, AnimationType, EasingFunction, AnimationStatus, AnimationDirection

# Utilities and helpers
from .utils.errors import SVGXError, ValidationError, BehaviorError, StateError, OptimizationError, MemoryError

# Version information
__version__ = "1.0.0"
__author__ = "Arxos Development Team"
__description__ = "SVGX Processing and Behavior Engine"

# Public API exports
__all__ = [
    # Behavior systems (global instances)
    "event_driven_behavior_engine",
    "advanced_state_machine", 
    "conditional_logic_engine",
    "performance_optimization_engine",
    
    # UI behavior systems (global instances)
    "selection_handler",
    "editing_handler",
    "navigation_handler", 
    "annotation_handler",
    
    # Time-based trigger system (global instance)
    "time_based_trigger_system",
    
    # Advanced Rule Engine (global instance)
    "advanced_rule_engine",
    
    # Behavior Management System (global instance)
    "behavior_management_system",
    
    # Animation Behavior System (global instance)
    "animation_behavior_system",
    
    # Custom Behavior Plugin System (global instance)
    "custom_behavior_plugin_system",
    "CustomBehaviorPluginSystem",
    
    # Classes
    "EventDrivenBehaviorEngine",
    "AdvancedStateMachine",
    "ConditionalLogicEngine", 
    "PerformanceOptimizationEngine",
    "SelectionHandler",
    "EditingHandler",
    "NavigationHandler",
    "AnnotationHandler",
    "TimeBasedTriggerSystem",
    "AdvancedRuleEngine",
    "BehaviorManagementSystem",
    "AnimationBehaviorSystem",
    
    # Data structures
    "Event", "EventType", "EventPriority",
    "State", "StateType", "StatePriority", "StateTransition",
    "Condition", "LogicType", "ComparisonOperator", 
    "CacheEntry", "CacheStrategy",
    "ViewportState",
    "Annotation", "AnnotationType", "AnnotationVisibility",
    "Trigger", "TriggerType", "TriggerStatus",
    "Rule", "RuleCondition", "RuleAction", "RuleResult", "RuleType", "RulePriority", "RuleStatus",
    "Behavior", "BehaviorMetadata", "BehaviorValidation", "BehaviorVersion", "BehaviorType", "BehaviorStatus", "ValidationLevel",
    "Animation", "AnimationConfig", "AnimationState", "Keyframe", "AnimationType", "EasingFunction", "AnimationStatus", "AnimationDirection",
    
    # Utilities
    "SVGXError", "ValidationError", "BehaviorError", 
    "StateError", "OptimizationError", "MemoryError"
]

def _initialize_core_systems():
    """Initialize core SVGX Engine systems."""
    try:
        # Initialize behavior systems
        from .runtime.event_driven_behavior_engine import event_driven_behavior_engine
        from .runtime.advanced_state_machine import advanced_state_machine
        from .runtime.conditional_logic_engine import conditional_logic_engine
        from .runtime.performance_optimization_engine import performance_optimization_engine
        
        # Initialize UI behavior systems
        from .runtime.ui_selection_handler import selection_handler
        from .runtime.ui_editing_handler import editing_handler
        from .runtime.ui_navigation_handler import navigation_handler
        from .runtime.ui_annotation_handler import annotation_handler
        
        # Initialize Time-based Trigger System
        from .runtime.time_based_trigger_system import time_based_trigger_system
        
        # Initialize Advanced Rule Engine
        from .runtime.advanced_rule_engine import advanced_rule_engine
        
        # Initialize Behavior Management System
        from .runtime.behavior_management_system import behavior_management_system
        
        # Initialize Animation Behavior System
        from .runtime.animation_behavior_system import animation_behavior_system
        
        # Initialize Custom Behavior Plugin System
        from .runtime.custom_behavior_plugin_system import custom_behavior_plugin_system
        
        print("All core SVGX Engine systems initialized successfully")
        
    except Exception as e:
        print(f"Error initializing core systems: {e}")
        raise

# Initialize core systems on import
_initialize_core_systems() 