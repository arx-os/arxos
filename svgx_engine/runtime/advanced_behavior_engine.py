"""
SVGX Advanced Behavior Engine for complex behavior management.

This module implements advanced behavior features including:
- Rule engines with complex logic evaluation
- State machines with transition management
- Time-based triggers and scheduling
- Advanced condition evaluation
- CAD-parity behaviors
- Infrastructure simulation behaviors
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
    """Advanced behavior engine with rule engines, state machines, and complex triggers."""
    
    def __init__(self):
        self.rules: Dict[str, BehaviorRule] = {}
        self.state_machines: Dict[str, Dict[str, BehaviorState]] = {}
        self.time_triggers: Dict[str, TimeTrigger] = {}
        self.conditions: Dict[str, Condition] = {}
        self.active_states: Dict[str, str] = {}  # element_id -> current_state
        self.rule_cache: Dict[str, Any] = {}
        self.running = False
        self.event_handlers: Dict[str, Callable] = {}
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Setup default event handlers for different behavior types."""
        self.event_handlers = {
            'user_interaction': self._handle_user_interaction,
            'system_event': self._handle_system_event,
            'physics_event': self._handle_physics_event,
            'environmental_event': self._handle_environmental_event,
            'operational_event': self._handle_operational_event,
            'cad_parity': self._handle_cad_parity,
            'infrastructure': self._handle_infrastructure
        }
    
    def register_rule(self, rule: BehaviorRule):
        """Register a behavior rule."""
        try:
            self.rules[rule.rule_id] = rule
            logger.info(f"Registered rule {rule.rule_id}")
        except Exception as e:
            logger.error(f"Failed to register rule {rule.rule_id}: {e}")
    
    def register_state_machine(self, element_id: str, states: List[BehaviorState], initial_state: str):
        """Register a state machine for an element."""
        try:
            state_dict = {state.state_id: state for state in states}
            self.state_machines[element_id] = state_dict
            self.active_states[element_id] = initial_state
            logger.info(f"Registered state machine for {element_id} with {len(states)} states")
        except Exception as e:
            logger.error(f"Failed to register state machine for {element_id}: {e}")
    
    def register_time_trigger(self, trigger: TimeTrigger):
        """Register a time-based trigger."""
        try:
            self.time_triggers[trigger.trigger_id] = trigger
            self._calculate_next_execution(trigger)
            logger.info(f"Registered time trigger {trigger.trigger_id}")
        except Exception as e:
            logger.error(f"Failed to register time trigger {trigger.trigger_id}: {e}")
    
    def register_condition(self, condition: Condition):
        """Register a complex condition."""
        try:
            self.conditions[condition.condition_id] = condition
            logger.info(f"Registered condition {condition.condition_id}")
        except Exception as e:
            logger.error(f"Failed to register condition {condition.condition_id}: {e}")
    
    async def evaluate_rules(self, element_id: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate all applicable rules for an element."""
        try:
            applicable_rules = []
            
            for rule in self.rules.values():
                if not rule.enabled:
                    continue
                
                # Check if rule applies to this element
                if self._rule_applies_to_element(rule, element_id, context):
                    # Evaluate rule conditions
                    if self._evaluate_rule_conditions(rule, context):
                        applicable_rules.append({
                            'rule_id': rule.rule_id,
                            'rule_type': rule.rule_type.value,
                            'actions': rule.actions,
                            'priority': rule.priority
                        })
            
            # Sort by priority (higher priority first)
            applicable_rules.sort(key=lambda x: x['priority'], reverse=True)
            
            return applicable_rules
            
        except Exception as e:
            logger.error(f"Failed to evaluate rules for {element_id}: {e}")
            return []
    
    def _rule_applies_to_element(self, rule: BehaviorRule, element_id: str, context: Dict[str, Any]) -> bool:
        """Check if a rule applies to a specific element."""
        # Check element-specific conditions in rule metadata
        if 'target_elements' in rule.metadata:
            target_elements = rule.metadata['target_elements']
            if isinstance(target_elements, list):
                return element_id in target_elements
            elif isinstance(target_elements, str):
                return element_id == target_elements
        
        # Check element type conditions
        if 'element_types' in rule.metadata:
            element_type = context.get('element_type', '')
            return element_type in rule.metadata['element_types']
        
        # Default: rule applies to all elements
        return True
    
    def _evaluate_rule_conditions(self, rule: BehaviorRule, context: Dict[str, Any]) -> bool:
        """Evaluate conditions for a rule."""
        try:
            for condition in rule.conditions:
                if not self._evaluate_single_condition(condition, context):
                    return False
            return True
        except Exception as e:
            logger.error(f"Failed to evaluate rule conditions: {e}")
            return False
    
    def _evaluate_single_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a single condition."""
        try:
            condition_type = condition.get('type', 'simple')
            
            if condition_type == 'threshold':
                return self._evaluate_threshold_condition(condition, context)
            elif condition_type == 'time':
                return self._evaluate_time_condition(condition, context)
            elif condition_type == 'spatial':
                return self._evaluate_spatial_condition(condition, context)
            elif condition_type == 'relational':
                return self._evaluate_relational_condition(condition, context)
            elif condition_type == 'complex':
                return self._evaluate_complex_condition(condition, context)
            else:
                return self._evaluate_simple_condition(condition, context)
                
        except Exception as e:
            logger.error(f"Failed to evaluate condition: {e}")
            return False
    
    def _evaluate_threshold_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate threshold-based conditions."""
        try:
            variable = condition.get('variable', '')
            operator = condition.get('operator', '==')
            threshold = condition.get('threshold', 0)
            
            value = context.get(variable, 0)
            
            if operator == '==':
                return value == threshold
            elif operator == '!=':
                return value != threshold
            elif operator == '>':
                return value > threshold
            elif operator == '<':
                return value < threshold
            elif operator == '>=':
                return value >= threshold
            elif operator == '<=':
                return value <= threshold
            else:
                return False
                
        except Exception as e:
            logger.error(f"Failed to evaluate threshold condition: {e}")
            return False
    
    def _evaluate_time_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate time-based conditions."""
        try:
            condition_type = condition.get('time_type', 'current')
            
            if condition_type == 'current':
                current_time = datetime.now()
                start_time = condition.get('start_time')
                end_time = condition.get('end_time')
                
                if start_time and current_time < start_time:
                    return False
                if end_time and current_time > end_time:
                    return False
                return True
                
            elif condition_type == 'duration':
                start_time = context.get('start_time')
                duration = condition.get('duration', 0)
                
                if start_time:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    return elapsed <= duration
                
            elif condition_type == 'schedule':
                current_time = datetime.now()
                schedule = condition.get('schedule', {})
                
                # Check day of week
                if 'days' in schedule:
                    current_day = current_time.weekday()
                    if current_day not in schedule['days']:
                        return False
                
                # Check time range
                if 'start_hour' in schedule and 'end_hour' in schedule:
                    current_hour = current_time.hour
                    if not (schedule['start_hour'] <= current_hour <= schedule['end_hour']):
                        return False
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to evaluate time condition: {e}")
            return False
    
    def _evaluate_spatial_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate spatial conditions."""
        try:
            condition_type = condition.get('spatial_type', 'proximity')
            
            if condition_type == 'proximity':
                target_position = condition.get('target_position', {})
                current_position = context.get('position', {})
                max_distance = condition.get('max_distance', 0)
                
                if target_position and current_position:
                    distance = self._calculate_distance(target_position, current_position)
                    return distance <= max_distance
                    
            elif condition_type == 'containment':
                boundary = condition.get('boundary', {})
                position = context.get('position', {})
                
                if boundary and position:
                    return self._is_point_in_boundary(position, boundary)
                    
            elif condition_type == 'intersection':
                object1_bounds = condition.get('object1_bounds', {})
                object2_bounds = condition.get('object2_bounds', {})
                
                if object1_bounds and object2_bounds:
                    return self._do_bounds_intersect(object1_bounds, object2_bounds)
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to evaluate spatial condition: {e}")
            return False
    
    def _evaluate_relational_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate relational conditions."""
        try:
            relation_type = condition.get('relation_type', 'dependency')
            
            if relation_type == 'dependency':
                dependent_element = condition.get('dependent_element', '')
                dependency_status = context.get('dependencies', {}).get(dependent_element, 'unknown')
                required_status = condition.get('required_status', 'active')
                return dependency_status == required_status
                
            elif relation_type == 'hierarchy':
                parent_element = condition.get('parent_element', '')
                current_parent = context.get('parent', '')
                return parent_element == current_parent
                
            elif relation_type == 'connection':
                connected_elements = condition.get('connected_elements', [])
                current_connections = context.get('connections', [])
                return all(elem in current_connections for elem in connected_elements)
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to evaluate relational condition: {e}")
            return False
    
    def _evaluate_complex_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate complex logical conditions."""
        try:
            expression = condition.get('expression', '')
            variables = condition.get('variables', {})
            
            # Create a safe evaluation environment
            safe_dict = {
                '__builtins__': {},
                'context': context,
                'variables': variables,
                'math': math,
                'time': time,
                'datetime': datetime
            }
            
            # Replace variables in expression
            for var_name, var_value in variables.items():
                expression = expression.replace(f"${var_name}", str(var_value))
            
            # Evaluate the expression
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to evaluate complex condition: {e}")
            return False
    
    def _evaluate_simple_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate simple conditions."""
        try:
            variable = condition.get('variable', '')
            operator = condition.get('operator', '==')
            value = condition.get('value')
            
            context_value = context.get(variable)
            
            if operator == '==':
                return context_value == value
            elif operator == '!=':
                return context_value != value
            elif operator == '>':
                return context_value > value
            elif operator == '<':
                return context_value < value
            elif operator == '>=':
                return context_value >= value
            elif operator == '<=':
                return context_value <= value
            elif operator == 'in':
                return context_value in value
            elif operator == 'not_in':
                return context_value not in value
            else:
                return False
                
        except Exception as e:
            logger.error(f"Failed to evaluate simple condition: {e}")
            return False
    
    async def execute_state_transition(self, element_id: str, target_state: str, context: Dict[str, Any] = None):
        """Execute a state transition for an element."""
        try:
            if element_id not in self.state_machines:
                logger.warning(f"No state machine found for {element_id}")
                return
            
            state_machine = self.state_machines[element_id]
            current_state_id = self.active_states.get(element_id)
            
            if current_state_id and current_state_id in state_machine:
                current_state = state_machine[current_state_id]
                
                # Check if transition is valid
                if self._is_transition_valid(current_state, target_state, context or {}):
                    # Execute exit actions for current state
                    await self._execute_actions(current_state.exit_actions, element_id, context or {})
                    
                    # Update active state
                    self.active_states[element_id] = target_state
                    
                    # Execute entry actions for new state
                    if target_state in state_machine:
                        new_state = state_machine[target_state]
                        await self._execute_actions(new_state.entry_actions, element_id, context or {})
                        
                        logger.info(f"State transition for {element_id}: {current_state_id} -> {target_state}")
                    else:
                        logger.error(f"Target state {target_state} not found in state machine for {element_id}")
                else:
                    logger.warning(f"Invalid state transition for {element_id}: {current_state_id} -> {target_state}")
            else:
                logger.warning(f"Current state not found for {element_id}")
                
        except Exception as e:
            logger.error(f"Failed to execute state transition for {element_id}: {e}")
    
    def _is_transition_valid(self, current_state: BehaviorState, target_state: str, context: Dict[str, Any]) -> bool:
        """Check if a state transition is valid."""
        try:
            for transition in current_state.transitions:
                if transition.get('target_state') == target_state:
                    # Check transition conditions
                    conditions = transition.get('conditions', [])
                    for condition in conditions:
                        if not self._evaluate_single_condition(condition, context):
                            return False
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to check transition validity: {e}")
            return False
    
    async def execute_time_triggers(self):
        """Execute time-based triggers that are due."""
        try:
            current_time = datetime.now()
            triggers_to_execute = []
            
            for trigger_id, trigger in self.time_triggers.items():
                if not trigger.enabled:
                    continue
                
                if trigger.next_execution and current_time >= trigger.next_execution:
                    triggers_to_execute.append(trigger)
            
            for trigger in triggers_to_execute:
                await self._execute_trigger_actions(trigger)
                self._calculate_next_execution(trigger)
                
        except Exception as e:
            logger.error(f"Failed to execute time triggers: {e}")
    
    async def _execute_trigger_actions(self, trigger: TimeTrigger):
        """Execute actions for a time trigger."""
        try:
            logger.info(f"Executing time trigger {trigger.trigger_id}")
            await self._execute_actions(trigger.actions, trigger.trigger_id, {})
            trigger.last_execution = datetime.now()
        except Exception as e:
            logger.error(f"Failed to execute trigger actions for {trigger.trigger_id}: {e}")
    
    def _calculate_next_execution(self, trigger: TimeTrigger):
        """Calculate the next execution time for a trigger."""
        try:
            schedule_type = trigger.schedule_type
            schedule_data = trigger.schedule_data
            
            if schedule_type == 'scheduled':
                # Fixed schedule
                trigger.next_execution = schedule_data.get('next_time')
                
            elif schedule_type == 'cyclic':
                # Repeating schedule
                interval = schedule_data.get('interval', 3600)  # Default 1 hour
                if trigger.last_execution:
                    trigger.next_execution = trigger.last_execution + timedelta(seconds=interval)
                else:
                    trigger.next_execution = datetime.now() + timedelta(seconds=interval)
                    
            elif schedule_type == 'sequential':
                # Sequential events
                sequence = schedule_data.get('sequence', [])
                current_index = schedule_data.get('current_index', 0)
                
                if current_index < len(sequence):
                    next_event = sequence[current_index]
                    trigger.next_execution = next_event.get('time')
                    schedule_data['current_index'] = current_index + 1
                    
            elif schedule_type == 'delayed':
                # Delayed execution
                delay = schedule_data.get('delay', 0)
                trigger.next_execution = datetime.now() + timedelta(seconds=delay)
                
        except Exception as e:
            logger.error(f"Failed to calculate next execution for trigger {trigger.trigger_id}: {e}")
    
    async def _execute_actions(self, actions: List[Dict[str, Any]], element_id: str, context: Dict[str, Any]):
        """Execute a list of actions."""
        try:
            for action in actions:
                action_type = action.get('type', 'update')
                
                if action_type == 'update':
                    await self._execute_update_action(action, element_id, context)
                elif action_type == 'animate':
                    await self._execute_animate_action(action, element_id, context)
                elif action_type == 'calculate':
                    await self._execute_calculate_action(action, element_id, context)
                elif action_type == 'trigger':
                    await self._execute_trigger_action(action, element_id, context)
                elif action_type == 'log':
                    await self._execute_log_action(action, element_id, context)
                elif action_type == 'cad_parity':
                    await self._execute_cad_parity_action(action, element_id, context)
                elif action_type == 'infrastructure':
                    await self._execute_infrastructure_action(action, element_id, context)
                else:
                    logger.warning(f"Unknown action type: {action_type}")
                    
        except Exception as e:
            logger.error(f"Failed to execute actions for {element_id}: {e}")
    
    async def _execute_update_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute an update action."""
        try:
            target_property = action.get('target_property', '')
            new_value = action.get('value')
            
            # Update context with new value
            context[target_property] = new_value
            logger.info(f"Updated {target_property} for {element_id} to {new_value}")
            
        except Exception as e:
            logger.error(f"Failed to execute update action: {e}")
    
    async def _execute_animate_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute an animation action."""
        try:
            animation_type = action.get('animation_type', 'motion')
            duration = action.get('duration', 1.0)
            properties = action.get('properties', {})
            
            logger.info(f"Executing {animation_type} animation for {element_id} (duration: {duration}s)")
            # Animation implementation would go here
            
        except Exception as e:
            logger.error(f"Failed to execute animate action: {e}")
    
    async def _execute_calculate_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute a calculation action."""
        try:
            formula = action.get('formula', '')
            target_variable = action.get('target_variable', '')
            
            # Create safe evaluation environment
            safe_dict = {
                '__builtins__': {},
                'math': math,
                'context': context,
                **context
            }
            
            result = eval(formula, {"__builtins__": {}}, safe_dict)
            context[target_variable] = result
            
            logger.info(f"Calculated {target_variable} = {result} for {element_id}")
            
        except Exception as e:
            logger.error(f"Failed to execute calculate action: {e}")
    
    async def _execute_trigger_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute a trigger action."""
        try:
            target_element = action.get('target_element', element_id)
            event_type = action.get('event_type', 'custom')
            event_data = action.get('event_data', {})
            
            # Trigger event on target element
            await self._handle_event(target_element, event_type, event_data)
            
        except Exception as e:
            logger.error(f"Failed to execute trigger action: {e}")
    
    async def _execute_log_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute a logging action."""
        try:
            message = action.get('message', '')
            level = action.get('level', 'info')
            
            # Format message with context
            formatted_message = message.format(**context)
            
            if level == 'debug':
                logger.debug(formatted_message)
            elif level == 'info':
                logger.info(formatted_message)
            elif level == 'warning':
                logger.warning(formatted_message)
            elif level == 'error':
                logger.error(formatted_message)
            else:
                logger.info(formatted_message)
                
        except Exception as e:
            logger.error(f"Failed to execute log action: {e}")
    
    async def _execute_cad_parity_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute a CAD-parity action."""
        try:
            action_type = action.get('cad_action_type', 'dimension')
            
            if action_type == 'dimension':
                await self._execute_dimension_action(action, element_id, context)
            elif action_type == 'constraint':
                await self._execute_constraint_action(action, element_id, context)
            elif action_type == 'snap':
                await self._execute_snap_action(action, element_id, context)
            elif action_type == 'selection':
                await self._execute_selection_action(action, element_id, context)
            elif action_type == 'editing':
                await self._execute_editing_action(action, element_id, context)
            else:
                logger.warning(f"Unknown CAD-parity action type: {action_type}")
                
        except Exception as e:
            logger.error(f"Failed to execute CAD-parity action: {e}")
    
    async def _execute_infrastructure_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute an infrastructure action."""
        try:
            system_type = action.get('system_type', 'hvac')
            
            if system_type == 'hvac':
                await self._execute_hvac_action(action, element_id, context)
            elif system_type == 'electrical':
                await self._execute_electrical_action(action, element_id, context)
            elif system_type == 'plumbing':
                await self._execute_plumbing_action(action, element_id, context)
            elif system_type == 'fire_protection':
                await self._execute_fire_protection_action(action, element_id, context)
            elif system_type == 'security':
                await self._execute_security_action(action, element_id, context)
            else:
                logger.warning(f"Unknown infrastructure system type: {system_type}")
                
        except Exception as e:
            logger.error(f"Failed to execute infrastructure action: {e}")
    
    # CAD-parity action implementations
    async def _execute_dimension_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute dimensioning action."""
        dimension_type = action.get('dimension_type', 'linear')
        logger.info(f"Executing {dimension_type} dimensioning for {element_id}")
    
    async def _execute_constraint_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute constraint action."""
        constraint_type = action.get('constraint_type', 'geometric')
        logger.info(f"Executing {constraint_type} constraint for {element_id}")
    
    async def _execute_snap_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute snap action."""
        snap_type = action.get('snap_type', 'point')
        logger.info(f"Executing {snap_type} snap for {element_id}")
    
    async def _execute_selection_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute selection action."""
        selection_mode = action.get('selection_mode', 'single')
        logger.info(f"Executing {selection_mode} selection for {element_id}")
    
    async def _execute_editing_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute editing action."""
        edit_type = action.get('edit_type', 'modify')
        logger.info(f"Executing {edit_type} editing for {element_id}")
    
    # Infrastructure action implementations
    async def _execute_hvac_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute HVAC system action."""
        hvac_action = action.get('hvac_action', 'temperature_control')
        logger.info(f"Executing HVAC {hvac_action} for {element_id}")
    
    async def _execute_electrical_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute electrical system action."""
        electrical_action = action.get('electrical_action', 'power_control')
        logger.info(f"Executing electrical {electrical_action} for {element_id}")
    
    async def _execute_plumbing_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute plumbing system action."""
        plumbing_action = action.get('plumbing_action', 'flow_control')
        logger.info(f"Executing plumbing {plumbing_action} for {element_id}")
    
    async def _execute_fire_protection_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute fire protection system action."""
        fire_action = action.get('fire_action', 'safety_check')
        logger.info(f"Executing fire protection {fire_action} for {element_id}")
    
    async def _execute_security_action(self, action: Dict[str, Any], element_id: str, context: Dict[str, Any]):
        """Execute security system action."""
        security_action = action.get('security_action', 'access_control')
        logger.info(f"Executing security {security_action} for {element_id}")
    
    # Event handler implementations
    async def _handle_user_interaction(self, element_id: str, event_data: Dict[str, Any]):
        """Handle user interaction events."""
        interaction_type = event_data.get('type', 'click')
        logger.info(f"Handling user interaction {interaction_type} for {element_id}")
    
    async def _handle_system_event(self, element_id: str, event_data: Dict[str, Any]):
        """Handle system events."""
        event_type = event_data.get('type', 'state_change')
        logger.info(f"Handling system event {event_type} for {element_id}")
    
    async def _handle_physics_event(self, element_id: str, event_data: Dict[str, Any]):
        """Handle physics events."""
        physics_type = event_data.get('type', 'collision')
        logger.info(f"Handling physics event {physics_type} for {element_id}")
    
    async def _handle_environmental_event(self, element_id: str, event_data: Dict[str, Any]):
        """Handle environmental events."""
        env_type = event_data.get('type', 'weather')
        logger.info(f"Handling environmental event {env_type} for {element_id}")
    
    async def _handle_operational_event(self, element_id: str, event_data: Dict[str, Any]):
        """Handle operational events."""
        op_type = event_data.get('type', 'start')
        logger.info(f"Handling operational event {op_type} for {element_id}")
    
    async def _handle_cad_parity(self, element_id: str, event_data: Dict[str, Any]):
        """Handle CAD-parity events."""
        cad_type = event_data.get('type', 'dimension')
        logger.info(f"Handling CAD-parity event {cad_type} for {element_id}")
    
    async def _handle_infrastructure(self, element_id: str, event_data: Dict[str, Any]):
        """Handle infrastructure events."""
        infra_type = event_data.get('type', 'system')
        logger.info(f"Handling infrastructure event {infra_type} for {element_id}")
    
    async def _handle_event(self, element_id: str, event_type: str, event_data: Dict[str, Any]):
        """Handle events for elements."""
        try:
            # Evaluate rules for this event
            context = {
                'element_id': element_id,
                'event_type': event_type,
                'event_data': event_data,
                'timestamp': datetime.now(),
                **event_data
            }
            
            applicable_rules = await self.evaluate_rules(element_id, context)
            
            # Execute applicable rules
            for rule in applicable_rules:
                await self._execute_actions(rule['actions'], element_id, context)
            
            # Handle specific event types
            if event_type in self.event_handlers:
                await self.event_handlers[event_type](element_id, event_data)
            
        except Exception as e:
            logger.error(f"Failed to handle event {event_type} for {element_id}: {e}")
    
    # Utility methods
    def _calculate_distance(self, pos1: Dict[str, float], pos2: Dict[str, float]) -> float:
        """Calculate distance between two positions."""
        try:
            dx = pos1.get('x', 0) - pos2.get('x', 0)
            dy = pos1.get('y', 0) - pos2.get('y', 0)
            dz = pos1.get('z', 0) - pos2.get('z', 0)
            return math.sqrt(dx**2 + dy**2 + dz**2)
        except Exception as e:
            logger.error(f"Failed to calculate distance: {e}")
            return float('inf')
    
    def _is_point_in_boundary(self, point: Dict[str, float], boundary: Dict[str, Any]) -> bool:
        """Check if a point is within a boundary."""
        try:
            # Simple rectangular boundary check
            x, y = point.get('x', 0), point.get('y', 0)
            min_x = boundary.get('min_x', float('-inf'))
            max_x = boundary.get('max_x', float('inf'))
            min_y = boundary.get('min_y', float('-inf'))
            max_y = boundary.get('max_y', float('inf'))
            
            return min_x <= x <= max_x and min_y <= y <= max_y
        except Exception as e:
            logger.error(f"Failed to check point in boundary: {e}")
            return False
    
    def _do_bounds_intersect(self, bounds1: Dict[str, Any], bounds2: Dict[str, Any]) -> bool:
        """Check if two bounding boxes intersect."""
        try:
            # Simple AABB intersection test
            return not (
                bounds1.get('max_x', 0) < bounds2.get('min_x', 0) or
                bounds1.get('min_x', 0) > bounds2.get('max_x', 0) or
                bounds1.get('max_y', 0) < bounds2.get('min_y', 0) or
                bounds1.get('min_y', 0) > bounds2.get('max_y', 0)
            )
        except Exception as e:
            logger.error(f"Failed to check bounds intersection: {e}")
            return False
    
    def start(self):
        """Start the behavior engine."""
        self.running = True
        logger.info("Advanced behavior engine started")
    
    def stop(self):
        """Stop the behavior engine."""
        self.running = False
        logger.info("Advanced behavior engine stopped")
    
    def get_element_state(self, element_id: str) -> Optional[str]:
        """Get the current state of an element."""
        return self.active_states.get(element_id)
    
    def get_registered_rules(self) -> List[str]:
        """Get list of registered rule IDs."""
        return list(self.rules.keys())
    
    def get_registered_state_machines(self) -> List[str]:
        """Get list of elements with state machines."""
        return list(self.state_machines.keys())
    
    def get_registered_time_triggers(self) -> List[str]:
        """Get list of registered time trigger IDs."""
        return list(self.time_triggers.keys()) 