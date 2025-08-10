"""
Advanced Workflow Execution Engine.

Provides comprehensive workflow execution capabilities including action execution,
conditional logic, parallel processing, error handling, and retry mechanisms.
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timezone, timedelta
import json
import traceback
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import asdict

from domain.entities.workflow_entity import (
    Workflow, WorkflowExecution, WorkflowAction, ExecutionStatus,
    ActionType, TriggerType, WorkflowStatus
)
from infrastructure.services.action_executors import ActionExecutorFactory
from infrastructure.services.notification_service import NotificationService
from infrastructure.logging.structured_logging import get_logger, log_context
from infrastructure.performance.monitoring import performance_monitor


logger = get_logger(__name__)


class WorkflowExecutionEngine:
    """Advanced workflow execution engine with comprehensive automation capabilities."""
    
    def __init__(self, notification_service: NotificationService = None,
                 max_workers: int = 10, default_timeout: int = 3600):
        self.notification_service = notification_service
        self.max_workers = max_workers
        self.default_timeout = default_timeout
        
        # Thread pool for parallel execution
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Action executors
        self.action_factory = ActionExecutorFactory()
        
        # Registered workflows for event-based triggering
        self.registered_workflows: Dict[str, Workflow] = {}
        
        # Active executions for monitoring
        self.active_executions: Dict[str, WorkflowExecution] = {}
        
        # Execution statistics
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time_ms": 0
        }
    
    def register_workflow(self, workflow: Workflow) -> None:
        """Register workflow for event-based execution."""
        if workflow.status == WorkflowStatus.ACTIVE:
            self.registered_workflows[str(workflow.id)] = workflow
            logger.info(f"Registered workflow for execution: {workflow.name}")
    
    def unregister_workflow(self, workflow_id: str) -> None:
        """Unregister workflow from event-based execution."""
        if workflow_id in self.registered_workflows:
            workflow = self.registered_workflows.pop(workflow_id)
            logger.info(f"Unregistered workflow: {workflow.name}")
    
    def update_workflow(self, workflow: Workflow) -> None:
        """Update registered workflow."""
        if str(workflow.id) in self.registered_workflows:
            self.registered_workflows[str(workflow.id)] = workflow
            logger.info(f"Updated registered workflow: {workflow.name}")
    
    async def execute_workflow(self, workflow: Workflow, execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute workflow with comprehensive error handling and monitoring."""
        with log_context(operation="execute_workflow", workflow_id=str(workflow.id), execution_id=execution.id):
            start_time = datetime.now(timezone.utc)
            self.active_executions[execution.id] = execution
            
            try:
                logger.info(f"Starting workflow execution: {workflow.name}")
                
                # Start execution
                execution.start_execution()
                
                # Set up execution timeout
                timeout = workflow.timeout_seconds or self.default_timeout
                
                # Execute workflow with timeout
                result = await asyncio.wait_for(
                    self._execute_workflow_internal(workflow, execution),
                    timeout=timeout
                )
                
                # Mark as completed
                execution.complete_execution(success=True)
                
                # Update statistics
                self._update_execution_stats(execution, success=True)
                
                logger.info(f"Workflow execution completed successfully: {execution.id}")
                
                return {
                    "success": True,
                    "execution_id": execution.id,
                    "status": execution.status.value,
                    "execution_time_ms": execution.execution_time_ms,
                    "completed_actions": len(execution.completed_actions),
                    "results": execution.results
                }
                
            except asyncio.TimeoutError:
                error_msg = f"Workflow execution timed out after {timeout} seconds"
                execution.complete_execution(success=False, error_message=error_msg)
                execution.status = ExecutionStatus.TIMEOUT
                
                logger.warning(f"Workflow execution timed out: {execution.id}")
                
                return {
                    "success": False,
                    "execution_id": execution.id,
                    "status": execution.status.value,
                    "error": error_msg
                }
                
            except Exception as e:
                error_msg = f"Workflow execution failed: {str(e)}"
                execution.complete_execution(success=False, error_message=error_msg)
                
                # Update statistics
                self._update_execution_stats(execution, success=False)
                
                logger.error(f"Workflow execution failed: {execution.id}, error: {e}")
                logger.error(f"Execution traceback: {traceback.format_exc()}")
                
                return {
                    "success": False,
                    "execution_id": execution.id,
                    "status": execution.status.value,
                    "error": error_msg,
                    "traceback": traceback.format_exc()
                }
                
            finally:
                # Remove from active executions
                if execution.id in self.active_executions:
                    del self.active_executions[execution.id]
    
    async def _execute_workflow_internal(self, workflow: Workflow, execution: WorkflowExecution) -> Dict[str, Any]:
        """Internal workflow execution logic."""
        execution_results = {}
        
        # Validate workflow before execution
        validation_errors = workflow.validate()
        if validation_errors:
            raise Exception(f"Workflow validation failed: {'; '.join(validation_errors)}")
        
        # Execute actions in sequence
        for i, action in enumerate(workflow.actions):
            execution.current_action_index = i
            
            # Check if execution should continue
            if execution.status != ExecutionStatus.RUNNING:
                break
            
            # Check action conditions
            if not action.should_execute(execution.context):
                logger.info(f"Skipping action {action.name} - conditions not met")
                continue
            
            try:
                # Execute action with timeout and retry
                action_result = await self._execute_action_with_retry(
                    workflow, execution, action
                )
                
                execution_results[action.id] = action_result
                
                if not action_result.get("success", False):
                    # Handle action failure based on workflow configuration
                    if self._should_stop_on_failure(workflow, action):
                        raise Exception(f"Action {action.name} failed: {action_result.get('error', 'Unknown error')}")
                
            except Exception as e:
                error_msg = f"Action {action.name} execution failed: {str(e)}"
                logger.error(error_msg)
                
                # Record action failure
                execution.record_action_result(
                    action_id=action.id,
                    action_type=action.type.value,
                    success=False,
                    error_message=error_msg
                )
                
                # Check if workflow should continue
                if self._should_stop_on_failure(workflow, action):
                    raise Exception(error_msg)
        
        return execution_results
    
    async def _execute_action_with_retry(self, workflow: Workflow, execution: WorkflowExecution,
                                       action: WorkflowAction) -> Dict[str, Any]:
        """Execute action with retry logic."""
        max_retries = action.retry_count
        retry_count = 0
        last_error = None
        
        while retry_count <= max_retries:
            try:
                action_start_time = datetime.now(timezone.utc)
                
                # Execute action
                result = await self._execute_single_action(workflow, execution, action)
                
                # Calculate execution time
                execution_time_ms = int((datetime.now(timezone.utc) - action_start_time).total_seconds() * 1000)
                
                # Record successful action execution
                execution.record_action_result(
                    action_id=action.id,
                    action_type=action.type.value,
                    success=True,
                    result=result,
                    execution_time_ms=execution_time_ms
                )
                
                logger.info(f"Action {action.name} executed successfully in {execution_time_ms}ms")
                
                return {
                    "success": True,
                    "result": result,
                    "execution_time_ms": execution_time_ms,
                    "retry_count": retry_count
                }
                
            except Exception as e:
                last_error = e
                retry_count += 1
                
                if retry_count <= max_retries:
                    # Calculate backoff delay
                    backoff_delay = self._calculate_backoff_delay(retry_count, workflow.retry_policy)
                    
                    logger.warning(f"Action {action.name} failed (attempt {retry_count}/{max_retries + 1}), retrying in {backoff_delay}s: {e}")
                    
                    # Wait before retry
                    await asyncio.sleep(backoff_delay)
                else:
                    logger.error(f"Action {action.name} failed after {retry_count} attempts: {e}")
        
        # All retries exhausted
        execution_time_ms = int((datetime.now(timezone.utc) - action_start_time).total_seconds() * 1000)
        
        execution.record_action_result(
            action_id=action.id,
            action_type=action.type.value,
            success=False,
            error_message=str(last_error),
            execution_time_ms=execution_time_ms
        )
        
        return {
            "success": False,
            "error": str(last_error),
            "retry_count": retry_count,
            "execution_time_ms": execution_time_ms
        }
    
    async def _execute_single_action(self, workflow: Workflow, execution: WorkflowExecution,
                                   action: WorkflowAction) -> Any:
        """Execute single action based on type."""
        # Get action executor
        executor = self.action_factory.get_executor(action.type)
        
        if not executor:
            raise Exception(f"No executor found for action type: {action.type.value}")
        
        # Prepare action context
        action_context = {
            "workflow_id": str(workflow.id),
            "workflow_name": workflow.name,
            "execution_id": execution.id,
            "action_id": action.id,
            "action_name": action.name,
            "execution_context": execution.context,
            "variables": execution.variables,
            "configuration": action.configuration
        }
        
        # Execute action with timeout
        try:
            result = await asyncio.wait_for(
                executor.execute(action_context),
                timeout=action.timeout_seconds
            )
            
            # Update execution context with action result if it's a dictionary
            if isinstance(result, dict) and "context_updates" in result:
                execution.update_context(result["context_updates"])
            
            return result
            
        except asyncio.TimeoutError:
            raise Exception(f"Action timed out after {action.timeout_seconds} seconds")
    
    def _calculate_backoff_delay(self, retry_count: int, retry_policy: Dict[str, Any]) -> float:
        """Calculate exponential backoff delay."""
        base_delay = retry_policy.get("base_delay_seconds", 1)
        multiplier = retry_policy.get("backoff_multiplier", 2)
        max_delay = retry_policy.get("max_delay_seconds", 300)  # 5 minutes
        
        delay = base_delay * (multiplier ** (retry_count - 1))
        return min(delay, max_delay)
    
    def _should_stop_on_failure(self, workflow: Workflow, failed_action: WorkflowAction) -> bool:
        """Determine if workflow should stop on action failure."""
        # Check workflow-level configuration
        continue_on_failure = workflow.retry_policy.get("continue_on_failure", False)
        
        # Check action-level configuration
        action_continue_on_failure = failed_action.configuration.get("continue_on_failure", continue_on_failure)
        
        # Check if action is marked as critical
        is_critical = failed_action.configuration.get("critical", True)
        
        return is_critical and not action_continue_on_failure
    
    def _update_execution_stats(self, execution: WorkflowExecution, success: bool) -> None:
        """Update execution statistics."""
        self.execution_stats["total_executions"] += 1
        
        if success:
            self.execution_stats["successful_executions"] += 1
        else:
            self.execution_stats["failed_executions"] += 1
        
        # Update average execution time
        if execution.execution_time_ms > 0:
            total_executions = self.execution_stats["total_executions"]
            current_avg = self.execution_stats["average_execution_time_ms"]
            new_avg = ((current_avg * (total_executions - 1)) + execution.execution_time_ms) / total_executions
            self.execution_stats["average_execution_time_ms"] = new_avg
    
    async def cancel_execution(self, execution_id: str, reason: str = "Cancelled by user") -> bool:
        """Cancel active workflow execution."""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.status = ExecutionStatus.CANCELLED
            execution.error_message = reason
            execution.complete_execution(success=False, error_message=reason)
            
            logger.info(f"Workflow execution cancelled: {execution_id}, reason: {reason}")
            return True
        
        return False
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get current execution status."""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            return {
                "execution_id": execution.id,
                "workflow_id": str(execution.workflow_id),
                "status": execution.status.value,
                "current_action_index": execution.current_action_index,
                "completed_actions": len(execution.completed_actions),
                "failed_actions": len(execution.failed_actions),
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "progress_percentage": execution.get_progress_percentage(
                    len(self.registered_workflows.get(str(execution.workflow_id), Workflow(None, "", None)).actions)
                )
            }
        
        return None
    
    def get_active_executions(self) -> List[Dict[str, Any]]:
        """Get all active executions."""
        active_list = []
        
        for execution_id, execution in self.active_executions.items():
            workflow = self.registered_workflows.get(str(execution.workflow_id))
            total_actions = len(workflow.actions) if workflow else 0
            
            active_list.append({
                "execution_id": execution.id,
                "workflow_id": str(execution.workflow_id),
                "workflow_name": workflow.name if workflow else "Unknown",
                "status": execution.status.value,
                "current_action_index": execution.current_action_index,
                "progress_percentage": execution.get_progress_percentage(total_actions),
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "elapsed_time_ms": int(
                    (datetime.now(timezone.utc) - execution.started_at).total_seconds() * 1000
                ) if execution.started_at else 0
            })
        
        return active_list
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get execution engine statistics."""
        success_rate = 0
        if self.execution_stats["total_executions"] > 0:
            success_rate = (self.execution_stats["successful_executions"] / self.execution_stats["total_executions"]) * 100
        
        return {
            "total_executions": self.execution_stats["total_executions"],
            "successful_executions": self.execution_stats["successful_executions"],
            "failed_executions": self.execution_stats["failed_executions"],
            "success_rate": round(success_rate, 2),
            "average_execution_time_ms": round(self.execution_stats["average_execution_time_ms"], 2),
            "active_executions_count": len(self.active_executions),
            "registered_workflows_count": len(self.registered_workflows),
            "max_workers": self.max_workers
        }
    
    async def test_workflow(self, workflow: Workflow, test_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test workflow execution in dry-run mode."""
        with log_context(operation="test_workflow", workflow_id=str(workflow.id)):
            try:
                # Create test execution
                test_trigger_data = test_data or {
                    "trigger_type": "test",
                    "test_mode": True,
                    "executed_by": "test_runner"
                }
                
                execution = workflow.create_execution(test_trigger_data)
                execution.context["test_mode"] = True
                
                # Validate workflow
                validation_errors = workflow.validate()
                if validation_errors:
                    return {
                        "success": False,
                        "test_result": "validation_failed",
                        "errors": validation_errors
                    }
                
                # Test each action without actually executing
                test_results = []
                
                for action in workflow.actions:
                    try:
                        # Check if action should execute
                        should_execute = action.should_execute(execution.context)
                        
                        # Get action executor for validation
                        executor = self.action_factory.get_executor(action.type)
                        executor_available = executor is not None
                        
                        # Validate action configuration
                        config_errors = action.validate_configuration()
                        
                        action_test_result = {
                            "action_id": action.id,
                            "action_name": action.name,
                            "action_type": action.type.value,
                            "should_execute": should_execute,
                            "executor_available": executor_available,
                            "configuration_valid": len(config_errors) == 0,
                            "configuration_errors": config_errors,
                            "estimated_execution_time_ms": self._estimate_action_execution_time(action)
                        }
                        
                        test_results.append(action_test_result)
                        
                    except Exception as e:
                        test_results.append({
                            "action_id": action.id,
                            "action_name": action.name,
                            "action_type": action.type.value,
                            "test_error": str(e)
                        })
                
                # Calculate overall test result
                all_valid = all(
                    result.get("executor_available", False) and result.get("configuration_valid", False)
                    for result in test_results
                )
                
                executable_actions = sum(1 for result in test_results if result.get("should_execute", False))
                total_estimated_time = sum(result.get("estimated_execution_time_ms", 0) for result in test_results)
                
                return {
                    "success": True,
                    "test_result": "valid" if all_valid else "issues_found",
                    "workflow_valid": all_valid,
                    "total_actions": len(workflow.actions),
                    "executable_actions": executable_actions,
                    "estimated_total_execution_time_ms": total_estimated_time,
                    "action_tests": test_results,
                    "recommendations": self._generate_test_recommendations(test_results)
                }
                
            except Exception as e:
                logger.error(f"Workflow test failed: {e}")
                return {
                    "success": False,
                    "test_result": "test_failed",
                    "error": str(e)
                }
    
    def _estimate_action_execution_time(self, action: WorkflowAction) -> int:
        """Estimate action execution time in milliseconds."""
        # Base estimates by action type
        time_estimates = {
            ActionType.DELAY: action.configuration.get("duration", 1) * 1000,
            ActionType.EMAIL_NOTIFICATION: 2000,
            ActionType.SMS_NOTIFICATION: 3000,
            ActionType.DEVICE_CONTROL: 1500,
            ActionType.HTTP_REQUEST: 5000,
            ActionType.API_CALL: 3000,
            ActionType.GENERATE_REPORT: 10000,
            ActionType.CUSTOM_SCRIPT: 5000
        }
        
        return time_estimates.get(action.type, 2000)  # Default 2 seconds
    
    def _generate_test_recommendations(self, test_results: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Check for missing executors
        missing_executors = [
            result for result in test_results 
            if not result.get("executor_available", False)
        ]
        if missing_executors:
            recommendations.append(f"Install executors for {len(missing_executors)} action types")
        
        # Check for configuration errors
        config_errors = [
            result for result in test_results 
            if not result.get("configuration_valid", False)
        ]
        if config_errors:
            recommendations.append(f"Fix configuration errors in {len(config_errors)} actions")
        
        # Check for very long estimated execution times
        long_running = [
            result for result in test_results 
            if result.get("estimated_execution_time_ms", 0) > 30000
        ]
        if long_running:
            recommendations.append("Consider breaking down long-running actions")
        
        # Check for actions that won't execute
        non_executable = [
            result for result in test_results 
            if not result.get("should_execute", False)
        ]
        if len(non_executable) == len(test_results):
            recommendations.append("Review action conditions - no actions will execute")
        
        return recommendations
    
    async def cleanup_completed_executions(self, max_age_hours: int = 24) -> int:
        """Clean up old completed executions from memory."""
        cleanup_count = 0
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        # Note: In a production system, execution history would be stored in database
        # This cleanup is for in-memory active executions only
        
        completed_executions = [
            exec_id for exec_id, execution in self.active_executions.items()
            if execution.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]
            and execution.completed_at
            and execution.completed_at < cutoff_time
        ]
        
        for exec_id in completed_executions:
            del self.active_executions[exec_id]
            cleanup_count += 1
        
        logger.info(f"Cleaned up {cleanup_count} old execution records")
        return cleanup_count
    
    def shutdown(self) -> None:
        """Shutdown execution engine gracefully."""
        logger.info("Shutting down workflow execution engine...")
        
        # Cancel all active executions
        for execution_id in list(self.active_executions.keys()):
            asyncio.create_task(self.cancel_execution(execution_id, "System shutdown"))
        
        # Shutdown thread pool
        self.executor.shutdown(wait=True)
        
        logger.info("Workflow execution engine shutdown complete")