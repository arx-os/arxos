"""
Advanced Workflow Domain Entities.

Domain entities for workflow automation including workflow definitions,
execution states, triggers, actions, and conditions with comprehensive
rule-based automation capabilities.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set, Union, Callable
from enum import Enum
import json
import uuid

from domain.value_objects import WorkflowId, UserId, BuildingId, DeviceId
from domain.events import DomainEvent
from domain.exceptions import InvalidWorkflowError, WorkflowExecutionError, BusinessRuleViolationError


class WorkflowStatus(Enum):
    """Workflow execution status."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ARCHIVED = "archived"


class ExecutionStatus(Enum):
    """Workflow execution instance status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TriggerType(Enum):
    """Types of workflow triggers."""
    # Time-based triggers
    SCHEDULE = "schedule"
    INTERVAL = "interval"
    CRON = "cron"
    
    # Event-based triggers
    DEVICE_EVENT = "device_event"
    SENSOR_READING = "sensor_reading"
    THRESHOLD_BREACH = "threshold_breach"
    STATUS_CHANGE = "status_change"
    
    # System triggers
    SYSTEM_EVENT = "system_event"
    API_CALL = "api_call"
    WEBHOOK = "webhook"
    
    # Manual triggers
    MANUAL = "manual"
    BUTTON_PRESS = "button_press"
    
    # Complex triggers
    COMPOSITE = "composite"
    CONDITIONAL = "conditional"


class ActionType(Enum):
    """Types of workflow actions."""
    # Device control
    DEVICE_CONTROL = "device_control"
    DEVICE_SETTING = "device_setting"
    DEVICE_RESTART = "device_restart"
    
    # Notifications
    EMAIL_NOTIFICATION = "email_notification"
    SMS_NOTIFICATION = "sms_notification"
    PUSH_NOTIFICATION = "push_notification"
    SLACK_NOTIFICATION = "slack_notification"
    
    # System actions
    CREATE_ALERT = "create_alert"
    UPDATE_STATUS = "update_status"
    LOG_EVENT = "log_event"
    GENERATE_REPORT = "generate_report"
    
    # Data actions
    STORE_DATA = "store_data"
    UPDATE_DATABASE = "update_database"
    EXPORT_DATA = "export_data"
    
    # External integrations
    HTTP_REQUEST = "http_request"
    API_CALL = "api_call"
    WEBHOOK_CALL = "webhook_call"
    
    # Workflow control
    START_WORKFLOW = "start_workflow"
    STOP_WORKFLOW = "stop_workflow"
    DELAY = "delay"
    CONDITIONAL = "conditional"
    
    # Custom actions
    CUSTOM_SCRIPT = "custom_script"
    LAMBDA_FUNCTION = "lambda_function"


class ConditionOperator(Enum):
    """Conditional operators for workflow logic."""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    REGEX = "regex"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class LogicOperator(Enum):
    """Logic operators for combining conditions."""
    AND = "and"
    OR = "or"
    NOT = "not"


@dataclass
class WorkflowVariable:
    """Workflow variable definition."""
    name: str
    type: str  # string, number, boolean, object, array
    default_value: Any = None
    description: str = ""
    required: bool = False
    
    def validate_value(self, value: Any) -> bool:
        """Validate variable value against type."""
        if value is None and self.required:
            return False
        
        if value is None:
            return True
        
        type_validators = {
            "string": lambda v: isinstance(v, str),
            "number": lambda v: isinstance(v, (int, float)),
            "boolean": lambda v: isinstance(v, bool),
            "object": lambda v: isinstance(v, dict),
            "array": lambda v: isinstance(v, list)
        }
        
        validator = type_validators.get(self.type)
        return validator(value) if validator else True


@dataclass
class WorkflowCondition:
    """Workflow condition for conditional logic."""
    field: str
    operator: ConditionOperator
    value: Any
    logic_operator: LogicOperator = LogicOperator.AND
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate condition against context."""
        field_value = self._get_field_value(context, self.field)
        
        if self.operator == ConditionOperator.EQUALS:
            return field_value == self.value
        elif self.operator == ConditionOperator.NOT_EQUALS:
            return field_value != self.value
        elif self.operator == ConditionOperator.GREATER_THAN:
            return field_value > self.value
        elif self.operator == ConditionOperator.GREATER_THAN_OR_EQUAL:
            return field_value >= self.value
        elif self.operator == ConditionOperator.LESS_THAN:
            return field_value < self.value
        elif self.operator == ConditionOperator.LESS_THAN_OR_EQUAL:
            return field_value <= self.value
        elif self.operator == ConditionOperator.CONTAINS:
            return self.value in str(field_value)
        elif self.operator == ConditionOperator.NOT_CONTAINS:
            return self.value not in str(field_value)
        elif self.operator == ConditionOperator.IN:
            return field_value in self.value
        elif self.operator == ConditionOperator.NOT_IN:
            return field_value not in self.value
        elif self.operator == ConditionOperator.IS_NULL:
            return field_value is None
        elif self.operator == ConditionOperator.IS_NOT_NULL:
            return field_value is not None
        elif self.operator == ConditionOperator.REGEX:
            import re
            return bool(re.match(str(self.value), str(field_value)))
        
        return False
    
    def _get_field_value(self, context: Dict[str, Any], field_path: str) -> Any:
        """Get field value from context using dot notation."""
        keys = field_path.split('.')
        value = context
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value


@dataclass
class WorkflowTrigger:
    """Workflow trigger configuration."""
    id: str
    type: TriggerType
    name: str
    configuration: Dict[str, Any] = field(default_factory=dict)
    conditions: List[WorkflowCondition] = field(default_factory=list)
    enabled: bool = True
    
    def should_trigger(self, event_data: Dict[str, Any]) -> bool:
        """Check if trigger should fire based on event data."""
        if not self.enabled:
            return False
        
        # Check basic trigger type matching
        if not self._matches_trigger_type(event_data):
            return False
        
        # Evaluate conditions
        return self._evaluate_conditions(event_data)
    
    def _matches_trigger_type(self, event_data: Dict[str, Any]) -> bool:
        """Check if event matches trigger type."""
        if self.type == TriggerType.DEVICE_EVENT:
            return event_data.get("event_type") == "device_event"
        elif self.type == TriggerType.SENSOR_READING:
            return event_data.get("event_type") == "sensor_reading"
        elif self.type == TriggerType.THRESHOLD_BREACH:
            return event_data.get("event_type") == "threshold_breach"
        elif self.type == TriggerType.STATUS_CHANGE:
            return event_data.get("event_type") == "status_change"
        elif self.type == TriggerType.WEBHOOK:
            return event_data.get("source") == "webhook"
        elif self.type == TriggerType.MANUAL:
            return event_data.get("trigger_type") == "manual"
        
        return True  # Default to match for other types
    
    def _evaluate_conditions(self, event_data: Dict[str, Any]) -> bool:
        """Evaluate all conditions."""
        if not self.conditions:
            return True
        
        # Group conditions by logic operator
        and_conditions = [c for c in self.conditions if c.logic_operator == LogicOperator.AND]
        or_conditions = [c for c in self.conditions if c.logic_operator == LogicOperator.OR]
        
        # All AND conditions must be true
        and_result = all(condition.evaluate(event_data) for condition in and_conditions) if and_conditions else True
        
        # At least one OR condition must be true
        or_result = any(condition.evaluate(event_data) for condition in or_conditions) if or_conditions else True
        
        return and_result and or_result


@dataclass
class WorkflowAction:
    """Workflow action configuration."""
    id: str
    type: ActionType
    name: str
    configuration: Dict[str, Any] = field(default_factory=dict)
    conditions: List[WorkflowCondition] = field(default_factory=list)
    retry_count: int = 3
    timeout_seconds: int = 300
    enabled: bool = True
    
    def should_execute(self, context: Dict[str, Any]) -> bool:
        """Check if action should execute based on context."""
        if not self.enabled:
            return False
        
        if not self.conditions:
            return True
        
        # Evaluate conditions
        and_conditions = [c for c in self.conditions if c.logic_operator == LogicOperator.AND]
        or_conditions = [c for c in self.conditions if c.logic_operator == LogicOperator.OR]
        
        and_result = all(condition.evaluate(context) for condition in and_conditions) if and_conditions else True
        or_result = any(condition.evaluate(context) for condition in or_conditions) if or_conditions else True
        
        return and_result and or_result
    
    def validate_configuration(self) -> List[str]:
        """Validate action configuration."""
        errors = []
        
        # Type-specific validation
        if self.type == ActionType.EMAIL_NOTIFICATION:
            if not self.configuration.get("to"):
                errors.append("Email notification requires 'to' address")
            if not self.configuration.get("subject"):
                errors.append("Email notification requires 'subject'")
        
        elif self.type == ActionType.DEVICE_CONTROL:
            if not self.configuration.get("device_id"):
                errors.append("Device control requires 'device_id'")
            if not self.configuration.get("command"):
                errors.append("Device control requires 'command'")
        
        elif self.type == ActionType.HTTP_REQUEST:
            if not self.configuration.get("url"):
                errors.append("HTTP request requires 'url'")
            if not self.configuration.get("method"):
                errors.append("HTTP request requires 'method'")
        
        elif self.type == ActionType.DELAY:
            if not self.configuration.get("duration"):
                errors.append("Delay action requires 'duration'")
        
        return errors


# Domain Events
@dataclass
class WorkflowCreated(DomainEvent):
    """Workflow created event."""
    workflow_id: str
    workflow_name: str
    created_by: str
    trigger_types: List[str]


@dataclass
class WorkflowTriggered(DomainEvent):
    """Workflow triggered event."""
    workflow_id: str
    execution_id: str
    trigger_id: str
    trigger_data: Dict[str, Any]


@dataclass
class WorkflowCompleted(DomainEvent):
    """Workflow completed event."""
    workflow_id: str
    execution_id: str
    execution_time_ms: int
    actions_executed: int
    success: bool


@dataclass
class WorkflowActionExecuted(DomainEvent):
    """Workflow action executed event."""
    workflow_id: str
    execution_id: str
    action_id: str
    action_type: str
    success: bool
    execution_time_ms: int
    error_message: Optional[str] = None


class WorkflowExecution:
    """Workflow execution instance."""
    
    def __init__(self, workflow_id: WorkflowId, execution_id: str, triggered_by: Dict[str, Any]):
        self.id = execution_id
        self.workflow_id = workflow_id
        self.triggered_by = triggered_by
        
        # Execution state
        self.status = ExecutionStatus.PENDING
        self.context: Dict[str, Any] = {}
        self.variables: Dict[str, Any] = {}
        
        # Progress tracking
        self.current_action_index = 0
        self.completed_actions: List[str] = []
        self.failed_actions: List[Dict[str, Any]] = []
        
        # Timing
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.execution_time_ms: int = 0
        
        # Results
        self.results: Dict[str, Any] = {}
        self.error_message: Optional[str] = None
        self.retry_count: int = 0
        
        # Domain Events
        self._domain_events: List[DomainEvent] = []
    
    def start_execution(self) -> None:
        """Start workflow execution."""
        self.status = ExecutionStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
    
    def complete_execution(self, success: bool = True, error_message: str = None) -> None:
        """Complete workflow execution."""
        self.status = ExecutionStatus.COMPLETED if success else ExecutionStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.error_message = error_message
        
        if self.started_at:
            self.execution_time_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
        
        # Add domain event
        self._add_domain_event(WorkflowCompleted(
            workflow_id=str(self.workflow_id),
            execution_id=self.id,
            execution_time_ms=self.execution_time_ms,
            actions_executed=len(self.completed_actions),
            success=success
        ))
    
    def record_action_result(self, action_id: str, action_type: str, success: bool, 
                           result: Any = None, error_message: str = None, execution_time_ms: int = 0) -> None:
        """Record result of action execution."""
        if success:
            self.completed_actions.append(action_id)
        else:
            self.failed_actions.append({
                "action_id": action_id,
                "error_message": error_message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        # Store result
        self.results[action_id] = {
            "success": success,
            "result": result,
            "error_message": error_message,
            "execution_time_ms": execution_time_ms
        }
        
        # Add domain event
        self._add_domain_event(WorkflowActionExecuted(
            workflow_id=str(self.workflow_id),
            execution_id=self.id,
            action_id=action_id,
            action_type=action_type,
            success=success,
            execution_time_ms=execution_time_ms,
            error_message=error_message
        ))
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set workflow variable."""
        self.variables[name] = value
        self.context[f"variables.{name}"] = value
    
    def get_variable(self, name: str) -> Any:
        """Get workflow variable."""
        return self.variables.get(name)
    
    def update_context(self, updates: Dict[str, Any]) -> None:
        """Update execution context."""
        self.context.update(updates)
    
    def get_progress_percentage(self, total_actions: int) -> float:
        """Get execution progress percentage."""
        if total_actions == 0:
            return 100.0
        return (len(self.completed_actions) / total_actions) * 100.0
    
    def get_domain_events(self) -> List[DomainEvent]:
        """Get domain events."""
        return self._domain_events.copy()
    
    def clear_domain_events(self) -> None:
        """Clear domain events."""
        self._domain_events.clear()
    
    def _add_domain_event(self, event: DomainEvent) -> None:
        """Add domain event."""
        self._domain_events.append(event)


class Workflow:
    """Advanced workflow entity with comprehensive automation capabilities."""
    
    def __init__(self, workflow_id: WorkflowId, name: str, created_by: UserId):
        # Core Identity
        self.id = workflow_id
        self.name = self._validate_name(name)
        self.created_by = created_by
        
        # Workflow Definition
        self.description: str = ""
        self.version: str = "1.0"
        self.status = WorkflowStatus.DRAFT
        
        # Components
        self.triggers: List[WorkflowTrigger] = []
        self.actions: List[WorkflowAction] = []
        self.variables: List[WorkflowVariable] = []
        
        # Configuration
        self.timeout_seconds: int = 3600  # 1 hour default
        self.max_concurrent_executions: int = 1
        self.retry_policy: Dict[str, Any] = {"max_retries": 3, "backoff_multiplier": 2}
        
        # Metadata
        self.tags: Set[str] = set()
        self.category: str = ""
        self.priority: int = 5  # 1-10 scale
        
        # Access Control
        self.is_public: bool = False
        self.allowed_users: Set[str] = set()
        self.allowed_roles: Set[str] = set()
        
        # Execution Tracking
        self.execution_count: int = 0
        self.success_count: int = 0
        self.failure_count: int = 0
        self.last_executed_at: Optional[datetime] = None
        self.average_execution_time_ms: float = 0
        
        # Lifecycle
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
        self.activated_at: Optional[datetime] = None
        
        # Domain Events
        self._domain_events: List[DomainEvent] = []
        
        # Add creation event
        self._add_domain_event(WorkflowCreated(
            workflow_id=str(self.id),
            workflow_name=self.name,
            created_by=str(self.created_by),
            trigger_types=[]
        ))
    
    def _validate_name(self, name: str) -> str:
        """Validate workflow name."""
        if not name or not name.strip():
            raise InvalidWorkflowError("Workflow name cannot be empty")
        
        name = name.strip()
        if len(name) > 200:
            raise InvalidWorkflowError("Workflow name cannot exceed 200 characters")
        
        return name
    
    def add_trigger(self, trigger_type: TriggerType, name: str, configuration: Dict[str, Any],
                   conditions: List[WorkflowCondition] = None) -> str:
        """Add trigger to workflow."""
        trigger_id = str(uuid.uuid4())
        
        trigger = WorkflowTrigger(
            id=trigger_id,
            type=trigger_type,
            name=name,
            configuration=configuration,
            conditions=conditions or []
        )
        
        self.triggers.append(trigger)
        self.updated_at = datetime.now(timezone.utc)
        
        return trigger_id
    
    def add_action(self, action_type: ActionType, name: str, configuration: Dict[str, Any],
                  conditions: List[WorkflowCondition] = None) -> str:
        """Add action to workflow."""
        action_id = str(uuid.uuid4())
        
        action = WorkflowAction(
            id=action_id,
            type=action_type,
            name=name,
            configuration=configuration,
            conditions=conditions or []
        )
        
        # Validate action configuration
        errors = action.validate_configuration()
        if errors:
            raise InvalidWorkflowError(f"Action configuration errors: {', '.join(errors)}")
        
        self.actions.append(action)
        self.updated_at = datetime.now(timezone.utc)
        
        return action_id
    
    def add_variable(self, name: str, var_type: str, default_value: Any = None,
                    description: str = "", required: bool = False) -> None:
        """Add variable to workflow."""
        if any(var.name == name for var in self.variables):
            raise InvalidWorkflowError(f"Variable '{name}' already exists")
        
        variable = WorkflowVariable(
            name=name,
            type=var_type,
            default_value=default_value,
            description=description,
            required=required
        )
        
        self.variables.append(variable)
        self.updated_at = datetime.now(timezone.utc)
    
    def remove_trigger(self, trigger_id: str) -> None:
        """Remove trigger from workflow."""
        self.triggers = [t for t in self.triggers if t.id != trigger_id]
        self.updated_at = datetime.now(timezone.utc)
    
    def remove_action(self, action_id: str) -> None:
        """Remove action from workflow."""
        self.actions = [a for a in self.actions if a.id != action_id]
        self.updated_at = datetime.now(timezone.utc)
    
    def activate(self) -> None:
        """Activate workflow for execution."""
        if self.status == WorkflowStatus.ACTIVE:
            return
        
        # Validate workflow before activation
        validation_errors = self.validate()
        if validation_errors:
            raise InvalidWorkflowError(f"Cannot activate workflow: {', '.join(validation_errors)}")
        
        self.status = WorkflowStatus.ACTIVE
        self.activated_at = datetime.now(timezone.utc)
        self.updated_at = self.activated_at
    
    def deactivate(self) -> None:
        """Deactivate workflow."""
        self.status = WorkflowStatus.PAUSED
        self.updated_at = datetime.now(timezone.utc)
    
    def disable(self) -> None:
        """Disable workflow permanently."""
        self.status = WorkflowStatus.DISABLED
        self.updated_at = datetime.now(timezone.utc)
    
    def validate(self) -> List[str]:
        """Validate workflow definition."""
        errors = []
        
        # Must have at least one trigger
        if not self.triggers:
            errors.append("Workflow must have at least one trigger")
        
        # Must have at least one action
        if not self.actions:
            errors.append("Workflow must have at least one action")
        
        # Validate triggers
        for trigger in self.triggers:
            if trigger.type == TriggerType.SCHEDULE and not trigger.configuration.get("schedule"):
                errors.append(f"Schedule trigger '{trigger.name}' requires schedule configuration")
        
        # Validate actions
        for action in self.actions:
            action_errors = action.validate_configuration()
            errors.extend([f"Action '{action.name}': {error}" for error in action_errors])
        
        # Validate variables
        for variable in self.variables:
            if not variable.name:
                errors.append("Variable name cannot be empty")
        
        return errors
    
    def should_trigger(self, event_data: Dict[str, Any]) -> List[WorkflowTrigger]:
        """Check which triggers should fire for given event data."""
        if self.status != WorkflowStatus.ACTIVE:
            return []
        
        triggered = []
        for trigger in self.triggers:
            if trigger.should_trigger(event_data):
                triggered.append(trigger)
        
        return triggered
    
    def create_execution(self, trigger_data: Dict[str, Any]) -> WorkflowExecution:
        """Create new execution instance."""
        execution_id = str(uuid.uuid4())
        execution = WorkflowExecution(self.id, execution_id, trigger_data)
        
        # Initialize variables with defaults
        for variable in self.variables:
            if variable.default_value is not None:
                execution.set_variable(variable.name, variable.default_value)
        
        # Set initial context
        execution.update_context({
            "workflow_id": str(self.id),
            "workflow_name": self.name,
            "trigger_data": trigger_data,
            "execution_id": execution_id,
            "started_at": datetime.now(timezone.utc).isoformat()
        })
        
        return execution
    
    def record_execution(self, execution: WorkflowExecution) -> None:
        """Record execution statistics."""
        self.execution_count += 1
        self.last_executed_at = execution.completed_at or datetime.now(timezone.utc)
        
        if execution.status == ExecutionStatus.COMPLETED:
            self.success_count += 1
        elif execution.status == ExecutionStatus.FAILED:
            self.failure_count += 1
        
        # Update average execution time
        if execution.execution_time_ms > 0:
            total_time = (self.average_execution_time_ms * (self.execution_count - 1)) + execution.execution_time_ms
            self.average_execution_time_ms = total_time / self.execution_count
        
        self.updated_at = datetime.now(timezone.utc)
    
    def get_success_rate(self) -> float:
        """Get workflow success rate."""
        if self.execution_count == 0:
            return 0.0
        return (self.success_count / self.execution_count) * 100.0
    
    def get_failure_rate(self) -> float:
        """Get workflow failure rate."""
        if self.execution_count == 0:
            return 0.0
        return (self.failure_count / self.execution_count) * 100.0
    
    def clone(self, new_name: str, new_created_by: UserId) -> 'Workflow':
        """Clone workflow with new name and owner."""
        cloned_workflow = Workflow(
            workflow_id=WorkflowId(),
            name=new_name,
            created_by=new_created_by
        )
        
        # Copy configuration
        cloned_workflow.description = f"Copy of {self.description}"
        cloned_workflow.version = "1.0"
        cloned_workflow.timeout_seconds = self.timeout_seconds
        cloned_workflow.max_concurrent_executions = self.max_concurrent_executions
        cloned_workflow.retry_policy = self.retry_policy.copy()
        cloned_workflow.category = self.category
        cloned_workflow.priority = self.priority
        cloned_workflow.tags = self.tags.copy()
        
        # Copy triggers (with new IDs)
        for trigger in self.triggers:
            cloned_workflow.add_trigger(
                trigger_type=trigger.type,
                name=f"Copy of {trigger.name}",
                configuration=trigger.configuration.copy(),
                conditions=trigger.conditions.copy()
            )
        
        # Copy actions (with new IDs)
        for action in self.actions:
            cloned_workflow.add_action(
                action_type=action.type,
                name=f"Copy of {action.name}",
                configuration=action.configuration.copy(),
                conditions=action.conditions.copy()
            )
        
        # Copy variables
        for variable in self.variables:
            cloned_workflow.add_variable(
                name=variable.name,
                var_type=variable.type,
                default_value=variable.default_value,
                description=variable.description,
                required=variable.required
            )
        
        return cloned_workflow
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary for serialization."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "status": self.status.value,
            "created_by": str(self.created_by),
            "triggers": [
                {
                    "id": t.id,
                    "type": t.type.value,
                    "name": t.name,
                    "configuration": t.configuration,
                    "conditions": [
                        {
                            "field": c.field,
                            "operator": c.operator.value,
                            "value": c.value,
                            "logic_operator": c.logic_operator.value
                        } for c in t.conditions
                    ],
                    "enabled": t.enabled
                } for t in self.triggers
            ],
            "actions": [
                {
                    "id": a.id,
                    "type": a.type.value,
                    "name": a.name,
                    "configuration": a.configuration,
                    "conditions": [
                        {
                            "field": c.field,
                            "operator": c.operator.value,
                            "value": c.value,
                            "logic_operator": c.logic_operator.value
                        } for c in a.conditions
                    ],
                    "retry_count": a.retry_count,
                    "timeout_seconds": a.timeout_seconds,
                    "enabled": a.enabled
                } for a in self.actions
            ],
            "variables": [
                {
                    "name": v.name,
                    "type": v.type,
                    "default_value": v.default_value,
                    "description": v.description,
                    "required": v.required
                } for v in self.variables
            ],
            "configuration": {
                "timeout_seconds": self.timeout_seconds,
                "max_concurrent_executions": self.max_concurrent_executions,
                "retry_policy": self.retry_policy
            },
            "metadata": {
                "tags": list(self.tags),
                "category": self.category,
                "priority": self.priority,
                "is_public": self.is_public
            },
            "statistics": {
                "execution_count": self.execution_count,
                "success_count": self.success_count,
                "failure_count": self.failure_count,
                "success_rate": self.get_success_rate(),
                "average_execution_time_ms": self.average_execution_time_ms
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "last_executed_at": self.last_executed_at.isoformat() if self.last_executed_at else None
        }
    
    def get_domain_events(self) -> List[DomainEvent]:
        """Get domain events."""
        return self._domain_events.copy()
    
    def clear_domain_events(self) -> None:
        """Clear domain events."""
        self._domain_events.clear()
    
    def _add_domain_event(self, event: DomainEvent) -> None:
        """Add domain event."""
        self._domain_events.append(event)
    
    def __str__(self) -> str:
        """String representation."""
        return f"Workflow(id={self.id}, name={self.name}, status={self.status.value})"
    
    def __eq__(self, other) -> bool:
        """Equality based on ID."""
        if not isinstance(other, Workflow):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.id)