"""
Logic Engine API Router

This router provides RESTful API endpoints for logic engine functionality
including rule management, rule execution, rule chains, and performance monitoring.

Endpoints:
- GET /logic/health - Engine health check
- GET /logic/rules - List all rules
- POST /logic/rules - Create new rule
- GET /logic/rules/{rule_id} - Get rule information
- PUT /logic/rules/{rule_id} - Update rule
- DELETE /logic/rules/{rule_id} - Delete rule
- POST /logic/rules/{rule_id}/execute - Execute rule
- GET /logic/chains - List all rule chains
- POST /logic/chains - Create new rule chain
- GET /logic/chains/{chain_id} - Get chain information
- POST /logic/chains/{chain_id}/execute - Execute rule chain
- GET /logic/performance - Get performance metrics
- GET /logic/statistics - Get detailed statistics
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from pydantic import BaseModel, Field

from services.logic_engine import (
    LogicEngine,
    Rule,
    RuleChain,
    RuleExecution,
    RuleType,
    RuleStatus,
    ExecutionStatus,
    DataContext
)

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/logic", tags=["Logic Engine"])

# Initialize service
logic_engine = LogicEngine()


# Pydantic models for request/response
class RuleCreateRequest(BaseModel):
    """Request model for rule creation."""
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    rule_type: str = Field(..., description="Rule type")
    conditions: List[Dict[str, Any]] = Field(..., description="Rule conditions")
    actions: List[Dict[str, Any]] = Field(..., description="Rule actions")
    priority: int = Field(1, description="Rule priority")
    tags: Optional[List[str]] = Field(None, description="Rule tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class RuleUpdateRequest(BaseModel):
    """Request model for rule updates."""
    name: Optional[str] = Field(None, description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    rule_type: Optional[str] = Field(None, description="Rule type")
    conditions: Optional[List[Dict[str, Any]]] = Field(None, description="Rule conditions")
    actions: Optional[List[Dict[str, Any]]] = Field(None, description="Rule actions")
    priority: Optional[int] = Field(None, description="Rule priority")
    status: Optional[str] = Field(None, description="Rule status")
    tags: Optional[List[str]] = Field(None, description="Rule tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class RuleResponse(BaseModel):
    """Response model for rule information."""
    rule_id: str = Field(..., description="Rule identifier")
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    rule_type: str = Field(..., description="Rule type")
    status: str = Field(..., description="Rule status")
    priority: int = Field(..., description="Rule priority")
    version: str = Field(..., description="Rule version")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    tags: List[str] = Field(..., description="Rule tags")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")
    execution_count: int = Field(..., description="Total executions")
    success_count: int = Field(..., description="Successful executions")
    error_count: int = Field(..., description="Failed executions")
    avg_execution_time: float = Field(..., description="Average execution time")


class RuleExecutionRequest(BaseModel):
    """Request model for rule execution."""
    data: Dict[str, Any] = Field(..., description="Input data")
    context: Optional[Dict[str, Any]] = Field(None, description="Execution context")


class RuleExecutionResponse(BaseModel):
    """Response model for rule execution result."""
    execution_id: str = Field(..., description="Execution identifier")
    rule_id: str = Field(..., description="Rule identifier")
    input_data: Dict[str, Any] = Field(..., description="Input data")
    output_data: Dict[str, Any] = Field(..., description="Output data")
    status: str = Field(..., description="Execution status")
    execution_time: float = Field(..., description="Execution time in seconds")
    error_message: Optional[str] = Field(None, description="Error message")
    timestamp: str = Field(..., description="Execution timestamp")
    metadata: Dict[str, Any] = Field(..., description="Execution metadata")


class RuleChainCreateRequest(BaseModel):
    """Request model for rule chain creation."""
    name: str = Field(..., description="Chain name")
    description: str = Field(..., description="Chain description")
    rules: List[str] = Field(..., description="List of rule IDs")
    execution_order: str = Field("sequential", description="Execution order")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class RuleChainResponse(BaseModel):
    """Response model for rule chain information."""
    chain_id: str = Field(..., description="Chain identifier")
    name: str = Field(..., description="Chain name")
    description: str = Field(..., description="Chain description")
    rules: List[str] = Field(..., description="List of rule IDs")
    execution_order: str = Field(..., description="Execution order")
    status: str = Field(..., description="Chain status")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")


class RuleChainExecutionRequest(BaseModel):
    """Request model for rule chain execution."""
    data: Dict[str, Any] = Field(..., description="Input data")
    context: Optional[Dict[str, Any]] = Field(None, description="Execution context")


class RuleChainExecutionResponse(BaseModel):
    """Response model for rule chain execution result."""
    chain_id: str = Field(..., description="Chain identifier")
    executions: List[RuleExecutionResponse] = Field(..., description="Execution results")
    total_executions: int = Field(..., description="Total executions")
    successful_executions: int = Field(..., description="Successful executions")
    failed_executions: int = Field(..., description="Failed executions")
    total_execution_time: float = Field(..., description="Total execution time")
    status: str = Field(..., description="Overall execution status")


class PerformanceMetricsResponse(BaseModel):
    """Response model for performance metrics."""
    total_executions: int = Field(..., description="Total executions")
    successful_executions: int = Field(..., description="Successful executions")
    failed_executions: int = Field(..., description="Failed executions")
    success_rate: float = Field(..., description="Success rate percentage")
    average_execution_time: float = Field(..., description="Average execution time")
    total_rules: int = Field(..., description="Total rules")
    active_rules: int = Field(..., description="Active rules")
    total_chains: int = Field(..., description="Total rule chains")
    active_chains: int = Field(..., description="Active rule chains")


class StatisticsResponse(BaseModel):
    """Response model for detailed statistics."""
    rules_by_type: Dict[str, int] = Field(..., description="Rules by type")
    rules_by_status: Dict[str, int] = Field(..., description="Rules by status")
    top_performing_rules: List[Dict[str, Any]] = Field(..., description="Top performing rules")
    recent_executions: List[Dict[str, Any]] = Field(..., description="Recent executions")
    execution_trends: Dict[str, Any] = Field(..., description="Execution trends")


@router.get("/health")
async def get_engine_health():
    """
    Get logic engine health status.
    
    Returns:
        Engine health information
    """
    try:
        logger.info("Getting logic engine health status")
        
        # Get performance metrics as health indicator
        metrics = logic_engine.get_performance_metrics()
        
        health_status = {
            "status": "healthy" if metrics['success_rate'] > 95 else "degraded",
            "total_rules": metrics['total_rules'],
            "active_rules": metrics['active_rules'],
            "total_chains": metrics['total_chains'],
            "active_chains": metrics['active_chains'],
            "success_rate": metrics['success_rate'],
            "average_execution_time": metrics['average_execution_time']
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/rules", response_model=List[RuleResponse])
async def list_rules(rule_type: Optional[str] = None, status: Optional[str] = None,
                     tags: Optional[str] = None):
    """
    List all rules with optional filtering.
    
    Args:
        rule_type: Filter by rule type
        status: Filter by status
        tags: Filter by tags (comma-separated)
        
    Returns:
        List of rules
    """
    try:
        logger.info("Getting list of rules")
        
        # Convert parameters to enums
        rule_type_enum = None
        if rule_type:
            try:
                rule_type_enum = RuleType(rule_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid rule type: {rule_type}")
        
        status_enum = None
        if status:
            try:
                status_enum = RuleStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        tags_list = None
        if tags:
            tags_list = [tag.strip() for tag in tags.split(',')]
        
        rules = logic_engine.list_rules(rule_type_enum, status_enum, tags_list)
        
        return [
            RuleResponse(
                rule_id=rule.rule_id,
                name=rule.name,
                description=rule.description,
                rule_type=rule.rule_type.value,
                status=rule.status.value,
                priority=rule.priority,
                version=rule.version,
                created_at=rule.created_at.isoformat(),
                updated_at=rule.updated_at.isoformat(),
                tags=rule.tags,
                metadata=rule.metadata,
                execution_count=rule.execution_count,
                success_count=rule.success_count,
                error_count=rule.error_count,
                avg_execution_time=rule.avg_execution_time
            )
            for rule in rules
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list rules: {e}")
        raise HTTPException(status_code=500, detail=f"Rule listing failed: {str(e)}")


@router.post("/rules", response_model=Dict[str, str])
async def create_rule(request: RuleCreateRequest):
    """
    Create a new rule.
    
    Args:
        request: Rule creation request
        
    Returns:
        Created rule information
    """
    try:
        logger.info(f"Creating rule: {request.name}")
        
        # Convert rule type
        try:
            rule_type = RuleType(request.rule_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid rule type: {request.rule_type}")
        
        rule_id = logic_engine.create_rule(
            name=request.name,
            description=request.description,
            rule_type=rule_type,
            conditions=request.conditions,
            actions=request.actions,
            priority=request.priority,
            tags=request.tags,
            metadata=request.metadata
        )
        
        logger.info(f"Rule {rule_id} created successfully")
        
        return {
            "rule_id": rule_id,
            "name": request.name,
            "status": "created",
            "created_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create rule: {e}")
        raise HTTPException(status_code=500, detail=f"Rule creation failed: {str(e)}")


@router.get("/rules/{rule_id}", response_model=RuleResponse)
async def get_rule(rule_id: str):
    """
    Get information about a specific rule.
    
    Args:
        rule_id: Rule identifier
        
    Returns:
        Rule information
    """
    try:
        logger.info(f"Getting rule information for {rule_id}")
        
        rule = logic_engine.get_rule(rule_id)
        
        if not rule:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
        
        return RuleResponse(
            rule_id=rule.rule_id,
            name=rule.name,
            description=rule.description,
            rule_type=rule.rule_type.value,
            status=rule.status.value,
            priority=rule.priority,
            version=rule.version,
            created_at=rule.created_at.isoformat(),
            updated_at=rule.updated_at.isoformat(),
            tags=rule.tags,
            metadata=rule.metadata,
            execution_count=rule.execution_count,
            success_count=rule.success_count,
            error_count=rule.error_count,
            avg_execution_time=rule.avg_execution_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get rule info for {rule_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Rule info retrieval failed: {str(e)}")


@router.put("/rules/{rule_id}")
async def update_rule(rule_id: str, request: RuleUpdateRequest):
    """
    Update an existing rule.
    
    Args:
        rule_id: Rule identifier
        request: Rule update request
        
    Returns:
        Update result
    """
    try:
        logger.info(f"Updating rule: {rule_id}")
        
        # Build updates dictionary
        updates = {}
        for field, value in request.dict(exclude_unset=True).items():
            if field == 'rule_type' and value:
                try:
                    updates[field] = RuleType(value)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid rule type: {value}")
            elif field == 'status' and value:
                try:
                    updates[field] = RuleStatus(value)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid status: {value}")
            else:
                updates[field] = value
        
        success = logic_engine.update_rule(rule_id, updates)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
        
        logger.info(f"Rule {rule_id} updated successfully")
        
        return {
            "rule_id": rule_id,
            "status": "updated",
            "updated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Rule update failed: {str(e)}")


@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str):
    """
    Delete a rule.
    
    Args:
        rule_id: Rule identifier
        
    Returns:
        Deletion result
    """
    try:
        logger.info(f"Deleting rule: {rule_id}")
        
        success = logic_engine.delete_rule(rule_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
        
        logger.info(f"Rule {rule_id} deleted successfully")
        
        return {
            "rule_id": rule_id,
            "status": "deleted",
            "deleted_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Rule deletion failed: {str(e)}")


@router.post("/rules/{rule_id}/execute", response_model=RuleExecutionResponse)
async def execute_rule(rule_id: str, request: RuleExecutionRequest):
    """
    Execute a specific rule.
    
    Args:
        rule_id: Rule identifier
        request: Execution request
        
    Returns:
        Execution result
    """
    try:
        logger.info(f"Executing rule: {rule_id}")
        
        # Create execution context if provided
        context = None
        if request.context:
            context = DataContext(
                data=request.data,
                variables=request.context.get('variables', {}),
                functions=logic_engine.builtin_functions,
                metadata=request.context.get('metadata', {})
            )
        
        execution = logic_engine.execute_rule(rule_id, request.data, context)
        
        return RuleExecutionResponse(
            execution_id=execution.execution_id,
            rule_id=execution.rule_id,
            input_data=execution.input_data,
            output_data=execution.output_data,
            status=execution.status.value,
            execution_time=execution.execution_time,
            error_message=execution.error_message,
            timestamp=execution.timestamp.isoformat(),
            metadata=execution.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Rule execution failed: {str(e)}")


@router.get("/chains", response_model=List[RuleChainResponse])
async def list_rule_chains():
    """
    List all rule chains.
    
    Returns:
        List of rule chains
    """
    try:
        logger.info("Getting list of rule chains")
        
        chains = list(logic_engine.rule_chains.values())
        
        return [
            RuleChainResponse(
                chain_id=chain.chain_id,
                name=chain.name,
                description=chain.description,
                rules=chain.rules,
                execution_order=chain.execution_order,
                status=chain.status.value,
                created_at=chain.created_at.isoformat(),
                updated_at=chain.updated_at.isoformat(),
                metadata=chain.metadata
            )
            for chain in chains
        ]
        
    except Exception as e:
        logger.error(f"Failed to list rule chains: {e}")
        raise HTTPException(status_code=500, detail=f"Rule chain listing failed: {str(e)}")


@router.post("/chains", response_model=Dict[str, str])
async def create_rule_chain(request: RuleChainCreateRequest):
    """
    Create a new rule chain.
    
    Args:
        request: Rule chain creation request
        
    Returns:
        Created chain information
    """
    try:
        logger.info(f"Creating rule chain: {request.name}")
        
        chain_id = logic_engine.create_rule_chain(
            name=request.name,
            description=request.description,
            rules=request.rules,
            execution_order=request.execution_order,
            metadata=request.metadata
        )
        
        logger.info(f"Rule chain {chain_id} created successfully")
        
        return {
            "chain_id": chain_id,
            "name": request.name,
            "status": "created",
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to create rule chain: {e}")
        raise HTTPException(status_code=500, detail=f"Rule chain creation failed: {str(e)}")


@router.get("/chains/{chain_id}", response_model=RuleChainResponse)
async def get_rule_chain(chain_id: str):
    """
    Get information about a specific rule chain.
    
    Args:
        chain_id: Chain identifier
        
    Returns:
        Rule chain information
    """
    try:
        logger.info(f"Getting rule chain information for {chain_id}")
        
        chain = logic_engine.rule_chains.get(chain_id)
        
        if not chain:
            raise HTTPException(status_code=404, detail=f"Rule chain {chain_id} not found")
        
        return RuleChainResponse(
            chain_id=chain.chain_id,
            name=chain.name,
            description=chain.description,
            rules=chain.rules,
            execution_order=chain.execution_order,
            status=chain.status.value,
            created_at=chain.created_at.isoformat(),
            updated_at=chain.updated_at.isoformat(),
            metadata=chain.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get rule chain info for {chain_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Rule chain info retrieval failed: {str(e)}")


@router.post("/chains/{chain_id}/execute", response_model=RuleChainExecutionResponse)
async def execute_rule_chain(chain_id: str, request: RuleChainExecutionRequest):
    """
    Execute a rule chain.
    
    Args:
        chain_id: Chain identifier
        request: Execution request
        
    Returns:
        Execution results
    """
    try:
        logger.info(f"Executing rule chain: {chain_id}")
        
        # Create execution context if provided
        context = None
        if request.context:
            context = DataContext(
                data=request.data,
                variables=request.context.get('variables', {}),
                functions=logic_engine.builtin_functions,
                metadata=request.context.get('metadata', {})
            )
        
        executions = logic_engine.execute_rule_chain(chain_id, request.data, context)
        
        # Calculate summary statistics
        total_executions = len(executions)
        successful_executions = len([e for e in executions if e.status == ExecutionStatus.SUCCESS])
        failed_executions = total_executions - successful_executions
        total_execution_time = sum(e.execution_time for e in executions)
        
        # Determine overall status
        if failed_executions == 0:
            overall_status = "success"
        elif successful_executions == 0:
            overall_status = "failed"
        else:
            overall_status = "partial"
        
        return RuleChainExecutionResponse(
            chain_id=chain_id,
            executions=[
                RuleExecutionResponse(
                    execution_id=e.execution_id,
                    rule_id=e.rule_id,
                    input_data=e.input_data,
                    output_data=e.output_data,
                    status=e.status.value,
                    execution_time=e.execution_time,
                    error_message=e.error_message,
                    timestamp=e.timestamp.isoformat(),
                    metadata=e.metadata
                )
                for e in executions
            ],
            total_executions=total_executions,
            successful_executions=successful_executions,
            failed_executions=failed_executions,
            total_execution_time=total_execution_time,
            status=overall_status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute rule chain {chain_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Rule chain execution failed: {str(e)}")


@router.get("/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics():
    """
    Get logic engine performance metrics.
    
    Returns:
        Performance metrics
    """
    try:
        logger.info("Getting performance metrics")
        
        metrics = logic_engine.get_performance_metrics()
        
        return PerformanceMetricsResponse(**metrics)
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Performance metrics retrieval failed: {str(e)}")


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """
    Get detailed statistics about rules and executions.
    
    Returns:
        Detailed statistics
    """
    try:
        logger.info("Getting detailed statistics")
        
        # Get rules by type
        rules_by_type = {}
        rules_by_status = {}
        
        for rule in logic_engine.rules.values():
            rule_type = rule.rule_type.value
            rule_status = rule.status.value
            
            rules_by_type[rule_type] = rules_by_type.get(rule_type, 0) + 1
            rules_by_status[rule_status] = rules_by_status.get(rule_status, 0) + 1
        
        # Get top performing rules
        top_performing_rules = []
        for rule in logic_engine.rules.values():
            if rule.execution_count > 0:
                success_rate = (rule.success_count / rule.execution_count * 100)
                top_performing_rules.append({
                    'rule_id': rule.rule_id,
                    'name': rule.name,
                    'execution_count': rule.execution_count,
                    'success_rate': success_rate,
                    'avg_execution_time': rule.avg_execution_time
                })
        
        # Sort by success rate
        top_performing_rules.sort(key=lambda x: x['success_rate'], reverse=True)
        top_performing_rules = top_performing_rules[:10]  # Top 10
        
        # Get execution trends (simplified)
        execution_trends = {
            'total_executions': logic_engine.total_executions,
            'success_rate': (logic_engine.successful_executions / logic_engine.total_executions * 100) if logic_engine.total_executions > 0 else 0,
            'avg_execution_time': logic_engine.average_execution_time
        }
        
        return StatisticsResponse(
            rules_by_type=rules_by_type,
            rules_by_status=rules_by_status,
            top_performing_rules=top_performing_rules,
            recent_executions=[],  # Would need to query database for recent executions
            execution_trends=execution_trends
        )
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Statistics retrieval failed: {str(e)}")


@router.get("/rules/{rule_id}/statistics")
async def get_rule_statistics(rule_id: str):
    """
    Get statistics for a specific rule.
    
    Args:
        rule_id: Rule identifier
        
    Returns:
        Rule statistics
    """
    try:
        logger.info(f"Getting statistics for rule: {rule_id}")
        
        stats = logic_engine.get_rule_statistics(rule_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get statistics for rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Rule statistics retrieval failed: {str(e)}")


@router.get("/rules/types")
async def get_rule_types():
    """
    Get all available rule types.
    
    Returns:
        List of rule types with descriptions
    """
    rule_types = [
        {
            "type": RuleType.CONDITIONAL.value,
            "name": "Conditional Rule",
            "description": "Rules that evaluate conditions and execute actions based on results",
            "examples": ["Data validation", "Business logic", "Decision making"]
        },
        {
            "type": RuleType.TRANSFORMATION.value,
            "name": "Transformation Rule",
            "description": "Rules that transform data from one format to another",
            "examples": ["Data formatting", "Type conversion", "Field mapping"]
        },
        {
            "type": RuleType.VALIDATION.value,
            "name": "Validation Rule",
            "description": "Rules that validate data integrity and business rules",
            "examples": ["Input validation", "Business rule validation", "Data quality checks"]
        },
        {
            "type": RuleType.WORKFLOW.value,
            "name": "Workflow Rule",
            "description": "Rules that orchestrate complex workflows and processes",
            "examples": ["Process automation", "Task routing", "State management"]
        },
        {
            "type": RuleType.ANALYSIS.value,
            "name": "Analysis Rule",
            "description": "Rules that perform data analysis and pattern recognition",
            "examples": ["Trend analysis", "Anomaly detection", "Predictive modeling"]
        }
    ]
    
    return {"rule_types": rule_types}


@router.get("/rules/operators")
async def get_operators():
    """
    Get all available condition operators.
    
    Returns:
        List of operators with descriptions
    """
    operators = [
        {
            "operator": "equals",
            "name": "Equals",
            "description": "Check if value equals the expected value",
            "example": "field equals 'value'"
        },
        {
            "operator": "not_equals",
            "name": "Not Equals",
            "description": "Check if value does not equal the expected value",
            "example": "field not_equals 'value'"
        },
        {
            "operator": "greater_than",
            "name": "Greater Than",
            "description": "Check if value is greater than the expected value",
            "example": "field greater_than 10"
        },
        {
            "operator": "greater_than_or_equal",
            "name": "Greater Than or Equal",
            "description": "Check if value is greater than or equal to the expected value",
            "example": "field greater_than_or_equal 10"
        },
        {
            "operator": "less_than",
            "name": "Less Than",
            "description": "Check if value is less than the expected value",
            "example": "field less_than 10"
        },
        {
            "operator": "less_than_or_equal",
            "name": "Less Than or Equal",
            "description": "Check if value is less than or equal to the expected value",
            "example": "field less_than_or_equal 10"
        },
        {
            "operator": "contains",
            "name": "Contains",
            "description": "Check if value contains the expected value",
            "example": "field contains 'substring'"
        },
        {
            "operator": "not_contains",
            "name": "Not Contains",
            "description": "Check if value does not contain the expected value",
            "example": "field not_contains 'substring'"
        },
        {
            "operator": "starts_with",
            "name": "Starts With",
            "description": "Check if value starts with the expected value",
            "example": "field starts_with 'prefix'"
        },
        {
            "operator": "ends_with",
            "name": "Ends With",
            "description": "Check if value ends with the expected value",
            "example": "field ends_with 'suffix'"
        },
        {
            "operator": "is_empty",
            "name": "Is Empty",
            "description": "Check if value is empty or null",
            "example": "field is_empty"
        },
        {
            "operator": "is_not_empty",
            "name": "Is Not Empty",
            "description": "Check if value is not empty",
            "example": "field is_not_empty"
        },
        {
            "operator": "is_null",
            "name": "Is Null",
            "description": "Check if value is null",
            "example": "field is_null"
        },
        {
            "operator": "is_not_null",
            "name": "Is Not Null",
            "description": "Check if value is not null",
            "example": "field is_not_null"
        },
        {
            "operator": "matches",
            "name": "Matches Pattern",
            "description": "Check if value matches a regular expression pattern",
            "example": "field matches '^[A-Z]+$'"
        },
        {
            "operator": "in",
            "name": "In List",
            "description": "Check if value is in a list of expected values",
            "example": "field in ['value1', 'value2', 'value3']"
        },
        {
            "operator": "not_in",
            "name": "Not In List",
            "description": "Check if value is not in a list of expected values",
            "example": "field not_in ['value1', 'value2', 'value3']"
        }
    ]
    
    return {"operators": operators}


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
    logger.error(f"Unhandled exception in logic engine API: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    ) 