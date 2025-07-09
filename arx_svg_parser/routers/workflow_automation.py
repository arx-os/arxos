"""
Workflow Automation API Router

This router provides RESTful API endpoints for workflow automation and orchestration
operations, including workflow creation, execution, monitoring, and scheduling.

Endpoints:
- POST /workflows - Create a new workflow
- GET /workflows - List all workflows
- GET /workflows/{workflow_id} - Get workflow details
- POST /workflows/{workflow_id}/execute - Execute a workflow
- GET /workflows/{workflow_id}/executions - Get workflow executions
- GET /executions/{execution_id} - Get execution status
- POST /executions/{execution_id}/cancel - Cancel execution
- GET /workflows/metrics - Get performance metrics
- GET /workflows/health - Health check
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from pydantic import BaseModel, Field

from services.workflow_automation import (
    WorkflowAutomationService,
    WorkflowType,
    WorkflowStatus,
    StepType,
    ConditionType
)

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/workflows", tags=["Workflow Automation"])

# Initialize service
workflow_service = WorkflowAutomationService()


# Pydantic models for request/response
class WorkflowStepRequest(BaseModel):
    """Request model for workflow step."""
    step_id: str = Field(..., description="Unique step identifier")
    name: str = Field(..., description="Step name")
    step_type: str = Field(..., description="Step type")
    parameters: Dict[str, Any] = Field(..., description="Step parameters")
    conditions: List[Dict[str, Any]] = Field(default=[], description="Step conditions")
    timeout: int = Field(300, description="Step timeout in seconds")
    retry_count: int = Field(3, description="Number of retries")
    retry_delay: int = Field(60, description="Retry delay in seconds")
    parallel: bool = Field(False, description="Whether step can run in parallel")
    required: bool = Field(True, description="Whether step is required")


class WorkflowCreateRequest(BaseModel):
    """Request model for creating a workflow."""
    workflow_id: str = Field(..., description="Unique workflow identifier")
    name: str = Field(..., description="Workflow name")
    description: str = Field(..., description="Workflow description")
    workflow_type: str = Field(..., description="Workflow type")
    steps: List[WorkflowStepRequest] = Field(..., description="Workflow steps")
    triggers: List[Dict[str, Any]] = Field(default=[], description="Workflow triggers")
    schedule: Optional[str] = Field(None, description="Cron schedule expression")
    timeout: int = Field(1800, description="Workflow timeout in seconds")
    max_retries: int = Field(3, description="Maximum retries")
    error_handling: Optional[Dict[str, Any]] = Field(None, description="Error handling configuration")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class WorkflowResponse(BaseModel):
    """Response model for workflow information."""
    workflow_id: str = Field(..., description="Workflow identifier")
    name: str = Field(..., description="Workflow name")
    description: str = Field(..., description="Workflow description")
    workflow_type: str = Field(..., description="Workflow type")
    steps_count: int = Field(..., description="Number of steps")
    timeout: int = Field(..., description="Workflow timeout")
    max_retries: int = Field(..., description="Maximum retries")
    created_at: str = Field(..., description="Creation timestamp")


class WorkflowExecuteRequest(BaseModel):
    """Request model for executing a workflow."""
    context: Optional[Dict[str, Any]] = Field(None, description="Execution context")
    priority: Optional[str] = Field("normal", description="Execution priority")


class WorkflowExecuteResponse(BaseModel):
    """Response model for workflow execution."""
    execution_id: str = Field(..., description="Execution identifier")
    workflow_id: str = Field(..., description="Workflow identifier")
    status: str = Field(..., description="Execution status")
    start_time: str = Field(..., description="Start timestamp")


class ExecutionStatusResponse(BaseModel):
    """Response model for execution status."""
    execution_id: str = Field(..., description="Execution identifier")
    workflow_id: str = Field(..., description="Workflow identifier")
    status: str = Field(..., description="Execution status")
    progress: float = Field(..., description="Progress percentage")
    current_step: Optional[str] = Field(None, description="Current step")
    start_time: str = Field(..., description="Start timestamp")
    end_time: Optional[str] = Field(None, description="End timestamp")
    error: Optional[str] = Field(None, description="Error message")


class ExecutionHistoryResponse(BaseModel):
    """Response model for execution history."""
    workflow_id: str = Field(..., description="Workflow identifier")
    executions: List[Dict[str, Any]] = Field(..., description="List of executions")
    total_executions: int = Field(..., description="Total number of executions")


class MetricsResponse(BaseModel):
    """Response model for performance metrics."""
    metrics: Dict[str, Any] = Field(..., description="Performance metrics")
    active_workflows: int = Field(..., description="Number of active workflows")
    active_executions: int = Field(..., description="Number of active executions")
    database_size: int = Field(..., description="Database size in bytes")


@router.post("/", response_model=WorkflowResponse)
async def create_workflow(request: WorkflowCreateRequest):
    """
    Create a new workflow definition.
    
    This endpoint allows creating custom workflows with steps, conditions,
    triggers, and scheduling options.
    
    Args:
        request: Workflow creation request
        
    Returns:
        Created workflow information
        
    Raises:
        HTTPException: If workflow creation fails
    """
    try:
        logger.info(f"Creating workflow: {request.workflow_id}")
        
        # Validate request data
        if not request.workflow_id:
            raise HTTPException(status_code=400, detail="Workflow ID is required")
        
        if not request.name:
            raise HTTPException(status_code=400, detail="Workflow name is required")
        
        if not request.steps:
            raise HTTPException(status_code=400, detail="At least one step is required")
        
        # Create workflow data
        workflow_data = {
            "workflow_id": request.workflow_id,
            "name": request.name,
            "description": request.description,
            "workflow_type": request.workflow_type,
            "steps": [
                {
                    "step_id": step.step_id,
                    "name": step.name,
                    "step_type": step.step_type,
                    "parameters": step.parameters,
                    "conditions": step.conditions,
                    "timeout": step.timeout,
                    "retry_count": step.retry_count,
                    "retry_delay": step.retry_delay,
                    "parallel": step.parallel,
                    "required": step.required
                }
                for step in request.steps
            ],
            "triggers": request.triggers,
            "schedule": request.schedule,
            "timeout": request.timeout,
            "max_retries": request.max_retries,
            "error_handling": request.error_handling,
            "metadata": request.metadata
        }
        
        # Create workflow
        workflow_id = workflow_service.create_workflow(workflow_data)
        
        # Get workflow details
        workflows = workflow_service.list_workflows()
        workflow = next((w for w in workflows if w['workflow_id'] == workflow_id), None)
        
        if not workflow:
            raise HTTPException(status_code=500, detail="Failed to retrieve created workflow")
        
        logger.info(f"Workflow {workflow_id} created successfully")
        
        return WorkflowResponse(
            workflow_id=workflow['workflow_id'],
            name=workflow['name'],
            description=workflow.get('description', ''),
            workflow_type=workflow['workflow_type'],
            steps_count=workflow['steps_count'],
            timeout=workflow['timeout'],
            max_retries=workflow['max_retries'],
            created_at=datetime.now().isoformat()
        )
        
    except ValueError as e:
        logger.error(f"Workflow creation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Workflow creation failed for {request.workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow creation failed: {str(e)}")


@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows():
    """
    List all available workflows.
    
    This endpoint provides access to all workflow definitions including
    their basic information and configuration.
    
    Returns:
        List of workflow definitions
        
    Raises:
        HTTPException: If workflow listing fails
    """
    try:
        logger.info("Getting workflow list")
        
        workflows = workflow_service.list_workflows()
        
        return [
            WorkflowResponse(
                workflow_id=workflow['workflow_id'],
                name=workflow['name'],
                description=workflow.get('description', ''),
                workflow_type=workflow['workflow_type'],
                steps_count=workflow['steps_count'],
                timeout=workflow['timeout'],
                max_retries=workflow['max_retries'],
                created_at=datetime.now().isoformat()
            )
            for workflow in workflows
        ]
        
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow listing failed: {str(e)}")


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str):
    """
    Get detailed information about a specific workflow.
    
    This endpoint provides comprehensive workflow information including
    steps, triggers, and configuration details.
    
    Args:
        workflow_id: Workflow identifier
        
    Returns:
        Detailed workflow information
        
    Raises:
        HTTPException: If workflow retrieval fails
    """
    try:
        logger.info(f"Getting workflow details for {workflow_id}")
        
        workflows = workflow_service.list_workflows()
        workflow = next((w for w in workflows if w['workflow_id'] == workflow_id), None)
        
        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
        
        return WorkflowResponse(
            workflow_id=workflow['workflow_id'],
            name=workflow['name'],
            description=workflow.get('description', ''),
            workflow_type=workflow['workflow_type'],
            steps_count=workflow['steps_count'],
            timeout=workflow['timeout'],
            max_retries=workflow['max_retries'],
            created_at=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow retrieval failed: {str(e)}")


@router.post("/{workflow_id}/execute", response_model=WorkflowExecuteResponse)
async def execute_workflow(workflow_id: str, request: WorkflowExecuteRequest):
    """
    Execute a workflow.
    
    This endpoint initiates workflow execution with optional context
    and priority settings.
    
    Args:
        workflow_id: Workflow identifier
        request: Execution request with context and priority
        
    Returns:
        Execution information
        
    Raises:
        HTTPException: If workflow execution fails
    """
    try:
        logger.info(f"Executing workflow {workflow_id}")
        
        # Validate workflow exists
        workflows = workflow_service.list_workflows()
        workflow = next((w for w in workflows if w['workflow_id'] == workflow_id), None)
        
        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
        
        # Execute workflow
        execution_id = workflow_service.execute_workflow(
            workflow_id=workflow_id,
            context=request.context or {}
        )
        
        # Get execution status
        status = workflow_service.get_workflow_status(execution_id)
        
        logger.info(f"Workflow execution {execution_id} started for {workflow_id}")
        
        return WorkflowExecuteResponse(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=status['status'],
            start_time=status['start_time']
        )
        
    except ValueError as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Workflow execution failed for {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@router.get("/{workflow_id}/executions", response_model=ExecutionHistoryResponse)
async def get_workflow_executions(workflow_id: str, limit: int = 50):
    """
    Get execution history for a workflow.
    
    This endpoint provides detailed history of workflow executions including
    status, timing, and results.
    
    Args:
        workflow_id: Workflow identifier
        limit: Maximum number of results to return (default: 50)
        
    Returns:
        Workflow execution history
        
    Raises:
        HTTPException: If history retrieval fails
    """
    try:
        logger.info(f"Getting execution history for workflow {workflow_id}")
        
        if limit < 1 or limit > 1000:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
        
        history = workflow_service.get_workflow_history(workflow_id, limit)
        
        return ExecutionHistoryResponse(
            workflow_id=workflow_id,
            executions=history,
            total_executions=len(history)
        )
        
    except Exception as e:
        logger.error(f"Failed to get execution history for {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")


@router.get("/executions/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(execution_id: str):
    """
    Get status of a workflow execution.
    
    This endpoint provides real-time status information about a workflow
    execution including progress and current step.
    
    Args:
        execution_id: Execution identifier
        
    Returns:
        Execution status information
        
    Raises:
        HTTPException: If status retrieval fails
    """
    try:
        logger.info(f"Getting execution status for {execution_id}")
        
        status = workflow_service.get_workflow_status(execution_id)
        
        if 'error' in status:
            raise HTTPException(status_code=404, detail=status['error'])
        
        return ExecutionStatusResponse(
            execution_id=status['execution_id'],
            workflow_id=status['workflow_id'],
            status=status['status'],
            progress=status['progress'],
            current_step=status['current_step'],
            start_time=status['start_time'],
            end_time=status['end_time'],
            error=status['error']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution status for {execution_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")


@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(execution_id: str):
    """
    Cancel a workflow execution.
    
    This endpoint allows cancelling running or pending workflow executions.
    
    Args:
        execution_id: Execution identifier
        
    Returns:
        Cancellation result
        
    Raises:
        HTTPException: If cancellation fails
    """
    try:
        logger.info(f"Cancelling execution {execution_id}")
        
        success = workflow_service.cancel_workflow(execution_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found or cannot be cancelled")
        
        logger.info(f"Execution {execution_id} cancelled successfully")
        
        return {
            "execution_id": execution_id,
            "status": "cancelled",
            "cancelled_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel execution {execution_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Cancellation failed: {str(e)}")


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get workflow automation performance metrics.
    
    This endpoint provides comprehensive performance metrics including
    workflow statistics, execution rates, and system health.
    
    Returns:
        Performance metrics and system statistics
        
    Raises:
        HTTPException: If metrics retrieval fails
    """
    try:
        logger.info("Getting workflow automation metrics")
        
        metrics = workflow_service.get_metrics()
        
        return MetricsResponse(**metrics)
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the workflow automation service.
    
    Returns:
        Service health status
    """
    try:
        # Basic health check
        metrics = workflow_service.get_metrics()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "workflow_automation",
            "database_accessible": True,
            "metrics_available": bool(metrics),
            "active_workflows": metrics.get('active_workflows', 0),
            "active_executions": metrics.get('active_executions', 0)
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "service": "workflow_automation",
                "error": str(e)
            }
        )


@router.get("/types/workflow")
async def get_workflow_types():
    """
    Get all available workflow types.
    
    Returns:
        List of workflow types with descriptions
    """
    workflow_types = [
        {
            "type": WorkflowType.VALIDATION.value,
            "name": "Validation Workflow",
            "description": "Automated validation and quality assurance workflows",
            "use_cases": ["BIM validation", "Data quality checks", "Compliance verification"]
        },
        {
            "type": WorkflowType.EXPORT.value,
            "name": "Export Workflow",
            "description": "Automated data export and format conversion workflows",
            "use_cases": ["Format conversion", "File generation", "Data distribution"]
        },
        {
            "type": WorkflowType.REPORTING.value,
            "name": "Reporting Workflow",
            "description": "Automated reporting and analytics workflows",
            "use_cases": ["Report generation", "Data aggregation", "Analytics processing"]
        },
        {
            "type": WorkflowType.DATA_PROCESSING.value,
            "name": "Data Processing Workflow",
            "description": "Automated data processing and transformation workflows",
            "use_cases": ["Data transformation", "ETL processes", "Data cleaning"]
        },
        {
            "type": WorkflowType.INTEGRATION.value,
            "name": "Integration Workflow",
            "description": "Automated system integration and synchronization workflows",
            "use_cases": ["API integration", "Data synchronization", "System coordination"]
        },
        {
            "type": WorkflowType.CLEANUP.value,
            "name": "Cleanup Workflow",
            "description": "Automated cleanup and maintenance workflows",
            "use_cases": ["Data cleanup", "File maintenance", "System optimization"]
        }
    ]
    
    return {"workflow_types": workflow_types}


@router.get("/types/step")
async def get_step_types():
    """
    Get all available step types.
    
    Returns:
        List of step types with descriptions
    """
    step_types = [
        {
            "type": StepType.VALIDATION.value,
            "name": "Validation Step",
            "description": "Execute validation operations",
            "parameters": ["service", "auto_apply_fixes", "strict_mode"]
        },
        {
            "type": StepType.EXPORT.value,
            "name": "Export Step",
            "description": "Execute export operations",
            "parameters": ["format", "destination", "options"]
        },
        {
            "type": StepType.TRANSFORM.value,
            "name": "Transform Step",
            "description": "Execute data transformation operations",
            "parameters": ["transformations", "input_format", "output_format"]
        },
        {
            "type": StepType.NOTIFY.value,
            "name": "Notify Step",
            "description": "Send notifications",
            "parameters": ["method", "template", "recipients"]
        },
        {
            "type": StepType.CONDITION.value,
            "name": "Condition Step",
            "description": "Evaluate conditions and branch execution",
            "parameters": ["conditions", "true_branch", "false_branch"]
        },
        {
            "type": StepType.LOOP.value,
            "name": "Loop Step",
            "description": "Execute steps in a loop",
            "parameters": ["items", "max_iterations", "loop_body"]
        },
        {
            "type": StepType.PARALLEL.value,
            "name": "Parallel Step",
            "description": "Execute steps in parallel",
            "parameters": ["steps", "max_workers", "timeout"]
        },
        {
            "type": StepType.DELAY.value,
            "name": "Delay Step",
            "description": "Add delay to workflow execution",
            "parameters": ["delay_seconds", "delay_type"]
        },
        {
            "type": StepType.API_CALL.value,
            "name": "API Call Step",
            "description": "Make API calls to external services",
            "parameters": ["endpoint", "method", "data", "headers"]
        },
        {
            "type": StepType.FILE_OPERATION.value,
            "name": "File Operation Step",
            "description": "Perform file operations",
            "parameters": ["operation", "file_path", "options"]
        }
    ]
    
    return {"step_types": step_types}


@router.get("/types/condition")
async def get_condition_types():
    """
    Get all available condition types.
    
    Returns:
        List of condition types with descriptions
    """
    condition_types = [
        {
            "type": ConditionType.EQUALS.value,
            "name": "Equals",
            "description": "Check if field equals value",
            "syntax": {"field": "field_name", "value": "expected_value"}
        },
        {
            "type": ConditionType.NOT_EQUALS.value,
            "name": "Not Equals",
            "description": "Check if field does not equal value",
            "syntax": {"field": "field_name", "value": "unexpected_value"}
        },
        {
            "type": ConditionType.GREATER_THAN.value,
            "name": "Greater Than",
            "description": "Check if field is greater than value",
            "syntax": {"field": "field_name", "value": "threshold"}
        },
        {
            "type": ConditionType.LESS_THAN.value,
            "name": "Less Than",
            "description": "Check if field is less than value",
            "syntax": {"field": "field_name", "value": "threshold"}
        },
        {
            "type": ConditionType.CONTAINS.value,
            "name": "Contains",
            "description": "Check if field contains value",
            "syntax": {"field": "field_name", "value": "substring"}
        },
        {
            "type": ConditionType.NOT_CONTAINS.value,
            "name": "Not Contains",
            "description": "Check if field does not contain value",
            "syntax": {"field": "field_name", "value": "substring"}
        },
        {
            "type": ConditionType.EXISTS.value,
            "name": "Exists",
            "description": "Check if field exists",
            "syntax": {"field": "field_name"}
        },
        {
            "type": ConditionType.NOT_EXISTS.value,
            "name": "Not Exists",
            "description": "Check if field does not exist",
            "syntax": {"field": "field_name"}
        }
    ]
    
    return {"condition_types": condition_types}


# Error handlers
@router.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with detailed error information."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )


@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions with logging."""
    logger.error(f"Unhandled exception in workflow automation API: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    ) 