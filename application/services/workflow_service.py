"""
Advanced Workflow Application Service.

Orchestrates workflow automation operations including workflow lifecycle management,
execution coordination, rule-based automation, and intelligent trigger processing.
"""

import asyncio
from typing import Dict, Any, List, Optional, Set, Union
from datetime import datetime, timezone, timedelta
from dataclasses import asdict
import json

from application.services.base_service import BaseApplicationService
from application.dto.workflow_dto import (
    CreateWorkflowRequest, CreateWorkflowResponse,
    WorkflowResponse, ListWorkflowsResponse,
    UpdateWorkflowRequest, UpdateWorkflowResponse,
    ExecuteWorkflowRequest, ExecuteWorkflowResponse,
    WorkflowExecutionResponse, TriggerWorkflowRequest,
    WorkflowStatsResponse, CloneWorkflowRequest
)
from domain.entities.workflow_entity import (
    Workflow, WorkflowExecution, WorkflowStatus, ExecutionStatus,
    TriggerType, ActionType, WorkflowCondition, WorkflowTrigger, WorkflowAction,
    ConditionOperator, LogicOperator
)
from domain.value_objects import WorkflowId, UserId
from domain.repositories import WorkflowRepository, UnitOfWork
from domain.exceptions import WorkflowNotFoundError, InvalidWorkflowError, WorkflowExecutionError
from application.exceptions import ValidationError, PermissionDeniedError
from infrastructure.services.workflow_engine import WorkflowExecutionEngine
from infrastructure.services.rule_engine import RuleEngine
from infrastructure.services.notification_service import NotificationService
from infrastructure.logging.structured_logging import get_logger, log_context
from infrastructure.performance.monitoring import performance_monitor, monitor_performance
from infrastructure.security import require_permission, Permission


logger = get_logger(__name__)


class WorkflowApplicationService(BaseApplicationService):
    """Advanced workflow automation service."""
    
    def __init__(self, unit_of_work: UnitOfWork,
                 execution_engine: WorkflowExecutionEngine,
                 rule_engine: RuleEngine,
                 notification_service: NotificationService,
                 cache_service=None, event_store=None, message_queue=None, metrics=None):
        super().__init__(unit_of_work, cache_service, event_store, message_queue, metrics)
        
        self.workflow_repository = unit_of_work.workflow_repository
        self.execution_engine = execution_engine
        self.rule_engine = rule_engine
        self.notification_service = notification_service
        
        # Active executions tracking
        self.active_executions: Dict[str, WorkflowExecution] = {}
        
        # Event handlers for workflow triggers
        self.event_handlers = {
            "device_event": self._handle_device_event,
            "sensor_reading": self._handle_sensor_reading,
            "threshold_breach": self._handle_threshold_breach,
            "status_change": self._handle_status_change,
            "system_event": self._handle_system_event
        }
    
    @monitor_performance("workflow_creation")
    @require_permission(Permission.CREATE_WORKFLOW)
    def create_workflow(self, request: CreateWorkflowRequest, created_by: str) -> CreateWorkflowResponse:
        """Create new workflow."""
        with log_context(operation="create_workflow", created_by=created_by):
            try:
                # Validate request
                if not request.name or not request.name.strip():
                    raise ValidationError("Workflow name is required")
                
                # Create workflow entity
                workflow = Workflow(
                    workflow_id=WorkflowId(),
                    name=request.name.strip(),
                    created_by=UserId(created_by)
                )
                
                # Set optional properties
                if request.description:
                    workflow.description = request.description
                
                if request.category:
                    workflow.category = request.category
                
                if request.tags:
                    workflow.tags = set(request.tags)
                
                if request.priority:
                    workflow.priority = max(1, min(10, request.priority))
                
                # Configure timeout and concurrency
                if request.timeout_seconds:
                    workflow.timeout_seconds = request.timeout_seconds
                
                if request.max_concurrent_executions:
                    workflow.max_concurrent_executions = request.max_concurrent_executions
                
                # Add triggers
                if request.triggers:
                    for trigger_data in request.triggers:
                        trigger_type = TriggerType(trigger_data["type"])
                        conditions = self._parse_conditions(trigger_data.get("conditions", []))
                        
                        workflow.add_trigger(
                            trigger_type=trigger_type,
                            name=trigger_data["name"],
                            configuration=trigger_data.get("configuration", {}),
                            conditions=conditions
                        )
                
                # Add actions
                if request.actions:
                    for action_data in request.actions:
                        action_type = ActionType(action_data["type"])
                        conditions = self._parse_conditions(action_data.get("conditions", []))
                        
                        workflow.add_action(
                            action_type=action_type,
                            name=action_data["name"],
                            configuration=action_data.get("configuration", {}),
                            conditions=conditions
                        )
                
                # Add variables
                if request.variables:
                    for var_data in request.variables:
                        workflow.add_variable(
                            name=var_data["name"],
                            var_type=var_data["type"],
                            default_value=var_data.get("default_value"),
                            description=var_data.get("description", ""),
                            required=var_data.get("required", False)
                        )
                
                # Save workflow
                with self.unit_of_work:
                    saved_workflow = self.workflow_repository.save(workflow)
                    self.unit_of_work.commit()
                
                # Register with execution engine if active
                if request.auto_activate:
                    self._activate_workflow_internal(saved_workflow)
                
                # Cache workflow
                if self.cache_service:
                    self._cache_workflow(saved_workflow)
                
                # Publish events
                self._publish_workflow_events(saved_workflow)
                
                # Record metrics
                if self.metrics:
                    self.metrics.increment_counter(
                        "workflows_created_total",
                        {"created_by": created_by, "category": workflow.category}
                    )
                
                logger.info("Workflow created successfully", extra={
                    "workflow_id": str(saved_workflow.id),
                    "workflow_name": saved_workflow.name,
                    "created_by": created_by
                })
                
                return CreateWorkflowResponse(
                    success=True,
                    workflow_id=str(saved_workflow.id),
                    message="Workflow created successfully",
                    workflow=self._workflow_to_dict(saved_workflow)
                )
                
            except InvalidWorkflowError as e:
                logger.warning(f"Invalid workflow data: {e}")
                return CreateWorkflowResponse(
                    success=False,
                    message=f"Invalid workflow configuration: {str(e)}"
                )
            except Exception as e:
                logger.error(f"Workflow creation failed: {e}")
                return CreateWorkflowResponse(
                    success=False,
                    message="Workflow creation failed due to internal error"
                )
    
    @monitor_performance("workflow_retrieval")
    @require_permission(Permission.READ_WORKFLOW)
    def get_workflow(self, workflow_id: str, include_executions: bool = False,
                    execution_limit: int = 10) -> WorkflowResponse:
        """Retrieve workflow by ID."""
        with log_context(operation="get_workflow", workflow_id=workflow_id):
            try:
                # Try cache first
                if self.cache_service:
                    cached_workflow = self.cache_service.get(f"workflow:{workflow_id}")
                    if cached_workflow:
                        workflow_data = json.loads(cached_workflow)
                        
                        if include_executions:
                            # Get recent executions
                            executions = self._get_recent_executions(workflow_id, execution_limit)
                            workflow_data["recent_executions"] = executions
                        
                        return WorkflowResponse(
                            success=True,
                            workflow=workflow_data
                        )
                
                # Get from database
                workflow = self.workflow_repository.get_by_id(WorkflowId(workflow_id))
                if not workflow:
                    return WorkflowResponse(
                        success=False,
                        message=f"Workflow {workflow_id} not found"
                    )
                
                workflow_data = self._workflow_to_dict(workflow)
                
                if include_executions:
                    executions = self._get_recent_executions(workflow_id, execution_limit)
                    workflow_data["recent_executions"] = executions
                
                # Cache the result
                if self.cache_service:
                    self.cache_service.set(
                        f"workflow:{workflow_id}",
                        json.dumps(workflow_data, default=str),
                        ttl=1800  # 30 minutes
                    )
                
                return WorkflowResponse(
                    success=True,
                    workflow=workflow_data
                )
                
            except Exception as e:
                logger.error(f"Workflow retrieval failed: {e}")
                return WorkflowResponse(
                    success=False,
                    message="Workflow retrieval failed"
                )
    
    @monitor_performance("workflow_listing")
    @require_permission(Permission.READ_WORKFLOW)
    def list_workflows(self, status: Optional[WorkflowStatus] = None, category: Optional[str] = None,
                      tags: Optional[List[str]] = None, page: int = 1, page_size: int = 50,
                      include_stats: bool = False) -> ListWorkflowsResponse:
        """List workflows with filtering and pagination."""
        with log_context(operation="list_workflows"):
            try:
                # Build filters
                filters = {}
                if status:
                    filters['status'] = status
                if category:
                    filters['category'] = category
                if tags:
                    filters['tags'] = tags
                
                # Get workflows from repository
                workflows = self.workflow_repository.find_by_criteria(filters, page, page_size)
                total_count = self.workflow_repository.count_by_criteria(filters)
                
                # Convert to response format
                workflow_list = []
                for workflow in workflows:
                    workflow_data = self._workflow_to_dict(workflow, include_details=False)
                    
                    if include_stats:
                        workflow_data["statistics"] = {
                            "execution_count": workflow.execution_count,
                            "success_rate": workflow.get_success_rate(),
                            "failure_rate": workflow.get_failure_rate(),
                            "average_execution_time_ms": workflow.average_execution_time_ms
                        }
                    
                    workflow_list.append(workflow_data)
                
                # Calculate pagination
                total_pages = (total_count + page_size - 1) // page_size
                has_next = page < total_pages
                has_prev = page > 1
                
                return ListWorkflowsResponse(
                    success=True,
                    workflows=workflow_list,
                    total_count=total_count,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages,
                    has_next=has_next,
                    has_prev=has_prev
                )
                
            except Exception as e:
                logger.error(f"Workflow listing failed: {e}")
                return ListWorkflowsResponse(
                    success=False,
                    message="Workflow listing failed",
                    workflows=[],
                    total_count=0,
                    page=page,
                    page_size=page_size
                )
    
    @monitor_performance("workflow_execution")
    @require_permission(Permission.EXECUTE_WORKFLOW)
    def execute_workflow(self, request: ExecuteWorkflowRequest, executed_by: str) -> ExecuteWorkflowResponse:
        """Execute workflow manually."""
        with log_context(operation="execute_workflow", workflow_id=request.workflow_id, executed_by=executed_by):
            try:
                # Get workflow
                workflow = self.workflow_repository.get_by_id(WorkflowId(request.workflow_id))
                if not workflow:
                    return ExecuteWorkflowResponse(
                        success=False,
                        message=f"Workflow {request.workflow_id} not found"
                    )
                
                # Check if workflow is executable
                if workflow.status not in [WorkflowStatus.ACTIVE, WorkflowStatus.DRAFT]:
                    return ExecuteWorkflowResponse(
                        success=False,
                        message=f"Workflow is {workflow.status.value} and cannot be executed"
                    )
                
                # Create execution context
                trigger_data = {
                    "trigger_type": "manual",
                    "executed_by": executed_by,
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "variables": request.variables or {}
                }
                
                # Create execution instance
                execution = workflow.create_execution(trigger_data)
                
                # Set provided variables
                if request.variables:
                    for name, value in request.variables.items():
                        execution.set_variable(name, value)
                
                # Execute workflow
                execution_result = asyncio.run(
                    self.execution_engine.execute_workflow(workflow, execution)
                )
                
                # Record execution statistics
                workflow.record_execution(execution)
                
                # Save workflow updates
                with self.unit_of_work:
                    self.workflow_repository.save(workflow)
                    self.unit_of_work.commit()
                
                # Invalidate cache
                if self.cache_service:
                    self.cache_service.delete(f"workflow:{request.workflow_id}")
                
                # Record metrics
                if self.metrics:
                    self.metrics.increment_counter(
                        "workflows_executed_total",
                        {"workflow_id": request.workflow_id, "trigger_type": "manual", "success": str(execution.status == ExecutionStatus.COMPLETED)}
                    )
                
                return ExecuteWorkflowResponse(
                    success=True,
                    execution_id=execution.id,
                    status=execution.status.value,
                    message="Workflow execution completed",
                    execution_details=self._execution_to_dict(execution)
                )
                
            except Exception as e:
                logger.error(f"Workflow execution failed: {e}")
                return ExecuteWorkflowResponse(
                    success=False,
                    message="Workflow execution failed due to internal error"
                )
    
    @monitor_performance("workflow_trigger")
    def trigger_workflow(self, request: TriggerWorkflowRequest) -> None:
        """Process workflow triggers from events."""
        with log_context(operation="trigger_workflow", event_type=request.event_type):
            try:
                # Find workflows that should be triggered
                active_workflows = self.workflow_repository.find_by_status(WorkflowStatus.ACTIVE)
                
                triggered_workflows = []
                for workflow in active_workflows:
                    triggers = workflow.should_trigger(request.event_data)
                    if triggers:
                        triggered_workflows.append((workflow, triggers))
                
                # Execute triggered workflows
                for workflow, triggers in triggered_workflows:
                    for trigger in triggers:
                        # Check concurrency limits
                        active_executions_count = len([
                            exec_id for exec_id, execution in self.active_executions.items()
                            if execution.workflow_id == workflow.id and execution.status == ExecutionStatus.RUNNING
                        ])
                        
                        if active_executions_count >= workflow.max_concurrent_executions:
                            logger.warning(f"Workflow {workflow.id} exceeded concurrency limit")
                            continue
                        
                        # Create and execute workflow
                        trigger_data = request.event_data.copy()
                        trigger_data.update({
                            "trigger_id": trigger.id,
                            "trigger_type": trigger.type.value,
                            "trigger_name": trigger.name
                        })
                        
                        execution = workflow.create_execution(trigger_data)
                        self.active_executions[execution.id] = execution
                        
                        # Execute asynchronously
                        asyncio.create_task(self._execute_workflow_async(workflow, execution))
                
                logger.info(f"Triggered {len(triggered_workflows)} workflows for event type {request.event_type}")
                
            except Exception as e:
                logger.error(f"Workflow triggering failed: {e}")
    
    @monitor_performance("workflow_update")
    @require_permission(Permission.UPDATE_WORKFLOW)
    def update_workflow(self, workflow_id: str, request: UpdateWorkflowRequest,
                       updated_by: str) -> UpdateWorkflowResponse:
        """Update workflow configuration."""
        with log_context(operation="update_workflow", workflow_id=workflow_id, updated_by=updated_by):
            try:
                # Get workflow
                workflow = self.workflow_repository.get_by_id(WorkflowId(workflow_id))
                if not workflow:
                    return UpdateWorkflowResponse(
                        success=False,
                        message=f"Workflow {workflow_id} not found"
                    )
                
                # Update basic properties
                if request.name:
                    workflow.name = request.name
                
                if request.description is not None:
                    workflow.description = request.description
                
                if request.category is not None:
                    workflow.category = request.category
                
                if request.tags is not None:
                    workflow.tags = set(request.tags)
                
                if request.priority is not None:
                    workflow.priority = max(1, min(10, request.priority))
                
                # Update configuration
                if request.timeout_seconds is not None:
                    workflow.timeout_seconds = request.timeout_seconds
                
                if request.max_concurrent_executions is not None:
                    workflow.max_concurrent_executions = request.max_concurrent_executions
                
                # Update triggers
                if request.triggers is not None:
                    # Remove existing triggers
                    workflow.triggers.clear()
                    
                    # Add new triggers
                    for trigger_data in request.triggers:
                        trigger_type = TriggerType(trigger_data["type"])
                        conditions = self._parse_conditions(trigger_data.get("conditions", []))
                        
                        workflow.add_trigger(
                            trigger_type=trigger_type,
                            name=trigger_data["name"],
                            configuration=trigger_data.get("configuration", {}),
                            conditions=conditions
                        )
                
                # Update actions
                if request.actions is not None:
                    # Remove existing actions
                    workflow.actions.clear()
                    
                    # Add new actions
                    for action_data in request.actions:
                        action_type = ActionType(action_data["type"])
                        conditions = self._parse_conditions(action_data.get("conditions", []))
                        
                        workflow.add_action(
                            action_type=action_type,
                            name=action_data["name"],
                            configuration=action_data.get("configuration", {}),
                            conditions=conditions
                        )
                
                # Validate updated workflow
                validation_errors = workflow.validate()
                if validation_errors:
                    return UpdateWorkflowResponse(
                        success=False,
                        message=f"Workflow validation failed: {'; '.join(validation_errors)}"
                    )
                
                # Save workflow
                with self.unit_of_work:
                    updated_workflow = self.workflow_repository.save(workflow)
                    self.unit_of_work.commit()
                
                # Update execution engine registration
                if updated_workflow.status == WorkflowStatus.ACTIVE:
                    self.execution_engine.update_workflow(updated_workflow)
                
                # Invalidate cache
                if self.cache_service:
                    self.cache_service.delete(f"workflow:{workflow_id}")
                
                # Publish events
                self._publish_workflow_events(updated_workflow)
                
                return UpdateWorkflowResponse(
                    success=True,
                    message="Workflow updated successfully"
                )
                
            except InvalidWorkflowError as e:
                logger.warning(f"Invalid workflow update: {e}")
                return UpdateWorkflowResponse(
                    success=False,
                    message=f"Invalid workflow configuration: {str(e)}"
                )
            except Exception as e:
                logger.error(f"Workflow update failed: {e}")
                return UpdateWorkflowResponse(
                    success=False,
                    message="Workflow update failed"
                )
    
    @monitor_performance("workflow_activation")
    @require_permission(Permission.UPDATE_WORKFLOW)
    def activate_workflow(self, workflow_id: str, activated_by: str) -> UpdateWorkflowResponse:
        """Activate workflow for execution."""
        return self._change_workflow_status(workflow_id, WorkflowStatus.ACTIVE, activated_by)
    
    @monitor_performance("workflow_deactivation")
    @require_permission(Permission.UPDATE_WORKFLOW)
    def deactivate_workflow(self, workflow_id: str, deactivated_by: str) -> UpdateWorkflowResponse:
        """Deactivate workflow."""
        return self._change_workflow_status(workflow_id, WorkflowStatus.PAUSED, deactivated_by)
    
    @monitor_performance("workflow_disable")
    @require_permission(Permission.UPDATE_WORKFLOW)
    def disable_workflow(self, workflow_id: str, disabled_by: str) -> UpdateWorkflowResponse:
        """Disable workflow permanently."""
        return self._change_workflow_status(workflow_id, WorkflowStatus.DISABLED, disabled_by)
    
    @monitor_performance("workflow_clone")
    @require_permission(Permission.CREATE_WORKFLOW)
    def clone_workflow(self, request: CloneWorkflowRequest, cloned_by: str) -> CreateWorkflowResponse:
        """Clone existing workflow."""
        with log_context(operation="clone_workflow", source_workflow_id=request.source_workflow_id, cloned_by=cloned_by):
            try:
                # Get source workflow
                source_workflow = self.workflow_repository.get_by_id(WorkflowId(request.source_workflow_id))
                if not source_workflow:
                    return CreateWorkflowResponse(
                        success=False,
                        message=f"Source workflow {request.source_workflow_id} not found"
                    )
                
                # Clone workflow
                cloned_workflow = source_workflow.clone(request.new_name, UserId(cloned_by))
                
                # Apply modifications if provided
                if request.modifications:
                    if "description" in request.modifications:
                        cloned_workflow.description = request.modifications["description"]
                    if "category" in request.modifications:
                        cloned_workflow.category = request.modifications["category"]
                    if "tags" in request.modifications:
                        cloned_workflow.tags = set(request.modifications["tags"])
                
                # Save cloned workflow
                with self.unit_of_work:
                    saved_workflow = self.workflow_repository.save(cloned_workflow)
                    self.unit_of_work.commit()
                
                # Record metrics
                if self.metrics:
                    self.metrics.increment_counter(
                        "workflows_cloned_total",
                        {"cloned_by": cloned_by, "source_category": source_workflow.category}
                    )
                
                logger.info("Workflow cloned successfully", extra={
                    "source_workflow_id": request.source_workflow_id,
                    "cloned_workflow_id": str(saved_workflow.id),
                    "cloned_by": cloned_by
                })
                
                return CreateWorkflowResponse(
                    success=True,
                    workflow_id=str(saved_workflow.id),
                    message="Workflow cloned successfully",
                    workflow=self._workflow_to_dict(saved_workflow)
                )
                
            except Exception as e:
                logger.error(f"Workflow cloning failed: {e}")
                return CreateWorkflowResponse(
                    success=False,
                    message="Workflow cloning failed"
                )
    
    @monitor_performance("workflow_stats")
    @require_permission(Permission.READ_WORKFLOW)
    def get_workflow_statistics(self, workflow_id: str, days: int = 30) -> WorkflowStatsResponse:
        """Get workflow execution statistics."""
        with log_context(operation="get_workflow_stats", workflow_id=workflow_id):
            try:
                # Get workflow
                workflow = self.workflow_repository.get_by_id(WorkflowId(workflow_id))
                if not workflow:
                    return WorkflowStatsResponse(
                        success=False,
                        message=f"Workflow {workflow_id} not found"
                    )
                
                # Get execution history
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(days=days)
                
                executions = self._get_executions_in_period(workflow_id, start_time, end_time)
                
                # Calculate statistics
                total_executions = len(executions)
                successful_executions = len([e for e in executions if e["status"] == ExecutionStatus.COMPLETED.value])
                failed_executions = len([e for e in executions if e["status"] == ExecutionStatus.FAILED.value])
                
                success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
                
                # Calculate average execution time
                completed_executions = [e for e in executions if e.get("execution_time_ms", 0) > 0]
                avg_execution_time = (
                    sum(e["execution_time_ms"] for e in completed_executions) / len(completed_executions)
                    if completed_executions else 0
                )
                
                # Group by day for trend analysis
                daily_stats = self._calculate_daily_stats(executions, start_time, end_time)
                
                # Most common failure reasons
                failure_reasons = self._analyze_failure_reasons(executions)
                
                # Performance metrics
                performance_metrics = {
                    "average_execution_time_ms": avg_execution_time,
                    "fastest_execution_ms": min((e["execution_time_ms"] for e in completed_executions), default=0),
                    "slowest_execution_ms": max((e["execution_time_ms"] for e in completed_executions), default=0),
                    "timeout_count": len([e for e in executions if e["status"] == ExecutionStatus.TIMEOUT.value])
                }
                
                stats_data = {
                    "workflow_id": workflow_id,
                    "period_days": days,
                    "summary": {
                        "total_executions": total_executions,
                        "successful_executions": successful_executions,
                        "failed_executions": failed_executions,
                        "success_rate": round(success_rate, 2),
                        "failure_rate": round(100 - success_rate, 2)
                    },
                    "performance": performance_metrics,
                    "daily_trends": daily_stats,
                    "failure_analysis": failure_reasons,
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
                
                return WorkflowStatsResponse(
                    success=True,
                    statistics=stats_data
                )
                
            except Exception as e:
                logger.error(f"Workflow statistics retrieval failed: {e}")
                return WorkflowStatsResponse(
                    success=False,
                    message="Statistics retrieval failed"
                )
    
    # Event handlers
    async def _handle_device_event(self, event_data: Dict[str, Any]) -> None:
        """Handle device events for workflow triggering."""
        trigger_request = TriggerWorkflowRequest(
            event_type="device_event",
            event_data=event_data
        )
        self.trigger_workflow(trigger_request)
    
    async def _handle_sensor_reading(self, event_data: Dict[str, Any]) -> None:
        """Handle sensor readings for workflow triggering."""
        # Check if reading crosses any thresholds
        threshold_breaches = self.rule_engine.evaluate_thresholds(event_data)
        
        for breach in threshold_breaches:
            breach_data = event_data.copy()
            breach_data.update({
                "event_type": "threshold_breach",
                "threshold": breach["threshold"],
                "breach_type": breach["type"]
            })
            
            trigger_request = TriggerWorkflowRequest(
                event_type="threshold_breach",
                event_data=breach_data
            )
            self.trigger_workflow(trigger_request)
        
        # Also trigger sensor reading workflows
        trigger_request = TriggerWorkflowRequest(
            event_type="sensor_reading",
            event_data=event_data
        )
        self.trigger_workflow(trigger_request)
    
    async def _handle_threshold_breach(self, event_data: Dict[str, Any]) -> None:
        """Handle threshold breach events."""
        trigger_request = TriggerWorkflowRequest(
            event_type="threshold_breach",
            event_data=event_data
        )
        self.trigger_workflow(trigger_request)
    
    async def _handle_status_change(self, event_data: Dict[str, Any]) -> None:
        """Handle status change events."""
        trigger_request = TriggerWorkflowRequest(
            event_type="status_change",
            event_data=event_data
        )
        self.trigger_workflow(trigger_request)
    
    async def _handle_system_event(self, event_data: Dict[str, Any]) -> None:
        """Handle system events."""
        trigger_request = TriggerWorkflowRequest(
            event_type="system_event",
            event_data=event_data
        )
        self.trigger_workflow(trigger_request)
    
    # Helper methods
    def _parse_conditions(self, conditions_data: List[Dict[str, Any]]) -> List[WorkflowCondition]:
        """Parse conditions from request data."""
        conditions = []
        
        for cond_data in conditions_data:
            condition = WorkflowCondition(
                field=cond_data["field"],
                operator=ConditionOperator(cond_data["operator"]),
                value=cond_data["value"],
                logic_operator=LogicOperator(cond_data.get("logic_operator", "and"))
            )
            conditions.append(condition)
        
        return conditions
    
    def _change_workflow_status(self, workflow_id: str, new_status: WorkflowStatus, changed_by: str) -> UpdateWorkflowResponse:
        """Change workflow status."""
        with log_context(operation="change_workflow_status", workflow_id=workflow_id, new_status=new_status.value):
            try:
                # Get workflow
                workflow = self.workflow_repository.get_by_id(WorkflowId(workflow_id))
                if not workflow:
                    return UpdateWorkflowResponse(
                        success=False,
                        message=f"Workflow {workflow_id} not found"
                    )
                
                old_status = workflow.status
                
                # Change status
                if new_status == WorkflowStatus.ACTIVE:
                    workflow.activate()
                elif new_status == WorkflowStatus.PAUSED:
                    workflow.deactivate()
                elif new_status == WorkflowStatus.DISABLED:
                    workflow.disable()
                
                # Save workflow
                with self.unit_of_work:
                    updated_workflow = self.workflow_repository.save(workflow)
                    self.unit_of_work.commit()
                
                # Update execution engine
                if new_status == WorkflowStatus.ACTIVE:
                    self.execution_engine.register_workflow(updated_workflow)
                else:
                    self.execution_engine.unregister_workflow(workflow_id)
                
                # Invalidate cache
                if self.cache_service:
                    self.cache_service.delete(f"workflow:{workflow_id}")
                
                # Record metrics
                if self.metrics:
                    self.metrics.increment_counter(
                        "workflow_status_changes_total",
                        {"old_status": old_status.value, "new_status": new_status.value, "changed_by": changed_by}
                    )
                
                logger.info(f"Workflow status changed from {old_status.value} to {new_status.value}", extra={
                    "workflow_id": workflow_id,
                    "changed_by": changed_by
                })
                
                return UpdateWorkflowResponse(
                    success=True,
                    message=f"Workflow {new_status.value} successfully"
                )
                
            except Exception as e:
                logger.error(f"Workflow status change failed: {e}")
                return UpdateWorkflowResponse(
                    success=False,
                    message="Workflow status change failed"
                )
    
    def _activate_workflow_internal(self, workflow: Workflow) -> None:
        """Activate workflow internally."""
        try:
            workflow.activate()
            self.execution_engine.register_workflow(workflow)
            logger.info(f"Workflow {workflow.id} activated internally")
        except Exception as e:
            logger.warning(f"Failed to activate workflow internally: {e}")
    
    async def _execute_workflow_async(self, workflow: Workflow, execution: WorkflowExecution) -> None:
        """Execute workflow asynchronously."""
        try:
            result = await self.execution_engine.execute_workflow(workflow, execution)
            
            # Record execution
            workflow.record_execution(execution)
            
            # Save workflow updates
            with self.unit_of_work:
                self.workflow_repository.save(workflow)
                self.unit_of_work.commit()
            
            # Remove from active executions
            if execution.id in self.active_executions:
                del self.active_executions[execution.id]
            
            logger.info(f"Workflow {workflow.id} execution completed", extra={
                "execution_id": execution.id,
                "status": execution.status.value
            })
            
        except Exception as e:
            logger.error(f"Async workflow execution failed: {e}")
            if execution.id in self.active_executions:
                del self.active_executions[execution.id]
    
    def _workflow_to_dict(self, workflow: Workflow, include_details: bool = True) -> Dict[str, Any]:
        """Convert workflow to dictionary."""
        base_dict = {
            "id": str(workflow.id),
            "name": workflow.name,
            "description": workflow.description,
            "status": workflow.status.value,
            "category": workflow.category,
            "created_by": str(workflow.created_by),
            "created_at": workflow.created_at.isoformat(),
            "updated_at": workflow.updated_at.isoformat()
        }
        
        if include_details:
            base_dict.update(workflow.to_dict())
        
        return base_dict
    
    def _execution_to_dict(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Convert execution to dictionary."""
        return {
            "id": execution.id,
            "workflow_id": str(execution.workflow_id),
            "status": execution.status.value,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "execution_time_ms": execution.execution_time_ms,
            "completed_actions": execution.completed_actions,
            "failed_actions": execution.failed_actions,
            "error_message": execution.error_message,
            "results": execution.results
        }
    
    def _get_recent_executions(self, workflow_id: str, limit: int) -> List[Dict[str, Any]]:
        """Get recent executions for workflow."""
        # This would typically query execution history from database
        # For now, return placeholder data
        return []
    
    def _get_executions_in_period(self, workflow_id: str, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get executions in time period."""
        # This would query actual execution history
        # For now, return placeholder data
        return []
    
    def _calculate_daily_stats(self, executions: List[Dict[str, Any]], start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Calculate daily execution statistics."""
        daily_stats = []
        current_date = start_time.date()
        end_date = end_time.date()
        
        while current_date <= end_date:
            day_executions = [
                e for e in executions 
                if datetime.fromisoformat(e.get("completed_at", "")).date() == current_date
            ]
            
            successful = len([e for e in day_executions if e["status"] == ExecutionStatus.COMPLETED.value])
            failed = len([e for e in day_executions if e["status"] == ExecutionStatus.FAILED.value])
            
            daily_stats.append({
                "date": current_date.isoformat(),
                "total_executions": len(day_executions),
                "successful_executions": successful,
                "failed_executions": failed,
                "success_rate": (successful / len(day_executions) * 100) if day_executions else 0
            })
            
            current_date += timedelta(days=1)
        
        return daily_stats
    
    def _analyze_failure_reasons(self, executions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze failure reasons from executions."""
        failure_reasons = {}
        
        failed_executions = [e for e in executions if e["status"] == ExecutionStatus.FAILED.value]
        
        for execution in failed_executions:
            error_message = execution.get("error_message", "Unknown error")
            # Categorize error messages
            if "timeout" in error_message.lower():
                category = "Timeout"
            elif "connection" in error_message.lower():
                category = "Connection Error"
            elif "permission" in error_message.lower():
                category = "Permission Error"
            elif "validation" in error_message.lower():
                category = "Validation Error"
            else:
                category = "Other"
            
            failure_reasons[category] = failure_reasons.get(category, 0) + 1
        
        return failure_reasons
    
    def _cache_workflow(self, workflow: Workflow) -> None:
        """Cache workflow data."""
        if self.cache_service:
            workflow_data = self._workflow_to_dict(workflow)
            cache_key = f"workflow:{workflow.id}"
            self.cache_service.set(cache_key, json.dumps(workflow_data, default=str), ttl=1800)
    
    def _publish_workflow_events(self, workflow: Workflow) -> None:
        """Publish workflow domain events."""
        if self.event_store:
            events = workflow.get_domain_events()
            for event in events:
                self.event_store.append(event)
            workflow.clear_domain_events()