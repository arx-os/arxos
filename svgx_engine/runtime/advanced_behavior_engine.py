"""
SVGX Advanced Behavior Engine for complex event-driven behavior management.

Implements:
- Event-driven architecture with modular event dispatcher
- Rule engines with complex logic evaluation
- State machines with transition management
- Time-based triggers and scheduling
- Advanced condition evaluation
- CAD-parity and infrastructure simulation behaviors
- Extensible event handler and plugin system
- Physics integration for realistic behavior simulation
- (TODO) UI Behavior System integration for interactive behaviors

See architecture.md and reference/behavior.md for design details.
"""

import asyncio
import logging
import time
import math
from typing import Dict, Any, List, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import re
import json
from svgx_engine.runtime.behavior.ui_event_dispatcher import UIEventDispatcher
from svgx_engine.runtime.behavior.ui_event_schemas import SelectionEvent
from svgx_engine.runtime.behavior.ui_event_schemas import EditingEvent
from svgx_engine.services.telemetry_logger import telemetry_instrumentation
import threading

# Import physics integration service
try:
    from svgx_engine.services.physics_integration_service import (
        PhysicsIntegrationService, PhysicsIntegrationConfig, 
        PhysicsBehaviorType, PhysicsBehaviorRequest, PhysicsBehaviorResult
    )
    PHYSICS_INTEGRATION_AVAILABLE = True
except ImportError:
    PHYSICS_INTEGRATION_AVAILABLE = False
    logger.warning("Physics integration service not available")

logger = logging.getLogger(__name__)


class BehaviorType(Enum):
    """Types of behaviors supported by the engine."""
    INTERACTIVE = "interactive"
    SIMULATION = "simulation"
    ANIMATION = "animation"
    PHYSICS = "physics"
    CUSTOM = "custom"
    CAD_PARITY = "cad_parity"
    INFRASTRUCTURE = "infrastructure"


class StateType(Enum):
    """Types of states in state machines."""
    EQUIPMENT = "equipment"
    PROCESS = "process"
    SYSTEM = "system"
    MAINTENANCE = "maintenance"
    SAFETY = "safety"


class RuleType(Enum):
    """Types of rules in rule engines."""
    BUSINESS = "business"
    SAFETY = "safety"
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    COMPLIANCE = "compliance"


class TriggerType(Enum):
    """Types of triggers for behavior activation."""
    EVENT = "event"
    TIME = "time"
    CONDITION = "condition"
    STATE = "state"
    EXTERNAL = "external"


@dataclass
class BehaviorRule:
    """Represents a behavior rule with conditions and actions."""
    rule_id: str
    rule_type: RuleType
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    priority: int = 1
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BehaviorState:
    """Represents a state in a state machine."""
    state_id: str
    state_type: StateType
    properties: Dict[str, Any]
    transitions: List[Dict[str, Any]]
    entry_actions: List[Dict[str, Any]] = field(default_factory=list)
    exit_actions: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TimeTrigger:
    """Represents a time-based trigger."""
    trigger_id: str
    schedule_type: str  # "scheduled", "duration", "cyclic", "sequential", "delayed"
    schedule_data: Dict[str, Any]
    actions: List[Dict[str, Any]]
    enabled: bool = True
    last_execution: Optional[datetime] = None
    next_execution: Optional[datetime] = None


@dataclass
class Condition:
    """Represents a complex condition for behavior evaluation."""
    condition_id: str
    condition_type: str  # "threshold", "time", "spatial", "relational", "complex"
    expression: str
    parameters: Dict[str, Any]
    operators: List[str] = field(default_factory=list)


class AdvancedBehaviorEngine:
    """Advanced behavior engine with physics integration."""
    
    def __init__(self):
        # Core registries
        self.event_handlers: Dict[str, Callable] = {}
        self.rules: List[BehaviorRule] = []
        self.state_machines: Dict[str, List[BehaviorState]] = {}
        self.time_triggers: List[TimeTrigger] = []
        self.conditions: List[Condition] = []
        
        # Physics integration
        self.physics_integration: Optional[PhysicsIntegrationService] = None
        if PHYSICS_INTEGRATION_AVAILABLE:
            try:
                config = PhysicsIntegrationConfig(
                    integration_type="real_time",
                    physics_enabled=True,
                    cache_enabled=True,
                    performance_monitoring=True,
                    ai_optimization_enabled=True
                )
                self.physics_integration = PhysicsIntegrationService(config)
                logger.info("Physics integration service initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize physics integration: {e}")
                self.physics_integration = None
        
        # UI event handling
        self.ui_event_dispatcher = UIEventDispatcher()
        self.selection_state: Dict[str, List[str]] = {}
        self.editing_locks: Dict[str, Dict[str, Any]] = {}
        self.lock_timeout = 300  # 5 minutes
        
        # Performance tracking
        self.performance_metrics: Dict[str, Any] = {}
        self.event_history: List[Dict[str, Any]] = []
        
        # Setup default handlers
        self._setup_default_handlers()
        
        # Start lock cleanup task
        self._start_lock_cleanup_task()
        
        logger.info("Advanced behavior engine initialized with physics integration")
    
    def _setup_default_handlers(self):
        """Setup default event handlers."""
        self.register_event_handler("user_interaction", self._handle_user_interaction)
        self.register_event_handler("system", self._handle_system_event)
        self.register_event_handler("physics", self._handle_physics_event)
        self.register_event_handler("environmental", self._handle_environmental_event)
        self.register_event_handler("operational", self._handle_operational_event)
        self.register_event_handler("cad_parity", self._handle_cad_parity)
        self.register_event_handler("infrastructure", self._handle_infrastructure)
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler."""
        self.event_handlers[event_type] = handler
    
    async def dispatch_event(self, element_id: str, event_type: str, event_data: Dict[str, Any]):
        """Dispatch an event to the appropriate handler."""
        if event_type in self.event_handlers:
            handler = self.event_handlers[event_type]
            try:
                await handler(element_id, event_data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
        else:
            logger.warning(f"No handler registered for event type: {event_type}")
    
    def register_rule(self, rule: BehaviorRule):
        """Register a behavior rule."""
        self.rules.append(rule)
        logger.info(f"Registered behavior rule: {rule.rule_id}")
    
    def register_state_machine(self, element_id: str, states: List[BehaviorState], initial_state: str):
        """Register a state machine for an element."""
        self.state_machines[element_id] = states
        logger.info(f"Registered state machine for element: {element_id}")
    
    def register_time_trigger(self, trigger: TimeTrigger):
        """Register a time-based trigger."""
        self.time_triggers.append(trigger)
        logger.info(f"Registered time trigger: {trigger.trigger_id}")
    
    def register_condition(self, condition: Condition):
        """Register a condition."""
        self.conditions.append(condition)
        logger.info(f"Registered condition: {condition.condition_id}")
    
    async def evaluate_rules(self, element_id: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate all applicable rules for an element."""
        applicable_rules = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            if self._rule_applies_to_element(rule, element_id, context):
                if self._evaluate_rule_conditions(rule, context):
                    applicable_rules.append({
                        "rule_id": rule.rule_id,
                        "rule_type": rule.rule_type.value,
                        "actions": rule.actions,
                        "priority": rule.priority
                    })
        
        # Sort by priority (higher priority first)
        applicable_rules.sort(key=lambda x: x["priority"], reverse=True)
        
        return applicable_rules
    
    def _rule_applies_to_element(self, rule: BehaviorRule, element_id: str, context: Dict[str, Any]) -> bool:
        """Check if a rule applies to a specific element."""
        # Check if rule has element-specific conditions
        for condition in rule.conditions:
            if "element_id" in condition:
                if condition["element_id"] != element_id:
                    return False
        
        return True
    
    def _evaluate_rule_conditions(self, rule: BehaviorRule, context: Dict[str, Any]) -> bool:
        """Evaluate all conditions for a rule."""
        for condition in rule.conditions:
            if not self._evaluate_single_condition(condition, context):
                return False
        return True
    
    def _evaluate_single_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a single condition."""
        condition_type = condition.get("type", "simple")
        
        if condition_type == "threshold":
            return self._evaluate_threshold_condition(condition, context)
        elif condition_type == "time":
            return self._evaluate_time_condition(condition, context)
        elif condition_type == "spatial":
            return self._evaluate_spatial_condition(condition, context)
        elif condition_type == "relational":
            return self._evaluate_relational_condition(condition, context)
        elif condition_type == "complex":
            return self._evaluate_complex_condition(condition, context)
        else:
            return self._evaluate_simple_condition(condition, context)
    
    def _evaluate_threshold_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a threshold condition."""
        variable = condition.get("variable")
        operator = condition.get("operator", ">")
        threshold = condition.get("threshold")
        
        if variable not in context:
            return False
        
        value = context[variable]
        
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return value == threshold
        elif operator == "!=":
            return value != threshold
        else:
            return False
    
    def _evaluate_time_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a time-based condition."""
        time_type = condition.get("time_type")
        current_time = datetime.now()
        
        if time_type == "time_of_day":
            start_time = condition.get("start_time")
            end_time = condition.get("end_time")
            
            current_hour = current_time.hour
            start_hour = int(start_time.split(":")[0])
            end_hour = int(end_time.split(":")[0])
            
            if start_hour <= end_hour:
                return start_hour <= current_hour <= end_hour
            else:  # Overnight
                return current_hour >= start_hour or current_hour <= end_hour
        
        elif time_type == "day_of_week":
            target_days = condition.get("days", [])
            current_day = current_time.weekday()
            return current_day in target_days
        
        elif time_type == "date_range":
            start_date = datetime.fromisoformat(condition.get("start_date"))
            end_date = datetime.fromisoformat(condition.get("end_date"))
            return start_date <= current_time <= end_date
        
        return False
    
    def _evaluate_spatial_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a spatial condition."""
        spatial_type = condition.get("spatial_type")
        
        if spatial_type == "distance":
            pos1 = context.get("position1")
            pos2 = context.get("position2")
            max_distance = condition.get("max_distance")
            
            if pos1 and pos2:
                distance = self._calculate_distance(pos1, pos2)
                return distance <= max_distance
        
        elif spatial_type == "boundary":
            point = context.get("point")
            boundary = condition.get("boundary")
            
            if point and boundary:
                return self._is_point_in_boundary(point, boundary)
        
        elif spatial_type == "intersection":
            bounds1 = context.get("bounds1")
            bounds2 = context.get("bounds2")
            
            if bounds1 and bounds2:
                return self._do_bounds_intersect(bounds1, bounds2)
        
        return False
    
    def _evaluate_relational_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a relational condition."""
        relation_type = condition.get("relation_type")
        
        if relation_type == "parent_child":
            parent_id = condition.get("parent_id")
            child_id = condition.get("child_id")
            
            # Check if child is actually a child of parent
            return context.get("parent_relationships", {}).get(child_id) == parent_id
        
        elif relation_type == "connected":
            element1_id = condition.get("element1_id")
            element2_id = condition.get("element2_id")
            
            # Check if elements are connected
            connections = context.get("connections", [])
            return (element1_id, element2_id) in connections or (element2_id, element1_id) in connections
        
        return False
    
    def _evaluate_complex_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a complex condition with multiple sub-conditions."""
        sub_conditions = condition.get("sub_conditions", [])
        logic_operator = condition.get("logic_operator", "AND")
        
        results = []
        for sub_condition in sub_conditions:
            results.append(self._evaluate_single_condition(sub_condition, context))
        
        if logic_operator == "AND":
            return all(results)
        elif logic_operator == "OR":
            return any(results)
        elif logic_operator == "NOT":
            return not results[0] if results else True
        else:
            return False
    
    def _evaluate_simple_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a simple condition."""
        variable = condition.get("variable")
        operator = condition.get("operator", "==")
        value = condition.get("value")
        
        if variable not in context:
            return False
        
        actual_value = context[variable]
        
        if operator == "==":
            return actual_value == value
        elif operator == "!=":
            return actual_value != value
        elif operator == "in":
            return actual_value in value
        elif operator == "not_in":
            return actual_value not in value
        else:
            return False
    
    async def execute_state_transition(self, element_id: str, target_state: str, context: Dict[str, Any] = None):
        """Execute a state transition for an element."""
        if element_id not in self.state_machines:
            logger.warning(f"No state machine found for element: {element_id}")
            return
        
        states = self.state_machines[element_id]
        current_state = None
        
        # Find current state
        for state in states:
            if state.state_id == target_state:
                current_state = state
                break
        
        if not current_state:
            logger.warning(f"Target state not found: {target_state}")
            return
        
        # Check if transition is valid
        if context and not self._is_transition_valid(current_state, target_state, context):
            logger.warning(f"Invalid state transition: {target_state}")
            return
        
        # Execute exit actions for current state
        # (Implementation would track current state)
        
        # Execute entry actions for target state
        for action in current_state.entry_actions:
            await self._execute_actions([action], element_id, context or {})
        
        logger.info(f"State transition executed for {element_id}: {target_state}")
    
    def _is_transition_valid(self, current_state: BehaviorState, target_state: str, context: Dict[str, Any]) -> bool:
        """Check if a state transition is valid."""
        for transition in current_state.transitions:
            if transition.get("target_state") == target_state:
                conditions = transition.get("conditions", [])
                
                # Check all conditions
                for condition in conditions:
                    if not self._evaluate_single_condition(condition, context):
                        return False
                
                return True
        
        return False
    
    async def execute_time_triggers(self):
        """Execute time-based triggers."""
        current_time = datetime.now()
        
        for trigger in self.time_triggers:
            if not trigger.enabled:
                continue
            
            # Check if trigger should execute
            if trigger.next_execution and current_time >= trigger.next_execution:
                await self._execute_trigger_actions(trigger)
                
                # Calculate next execution
                trigger.last_execution = current_time
                trigger.next_execution = self._calculate_next_execution(trigger)
    
    async def _execute_trigger_actions(self, trigger: TimeTrigger):
        """Execute actions for a time trigger."""
        logger.info(f"Executing time trigger: {trigger.trigger_id}")
        
        for action in trigger.actions:
            # Execute action (simplified)
            logger.debug(f"Executing action for trigger {trigger.trigger_id}")
    
    def _calculate_next_execution(self, trigger: TimeTrigger) -> datetime:
        """Calculate next execution time for a trigger."""
        current_time = datetime.now()
        
        if trigger.schedule_type == "scheduled":
            # Fixed schedule
            schedule_data = trigger.schedule_data
            hour = schedule_data.get("hour", 0)
            minute = schedule_data.get("minute", 0)
            
            next_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_time <= current_time:
                next_time += timedelta(days=1)
            
            return next_time
        
        elif trigger.schedule_type == "cyclic":
            # Cyclic schedule
            interval = trigger.schedule_data.get("interval_seconds", 3600)
            return current_time + timedelta(seconds=interval)
        
        elif trigger.schedule_type == "duration":
            # Duration-based
            duration = trigger.schedule_data.get("duration_seconds", 3600)
            return current_time + timedelta(seconds=duration)
        
        else:
            # Default to 1 hour
            return current_time + timedelta(hours=1)
    
    async def _execute_actions(self, actions: List[Dict[str, Any]], element_id: str, context: Dict[str, Any]):
        """Execute a list of actions."""
        for action in actions:
            action_type = action.get("type")
            
            if action_type == "update":
                await self._execute_update_action(action, element_id, context)
            elif action_type == "animate":
                await self._execute_animate_action(action, element_id, context)
            elif action_type == "calculate":
                await self._execute_calculate_action(action, element_id, context)
            elif action_type == "trigger":
                await self._execute_trigger_action(action, element_id, context)
            elif action_type == "log":
                await self._execute_log_action(action, element_id, context)
            elif action_type == "cad_parity":
                await self._execute_cad_parity_action(action, element_id, context)
            elif action_type == "infrastructure":
                await self._execute_infrastructure_action(action, element_id, context)
            elif action_type == "physics":
                await self._execute_physics_action(action, element_id, context)
            else:
                logger.warning(f"Unknown action type: {action_type}")
    
    async def _execute_update_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute an update action."""
        property_name = action.get("property")
        new_value = action.get("value")
        
        logger.debug(f"Updating {element_id}.{property_name} = {new_value}")
    
    async def _execute_animate_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute an animation action."""
        animation_type = action.get("animation_type")
        duration = action.get("duration", 1.0)
        
        logger.debug(f"Animating {element_id}: {animation_type} for {duration}s")
    
    async def _execute_calculate_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute a calculation action."""
        calculation_type = action.get("calculation_type")
        parameters = action.get("parameters", {})
        
        logger.debug(f"Calculating {calculation_type} for {element_id}")
    
    async def _execute_trigger_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute a trigger action."""
        event_type = action.get("event_type")
        event_data = action.get("event_data", {})
        
        await self.dispatch_event(element_id, event_type, event_data)
    
    async def _execute_log_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute a logging action."""
        message = action.get("message", "")
        level = action.get("level", "info")
        
        log_message = f"[{element_id}] {message}"
        
        if level == "debug":
            logger.debug(log_message)
        elif level == "info":
            logger.info(log_message)
        elif level == "warning":
            logger.warning(log_message)
        elif level == "error":
            logger.error(log_message)
    
    async def _execute_cad_parity_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute a CAD parity action."""
        cad_action = action.get("cad_action")
        
        logger.debug(f"Executing CAD parity action for {element_id}: {cad_action}")
    
    async def _execute_infrastructure_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute an infrastructure action."""
        infra_action = action.get("infrastructure_action")
        
        logger.debug(f"Executing infrastructure action for {element_id}: {infra_action}")
    
    async def _execute_physics_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute a physics action using physics integration service."""
        if not self.physics_integration:
            logger.warning("Physics integration not available")
            return
        
        physics_type = action.get("physics_type")
        element_data = action.get("element_data", {})
        
        try:
            if physics_type == "hvac":
                result = self.physics_integration.simulate_hvac_behavior(element_id, element_data)
            elif physics_type == "electrical":
                result = self.physics_integration.simulate_electrical_behavior(element_id, element_data)
            elif physics_type == "structural":
                result = self.physics_integration.simulate_structural_behavior(element_id, element_data)
            elif physics_type == "thermal":
                result = self.physics_integration.simulate_thermal_behavior(element_id, element_data)
            elif physics_type == "acoustic":
                result = self.physics_integration.simulate_acoustic_behavior(element_id, element_data)
            else:
                logger.warning(f"Unknown physics type: {physics_type}")
                return
            
            logger.info(f"Physics simulation completed for {element_id}: {result.behavior_state}")
            
            # Store result in context for other actions
            context["physics_result"] = result
            
        except Exception as e:
            logger.error(f"Physics simulation failed for {element_id}: {e}")
    
    async def _handle_user_interaction(self, element_id: str, event_data: Dict[str, Any]):
        """Handle user interaction events."""
        logger.debug(f"Handling user interaction for {element_id}")
    
    async def _handle_system_event(self, element_id: str, event_data: Dict[str, Any]):
        """Handle system events."""
        logger.debug(f"Handling system event for {element_id}")
    
    async def _handle_physics_event(self, element_id: str, event_data: Dict[str, Any]):
        """Handle physics events."""
        logger.debug(f"Handling physics event for {element_id}")
    
    async def _handle_environmental_event(self, element_id: str, event_data: Dict[str, Any]):
        """Handle environmental events."""
        logger.debug(f"Handling environmental event for {element_id}")
    
    async def _handle_operational_event(self, element_id: str, event_data: Dict[str, Any]):
        """Handle operational events."""
        logger.debug(f"Handling operational event for {element_id}")
    
    async def _handle_cad_parity(self, element_id: str, event_data: Dict[str, Any]):
        """Handle CAD parity events."""
        logger.debug(f"Handling CAD parity event for {element_id}")
    
    async def _handle_infrastructure(self, element_id: str, event_data: Dict[str, Any]):
        """Handle infrastructure events."""
        logger.debug(f"Handling infrastructure event for {element_id}")
    
    @telemetry_instrumentation
    async def _handle_selection_event(self, event: SelectionEvent) -> dict:
        """Handle selection events with telemetry."""
        canvas_id = event.canvas_id
        selected_ids = event.selected_ids
        selection_type = event.selection_type
        
        # Update selection state
        self._update_selection_state(canvas_id, selected_ids)
        
        # Log selection event
        logger.info(f"Selection event on canvas {canvas_id}: {selection_type} - {len(selected_ids)} items")
        
        # Execute selection-based behaviors
        for element_id in selected_ids:
            await self.dispatch_event(element_id, "user_interaction", {
                "type": "selection",
                "selection_type": selection_type,
                "canvas_id": canvas_id
            })
        
        return {
            "status": "success",
            "canvas_id": canvas_id,
            "selected_count": len(selected_ids),
            "selection_type": selection_type
        }
    
    @telemetry_instrumentation
    async def _handle_editing_event(self, event: EditingEvent) -> dict:
        """Handle editing events with telemetry."""
        canvas_id = event.canvas_id
        target_id = event.target_id
        edit_type = event.edit_type
        edit_data = event.edit_data
        
        # Check if element is locked
        lock_status = self.get_lock_status(canvas_id, target_id)
        if lock_status.get("locked") and lock_status.get("session_id") != event.session_id:
            return {
                "status": "error",
                "message": "Element is locked by another user",
                "lock_info": lock_status
            }
        
        # Lock element for editing
        lock_result = self.lock_object(canvas_id, target_id, event.session_id, event.user_id)
        if not lock_result.get("success"):
            return {
                "status": "error",
                "message": "Failed to lock element for editing",
                "lock_result": lock_result
            }
        
        try:
            # Execute edit action
            await self.dispatch_event(target_id, "user_interaction", {
                "type": "editing",
                "edit_type": edit_type,
                "edit_data": edit_data,
                "canvas_id": canvas_id,
                "session_id": event.session_id,
                "user_id": event.user_id
            })
            
            logger.info(f"Edit event on canvas {canvas_id}: {edit_type} for {target_id}")
            
            return {
                "status": "success",
                "canvas_id": canvas_id,
                "target_id": target_id,
                "edit_type": edit_type,
                "lock_result": lock_result
            }
            
        except Exception as e:
            # Unlock element on error
            self.unlock_object(canvas_id, target_id, event.session_id)
            raise e
    
    @telemetry_instrumentation
    async def _handle_navigation_event(self, element_id: str, event_data: Dict[str, Any]):
        """Handle navigation events with telemetry."""
        navigation_type = event_data.get("navigation_type")
        logger.info(f"Navigation event: {navigation_type} for {element_id}")
    
    @telemetry_instrumentation
    async def _handle_annotation_event(self, element_id: str, event_data: Dict[str, Any]):
        """Handle annotation events with telemetry."""
        annotation_type = event_data.get("annotation_type")
        logger.info(f"Annotation event: {annotation_type} for {element_id}")
    
    async def _handle_event(self, element_id: str, event_type: str, event_data: Dict[str, Any]):
        """Handle generic events."""
        # Add event to history
        self.event_history.append({
            "element_id": element_id,
            "event_type": event_type,
            "event_data": event_data,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 1000 events
        if len(self.event_history) > 1000:
            self.event_history = self.event_history[-1000:]
        
        # Dispatch to appropriate handler
        await self.dispatch_event(element_id, event_type, event_data)
    
    def _calculate_distance(self, pos1: Dict[str, float], pos2: Dict[str, float]) -> float:
        """Calculate distance between two positions."""
        dx = pos1.get("x", 0) - pos2.get("x", 0)
        dy = pos1.get("y", 0) - pos2.get("y", 0)
        dz = pos1.get("z", 0) - pos2.get("z", 0)
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def _is_point_in_boundary(self, point: Dict[str, float], boundary: Dict[str, Any]) -> bool:
        """Check if a point is within a boundary."""
        boundary_type = boundary.get("type")
        
        if boundary_type == "rectangle":
            x, y = point.get("x", 0), point.get("y", 0)
            min_x = boundary.get("min_x", 0)
            max_x = boundary.get("max_x", 0)
            min_y = boundary.get("min_y", 0)
            max_y = boundary.get("max_y", 0)
            
            return min_x <= x <= max_x and min_y <= y <= max_y
        
        elif boundary_type == "circle":
            x, y = point.get("x", 0), point.get("y", 0)
            center_x = boundary.get("center_x", 0)
            center_y = boundary.get("center_y", 0)
            radius = boundary.get("radius", 0)
            
            distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
            return distance <= radius
        
        return False
    
    def _do_bounds_intersect(self, bounds1: Dict[str, Any], bounds2: Dict[str, Any]) -> bool:
        """Check if two bounding boxes intersect."""
        # Simple AABB intersection test
        return not (
            bounds1.get("max_x", 0) < bounds2.get("min_x", 0) or
            bounds1.get("min_x", 0) > bounds2.get("max_x", 0) or
            bounds1.get("max_y", 0) < bounds2.get("min_y", 0) or
            bounds1.get("min_y", 0) > bounds2.get("max_y", 0)
        )
    
    def start(self):
        """Start the behavior engine."""
        logger.info("Advanced behavior engine started")
    
    def stop(self):
        """Stop the behavior engine."""
        logger.info("Advanced behavior engine stopped")
    
    def get_element_state(self, element_id: str) -> Optional[str]:
        """Get the current state of an element."""
        # Implementation would track current states
        return "unknown"
    
    def get_registered_rules(self) -> List[str]:
        """Get list of registered rule IDs."""
        return [rule.rule_id for rule in self.rules]
    
    def get_registered_state_machines(self) -> List[str]:
        """Get list of registered state machine element IDs."""
        return list(self.state_machines.keys())
    
    def get_registered_time_triggers(self) -> List[str]:
        """Get list of registered time trigger IDs."""
        return [trigger.trigger_id for trigger in self.time_triggers]
    
    def handle_ui_event(self, event: dict) -> dict:
        """Handle UI events and return response."""
        event_type = event.get("type")
        
        if event_type == "selection":
            selection_event = SelectionEvent(**event)
            return asyncio.run(self._handle_selection_event(selection_event))
        elif event_type == "editing":
            editing_event = EditingEvent(**event)
            return asyncio.run(self._handle_editing_event(editing_event))
        else:
            return {"status": "error", "message": f"Unknown event type: {event_type}"}
    
    def get_selection_state(self, canvas_id: str) -> list:
        """Get current selection state for a canvas."""
        return self.selection_state.get(canvas_id, [])
    
    def _update_selection_state(self, canvas_id: str, selected_ids: list):
        """Update selection state for a canvas."""
        self.selection_state[canvas_id] = selected_ids
    
    def perform_undo(self, canvas_id: str) -> dict:
        """Perform undo operation for a canvas."""
        # Implementation would track operation history
        logger.info(f"Undo operation on canvas {canvas_id}")
        return {"status": "success", "message": "Undo completed"}
    
    def perform_redo(self, canvas_id: str) -> dict:
        """Perform redo operation for a canvas."""
        # Implementation would track operation history
        logger.info(f"Redo operation on canvas {canvas_id}")
        return {"status": "success", "message": "Redo completed"}
    
    def update_annotation(self, canvas_id: str, target_id: str, annotation_index: int, new_data: dict) -> dict:
        """Update an annotation."""
        logger.info(f"Updating annotation {annotation_index} for {target_id} on canvas {canvas_id}")
        return {"status": "success", "message": "Annotation updated"}
    
    def delete_annotation(self, canvas_id: str, target_id: str, annotation_index: int) -> dict:
        """Delete an annotation."""
        logger.info(f"Deleting annotation {annotation_index} for {target_id} on canvas {canvas_id}")
        return {"status": "success", "message": "Annotation deleted"}
    
    def _start_lock_cleanup_task(self):
        """Start background task to clean up expired locks."""
        def cleanup_expired_locks():
            while True:
                try:
                    self._cleanup_expired_locks()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Error in lock cleanup: {e}")
                    time.sleep(60)
        
        cleanup_thread = threading.Thread(target=cleanup_expired_locks, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_expired_locks(self):
        """Clean up expired editing locks."""
        current_time = time.time()
        expired_locks = []
        
        for canvas_id, locks in self.editing_locks.items():
            for object_id, lock_info in locks.items():
                if current_time - lock_info.get("lock_time", 0) > self.lock_timeout:
                    expired_locks.append((canvas_id, object_id))
        
        for canvas_id, object_id in expired_locks:
            if canvas_id in self.editing_locks and object_id in self.editing_locks[canvas_id]:
                del self.editing_locks[canvas_id][object_id]
                logger.info(f"Expired lock cleaned up: {canvas_id}/{object_id}")
    
    def set_lock_timeout(self, timeout_seconds: int):
        """Set the lock timeout in seconds."""
        self.lock_timeout = timeout_seconds
        logger.info(f"Lock timeout set to {timeout_seconds} seconds")
    
    def get_lock_timeout(self) -> int:
        """Get the current lock timeout in seconds."""
        return self.lock_timeout
    
    def lock_object(self, canvas_id: str, object_id: str, session_id: str, user_id: str) -> dict:
        """Lock an object for editing."""
        if canvas_id not in self.editing_locks:
            self.editing_locks[canvas_id] = {}
        
        # Check if already locked
        if object_id in self.editing_locks[canvas_id]:
            existing_lock = self.editing_locks[canvas_id][object_id]
            if existing_lock.get("session_id") != session_id:
                return {
                    "success": False,
                    "message": "Object is already locked by another session",
                    "lock_info": existing_lock
                }
        
        # Create lock
        lock_info = {
            "session_id": session_id,
            "user_id": user_id,
            "lock_time": time.time(),
            "lock_timeout": self.lock_timeout
        }
        
        self.editing_locks[canvas_id][object_id] = lock_info
        
        logger.info(f"Object locked: {canvas_id}/{object_id} by session {session_id}")
        
        return {
            "success": True,
            "message": "Object locked successfully",
            "lock_info": lock_info
        }
    
    def unlock_object(self, canvas_id: str, object_id: str, session_id: str) -> dict:
        """Unlock an object."""
        if canvas_id not in self.editing_locks:
            return {"success": False, "message": "No locks found for canvas"}
        
        if object_id not in self.editing_locks[canvas_id]:
            return {"success": False, "message": "Object not locked"}
        
        lock_info = self.editing_locks[canvas_id][object_id]
        if lock_info.get("session_id") != session_id:
            return {
                "success": False, 
                "message": "Cannot unlock object locked by another session",
                "lock_info": lock_info
            }
        
        # Remove lock
        del self.editing_locks[canvas_id][object_id]
        
        logger.info(f"Object unlocked: {canvas_id}/{object_id} by session {session_id}")
        
        return {"success": True, "message": "Object unlocked successfully"}
    
    def get_lock_status(self, canvas_id: str, object_id: str) -> dict:
        """Get the lock status of an object."""
        if canvas_id not in self.editing_locks:
            return {"locked": False}
        
        if object_id not in self.editing_locks[canvas_id]:
            return {"locked": False}
        
        lock_info = self.editing_locks[canvas_id][object_id]
        current_time = time.time()
        
        # Check if lock is expired
        if current_time - lock_info.get("lock_time", 0) > self.lock_timeout:
            # Clean up expired lock
            del self.editing_locks[canvas_id][object_id]
            return {"locked": False}
        
        return {
            "locked": True,
            "session_id": lock_info.get("session_id"),
            "user_id": lock_info.get("user_id"),
            "lock_time": lock_info.get("lock_time"),
            "remaining_time": self.lock_timeout - (current_time - lock_info.get("lock_time", 0))
        }
    
    def release_session_locks(self, session_id: str) -> dict:
        """Release all locks for a session."""
        released_count = 0
        
        for canvas_id, locks in self.editing_locks.items():
            objects_to_remove = []
            for object_id, lock_info in locks.items():
                if lock_info.get("session_id") == session_id:
                    objects_to_remove.append(object_id)
            
            for object_id in objects_to_remove:
                del locks[object_id]
                released_count += 1
        
        logger.info(f"Released {released_count} locks for session {session_id}")
        
        return {
            "success": True,
            "message": f"Released {released_count} locks",
            "released_count": released_count
        }
    
    def get_all_locks(self, canvas_id: str = None) -> dict:
        """Get all current locks."""
        if canvas_id:
            return {
                "canvas_id": canvas_id,
                "locks": self.editing_locks.get(canvas_id, {})
            }
        else:
            return {
                "all_locks": self.editing_locks.copy()
            } 