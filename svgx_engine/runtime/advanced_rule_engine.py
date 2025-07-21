"""
SVGX Engine - Advanced Rule Engine

Handles complex rule evaluation and management for business, safety, operational, maintenance, and compliance rules.
Supports rule chaining, dependencies, validation, and dynamic loading with enterprise-grade performance.
Integrates with the event-driven behavior engine and provides comprehensive rule management.
Follows Arxos engineering standards: absolute imports, global instances, modular/testable code, and comprehensive documentation.
"""

from typing import Dict, Any, List, Optional, Callable, Union, Set
from svgx_engine.runtime.event_driven_behavior_engine import Event, EventType, EventPriority
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import threading
from copy import deepcopy

logger = logging.getLogger(__name__)

class RuleType(Enum):
    """Types of rules supported by the Advanced Rule Engine."""
    BUSINESS = "business"
    SAFETY = "safety"
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    COMPLIANCE = "compliance"

class RulePriority(Enum):
    """Priority levels for rule execution."""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

class RuleStatus(Enum):
    """Status states for rules."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    TESTING = "testing"

@dataclass
class RuleCondition:
    """Represents a condition for rule evaluation."""
    field: str
    operator: str  # 'equals', 'not_equals', 'greater', 'less', 'contains', 'regex'
    value: Any
    logical_operator: str = "AND"  # AND, OR, NOT

@dataclass
class RuleAction:
    """Represents an action to execute when a rule is triggered."""
    action_type: str
    parameters: Dict[str, Any]
    target_element: Optional[str] = None
    delay: Optional[float] = None

@dataclass
class Rule:
    """Represents a rule in the Advanced Rule Engine."""
    id: str
    name: str
    description: str
    rule_type: RuleType
    priority: RulePriority
    conditions: List[RuleCondition]
    actions: List[RuleAction]
    dependencies: List[str] = field(default_factory=list)
    status: RuleStatus = RuleStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_count: int = 0
    last_executed: Optional[datetime] = None
    success_rate: float = 0.0

@dataclass
class RuleResult:
    """Represents the result of a rule evaluation."""
    rule_id: str
    triggered: bool
    execution_time: float
    conditions_met: List[bool]
    actions_executed: List[str]
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

class AdvancedRuleEngine:
    """
    Advanced Rule Engine for comprehensive rule evaluation and management.
    Supports business, safety, operational, maintenance, and compliance rules.
    """
    def __init__(self):
        # {rule_id: Rule}
        self.rules: Dict[str, Rule] = {}
        # {rule_type: Set[rule_id]}
        self.rules_by_type: Dict[RuleType, Set[str]] = {}
        # {priority: Set[rule_id]}
        self.rules_by_priority: Dict[RulePriority, Set[str]] = {}
        # {element_id: Set[rule_id]}
        self.rules_by_element: Dict[str, Set[str]] = {}
        # {rule_id: List[RuleResult]}
        self.execution_history: Dict[str, List[RuleResult]] = {}
        # Rule dependency graph
        self.dependency_graph: Dict[str, Set[str]] = {}
        # Performance monitoring
        self.performance_stats: Dict[str, Any] = {
            'total_evaluations': 0,
            'total_executions': 0,
            'average_evaluation_time': 0.0,
            'success_rate': 0.0
        }
        # Thread safety
        self._lock = threading.RLock()

    def register_business_rule(self, rule: Rule) -> bool:
        """Register a business rule."""
        return self._register_rule(rule, RuleType.BUSINESS)

    def register_safety_rule(self, rule: Rule) -> bool:
        """Register a safety rule."""
        return self._register_rule(rule, RuleType.SAFETY)

    def register_operational_rule(self, rule: Rule) -> bool:
        """Register an operational rule."""
        return self._register_rule(rule, RuleType.OPERATIONAL)

    def register_maintenance_rule(self, rule: Rule) -> bool:
        """Register a maintenance rule."""
        return self._register_rule(rule, RuleType.MAINTENANCE)

    def register_compliance_rule(self, rule: Rule) -> bool:
        """Register a compliance rule."""
        return self._register_rule(rule, RuleType.COMPLIANCE)

    def _register_rule(self, rule: Rule, expected_type: RuleType) -> bool:
        """Register a rule with validation and dependency management."""
        try:
            with self._lock:
                # Validate rule
                if not self._validate_rule(rule):
                    logger.error(f"Rule validation failed for {rule.id}")
                    return False

                # Check for conflicts
                if rule.id in self.rules:
                    logger.warning(f"Rule {rule.id} already exists, updating")
                    self._unregister_rule(rule.id)

                # Register rule
                self.rules[rule.id] = rule
                
                # Update type index
                if rule.rule_type not in self.rules_by_type:
                    self.rules_by_type[rule.rule_type] = set()
                self.rules_by_type[rule.rule_type].add(rule.id)
                
                # Update priority index
                if rule.priority not in self.rules_by_priority:
                    self.rules_by_priority[rule.priority] = set()
                self.rules_by_priority[rule.priority].add(rule.id)
                
                # Update element index
                for action in rule.actions:
                    if action.target_element:
                        if action.target_element not in self.rules_by_element:
                            self.rules_by_element[action.target_element] = set()
                        self.rules_by_element[action.target_element].add(rule.id)
                
                # Update dependency graph
                self.dependency_graph[rule.id] = set(rule.dependencies)
                
                # Initialize execution history
                self.execution_history[rule.id] = []
                
                logger.info(f"Registered {rule.rule_type.value} rule: {rule.id}")
                return True
                
        except Exception as e:
            logger.error(f"Error registering rule {rule.id}: {e}")
            return False

    def _validate_rule(self, rule: Rule) -> bool:
        """Validate a rule for correctness and completeness."""
        try:
            # Check required fields
            if not rule.id or not rule.name or not rule.conditions or not rule.actions:
                logger.error(f"Rule {rule.id} missing required fields")
                return False
            
            # Validate conditions
            for condition in rule.conditions:
                if not condition.field or not condition.operator:
                    logger.error(f"Rule {rule.id} has invalid condition")
                    return False
            
            # Validate actions
            for action in rule.actions:
                if not action.action_type:
                    logger.error(f"Rule {rule.id} has invalid action")
                    return False
            
            # Check for circular dependencies
            if self._has_circular_dependencies(rule.id, rule.dependencies):
                logger.error(f"Rule {rule.id} has circular dependencies")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating rule {rule.id}: {e}")
            return False

    def _has_circular_dependencies(self, rule_id: str, dependencies: List[str]) -> bool:
        """Check for circular dependencies in rule dependencies."""
        # Create a temporary graph with the new rule
        temp_graph = self.dependency_graph.copy()
        temp_graph[rule_id] = set(dependencies)
        
        visited = set()
        rec_stack = set()
        
        def dfs(node: str) -> bool:
            if node in rec_stack:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for dep in temp_graph.get(node, set()):
                if dfs(dep):
                    return True
            
            rec_stack.remove(node)
            return False
        
        # Check if adding this rule creates a cycle
        return dfs(rule_id)

    def _unregister_rule(self, rule_id: str):
        """Unregister a rule and clean up indexes."""
        if rule_id not in self.rules:
            return
        
        rule = self.rules[rule_id]
        
        # Remove from type index
        if rule.rule_type in self.rules_by_type:
            self.rules_by_type[rule.rule_type].discard(rule_id)
        
        # Remove from priority index
        if rule.priority in self.rules_by_priority:
            self.rules_by_priority[rule.priority].discard(rule_id)
        
        # Remove from element index
        for action in rule.actions:
            if action.target_element and action.target_element in self.rules_by_element:
                self.rules_by_element[action.target_element].discard(rule_id)
        
        # Remove from dependency graph
        if rule_id in self.dependency_graph:
            del self.dependency_graph[rule_id]
        
        # Remove from rules
        del self.rules[rule_id]

    async def evaluate_rules(self, context: Dict[str, Any], rule_types: Optional[List[RuleType]] = None) -> List[RuleResult]:
        """
        Evaluate all applicable rules against the given context.
        
        Args:
            context: Context data for rule evaluation
            rule_types: Optional filter for specific rule types
            
        Returns:
            List of rule evaluation results
        """
        try:
            with self._lock:
                start_time = datetime.utcnow()
                results = []
                
                # Get rules to evaluate
                rules_to_evaluate = self._get_rules_to_evaluate(rule_types)
                
                # Sort by priority (critical first)
                priority_order = [RulePriority.CRITICAL, RulePriority.HIGH, RulePriority.NORMAL, RulePriority.LOW]
                sorted_rules = []
                for priority in priority_order:
                    priority_rules = [r for r in rules_to_evaluate if r.priority == priority]
                    sorted_rules.extend(priority_rules)
                
                # Evaluate rules
                for rule in sorted_rules:
                    if rule.status != RuleStatus.ACTIVE:
                        continue
                    
                    result = await self._evaluate_rule(rule, context)
                    if result:
                        results.append(result)
                        
                        # Update rule statistics
                        rule.execution_count += 1
                        rule.last_executed = result.timestamp
                        
                        # Update success rate
                        if result.triggered:
                            rule.success_rate = (rule.success_rate * (rule.execution_count - 1) + 1.0) / rule.execution_count
                        else:
                            rule.success_rate = (rule.success_rate * (rule.execution_count - 1)) / rule.execution_count
                
                # Update performance statistics
                self._update_performance_stats(results, start_time)
                
                return results
                
        except Exception as e:
            logger.error(f"Error evaluating rules: {e}")
            return []

    def _get_rules_to_evaluate(self, rule_types: Optional[List[RuleType]] = None) -> List[Rule]:
        """Get rules to evaluate, optionally filtered by type."""
        if rule_types:
            rules = []
            for rule_type in rule_types:
                if rule_type in self.rules_by_type:
                    for rule_id in self.rules_by_type[rule_type]:
                        if rule_id in self.rules:
                            rules.append(self.rules[rule_id])
            return rules
        else:
            return list(self.rules.values())

    async def _evaluate_rule(self, rule: Rule, context: Dict[str, Any]) -> Optional[RuleResult]:
        """Evaluate a single rule against the context."""
        try:
            start_time = datetime.utcnow()
            
            # Evaluate conditions
            conditions_met = []
            for condition in rule.conditions:
                condition_result = self._evaluate_condition(condition, context)
                conditions_met.append(condition_result)
            
            # Determine if rule should trigger
            triggered = self._evaluate_conditions(rule.conditions, conditions_met)
            
            # Execute actions if triggered
            actions_executed = []
            error_message = None
            
            if triggered:
                try:
                    actions_executed = await self._execute_actions(rule.actions, context)
                except Exception as e:
                    error_message = str(e)
                    logger.error(f"Error executing actions for rule {rule.id}: {e}")
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create result
            result = RuleResult(
                rule_id=rule.id,
                triggered=triggered,
                execution_time=execution_time,
                conditions_met=conditions_met,
                actions_executed=actions_executed,
                error_message=error_message
            )
            
            # Record in history
            self.execution_history[rule.id].append(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.id}: {e}")
            return None

    def _evaluate_condition(self, condition: RuleCondition, context: Dict[str, Any]) -> bool:
        """Evaluate a single condition against the context."""
        try:
            field_value = context.get(condition.field)
            
            if condition.operator == "equals":
                return field_value == condition.value
            elif condition.operator == "not_equals":
                return field_value != condition.value
            elif condition.operator == "greater":
                return field_value > condition.value
            elif condition.operator == "less":
                return field_value < condition.value
            elif condition.operator == "greater_equal":
                return field_value >= condition.value
            elif condition.operator == "less_equal":
                return field_value <= condition.value
            elif condition.operator == "contains":
                return condition.value in field_value if field_value else False
            elif condition.operator == "regex":
                import re
                return bool(re.search(condition.value, str(field_value)))
            else:
                logger.warning(f"Unknown condition operator: {condition.operator}")
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False

    def _evaluate_conditions(self, conditions: List[RuleCondition], condition_results: List[bool]) -> bool:
        """Evaluate multiple conditions with logical operators."""
        if not conditions:
            return True
        
        result = condition_results[0]
        
        for i in range(1, len(conditions)):
            condition = conditions[i]
            condition_result = condition_results[i]
            
            if condition.logical_operator == "AND":
                result = result and condition_result
            elif condition.logical_operator == "OR":
                result = result or condition_result
            elif condition.logical_operator == "NOT":
                result = not condition_result
            else:
                logger.warning(f"Unknown logical operator: {condition.logical_operator}")
                result = result and condition_result
        
        return result

    async def _execute_actions(self, actions: List[RuleAction], context: Dict[str, Any]) -> List[str]:
        """Execute rule actions."""
        executed_actions = []
        
        for action in actions:
            try:
                # Create action event
                event = Event(
                    id=f"rule_action_{action.action_type}_{int(datetime.utcnow().timestamp())}",
                    type=EventType.SYSTEM,
                    priority=EventPriority.NORMAL,
                    timestamp=datetime.utcnow(),
                    element_id=action.target_element,
                    data={
                        "action_type": action.action_type,
                        "parameters": action.parameters,
                        "context": context
                    }
                )
                
                # Process event through behavior engine
                from svgx_engine.runtime.event_driven_behavior_engine import event_driven_behavior_engine
                result = event_driven_behavior_engine.process_event(event)
                if hasattr(result, '__await__'):
                    await result
                
                executed_actions.append(action.action_type)
                
                # Handle delayed actions
                if action.delay:
                    await asyncio.sleep(action.delay)
                
            except Exception as e:
                logger.error(f"Error executing action {action.action_type}: {e}")
        
        return executed_actions

    def _update_performance_stats(self, results: List[RuleResult], start_time: datetime):
        """Update performance statistics."""
        total_evaluations = len(results)
        total_executions = len([r for r in results if r.triggered])
        total_time = sum(r.execution_time for r in results)
        
        self.performance_stats['total_evaluations'] += total_evaluations
        self.performance_stats['total_executions'] += total_executions
        
        if total_evaluations > 0:
            avg_time = total_time / total_evaluations
            current_avg = self.performance_stats['average_evaluation_time']
            total_evals = self.performance_stats['total_evaluations']
            self.performance_stats['average_evaluation_time'] = (
                (current_avg * (total_evals - total_evaluations) + total_time) / total_evals
            )
        
        if self.performance_stats['total_evaluations'] > 0:
            self.performance_stats['success_rate'] = (
                self.performance_stats['total_executions'] / self.performance_stats['total_evaluations']
            )

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get a rule by ID."""
        return self.rules.get(rule_id)

    def get_rules_by_type(self, rule_type: RuleType) -> List[Rule]:
        """Get all rules of a specific type."""
        rule_ids = self.rules_by_type.get(rule_type, set())
        return [self.rules[rule_id] for rule_id in rule_ids if rule_id in self.rules]

    def get_rules_by_priority(self, priority: RulePriority) -> List[Rule]:
        """Get all rules of a specific priority."""
        rule_ids = self.rules_by_priority.get(priority, set())
        return [self.rules[rule_id] for rule_id in rule_ids if rule_id in self.rules]

    def get_rules_by_element(self, element_id: str) -> List[Rule]:
        """Get all rules that target a specific element."""
        rule_ids = self.rules_by_element.get(element_id, set())
        return [self.rules[rule_id] for rule_id in rule_ids if rule_id in self.rules]

    def get_execution_history(self, rule_id: str) -> List[RuleResult]:
        """Get execution history for a rule."""
        return self.execution_history.get(rule_id, [])

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return deepcopy(self.performance_stats)

    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update a rule with new parameters."""
        try:
            with self._lock:
                if rule_id not in self.rules:
                    logger.warning(f"Rule {rule_id} not found")
                    return False
                
                rule = self.rules[rule_id]
                
                # Update fields
                for field, value in updates.items():
                    if hasattr(rule, field):
                        setattr(rule, field, value)
                
                rule.updated_at = datetime.utcnow()
                
                logger.info(f"Updated rule: {rule_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating rule {rule_id}: {e}")
            return False

    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule."""
        try:
            with self._lock:
                if rule_id not in self.rules:
                    logger.warning(f"Rule {rule_id} not found")
                    return False
                
                self._unregister_rule(rule_id)
                
                # Clean up execution history
                if rule_id in self.execution_history:
                    del self.execution_history[rule_id]
                
                logger.info(f"Deleted rule: {rule_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting rule {rule_id}: {e}")
            return False

    def clear_rules(self, rule_type: Optional[RuleType] = None):
        """Clear all rules, optionally filtered by type."""
        try:
            with self._lock:
                if rule_type:
                    rule_ids = list(self.rules_by_type.get(rule_type, set()))
                else:
                    rule_ids = list(self.rules.keys())
                
                for rule_id in rule_ids:
                    self._unregister_rule(rule_id)
                    if rule_id in self.execution_history:
                        del self.execution_history[rule_id]
                
                logger.info(f"Cleared {len(rule_ids)} rules")
                
        except Exception as e:
            logger.error(f"Error clearing rules: {e}")

# Global instance
advanced_rule_engine = AdvancedRuleEngine()

# Register with the event-driven engine
def _register_advanced_rule_engine():
    def handler(event: Event):
        if event.type == EventType.SYSTEM and event.data.get('rule_evaluation'):
            # Rule evaluation events are handled internally
            return None
        return None
    
    # Import here to avoid circular imports
    from svgx_engine.runtime.event_driven_behavior_engine import event_driven_behavior_engine
    event_driven_behavior_engine.register_handler(
        event_type=EventType.SYSTEM,
        handler_id='advanced_rule_engine',
        handler=handler,
        priority=1
    )

_register_advanced_rule_engine() 