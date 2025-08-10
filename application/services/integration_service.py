"""
Enterprise Integration Service.

Application service for managing enterprise integrations, connectors,
data transformations, and integration flows.
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone, timedelta
from dataclasses import asdict
import json
import uuid

from domain.entities.integration_entity import (
    IntegrationConnector, IntegrationEndpoint, DataTransformation,
    IntegrationFlow, IntegrationType, ConnectorStatus, DataFormat,
    TransformationType, IntegrationDirection
)
from application.dto.integration_dto import (
    CreateConnectorRequest, CreateConnectorResponse,
    UpdateConnectorRequest, UpdateConnectorResponse,
    ConnectorResponse, ListConnectorsResponse,
    ExecuteConnectorRequest, ExecuteConnectorResponse,
    CreateFlowRequest, CreateFlowResponse,
    FlowExecutionResponse, TestConnectorRequest, TestConnectorResponse,
    ConnectorStatsResponse, IntegrationHealthResponse
)
from infrastructure.services.integration_engine import IntegrationEngine
from infrastructure.logging.structured_logging import get_logger, log_context
from infrastructure.performance.monitoring import monitor_performance, performance_monitor
from infrastructure.security.authorization import require_permission, Permission
from infrastructure.services.notification_service import NotificationService


logger = get_logger(__name__)


class IntegrationService:
    """Enterprise integration management service."""
    
    def __init__(self, integration_engine: IntegrationEngine,
                 notification_service: NotificationService = None):
        self.integration_engine = integration_engine
        self.notification_service = notification_service
        
        # In-memory storage (production would use database)
        self.connectors: Dict[str, IntegrationConnector] = {}
        self.flows: Dict[str, IntegrationFlow] = {}
        
        # Service statistics
        self.service_stats = {
            "total_connectors": 0,
            "active_connectors": 0,
            "total_flows": 0,
            "active_flows": 0,
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0
        }
    
    @monitor_performance("create_connector")
    @require_permission(Permission.MANAGE_INTEGRATIONS)
    def create_connector(self, request: CreateConnectorRequest, created_by: str) -> CreateConnectorResponse:
        """Create new integration connector."""
        with log_context(operation="create_connector", user=created_by):
            try:
                # Create source endpoint if provided
                source_endpoint = None
                if request.source_endpoint:
                    source_endpoint = IntegrationEndpoint(
                        id=str(uuid.uuid4()),
                        name=request.source_endpoint["name"],
                        url=request.source_endpoint["url"],
                        integration_type=IntegrationType(request.source_endpoint["integration_type"]),
                        data_format=DataFormat(request.source_endpoint["data_format"]),
                        authentication=request.source_endpoint.get("authentication", {}),
                        headers=request.source_endpoint.get("headers", {}),
                        parameters=request.source_endpoint.get("parameters", {}),
                        timeout_seconds=request.source_endpoint.get("timeout_seconds", 30),
                        retry_config=request.source_endpoint.get("retry_config", {}),
                        rate_limit=request.source_endpoint.get("rate_limit", {}),
                        enabled=request.source_endpoint.get("enabled", True)
                    )
                
                # Create target endpoint if provided
                target_endpoint = None
                if request.target_endpoint:
                    target_endpoint = IntegrationEndpoint(
                        id=str(uuid.uuid4()),
                        name=request.target_endpoint["name"],
                        url=request.target_endpoint["url"],
                        integration_type=IntegrationType(request.target_endpoint["integration_type"]),
                        data_format=DataFormat(request.target_endpoint["data_format"]),
                        authentication=request.target_endpoint.get("authentication", {}),
                        headers=request.target_endpoint.get("headers", {}),
                        parameters=request.target_endpoint.get("parameters", {}),
                        timeout_seconds=request.target_endpoint.get("timeout_seconds", 30),
                        retry_config=request.target_endpoint.get("retry_config", {}),
                        rate_limit=request.target_endpoint.get("rate_limit", {}),
                        enabled=request.target_endpoint.get("enabled", True)
                    )
                
                # Create transformations
                transformations = []
                for i, transform_data in enumerate(request.transformations):
                    transformation = DataTransformation(
                        id=str(uuid.uuid4()),
                        name=transform_data["name"],
                        transformation_type=TransformationType(transform_data["transformation_type"]),
                        source_field=transform_data.get("source_field"),
                        target_field=transform_data.get("target_field"),
                        transformation_logic=transform_data.get("transformation_logic", {}),
                        conditions=transform_data.get("conditions", []),
                        enabled=transform_data.get("enabled", True),
                        order=transform_data.get("order", i)
                    )
                    transformations.append(transformation)
                
                # Create connector
                connector = IntegrationConnector(
                    name=request.name,
                    description=request.description,
                    connector_type=IntegrationType(request.connector_type),
                    direction=IntegrationDirection(request.direction),
                    status=ConnectorStatus.INACTIVE,
                    source_endpoint=source_endpoint,
                    target_endpoint=target_endpoint,
                    input_format=DataFormat(request.input_format),
                    output_format=DataFormat(request.output_format),
                    transformations=transformations,
                    error_handling=request.error_handling,
                    dead_letter_queue=request.dead_letter_queue,
                    health_check_config=request.health_check_config,
                    monitoring_enabled=request.monitoring_enabled,
                    created_by=created_by,
                    tags=request.tags
                )
                
                # Validate connector
                validation_errors = connector.validate()
                if validation_errors:
                    return CreateConnectorResponse(
                        success=False,
                        message=f"Connector validation failed: {'; '.join(validation_errors)}"
                    )
                
                # Store connector
                self.connectors[connector.id] = connector
                self.service_stats["total_connectors"] += 1
                
                # Register with integration engine
                self.integration_engine.register_connector(connector)
                
                # Auto-activate if requested
                if request.auto_activate:
                    connector.status = ConnectorStatus.ACTIVE
                    self.service_stats["active_connectors"] += 1
                
                logger.info(f"Created integration connector: {connector.name}")
                
                return CreateConnectorResponse(
                    success=True,
                    connector_id=connector.id,
                    message="Integration connector created successfully",
                    connector=connector.to_dict()
                )
                
            except Exception as e:
                logger.error(f"Failed to create integration connector: {e}")
                return CreateConnectorResponse(
                    success=False,
                    message=f"Failed to create connector: {str(e)}"
                )
    
    @monitor_performance("update_connector")
    @require_permission(Permission.MANAGE_INTEGRATIONS)
    def update_connector(self, connector_id: str, request: UpdateConnectorRequest) -> UpdateConnectorResponse:
        """Update existing integration connector."""
        with log_context(operation="update_connector", connector_id=connector_id):
            try:
                if connector_id not in self.connectors:
                    return UpdateConnectorResponse(
                        success=False,
                        message="Connector not found"
                    )
                
                connector = self.connectors[connector_id]
                updated_fields = []
                
                # Update basic fields
                if request.name is not None:
                    connector.name = request.name
                    updated_fields.append("name")
                
                if request.description is not None:
                    connector.description = request.description
                    updated_fields.append("description")
                
                if request.status is not None:
                    old_status = connector.status
                    connector.status = ConnectorStatus(request.status)
                    updated_fields.append("status")
                    
                    # Update active connectors count
                    if old_status != ConnectorStatus.ACTIVE and connector.status == ConnectorStatus.ACTIVE:
                        self.service_stats["active_connectors"] += 1
                    elif old_status == ConnectorStatus.ACTIVE and connector.status != ConnectorStatus.ACTIVE:
                        self.service_stats["active_connectors"] -= 1
                
                if request.tags is not None:
                    connector.tags = request.tags
                    updated_fields.append("tags")
                
                if request.error_handling is not None:
                    connector.error_handling = request.error_handling
                    updated_fields.append("error_handling")
                
                if request.monitoring_enabled is not None:
                    connector.monitoring_enabled = request.monitoring_enabled
                    updated_fields.append("monitoring_enabled")
                
                # Update transformations if provided
                if request.transformations is not None:
                    transformations = []
                    for i, transform_data in enumerate(request.transformations):
                        transformation = DataTransformation(
                            id=transform_data.get("id", str(uuid.uuid4())),
                            name=transform_data["name"],
                            transformation_type=TransformationType(transform_data["transformation_type"]),
                            source_field=transform_data.get("source_field"),
                            target_field=transform_data.get("target_field"),
                            transformation_logic=transform_data.get("transformation_logic", {}),
                            conditions=transform_data.get("conditions", []),
                            enabled=transform_data.get("enabled", True),
                            order=transform_data.get("order", i)
                        )
                        transformations.append(transformation)
                    
                    connector.transformations = transformations
                    updated_fields.append("transformations")
                
                # Update timestamp
                connector.updated_at = datetime.now(timezone.utc)
                
                # Re-validate connector
                validation_errors = connector.validate()
                if validation_errors:
                    return UpdateConnectorResponse(
                        success=False,
                        message=f"Connector validation failed: {'; '.join(validation_errors)}"
                    )
                
                # Update in integration engine
                self.integration_engine.update_connector(connector)
                
                logger.info(f"Updated integration connector: {connector.name}")
                
                return UpdateConnectorResponse(
                    success=True,
                    message="Integration connector updated successfully",
                    updated_fields=updated_fields
                )
                
            except Exception as e:
                logger.error(f"Failed to update integration connector: {e}")
                return UpdateConnectorResponse(
                    success=False,
                    message=f"Failed to update connector: {str(e)}"
                )
    
    @monitor_performance("get_connector")
    @require_permission(Permission.VIEW_INTEGRATIONS)
    def get_connector(self, connector_id: str) -> ConnectorResponse:
        """Get integration connector by ID."""
        try:
            if connector_id not in self.connectors:
                return ConnectorResponse(
                    success=False,
                    message="Connector not found"
                )
            
            connector = self.connectors[connector_id]
            
            return ConnectorResponse(
                success=True,
                connector=connector.to_dict()
            )
            
        except Exception as e:
            logger.error(f"Failed to get connector: {e}")
            return ConnectorResponse(
                success=False,
                message=f"Failed to get connector: {str(e)}"
            )
    
    @monitor_performance("list_connectors")
    @require_permission(Permission.VIEW_INTEGRATIONS)
    def list_connectors(self, status: Optional[str] = None, connector_type: Optional[str] = None,
                       page: int = 1, page_size: int = 50) -> ListConnectorsResponse:
        """List integration connectors with filtering."""
        try:
            connectors = list(self.connectors.values())
            
            # Apply filters
            if status:
                connectors = [c for c in connectors if c.status.value == status]
            
            if connector_type:
                connectors = [c for c in connectors if c.connector_type.value == connector_type]
            
            # Pagination
            total_count = len(connectors)
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_connectors = connectors[start_index:end_index]
            
            # Convert to dict format
            connector_dicts = [c.to_dict() for c in paginated_connectors]
            
            return ListConnectorsResponse(
                success=True,
                connectors=connector_dicts,
                total_count=total_count,
                page=page,
                page_size=page_size,
                total_pages=(total_count + page_size - 1) // page_size,
                has_next=end_index < total_count,
                has_prev=page > 1
            )
            
        except Exception as e:
            logger.error(f"Failed to list connectors: {e}")
            return ListConnectorsResponse(
                success=False,
                message=f"Failed to list connectors: {str(e)}"
            )
    
    @monitor_performance("execute_connector")
    @require_permission(Permission.EXECUTE_INTEGRATIONS)
    async def execute_connector(self, request: ExecuteConnectorRequest, executed_by: str) -> ExecuteConnectorResponse:
        """Execute integration connector."""
        with log_context(operation="execute_connector", connector_id=request.connector_id, user=executed_by):
            try:
                if request.connector_id not in self.connectors:
                    return ExecuteConnectorResponse(
                        success=False,
                        message="Connector not found"
                    )
                
                connector = self.connectors[request.connector_id]
                
                # Check if connector can be executed
                if not connector.can_execute():
                    return ExecuteConnectorResponse(
                        success=False,
                        message="Connector cannot be executed (inactive or has validation errors)"
                    )
                
                # Execute connector
                execution_result = await self.integration_engine.execute_connector(
                    connector, request.input_data, request.execution_context
                )
                
                # Update statistics
                self.service_stats["total_executions"] += 1
                if execution_result["success"]:
                    self.service_stats["successful_executions"] += 1
                else:
                    self.service_stats["failed_executions"] += 1
                
                logger.info(f"Executed connector: {connector.name}, success: {execution_result['success']}")
                
                return ExecuteConnectorResponse(
                    success=execution_result["success"],
                    execution_id=execution_result.get("execution_id"),
                    output_data=execution_result.get("output_data"),
                    execution_time_ms=execution_result.get("execution_time_ms"),
                    message=execution_result.get("message", "Connector executed successfully" if execution_result["success"] else "Connector execution failed"),
                    error_details=execution_result.get("error_details")
                )
                
            except Exception as e:
                logger.error(f"Failed to execute connector: {e}")
                return ExecuteConnectorResponse(
                    success=False,
                    message=f"Failed to execute connector: {str(e)}"
                )
    
    @monitor_performance("test_connector")
    @require_permission(Permission.EXECUTE_INTEGRATIONS)
    async def test_connector(self, request: TestConnectorRequest) -> TestConnectorResponse:
        """Test integration connector configuration."""
        try:
            if request.connector_id not in self.connectors:
                return TestConnectorResponse(
                    success=False,
                    message="Connector not found"
                )
            
            connector = self.connectors[request.connector_id]
            
            # Test connector
            test_result = await self.integration_engine.test_connector(
                connector, request.test_data, request.test_options
            )
            
            return TestConnectorResponse(
                success=test_result["success"],
                test_result=test_result.get("test_result", "unknown"),
                validation_results=test_result.get("validation_results", {}),
                connectivity_test=test_result.get("connectivity_test", {}),
                transformation_test=test_result.get("transformation_test", {}),
                performance_metrics=test_result.get("performance_metrics", {}),
                recommendations=test_result.get("recommendations", []),
                message=test_result.get("message", "Connector test completed")
            )
            
        except Exception as e:
            logger.error(f"Failed to test connector: {e}")
            return TestConnectorResponse(
                success=False,
                message=f"Failed to test connector: {str(e)}"
            )
    
    @monitor_performance("create_flow")
    @require_permission(Permission.MANAGE_INTEGRATIONS)
    def create_flow(self, request: CreateFlowRequest, created_by: str) -> CreateFlowResponse:
        """Create integration flow."""
        with log_context(operation="create_flow", user=created_by):
            try:
                # Validate that all connectors exist
                for connector_id in request.connector_ids:
                    if connector_id not in self.connectors:
                        return CreateFlowResponse(
                            success=False,
                            message=f"Connector {connector_id} not found"
                        )
                
                # Create flow
                flow = IntegrationFlow(
                    name=request.name,
                    description=request.description,
                    connectors=request.connector_ids,
                    trigger_config=request.trigger_config,
                    error_handling=request.error_handling,
                    parallel_execution=request.parallel_execution,
                    timeout_seconds=request.timeout_seconds,
                    retry_config=request.retry_config,
                    enabled=request.auto_activate,
                    created_by=created_by
                )
                
                # Validate flow
                validation_errors = flow.validate()
                if validation_errors:
                    return CreateFlowResponse(
                        success=False,
                        message=f"Flow validation failed: {'; '.join(validation_errors)}"
                    )
                
                # Store flow
                self.flows[flow.id] = flow
                self.service_stats["total_flows"] += 1
                
                if flow.enabled:
                    self.service_stats["active_flows"] += 1
                
                # Register with integration engine
                self.integration_engine.register_flow(flow)
                
                logger.info(f"Created integration flow: {flow.name}")
                
                return CreateFlowResponse(
                    success=True,
                    flow_id=flow.id,
                    message="Integration flow created successfully"
                )
                
            except Exception as e:
                logger.error(f"Failed to create integration flow: {e}")
                return CreateFlowResponse(
                    success=False,
                    message=f"Failed to create flow: {str(e)}"
                )
    
    @monitor_performance("execute_flow")
    @require_permission(Permission.EXECUTE_INTEGRATIONS)
    async def execute_flow(self, flow_id: str, input_data: Dict[str, Any],
                          executed_by: str) -> FlowExecutionResponse:
        """Execute integration flow."""
        with log_context(operation="execute_flow", flow_id=flow_id, user=executed_by):
            try:
                if flow_id not in self.flows:
                    return FlowExecutionResponse(
                        success=False,
                        message="Integration flow not found"
                    )
                
                flow = self.flows[flow_id]
                
                if not flow.enabled:
                    return FlowExecutionResponse(
                        success=False,
                        message="Integration flow is disabled"
                    )
                
                # Execute flow
                execution_result = await self.integration_engine.execute_flow(
                    flow, input_data
                )
                
                return FlowExecutionResponse(
                    success=execution_result["success"],
                    execution_id=execution_result.get("execution_id"),
                    flow_results=execution_result.get("flow_results", []),
                    execution_time_ms=execution_result.get("execution_time_ms"),
                    message=execution_result.get("message", "Flow executed successfully" if execution_result["success"] else "Flow execution failed")
                )
                
            except Exception as e:
                logger.error(f"Failed to execute integration flow: {e}")
                return FlowExecutionResponse(
                    success=False,
                    message=f"Failed to execute flow: {str(e)}"
                )
    
    @monitor_performance("get_connector_stats")
    @require_permission(Permission.VIEW_INTEGRATIONS)
    def get_connector_statistics(self, connector_id: str, days: int = 30) -> ConnectorStatsResponse:
        """Get connector statistics."""
        try:
            if connector_id not in self.connectors:
                return ConnectorStatsResponse(
                    success=False,
                    message="Connector not found"
                )
            
            connector = self.connectors[connector_id]
            
            # Get detailed statistics from integration engine
            detailed_stats = self.integration_engine.get_connector_statistics(connector_id, days)
            
            return ConnectorStatsResponse(
                success=True,
                statistics={
                    "basic_stats": {
                        "execution_count": connector.execution_count,
                        "success_count": connector.success_count,
                        "failure_count": connector.failure_count,
                        "success_rate": connector.get_success_rate(),
                        "average_execution_time_ms": connector.average_execution_time_ms
                    },
                    "detailed_stats": detailed_stats,
                    "health_status": connector.get_health_status()
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to get connector statistics: {e}")
            return ConnectorStatsResponse(
                success=False,
                message=f"Failed to get statistics: {str(e)}"
            )
    
    @monitor_performance("get_integration_health")
    @require_permission(Permission.VIEW_INTEGRATIONS)
    def get_integration_health(self) -> IntegrationHealthResponse:
        """Get overall integration system health."""
        try:
            # Calculate overall health metrics
            total_connectors = len(self.connectors)
            active_connectors = len([c for c in self.connectors.values() if c.status == ConnectorStatus.ACTIVE])
            healthy_connectors = len([c for c in self.connectors.values() if c.get_health_status()["health"] == "healthy"])
            
            # Calculate system success rate
            system_success_rate = 0.0
            if self.service_stats["total_executions"] > 0:
                system_success_rate = (self.service_stats["successful_executions"] / self.service_stats["total_executions"]) * 100
            
            # Determine overall health
            if total_connectors == 0:
                overall_health = "no_connectors"
            elif healthy_connectors / max(active_connectors, 1) >= 0.9:
                overall_health = "healthy"
            elif healthy_connectors / max(active_connectors, 1) >= 0.7:
                overall_health = "warning"
            else:
                overall_health = "unhealthy"
            
            # Get connector health details
            connector_health = {}
            for connector_id, connector in self.connectors.items():
                connector_health[connector_id] = {
                    "name": connector.name,
                    "status": connector.status.value,
                    "health": connector.get_health_status()
                }
            
            return IntegrationHealthResponse(
                success=True,
                overall_health=overall_health,
                system_metrics={
                    "total_connectors": total_connectors,
                    "active_connectors": active_connectors,
                    "healthy_connectors": healthy_connectors,
                    "total_flows": len(self.flows),
                    "active_flows": len([f for f in self.flows.values() if f.enabled]),
                    "system_success_rate": system_success_rate,
                    "total_executions": self.service_stats["total_executions"]
                },
                connector_health=connector_health,
                alerts=[],  # Would be populated with actual alerts
                recommendations=self._generate_health_recommendations()
            )
            
        except Exception as e:
            logger.error(f"Failed to get integration health: {e}")
            return IntegrationHealthResponse(
                success=False,
                message=f"Failed to get health status: {str(e)}"
            )
    
    def _generate_health_recommendations(self) -> List[str]:
        """Generate health recommendations."""
        recommendations = []
        
        inactive_connectors = [c for c in self.connectors.values() if c.status != ConnectorStatus.ACTIVE]
        if len(inactive_connectors) > 0:
            recommendations.append(f"Consider activating {len(inactive_connectors)} inactive connectors")
        
        unhealthy_connectors = [c for c in self.connectors.values() if c.get_health_status()["health"] == "unhealthy"]
        if len(unhealthy_connectors) > 0:
            recommendations.append(f"Review and fix {len(unhealthy_connectors)} unhealthy connectors")
        
        if self.service_stats["total_executions"] == 0:
            recommendations.append("No connector executions recorded - consider testing your integrations")
        
        return recommendations
    
    @require_permission(Permission.MANAGE_INTEGRATIONS)
    def delete_connector(self, connector_id: str) -> Dict[str, Any]:
        """Delete integration connector."""
        try:
            if connector_id not in self.connectors:
                return {"success": False, "message": "Connector not found"}
            
            connector = self.connectors[connector_id]
            
            # Unregister from integration engine
            self.integration_engine.unregister_connector(connector_id)
            
            # Remove from storage
            del self.connectors[connector_id]
            self.service_stats["total_connectors"] -= 1
            
            if connector.status == ConnectorStatus.ACTIVE:
                self.service_stats["active_connectors"] -= 1
            
            # Remove from any flows
            for flow in self.flows.values():
                if connector_id in flow.connectors:
                    flow.connectors.remove(connector_id)
            
            logger.info(f"Deleted integration connector: {connector.name}")
            
            return {"success": True, "message": "Connector deleted successfully"}
            
        except Exception as e:
            logger.error(f"Failed to delete connector: {e}")
            return {"success": False, "message": f"Failed to delete connector: {str(e)}"}
    
    def get_service_statistics(self) -> Dict[str, Any]:
        """Get integration service statistics."""
        return {
            **self.service_stats,
            "engine_stats": self.integration_engine.get_engine_statistics() if self.integration_engine else {}
        }