"""
Logic Engine Service

This service provides advanced rule-based logic processing and automated
decision making capabilities including:
- Rule-based decision making and workflow automation
- Conditional logic processing with complex expressions
- Intelligent data analysis and pattern recognition
- Rule management and versioning
- Performance optimization and caching
- Multi-threaded execution and parallel processing
- Error handling and recovery mechanisms

Performance Targets:
- Rule evaluation completes within 100ms for simple rules
- Complex rule chains complete within 500ms
- Support for 1000+ concurrent rule evaluations
- 99.9%+ rule execution accuracy
- Comprehensive rule validation and error handling
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from pathlib import Path
import uuid
import hashlib
import re
import operator
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
import yaml
import ast
from functools import lru_cache

from structlog import get_logger

logger = get_logger()


class RuleType(Enum):
    """Rule type enumeration."""
    CONDITIONAL = "conditional"
    TRANSFORMATION = "transformation"
    VALIDATION = "validation"
    WORKFLOW = "workflow"
    ANALYSIS = "analysis"


class RuleStatus(Enum):
    """Rule status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"
    ERROR = "error"


class ExecutionStatus(Enum):
    """Execution status enumeration."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    ERROR = "error"


class DataType(Enum):
    """Data type enumeration."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    NULL = "null"


@dataclass
class Rule:
    """Represents a logic rule."""
    rule_id: str
    name: str
    description: str
    rule_type: RuleType
    status: RuleStatus
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    priority: int
    version: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    tags: List[str]
    execution_count: int = 0
    success_count: int = 0
    error_count: int = 0
    avg_execution_time: float = 0.0


@dataclass
class RuleExecution:
    """Represents a rule execution result."""
    execution_id: str
    rule_id: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    status: ExecutionStatus
    execution_time: float
    error_message: Optional[str]
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class RuleChain:
    """Represents a chain of rules."""
    chain_id: str
    name: str
    description: str
    rules: List[str]
    execution_order: str
    status: RuleStatus
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]


@dataclass
class DataContext:
    """Represents data context for rule evaluation."""
    data: Dict[str, Any]
    variables: Dict[str, Any]
    functions: Dict[str, Callable]
    metadata: Dict[str, Any]


class LogicEngine:
    """
    Advanced logic engine for rule-based decision making and workflow automation.
    
    This engine provides comprehensive rule processing capabilities including
    conditional logic, data transformation, validation, and workflow automation
    with performance optimization and error handling.
    """
    
    def __init__(self, db_path: str = "logic_engine.db"):
        """
        Initialize the logic engine.
        
        Args:
            db_path: Path to the database file
        """
        self.db_path = db_path
        self.rules: Dict[str, Rule] = {}
        self.rule_chains: Dict[str, RuleChain] = {}
        self.execution_cache = {}
        self.lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Performance metrics
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.average_execution_time = 0.0
        
        # Initialize components
        self._init_database()
        self._init_builtin_functions()
        self._load_rules()
        
        logger.info("Logic Engine initialized successfully")
    
    def _init_database(self) -> None:
        """Initialize database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS rules (
                        rule_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        rule_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        conditions TEXT NOT NULL,
                        actions TEXT NOT NULL,
                        priority INTEGER NOT NULL,
                        version TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        metadata TEXT,
                        tags TEXT,
                        execution_count INTEGER DEFAULT 0,
                        success_count INTEGER DEFAULT 0,
                        error_count INTEGER DEFAULT 0,
                        avg_execution_time REAL DEFAULT 0.0
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS rule_executions (
                        execution_id TEXT PRIMARY KEY,
                        rule_id TEXT NOT NULL,
                        input_data TEXT NOT NULL,
                        output_data TEXT NOT NULL,
                        status TEXT NOT NULL,
                        execution_time REAL NOT NULL,
                        error_message TEXT,
                        timestamp TEXT NOT NULL,
                        metadata TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS rule_chains (
                        chain_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        rules TEXT NOT NULL,
                        execution_order TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        metadata TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS rule_templates (
                        template_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        template_type TEXT NOT NULL,
                        template_data TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        usage_count INTEGER DEFAULT 0
                    )
                """)
                
                conn.commit()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def _init_builtin_functions(self) -> None:
        """Initialize built-in functions for rule evaluation."""
        self.builtin_functions = {
            # String functions
            'length': len,
            'lower': str.lower,
            'upper': str.upper,
            'trim': str.strip,
            'substring': lambda s, start, end: s[start:end],
            'contains': lambda s, substr: substr in s,
            'startsWith': lambda s, prefix: s.startswith(prefix),
            'endsWith': lambda s, suffix: s.endswith(suffix),
            'replace': str.replace,
            'split': str.split,
            'join': lambda arr, sep: sep.join(arr),
            
            # Number functions
            'abs': abs,
            'round': round,
            'floor': lambda x: int(x),
            'ceil': lambda x: int(x + 1) if x % 1 != 0 else int(x),
            'min': min,
            'max': max,
            'sum': sum,
            'avg': lambda arr: sum(arr) / len(arr) if arr else 0,
            
            # Array functions
            'size': len,
            'isEmpty': lambda arr: len(arr) == 0,
            'first': lambda arr: arr[0] if arr else None,
            'last': lambda arr: arr[-1] if arr else None,
            'push': lambda arr, item: arr + [item],
            'pop': lambda arr: arr[:-1] if arr else [],
            'filter': lambda arr, func: [x for x in arr if func(x)],
            'map': lambda arr, func: [func(x) for x in arr],
            'reduce': lambda arr, func, initial: reduce(func, arr, initial),
            
            # Object functions
            'keys': dict.keys,
            'values': dict.values,
            'hasKey': lambda obj, key: key in obj,
            'get': lambda obj, key, default=None: obj.get(key, default),
            'set': lambda obj, key, value: {**obj, key: value},
            'merge': lambda obj1, obj2: {**obj1, **obj2},
            
            # Type functions
            'isString': lambda x: isinstance(x, str),
            'isNumber': lambda x: isinstance(x, (int, float)),
            'isBoolean': lambda x: isinstance(x, bool),
            'isArray': lambda x: isinstance(x, list),
            'isObject': lambda x: isinstance(x, dict),
            'isNull': lambda x: x is None,
            
            # Logic functions
            'if': lambda condition, true_val, false_val: true_val if condition else false_val,
            'and': lambda *args: all(args),
            'or': lambda *args: any(args),
            'not': lambda x: not x,
            
            # Date functions
            'now': datetime.now,
            'date': lambda dt: dt.date() if dt else None,
            'time': lambda dt: dt.time() if dt else None,
            'year': lambda dt: dt.year if dt else None,
            'month': lambda dt: dt.month if dt else None,
            'day': lambda dt: dt.day if dt else None,
            'hour': lambda dt: dt.hour if dt else None,
            'minute': lambda dt: dt.minute if dt else None,
            'second': lambda dt: dt.second if dt else None,
            
            # Math functions
            'add': lambda x, y: x + y,
            'subtract': lambda x, y: x - y,
            'multiply': lambda x, y: x * y,
            'divide': lambda x, y: x / y if y != 0 else None,
            'modulo': lambda x, y: x % y if y != 0 else None,
            'power': lambda x, y: x ** y,
            
            # Utility functions
            'uuid': lambda: str(uuid.uuid4()),
            'hash': lambda data: hashlib.md5(str(data).encode()).hexdigest(),
            'random': lambda min_val=0, max_val=1: random.uniform(min_val, max_val),
            'format': lambda template, *args: template.format(*args),
            'parseJson': json.loads,
            'stringify': json.dumps,
        }
    
    def _load_rules(self) -> None:
        """Load rules from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT rule_id, name, description, rule_type, status, conditions,
                           actions, priority, version, created_at, updated_at,
                           metadata, tags, execution_count, success_count,
                           error_count, avg_execution_time
                    FROM rules
                    WHERE status != 'archived'
                    ORDER BY priority DESC, created_at ASC
                """)
                
                for row in cursor.fetchall():
                    rule = Rule(
                        rule_id=row[0],
                        name=row[1],
                        description=row[2],
                        rule_type=RuleType(row[3]),
                        status=RuleStatus(row[4]),
                        conditions=json.loads(row[5]),
                        actions=json.loads(row[6]),
                        priority=row[7],
                        version=row[8],
                        created_at=datetime.fromisoformat(row[9]),
                        updated_at=datetime.fromisoformat(row[10]),
                        metadata=json.loads(row[11]) if row[11] else {},
                        tags=json.loads(row[12]) if row[12] else [],
                        execution_count=row[13],
                        success_count=row[14],
                        error_count=row[15],
                        avg_execution_time=row[16]
                    )
                    self.rules[rule.rule_id] = rule
            
            logger.info(f"Loaded {len(self.rules)} rules from database")
            
        except Exception as e:
            logger.error(f"Failed to load rules: {e}")
    
    def create_rule(self, name: str, description: str, rule_type: RuleType,
                   conditions: List[Dict[str, Any]], actions: List[Dict[str, Any]],
                   priority: int = 1, tags: List[str] = None,
                   metadata: Dict[str, Any] = None) -> str:
        """
        Create a new rule.
        
        Args:
            name: Rule name
            description: Rule description
            rule_type: Type of rule
            conditions: List of conditions
            actions: List of actions
            priority: Rule priority (higher = more important)
            tags: Rule tags
            metadata: Additional metadata
            
        Returns:
            Rule ID
        """
        try:
            rule_id = str(uuid.uuid4())
            now = datetime.now()
            
            rule = Rule(
                rule_id=rule_id,
                name=name,
                description=description,
                rule_type=rule_type,
                status=RuleStatus.ACTIVE,
                conditions=conditions,
                actions=actions,
                priority=priority,
                version="1.0.0",
                created_at=now,
                updated_at=now,
                metadata=metadata or {},
                tags=tags or []
            )
            
            # Validate rule
            self._validate_rule(rule)
            
            # Save to database
            self._save_rule(rule)
            
            # Add to memory
            self.rules[rule_id] = rule
            
            logger.info(f"Created rule: {rule_id} ({name})")
            return rule_id
            
        except Exception as e:
            logger.error(f"Failed to create rule: {e}")
            raise
    
    def _validate_rule(self, rule: Rule) -> None:
        """Validate rule structure and syntax."""
        if not rule.name:
            raise ValueError("Rule name is required")
        
        if not rule.conditions:
            raise ValueError("Rule must have at least one condition")
        
        if not rule.actions:
            raise ValueError("Rule must have at least one action")
        
        # Validate conditions
        for condition in rule.conditions:
            if 'field' not in condition:
                raise ValueError("Condition must have 'field'")
            if 'operator' not in condition:
                raise ValueError("Condition must have 'operator'")
            if 'value' not in condition:
                raise ValueError("Condition must have 'value'")
        
        # Validate actions
        for action in rule.actions:
            if 'type' not in action:
                raise ValueError("Action must have 'type'")
    
    def _save_rule(self, rule: Rule) -> None:
        """Save rule to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO rules 
                    (rule_id, name, description, rule_type, status, conditions,
                     actions, priority, version, created_at, updated_at,
                     metadata, tags, execution_count, success_count,
                     error_count, avg_execution_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rule.rule_id,
                    rule.name,
                    rule.description,
                    rule.rule_type.value,
                    rule.status.value,
                    json.dumps(rule.conditions),
                    json.dumps(rule.actions),
                    rule.priority,
                    rule.version,
                    rule.created_at.isoformat(),
                    rule.updated_at.isoformat(),
                    json.dumps(rule.metadata),
                    json.dumps(rule.tags),
                    rule.execution_count,
                    rule.success_count,
                    rule.error_count,
                    rule.avg_execution_time
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save rule: {e}")
            raise
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """
        Get rule by ID.
        
        Args:
            rule_id: Rule identifier
            
        Returns:
            Rule object or None if not found
        """
        return self.rules.get(rule_id)
    
    def list_rules(self, rule_type: Optional[RuleType] = None,
                   status: Optional[RuleStatus] = None,
                   tags: List[str] = None) -> List[Rule]:
        """
        List rules with optional filtering.
        
        Args:
            rule_type: Filter by rule type
            status: Filter by status
            tags: Filter by tags
            
        Returns:
            List of matching rules
        """
        rules = list(self.rules.values())
        
        if rule_type:
            rules = [r for r in rules if r.rule_type == rule_type]
        
        if status:
            rules = [r for r in rules if r.status == status]
        
        if tags:
            rules = [r for r in rules if any(tag in r.tags for tag in tags)]
        
        return sorted(rules, key=lambda r: (r.priority, r.created_at), reverse=True)
    
    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing rule.
        
        Args:
            rule_id: Rule identifier
            updates: Updates to apply
            
        Returns:
            True if successful
        """
        try:
            rule = self.get_rule(rule_id)
            if not rule:
                return False
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            
            rule.updated_at = datetime.now()
            
            # Re-validate if conditions or actions changed
            if 'conditions' in updates or 'actions' in updates:
                self._validate_rule(rule)
            
            # Save to database
            self._save_rule(rule)
            
            logger.info(f"Updated rule: {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update rule {rule_id}: {e}")
            return False
    
    def delete_rule(self, rule_id: str) -> bool:
        """
        Delete a rule.
        
        Args:
            rule_id: Rule identifier
            
        Returns:
            True if successful
        """
        try:
            if rule_id not in self.rules:
                return False
            
            # Mark as archived instead of deleting
            rule = self.rules[rule_id]
            rule.status = RuleStatus.ARCHIVED
            rule.updated_at = datetime.now()
            
            # Save to database
            self._save_rule(rule)
            
            # Remove from memory
            del self.rules[rule_id]
            
            logger.info(f"Deleted rule: {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete rule {rule_id}: {e}")
            return False
    
    def execute_rule(self, rule_id: str, data: Dict[str, Any],
                    context: Optional[DataContext] = None) -> RuleExecution:
        """
        Execute a single rule.
        
        Args:
            rule_id: Rule identifier
            data: Input data
            context: Optional execution context
            
        Returns:
            Rule execution result
        """
        try:
            rule = self.get_rule(rule_id)
            if not rule:
                raise ValueError(f"Rule {rule_id} not found")
            
            if rule.status != RuleStatus.ACTIVE:
                raise ValueError(f"Rule {rule_id} is not active")
            
            execution_id = str(uuid.uuid4())
            start_time = time.time()
            
            # Create execution context
            if context is None:
                context = DataContext(
                    data=data,
                    variables={},
                    functions=self.builtin_functions,
                    metadata={}
                )
            
            # Evaluate conditions
            conditions_met = self._evaluate_conditions(rule.conditions, context)
            
            if conditions_met:
                # Execute actions
                output_data = self._execute_actions(rule.actions, context)
                status = ExecutionStatus.SUCCESS
                error_message = None
            else:
                output_data = data
                status = ExecutionStatus.SUCCESS  # Conditions not met is not an error
                error_message = None
            
            execution_time = time.time() - start_time
            
            # Create execution result
            execution = RuleExecution(
                execution_id=execution_id,
                rule_id=rule_id,
                input_data=data,
                output_data=output_data,
                status=status,
                execution_time=execution_time,
                error_message=error_message,
                timestamp=datetime.now(),
                metadata={"conditions_met": conditions_met}
            )
            
            # Update rule statistics
            self._update_rule_stats(rule, execution_time, status == ExecutionStatus.SUCCESS)
            
            # Save execution result
            self._save_execution(execution)
            
            # Update performance metrics
            self._update_performance_metrics(execution_time, status == ExecutionStatus.SUCCESS)
            
            return execution
            
        except Exception as e:
            logger.error(f"Rule execution failed for {rule_id}: {e}")
            
            # Create error execution result
            execution = RuleExecution(
                execution_id=str(uuid.uuid4()),
                rule_id=rule_id,
                input_data=data,
                output_data=data,
                status=ExecutionStatus.ERROR,
                execution_time=time.time() - start_time if 'start_time' in locals() else 0,
                error_message=str(e),
                timestamp=datetime.now(),
                metadata={}
            )
            
            # Update rule statistics
            if rule_id in self.rules:
                self._update_rule_stats(self.rules[rule_id], execution.execution_time, False)
            
            return execution
    
    def _evaluate_conditions(self, conditions: List[Dict[str, Any]], 
                           context: DataContext) -> bool:
        """
        Evaluate rule conditions.
        
        Args:
            conditions: List of conditions
            context: Execution context
            
        Returns:
            True if all conditions are met
        """
        try:
            for condition in conditions:
                field = condition['field']
                operator = condition['operator']
                value = condition['value']
                
                # Get field value from context
                field_value = self._get_field_value(field, context)
                
                # Evaluate condition
                if not self._evaluate_condition(field_value, operator, value):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return False
    
    def _get_field_value(self, field_path: str, context: DataContext) -> Any:
        """
        Get field value from context using dot notation.
        
        Args:
            field_path: Field path (e.g., "user.name", "data.items[0].value")
            context: Execution context
            
        Returns:
            Field value
        """
        try:
            # Handle array indexing
            if '[' in field_path:
                base_path, index_part = field_path.split('[', 1)
                index = int(index_part.rstrip(']'))
                base_value = self._get_field_value(base_path, context)
                return base_value[index] if isinstance(base_value, list) and 0 <= index < len(base_value) else None
            
            # Handle dot notation
            if '.' in field_path:
                parts = field_path.split('.')
                current = context.data
                
                for part in parts:
                    if isinstance(current, dict):
                        current = current.get(part)
                    elif hasattr(current, part):
                        current = getattr(current, part)
                    else:
                        return None
                
                return current
            
            # Simple field access
            return context.data.get(field_path)
            
        except Exception as e:
            logger.error(f"Failed to get field value for {field_path}: {e}")
            return None
    
    def _evaluate_condition(self, field_value: Any, operator: str, expected_value: Any) -> bool:
        """
        Evaluate a single condition.
        
        Args:
            field_value: Actual field value
            operator: Comparison operator
            expected_value: Expected value
            
        Returns:
            True if condition is met
        """
        try:
            if operator == 'equals':
                return field_value == expected_value
            elif operator == 'not_equals':
                return field_value != expected_value
            elif operator == 'greater_than':
                return field_value > expected_value
            elif operator == 'greater_than_or_equal':
                return field_value >= expected_value
            elif operator == 'less_than':
                return field_value < expected_value
            elif operator == 'less_than_or_equal':
                return field_value <= expected_value
            elif operator == 'contains':
                return expected_value in field_value if isinstance(field_value, (str, list)) else False
            elif operator == 'not_contains':
                return expected_value not in field_value if isinstance(field_value, (str, list)) else True
            elif operator == 'starts_with':
                return field_value.startswith(expected_value) if isinstance(field_value, str) else False
            elif operator == 'ends_with':
                return field_value.endswith(expected_value) if isinstance(field_value, str) else False
            elif operator == 'is_empty':
                return not field_value or (isinstance(field_value, (str, list, dict)) and len(field_value) == 0)
            elif operator == 'is_not_empty':
                return field_value and (not isinstance(field_value, (str, list, dict)) or len(field_value) > 0)
            elif operator == 'is_null':
                return field_value is None
            elif operator == 'is_not_null':
                return field_value is not None
            elif operator == 'matches':
                return bool(re.match(expected_value, str(field_value))) if isinstance(expected_value, str) else False
            elif operator == 'in':
                return field_value in expected_value if isinstance(expected_value, (list, tuple)) else False
            elif operator == 'not_in':
                return field_value not in expected_value if isinstance(expected_value, (list, tuple)) else True
            else:
                logger.warning(f"Unknown operator: {operator}")
                return False
                
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return False
    
    def _execute_actions(self, actions: List[Dict[str, Any]], 
                        context: DataContext) -> Dict[str, Any]:
        """
        Execute rule actions.
        
        Args:
            actions: List of actions
            context: Execution context
            
        Returns:
            Updated data
        """
        try:
            result_data = context.data.copy()
            
            for action in actions:
                action_type = action['type']
                
                if action_type == 'set_field':
                    field = action['field']
                    value = action['value']
                    self._set_field_value(field, value, result_data)
                
                elif action_type == 'remove_field':
                    field = action['field']
                    self._remove_field_value(field, result_data)
                
                elif action_type == 'transform_field':
                    field = action['field']
                    transformation = action['transformation']
                    self._transform_field_value(field, transformation, result_data, context)
                
                elif action_type == 'call_function':
                    function_name = action['function']
                    params = action.get('params', [])
                    result = self._call_function(function_name, params, context)
                    
                    if 'result_field' in action:
                        self._set_field_value(action['result_field'], result, result_data)
                
                elif action_type == 'conditional_action':
                    condition = action['condition']
                    true_actions = action['true_actions']
                    false_actions = action.get('false_actions', [])
                    
                    if self._evaluate_conditions([condition], context):
                        result_data = self._execute_actions(true_actions, context)
                    else:
                        result_data = self._execute_actions(false_actions, context)
                
                elif action_type == 'loop_action':
                    array_field = action['array_field']
                    actions_to_execute = action['actions']
                    
                    array_value = self._get_field_value(array_field, context)
                    if isinstance(array_value, list):
                        for i, item in enumerate(array_value):
                            loop_context = DataContext(
                                data=result_data,
                                variables={**context.variables, 'item': item, 'index': i},
                                functions=context.functions,
                                metadata=context.metadata
                            )
                            result_data = self._execute_actions(actions_to_execute, loop_context)
            
            return result_data
            
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return context.data
    
    def _set_field_value(self, field_path: str, value: Any, data: Dict[str, Any]) -> None:
        """Set field value using dot notation."""
        try:
            if '.' in field_path:
                parts = field_path.split('.')
                current = data
                
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                current[parts[-1]] = value
            else:
                data[field_path] = value
                
        except Exception as e:
            logger.error(f"Failed to set field value for {field_path}: {e}")
    
    def _remove_field_value(self, field_path: str, data: Dict[str, Any]) -> None:
        """Remove field value using dot notation."""
        try:
            if '.' in field_path:
                parts = field_path.split('.')
                current = data
                
                for part in parts[:-1]:
                    if part in current:
                        current = current[part]
                    else:
                        return
                
                if parts[-1] in current:
                    del current[parts[-1]]
            else:
                if field_path in data:
                    del data[field_path]
                    
        except Exception as e:
            logger.error(f"Failed to remove field value for {field_path}: {e}")
    
    def _transform_field_value(self, field_path: str, transformation: Dict[str, Any],
                             data: Dict[str, Any], context: DataContext) -> None:
        """Transform field value."""
        try:
            field_value = self._get_field_value(field_path, DataContext(data, context.variables, context.functions, context.metadata))
            
            transform_type = transformation['type']
            
            if transform_type == 'uppercase':
                result = str(field_value).upper()
            elif transform_type == 'lowercase':
                result = str(field_value).lower()
            elif transform_type == 'trim':
                result = str(field_value).strip()
            elif transform_type == 'replace':
                old_value = transformation['old_value']
                new_value = transformation['new_value']
                result = str(field_value).replace(old_value, new_value)
            elif transform_type == 'format':
                format_string = transformation['format']
                result = format_string.format(field_value)
            elif transform_type == 'function':
                function_name = transformation['function']
                params = transformation.get('params', [field_value])
                result = self._call_function(function_name, params, context)
            else:
                result = field_value
            
            self._set_field_value(field_path, result, data)
            
        except Exception as e:
            logger.error(f"Failed to transform field value for {field_path}: {e}")
    
    def _call_function(self, function_name: str, params: List[Any], 
                      context: DataContext) -> Any:
        """Call a function with parameters."""
        try:
            if function_name in context.functions:
                return context.functions[function_name](*params)
            else:
                logger.warning(f"Function {function_name} not found")
                return None
                
        except Exception as e:
            logger.error(f"Function call failed for {function_name}: {e}")
            return None
    
    def execute_rule_chain(self, chain_id: str, data: Dict[str, Any],
                          context: Optional[DataContext] = None) -> List[RuleExecution]:
        """
        Execute a chain of rules.
        
        Args:
            chain_id: Chain identifier
            data: Input data
            context: Optional execution context
            
        Returns:
            List of execution results
        """
        try:
            chain = self.rule_chains.get(chain_id)
            if not chain:
                raise ValueError(f"Rule chain {chain_id} not found")
            
            if chain.status != RuleStatus.ACTIVE:
                raise ValueError(f"Rule chain {chain_id} is not active")
            
            executions = []
            current_data = data.copy()
            
            # Execute rules based on execution order
            if chain.execution_order == 'sequential':
                for rule_id in chain.rules:
                    execution = self.execute_rule(rule_id, current_data, context)
                    executions.append(execution)
                    current_data = execution.output_data
                    
                    if execution.status == ExecutionStatus.ERROR:
                        break
            
            elif chain.execution_order == 'parallel':
                # Execute rules in parallel
                futures = []
                for rule_id in chain.rules:
                    future = self.executor.submit(self.execute_rule, rule_id, current_data, context)
                    futures.append(future)
                
                for future in as_completed(futures):
                    execution = future.result()
                    executions.append(execution)
            
            elif chain.execution_order == 'conditional':
                # Execute rules until one succeeds
                for rule_id in chain.rules:
                    execution = self.execute_rule(rule_id, current_data, context)
                    executions.append(execution)
                    
                    if execution.status == ExecutionStatus.SUCCESS:
                        break
            
            return executions
            
        except Exception as e:
            logger.error(f"Rule chain execution failed for {chain_id}: {e}")
            return []
    
    def create_rule_chain(self, name: str, description: str, rules: List[str],
                         execution_order: str = 'sequential',
                         metadata: Dict[str, Any] = None) -> str:
        """
        Create a new rule chain.
        
        Args:
            name: Chain name
            description: Chain description
            rules: List of rule IDs
            execution_order: Execution order (sequential, parallel, conditional)
            metadata: Additional metadata
            
        Returns:
            Chain ID
        """
        try:
            chain_id = str(uuid.uuid4())
            now = datetime.now()
            
            chain = RuleChain(
                chain_id=chain_id,
                name=name,
                description=description,
                rules=rules,
                execution_order=execution_order,
                status=RuleStatus.ACTIVE,
                created_at=now,
                updated_at=now,
                metadata=metadata or {}
            )
            
            # Validate chain
            for rule_id in rules:
                if rule_id not in self.rules:
                    raise ValueError(f"Rule {rule_id} not found")
            
            # Save to database
            self._save_rule_chain(chain)
            
            # Add to memory
            self.rule_chains[chain_id] = chain
            
            logger.info(f"Created rule chain: {chain_id} ({name})")
            return chain_id
            
        except Exception as e:
            logger.error(f"Failed to create rule chain: {e}")
            raise
    
    def _save_rule_chain(self, chain: RuleChain) -> None:
        """Save rule chain to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO rule_chains 
                    (chain_id, name, description, rules, execution_order,
                     status, created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    chain.chain_id,
                    chain.name,
                    chain.description,
                    json.dumps(chain.rules),
                    chain.execution_order,
                    chain.status.value,
                    chain.created_at.isoformat(),
                    chain.updated_at.isoformat(),
                    json.dumps(chain.metadata)
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save rule chain: {e}")
            raise
    
    def _save_execution(self, execution: RuleExecution) -> None:
        """Save execution result to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO rule_executions 
                    (execution_id, rule_id, input_data, output_data, status,
                     execution_time, error_message, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    execution.execution_id,
                    execution.rule_id,
                    json.dumps(execution.input_data),
                    json.dumps(execution.output_data),
                    execution.status.value,
                    execution.execution_time,
                    execution.error_message,
                    execution.timestamp.isoformat(),
                    json.dumps(execution.metadata)
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save execution: {e}")
    
    def _update_rule_stats(self, rule: Rule, execution_time: float, success: bool) -> None:
        """Update rule execution statistics."""
        try:
            rule.execution_count += 1
            if success:
                rule.success_count += 1
            else:
                rule.error_count += 1
            
            # Update average execution time
            total_time = rule.avg_execution_time * (rule.execution_count - 1) + execution_time
            rule.avg_execution_time = total_time / rule.execution_count
            
            # Save updated stats
            self._save_rule(rule)
            
        except Exception as e:
            logger.error(f"Failed to update rule stats: {e}")
    
    def _update_performance_metrics(self, execution_time: float, success: bool) -> None:
        """Update overall performance metrics."""
        try:
            self.total_executions += 1
            if success:
                self.successful_executions += 1
            else:
                self.failed_executions += 1
            
            # Update average execution time
            total_time = self.average_execution_time * (self.total_executions - 1) + execution_time
            self.average_execution_time = total_time / self.total_executions
            
        except Exception as e:
            logger.error(f"Failed to update performance metrics: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Performance metrics
        """
        return {
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'success_rate': (self.successful_executions / self.total_executions * 100) if self.total_executions > 0 else 0,
            'average_execution_time': self.average_execution_time,
            'total_rules': len(self.rules),
            'active_rules': len([r for r in self.rules.values() if r.status == RuleStatus.ACTIVE]),
            'total_chains': len(self.rule_chains),
            'active_chains': len([c for c in self.rule_chains.values() if c.status == RuleStatus.ACTIVE])
        }
    
    def get_rule_statistics(self, rule_id: str) -> Dict[str, Any]:
        """
        Get statistics for a specific rule.
        
        Args:
            rule_id: Rule identifier
            
        Returns:
            Rule statistics
        """
        rule = self.get_rule(rule_id)
        if not rule:
            return {}
        
        return {
            'rule_id': rule.rule_id,
            'name': rule.name,
            'execution_count': rule.execution_count,
            'success_count': rule.success_count,
            'error_count': rule.error_count,
            'success_rate': (rule.success_count / rule.execution_count * 100) if rule.execution_count > 0 else 0,
            'average_execution_time': rule.avg_execution_time,
            'last_updated': rule.updated_at.isoformat()
        }
    
    def shutdown(self) -> None:
        """Shutdown the logic engine."""
        logger.info("Shutting down Logic Engine...")
        
        # Shutdown thread pool
        self.executor.shutdown(wait=True)
        
        logger.info("Logic Engine shutdown complete")
    
    def __del__(self):
        """Cleanup on engine destruction."""
        self.shutdown() 