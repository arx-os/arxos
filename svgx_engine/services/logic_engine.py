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
from datetime import datetime, timedelta, date
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
from functools import lru_cache, reduce
import base64
import urllib.parse
import random
import logging

logger = logging.getLogger(__name__)


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
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def _init_builtin_functions(self) -> None:
        """Initialize built-in functions for rule evaluation."""
        self.builtin_functions = {
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'sum': sum,
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
            'upper': lambda x: str(x).upper() if x else '',
            'lower': lambda x: str(x).lower() if x else '',
            'strip': lambda x: str(x).strip() if x else '',
            'split': lambda x, sep=',': str(x).split(sep) if x else [],
            'join': lambda arr, sep=',': sep.join(str(x) for x in arr) if arr else '',
            'contains': lambda text, substr: substr in str(text) if text else False,
            'starts_with': lambda text, prefix: str(text).startswith(prefix) if text else False,
            'ends_with': lambda text, suffix: str(text).endswith(suffix) if text else False,
            'replace': lambda text, old, new: str(text).replace(old, new) if text else '',
            'substring': lambda text, start, end=None: str(text)[start:end] if text else '',
            'is_empty': lambda x: not x or (isinstance(x, str) and not x.strip()),
            'is_not_empty': lambda x: bool(x and (not isinstance(x, str) or x.strip())),
            'is_null': lambda x: x is None,
            'is_not_null': lambda x: x is not None,
            'is_number': lambda x: isinstance(x, (int, float)) and not isinstance(x, bool),
            'is_string': lambda x: isinstance(x, str),
            'is_boolean': lambda x: isinstance(x, bool),
            'is_array': lambda x: isinstance(x, (list, tuple)),
            'is_object': lambda x: isinstance(x, dict),
            'array_length': lambda x: len(x) if isinstance(x, (list, tuple)) else 0,
            'object_keys': lambda x: list(x.keys()) if isinstance(x, dict) else [],
            'object_values': lambda x: list(x.values()) if isinstance(x, dict) else [],
            'has_key': lambda obj, key: key in obj if isinstance(obj, dict) else False,
            'get_value': lambda obj, key, default=None: obj.get(key, default) if isinstance(obj, dict) else default,
            'set_value': lambda obj, key, value: obj.update({key: value}) if isinstance(obj, dict) else None,
            'remove_key': lambda obj, key: obj.pop(key, None) if isinstance(obj, dict) else None,
            'merge_objects': lambda *objs: {k: v for obj in objs if isinstance(obj, dict) for k, v in obj.items()},
            'filter_array': lambda arr, condition: [x for x in arr if condition(x)] if isinstance(arr, (list, tuple)) else [],
            'map_array': lambda arr, func: [func(x) for x in arr] if isinstance(arr, (list, tuple)) else [],
            'reduce_array': lambda arr, func, initial=None: (lambda f, xs, acc: f(f, xs, acc) if xs else acc)(lambda f, xs, acc: f(f, xs[1:], func(acc, xs[0])), arr, initial) if isinstance(arr, (list, tuple)) else initial,
            'sort_array': lambda arr, key=None, reverse=False: sorted(arr, key=key, reverse=reverse) if isinstance(arr, (list, tuple)) else [],
            'unique_array': lambda arr: list(dict.fromkeys(arr)) if isinstance(arr, (list, tuple)) else [],
            'array_contains': lambda arr, item: item in arr if isinstance(arr, (list, tuple)) else False,
            'array_index': lambda arr, item: arr.index(item) if isinstance(arr, (list, tuple)) and item in arr else -1,
            'array_slice': lambda arr, start, end=None: arr[start:end] if isinstance(arr, (list, tuple)) else [],
            'array_push': lambda arr, *items: arr.extend(items) if isinstance(arr, list) else None,
            'array_pop': lambda arr: arr.pop() if isinstance(arr, list) and arr else None,
            'array_shift': lambda arr: arr.pop(0) if isinstance(arr, list) and arr else None,
            'array_unshift': lambda arr, *items: (arr.insert(0, item) for item in reversed(items)) if isinstance(arr, list) else None,
            'math_add': lambda x, y: float(x) + float(y) if x is not None and y is not None else None,
            'math_subtract': lambda x, y: float(x) - float(y) if x is not None and y is not None else None,
            'math_multiply': lambda x, y: float(x) * float(y) if x is not None and y is not None else None,
            'math_divide': lambda x, y: float(x) / float(y) if x is not None and y is not None and float(y) != 0 else None,
            'math_modulo': lambda x, y: float(x) % float(y) if x is not None and y is not None and float(y) != 0 else None,
            'math_power': lambda x, y: float(x) ** float(y) if x is not None and y is not None else None,
            'math_sqrt': lambda x: float(x) ** 0.5 if x is not None and float(x) >= 0 else None,
            'math_floor': lambda x: int(float(x)) if x is not None else None,
            'math_ceil': lambda x: int(float(x) + 0.5) if x is not None else None,
            'math_round': lambda x, decimals=0: round(float(x), decimals) if x is not None else None,
            'string_concat': lambda *args: ''.join(str(arg) for arg in args),
            'string_format': lambda template, *args: template.format(*args),
            'string_pad_left': lambda text, length, char=' ': str(text).rjust(length, char),
            'string_pad_right': lambda text, length, char=' ': str(text).ljust(length, char),
            'string_trim': lambda text: str(text).strip() if text else '',
            'string_trim_left': lambda text: str(text).lstrip() if text else '',
            'string_trim_right': lambda text: str(text).rstrip() if text else '',
            'string_reverse': lambda text: str(text)[::-1] if text else '',
            'string_repeat': lambda text, count: str(text) * count if text and count > 0 else '',
            'date_now': lambda: datetime.now().isoformat(),
            'date_format': lambda date, format_str: date.strftime(format_str) if hasattr(date, 'strftime') else str(date),
            'date_parse': lambda date_str, format_str: datetime.strptime(date_str, format_str),
            'date_add_days': lambda date, days: date + timedelta(days=days) if hasattr(date, '__add__') else date,
            'date_subtract_days': lambda date, days: date - timedelta(days=days) if hasattr(date, '__sub__') else date,
            'date_diff_days': lambda date1, date2: (date1 - date2).days if hasattr(date1, '__sub__') else 0,
            'uuid_generate': lambda: str(uuid.uuid4()),
            'hash_md5': lambda text: hashlib.md5(str(text).encode()).hexdigest(),
            'hash_sha1': lambda text: hashlib.sha1(str(text).encode()).hexdigest(),
            'hash_sha256': lambda text: hashlib.sha256(str(text).encode()).hexdigest(),
            'json_stringify': lambda obj: json.dumps(obj),
            'json_parse': lambda text: json.loads(text),
            'base64_encode': lambda text: base64.b64encode(str(text).encode()).decode(),
            'base64_decode': lambda text: base64.b64decode(text.encode()).decode(),
            'url_encode': lambda text: urllib.parse.quote(str(text)),
            'url_decode': lambda text: urllib.parse.unquote(text),
            'regex_match': lambda pattern, text: bool(re.search(pattern, str(text))),
            'regex_replace': lambda pattern, replacement, text: re.sub(pattern, replacement, str(text)),
            'regex_extract': lambda pattern, text: re.findall(pattern, str(text)),
            'type_of': lambda value: type(value).__name__,
            'is_type': lambda value, type_name: type(value).__name__ == type_name,
            'coalesce': lambda *args: next((arg for arg in args if arg is not None), None),
            'if_then_else': lambda condition, then_value, else_value: then_value if condition else else_value,
            'switch_case': lambda value, *cases: next((case[1] for case in cases[::2] if case[0] == value), cases[-1] if len(cases) % 2 == 1 else None),
            'range': lambda start, end, step=1: list(range(start, end + 1, step)),
            'random_int': lambda min_val, max_val: random.randint(min_val, max_val),
            'random_float': lambda min_val, max_val: random.uniform(min_val, max_val),
            'random_choice': lambda arr: random.choice(arr) if arr else None,
            'random_shuffle': lambda arr: random.shuffle(arr) if isinstance(arr, list) else arr,
            'log_info': lambda message: logger.info(message),
            'log_warning': lambda message: logger.warning(message),
            'log_error': lambda message: logger.error(message),
            'log_debug': lambda message: logger.debug(message),
        }
    
    def _load_rules(self) -> None:
        """Load rules from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM rules WHERE status != 'archived'")
                rows = cursor.fetchall()
                
                for row in rows:
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
            priority: Rule priority
            tags: Rule tags
            metadata: Rule metadata
            
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
            
            self._validate_rule(rule)
            self._save_rule(rule)
            
            with self.lock:
                self.rules[rule_id] = rule
            
            logger.info(f"Created rule: {rule_id}")
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
        
        # Validate conditions structure
        for condition in rule.conditions:
            if not isinstance(condition, dict):
                raise ValueError("Condition must be a dictionary")
            
            required_fields = ['field', 'operator', 'value']
            for field in required_fields:
                if field not in condition:
                    raise ValueError(f"Condition missing required field: {field}")
        
        # Validate actions structure
        for action in rule.actions:
            if not isinstance(action, dict):
                raise ValueError("Action must be a dictionary")
            
            if 'type' not in action:
                raise ValueError("Action missing required field: type")
    
    def _save_rule(self, rule: Rule) -> None:
        """Save rule to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO rules 
                    (rule_id, name, description, rule_type, status, conditions, actions,
                     priority, version, created_at, updated_at, metadata, tags,
                     execution_count, success_count, error_count, avg_execution_time)
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
        """Get rule by ID."""
        try:
            with self.lock:
                return self.rules.get(rule_id)
                
        except Exception as e:
            logger.error(f"Failed to get rule: {e}")
            return None
    
    def list_rules(self, rule_type: Optional[RuleType] = None,
                   status: Optional[RuleStatus] = None,
                   tags: List[str] = None) -> List[Rule]:
        """List rules with optional filtering."""
        try:
            with self.lock:
                rules = list(self.rules.values())
                
                if rule_type:
                    rules = [r for r in rules if r.rule_type == rule_type]
                
                if status:
                    rules = [r for r in rules if r.status == status]
                
                if tags:
                    rules = [r for r in rules if any(tag in r.tags for tag in tags)]
                
                return sorted(rules, key=lambda r: r.priority, reverse=True)
                
        except Exception as e:
            logger.error(f"Failed to list rules: {e}")
            return []
    
    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update rule."""
        try:
            with self.lock:
                if rule_id not in self.rules:
                    return False
                
                rule = self.rules[rule_id]
                
                # Update fields
                for field, value in updates.items():
                    if hasattr(rule, field):
                        setattr(rule, field, value)
                
                rule.updated_at = datetime.now()
                
                # Revalidate and save
                self._validate_rule(rule)
                self._save_rule(rule)
                
                logger.info(f"Updated rule: {rule_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update rule: {e}")
            return False
    
    def delete_rule(self, rule_id: str) -> bool:
        """Delete rule (mark as archived)."""
        try:
            with self.lock:
                if rule_id not in self.rules:
                    return False
                
                rule = self.rules[rule_id]
                rule.status = RuleStatus.ARCHIVED
                rule.updated_at = datetime.now()
                
                self._save_rule(rule)
                del self.rules[rule_id]
                
                logger.info(f"Deleted rule: {rule_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete rule: {e}")
            return False
    
    def execute_rule(self, rule_id: str, data: Dict[str, Any],
                    context: Optional[DataContext] = None) -> RuleExecution:
        """
        Execute a rule with given data.
        
        Args:
            rule_id: Rule ID to execute
            data: Input data
            context: Optional execution context
            
        Returns:
            Rule execution result
        """
        try:
            with self.lock:
                if rule_id not in self.rules:
                    raise ValueError(f"Rule not found: {rule_id}")
                
                rule = self.rules[rule_id]
                if rule.status != RuleStatus.ACTIVE:
                    raise ValueError(f"Rule is not active: {rule_id}")
            
            # Prepare context
            if context is None:
                context = DataContext(
                    data=data,
                    variables={},
                    functions=self.builtin_functions.copy(),
                    metadata={}
                )
            
            # Execute rule
            start_time = time.time()
            
            try:
                # Evaluate conditions
                conditions_met = self._evaluate_conditions(rule.conditions, context)
                
                if conditions_met:
                    # Execute actions
                    output_data = self._execute_actions(rule.actions, context)
                    status = ExecutionStatus.SUCCESS
                    error_message = None
                else:
                    output_data = data
                    status = ExecutionStatus.SUCCESS
                    error_message = None
                
            except Exception as e:
                output_data = data
                status = ExecutionStatus.ERROR
                error_message = str(e)
            
            execution_time = time.time() - start_time
            
            # Create execution result
            execution = RuleExecution(
                execution_id=str(uuid.uuid4()),
                rule_id=rule_id,
                input_data=data,
                output_data=output_data,
                status=status,
                execution_time=execution_time,
                error_message=error_message,
                timestamp=datetime.now(),
                metadata={}
            )
            
            # Save execution and update stats
            self._save_execution(execution)
            self._update_rule_stats(rule, execution_time, status == ExecutionStatus.SUCCESS)
            self._update_performance_metrics(execution_time, status == ExecutionStatus.SUCCESS)
            
            logger.info(f"Executed rule {rule_id}: {status.value}")
            return execution
            
        except Exception as e:
            logger.error(f"Failed to execute rule {rule_id}: {e}")
            raise
    
    def _evaluate_conditions(self, conditions: List[Dict[str, Any]], 
                           context: DataContext) -> bool:
        """Evaluate rule conditions."""
        try:
            for condition in conditions:
                field_path = condition.get('field', '')
                operator = condition.get('operator', '')
                expected_value = condition.get('value')
                
                # Get field value
                field_value = self._get_field_value(field_path, context)
                
                # Evaluate condition
                if not self._evaluate_condition(field_value, operator, expected_value):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to evaluate conditions: {e}")
            return False
    
    def _get_field_value(self, field_path: str, context: DataContext) -> Any:
        """Get field value from context data."""
        try:
            if not field_path:
                return None
            
            # Handle nested field paths (e.g., "user.profile.name")
            parts = field_path.split('.')
            value = context.data
            
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                elif isinstance(value, (list, tuple)) and part.isdigit():
                    index = int(part)
                    if 0 <= index < len(value):
                        value = value[index]
                    else:
                        return None
                else:
                    return None
            
            return value
            
        except Exception as e:
            logger.error(f"Failed to get field value for {field_path}: {e}")
            return None
    
    def _evaluate_condition(self, field_value: Any, operator: str, expected_value: Any) -> bool:
        """Evaluate a single condition."""
        try:
            if operator == 'equals':
                return field_value == expected_value
            elif operator == 'not_equals':
                return field_value != expected_value
            elif operator == 'greater_than':
                return float(field_value) > float(expected_value)
            elif operator == 'greater_than_or_equal':
                return float(field_value) >= float(expected_value)
            elif operator == 'less_than':
                return float(field_value) < float(expected_value)
            elif operator == 'less_than_or_equal':
                return float(field_value) <= float(expected_value)
            elif operator == 'contains':
                return expected_value in str(field_value)
            elif operator == 'not_contains':
                return expected_value not in str(field_value)
            elif operator == 'starts_with':
                return str(field_value).startswith(str(expected_value))
            elif operator == 'ends_with':
                return str(field_value).endswith(str(expected_value))
            elif operator == 'is_empty':
                return not field_value or (isinstance(field_value, str) and not field_value.strip())
            elif operator == 'is_not_empty':
                return field_value and (not isinstance(field_value, str) or field_value.strip())
            elif operator == 'is_null':
                return field_value is None
            elif operator == 'is_not_null':
                return field_value is not None
            elif operator == 'in':
                return field_value in expected_value if isinstance(expected_value, (list, tuple)) else False
            elif operator == 'not_in':
                return field_value not in expected_value if isinstance(expected_value, (list, tuple)) else True
            elif operator == 'regex_match':
                return bool(re.search(str(expected_value), str(field_value)))
            elif operator == 'regex_not_match':
                return not bool(re.search(str(expected_value), str(field_value)))
            else:
                logger.warning(f"Unknown operator: {operator}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to evaluate condition: {e}")
            return False
    
    def _execute_actions(self, actions: List[Dict[str, Any]], 
                        context: DataContext) -> Dict[str, Any]:
        """Execute rule actions."""
        try:
            result_data = context.data.copy()
            
            for action in actions:
                action_type = action.get('type', '')
                
                if action_type == 'set_field':
                    field_path = action.get('field', '')
                    value = action.get('value')
                    self._set_field_value(field_path, value, result_data)
                    
                elif action_type == 'remove_field':
                    field_path = action.get('field', '')
                    self._remove_field_value(field_path, result_data)
                    
                elif action_type == 'transform_field':
                    field_path = action.get('field', '')
                    transformation = action.get('transformation', {})
                    self._transform_field_value(field_path, transformation, result_data, context)
                    
                elif action_type == 'call_function':
                    function_name = action.get('function', '')
                    params = action.get('parameters', [])
                    result = self._call_function(function_name, params, context)
                    
                    # Store result in specified field
                    if 'result_field' in action:
                        self._set_field_value(action['result_field'], result, result_data)
                    
                elif action_type == 'conditional':
                    condition = action.get('condition', {})
                    then_actions = action.get('then_actions', [])
                    else_actions = action.get('else_actions', [])
                    
                    if self._evaluate_conditions([condition], context):
                        for then_action in then_actions:
                            self._execute_single_action(then_action, result_data, context)
                    else:
                        for else_action in else_actions:
                            self._execute_single_action(else_action, result_data, context)
                            
            return result_data
            
        except Exception as e:
            logger.error(f"Failed to execute actions: {e}")
            raise
    
    def _execute_single_action(self, action: Dict[str, Any], data: Dict[str, Any], context: DataContext) -> None:
        """Execute a single action."""
        action_type = action.get('type', '')
        
        if action_type == 'set_field':
            field_path = action.get('field', '')
            value = action.get('value')
            self._set_field_value(field_path, value, data)
        elif action_type == 'remove_field':
            field_path = action.get('field', '')
            self._remove_field_value(field_path, data)
        elif action_type == 'transform_field':
            field_path = action.get('field', '')
            transformation = action.get('transformation', {})
            self._transform_field_value(field_path, transformation, data, context)
    
    def _set_field_value(self, field_path: str, value: Any, data: Dict[str, Any]) -> None:
        """Set field value in data."""
        try:
            if not field_path:
                return
            
            parts = field_path.split('.')
            current = data
            
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            current[parts[-1]] = value
            
        except Exception as e:
            logger.error(f"Failed to set field value for {field_path}: {e}")
    
    def _remove_field_value(self, field_path: str, data: Dict[str, Any]) -> None:
        """Remove field value from data."""
        try:
            if not field_path:
                return
            
            parts = field_path.split('.')
            current = data
            
            for part in parts[:-1]:
                if part not in current:
                    return
                current = current[part]
            
            if parts[-1] in current:
                del current[parts[-1]]
                
        except Exception as e:
            logger.error(f"Failed to remove field value for {field_path}: {e}")
    
    def _transform_field_value(self, field_path: str, transformation: Dict[str, Any],
                             data: Dict[str, Any], context: DataContext) -> None:
        """Transform field value."""
        try:
            field_value = self._get_field_value(field_path, context)
            
            transform_type = transformation.get('type', '')
            
            if transform_type == 'uppercase':
                new_value = str(field_value).upper()
            elif transform_type == 'lowercase':
                new_value = str(field_value).lower()
            elif transform_type == 'trim':
                new_value = str(field_value).strip()
            elif transform_type == 'replace':
                old = transformation.get('old', '')
                new = transformation.get('new', '')
                new_value = str(field_value).replace(old, new)
            elif transform_type == 'format':
                format_str = transformation.get('format', '{}')
                new_value = format_str.format(field_value)
            elif transform_type == 'function':
                function_name = transformation.get('function', '')
                params = transformation.get('parameters', [field_value])
                new_value = self._call_function(function_name, params, context)
            else:
                new_value = field_value
            
            self._set_field_value(field_path, new_value, data)
            
        except Exception as e:
            logger.error(f"Failed to transform field value for {field_path}: {e}")
    
    def _call_function(self, function_name: str, params: List[Any], 
                      context: DataContext) -> Any:
        """Call a function with parameters."""
        try:
            if function_name in context.functions:
                return context.functions[function_name](*params)
            else:
                logger.warning(f"Function not found: {function_name}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to call function {function_name}: {e}")
            return None
    
    def execute_rule_chain(self, chain_id: str, data: Dict[str, Any],
                          context: Optional[DataContext] = None) -> List[RuleExecution]:
        """
        Execute a chain of rules.
        
        Args:
            chain_id: Chain ID to execute
            data: Input data
            context: Optional execution context
            
        Returns:
            List of rule execution results
        """
        try:
            with self.lock:
                if chain_id not in self.rule_chains:
                    raise ValueError(f"Rule chain not found: {chain_id}")
                
                chain = self.rule_chains[chain_id]
                if chain.status != RuleStatus.ACTIVE:
                    raise ValueError(f"Rule chain is not active: {chain_id}")
            
            executions = []
            current_data = data.copy()
            
            if context is None:
                context = DataContext(
                    data=current_data,
                    variables={},
                    functions=self.builtin_functions.copy(),
                    metadata={}
                )
            
            # Execute rules based on execution order
            if chain.execution_order == 'sequential':
                for rule_id in chain.rules:
                    execution = self.execute_rule(rule_id, current_data, context)
                    executions.append(execution)
                    current_data = execution.output_data
                    context.data = current_data
                    
            elif chain.execution_order == 'parallel':
                # Execute rules in parallel
                with ThreadPoolExecutor(max_workers=len(chain.rules)) as executor:
                    future_to_rule = {
                        executor.submit(self.execute_rule, rule_id, current_data, context): rule_id
                        for rule_id in chain.rules
                    }
                    
                    for future in as_completed(future_to_rule):
                        execution = future.result()
                        executions.append(execution)
                        
            else:
                raise ValueError(f"Unknown execution order: {chain.execution_order}")
            
            logger.info(f"Executed rule chain {chain_id}: {len(executions)} rules")
            return executions
            
        except Exception as e:
            logger.error(f"Failed to execute rule chain {chain_id}: {e}")
            raise
    
    def create_rule_chain(self, name: str, description: str, rules: List[str],
                         execution_order: str = 'sequential',
                         metadata: Dict[str, Any] = None) -> str:
        """
        Create a new rule chain.
        
        Args:
            name: Chain name
            description: Chain description
            rules: List of rule IDs
            execution_order: Execution order ('sequential' or 'parallel')
            metadata: Chain metadata
            
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
            
            self._save_rule_chain(chain)
            
            with self.lock:
                self.rule_chains[chain_id] = chain
            
            logger.info(f"Created rule chain: {chain_id}")
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
                    (chain_id, name, description, rules, execution_order, status,
                     created_at, updated_at, metadata)
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
            if rule.execution_count == 1:
                rule.avg_execution_time = execution_time
            else:
                rule.avg_execution_time = (
                    (rule.avg_execution_time * (rule.execution_count - 1) + execution_time) /
                    rule.execution_count
                )
            
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
            if self.total_executions == 1:
                self.average_execution_time = execution_time
            else:
                self.average_execution_time = (
                    (self.average_execution_time * (self.total_executions - 1) + execution_time) /
                    self.total_executions
                )
                
        except Exception as e:
            logger.error(f"Failed to update performance metrics: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        try:
            return {
                'total_executions': self.total_executions,
                'successful_executions': self.successful_executions,
                'failed_executions': self.failed_executions,
                'success_rate': (self.successful_executions / self.total_executions * 100) if self.total_executions > 0 else 0,
                'average_execution_time': self.average_execution_time,
                'active_rules': len([r for r in self.rules.values() if r.status == RuleStatus.ACTIVE]),
                'total_rules': len(self.rules),
                'active_chains': len([c for c in self.rule_chains.values() if c.status == RuleStatus.ACTIVE]),
                'total_chains': len(self.rule_chains)
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {'error': str(e)}
    
    def get_rule_statistics(self, rule_id: str) -> Dict[str, Any]:
        """Get statistics for a specific rule."""
        try:
            with self.lock:
                if rule_id not in self.rules:
                    return {'error': 'Rule not found'}
                
                rule = self.rules[rule_id]
                
                return {
                    'rule_id': rule.rule_id,
                    'name': rule.name,
                    'execution_count': rule.execution_count,
                    'success_count': rule.success_count,
                    'error_count': rule.error_count,
                    'success_rate': (rule.success_count / rule.execution_count * 100) if rule.execution_count > 0 else 0,
                    'average_execution_time': rule.avg_execution_time,
                    'last_execution': rule.updated_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get rule statistics: {e}")
            return {'error': str(e)}
    
    def shutdown(self) -> None:
        """Shutdown the logic engine."""
        try:
            self.executor.shutdown(wait=True)
            logger.info("Logic Engine shutdown successfully")
            
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
    
    def __del__(self):
        """Cleanup on deletion."""
        self.shutdown() 