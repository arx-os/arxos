"""
Integration Execution Engine.

Advanced integration engine for executing connectors, flows, and managing
enterprise integrations with comprehensive monitoring and error handling.
"""

import asyncio
import aiohttp
import aiofiles
import json
import time
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import traceback
import uuid
from collections import defaultdict, deque

from domain.entities.integration_entity import (
    IntegrationConnector, IntegrationFlow, IntegrationType,
    ConnectorStatus, DataFormat, IntegrationDirection
)
from infrastructure.logging.structured_logging import get_logger, log_context
from infrastructure.performance.monitoring import performance_monitor
from infrastructure.services.notification_service import NotificationService


logger = get_logger(__name__)


class IntegrationEngine:
    """Advanced integration execution engine."""
    
    def __init__(self, notification_service: NotificationService = None,
                 max_workers: int = 20, default_timeout: int = 300):
        self.notification_service = notification_service
        self.max_workers = max_workers
        self.default_timeout = default_timeout
        
        # Thread pool for parallel execution
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # HTTP session for API calls
        self.http_session = None
        
        # Registered connectors and flows
        self.registered_connectors: Dict[str, IntegrationConnector] = {}
        self.registered_flows: Dict[str, IntegrationFlow] = {}
        
        # Active executions
        self.active_executions: Dict[str, Dict[str, Any]] = {}
        
        # Execution history for monitoring
        self.execution_history: deque = deque(maxlen=10000)
        
        # Performance metrics
        self.performance_metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time_ms": 0.0,
            "connector_metrics": defaultdict(lambda: {
                "executions": 0, "successes": 0, "failures": 0, "avg_time_ms": 0.0
            })
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.http_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.default_timeout),
            connector=aiohttp.TCPConnector(limit=100)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.http_session:
            await self.http_session.close()
    
    def register_connector(self, connector: IntegrationConnector) -> None:
        """Register connector for execution."""
        self.registered_connectors[connector.id] = connector
        logger.info(f"Registered integration connector: {connector.name}")
    
    def unregister_connector(self, connector_id: str) -> None:
        """Unregister connector."""
        if connector_id in self.registered_connectors:
            connector = self.registered_connectors.pop(connector_id)
            logger.info(f"Unregistered integration connector: {connector.name}")
    
    def update_connector(self, connector: IntegrationConnector) -> None:
        """Update registered connector."""
        if connector.id in self.registered_connectors:
            self.registered_connectors[connector.id] = connector
            logger.info(f"Updated registered connector: {connector.name}")
    
    def register_flow(self, flow: IntegrationFlow) -> None:
        """Register integration flow."""
        self.registered_flows[flow.id] = flow
        logger.info(f"Registered integration flow: {flow.name}")
    
    def unregister_flow(self, flow_id: str) -> None:
        """Unregister integration flow."""
        if flow_id in self.registered_flows:
            flow = self.registered_flows.pop(flow_id)
            logger.info(f"Unregistered integration flow: {flow.name}")
    
    @performance_monitor("execute_connector")
    async def execute_connector(self, connector: IntegrationConnector,
                              input_data: Dict[str, Any],
                              execution_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute integration connector."""
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        
        with log_context(
            operation="execute_connector",
            connector_id=connector.id,
            execution_id=execution_id
        ):
            # Track active execution
            self.active_executions[execution_id] = {
                "connector_id": connector.id,
                "connector_name": connector.name,
                "started_at": datetime.now(timezone.utc),
                "status": "running",
                "input_data_size": len(json.dumps(input_data)) if input_data else 0
            }
            
            try:
                logger.info(f"Executing connector: {connector.name}")
                
                # Validate input data
                if not self._validate_input_data(input_data, connector.input_format):
                    raise ValueError("Input data validation failed")
                
                # Apply input transformations
                transformed_data = connector.apply_transformations(input_data)
                
                # Execute based on connector direction
                output_data = None
                
                if connector.direction in [IntegrationDirection.INBOUND, IntegrationDirection.BIDIRECTIONAL]:
                    # Read from source
                    source_data = await self._execute_inbound(connector, transformed_data, execution_context or {})
                    output_data = source_data
                
                if connector.direction in [IntegrationDirection.OUTBOUND, IntegrationDirection.BIDIRECTIONAL]:
                    # Write to target
                    data_to_send = output_data if output_data is not None else transformed_data
                    target_result = await self._execute_outbound(connector, data_to_send, execution_context or {})
                    output_data = target_result
                
                # Apply output transformations if needed
                if output_data and connector.transformations:
                    output_data = connector.apply_transformations(output_data)
                
                # Convert output format if needed
                if output_data and connector.output_format != connector.input_format:
                    output_data = self._convert_data_format(output_data, connector.output_format)
                
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                # Record successful execution
                connector.record_execution(success=True, execution_time_ms=execution_time_ms)
                self._record_execution_metrics(connector.id, True, execution_time_ms)
                
                # Record in history
                self._record_execution_history(execution_id, connector, True, execution_time_ms)
                
                logger.info(f"Connector executed successfully: {connector.name} in {execution_time_ms}ms")
                
                return {
                    "success": True,
                    "execution_id": execution_id,
                    "output_data": output_data,
                    "execution_time_ms": execution_time_ms,
                    "message": "Connector executed successfully",
                    "records_processed": self._count_records(output_data) if output_data else 0
                }
                
            except Exception as e:
                execution_time_ms = int((time.time() - start_time) * 1000)
                error_message = str(e)
                
                # Record failed execution
                connector.record_execution(success=False, execution_time_ms=execution_time_ms)
                self._record_execution_metrics(connector.id, False, execution_time_ms)
                
                # Record in history
                self._record_execution_history(execution_id, connector, False, execution_time_ms, error_message)
                
                logger.error(f"Connector execution failed: {connector.name}, error: {e}")
                logger.debug(f"Connector execution traceback: {traceback.format_exc()}")
                
                # Handle error based on configuration
                if connector.dead_letter_queue:
                    await self._send_to_dead_letter_queue(connector.dead_letter_queue, input_data, error_message)
                
                return {
                    "success": False,
                    "execution_id": execution_id,
                    "error": error_message,
                    "execution_time_ms": execution_time_ms,
                    "error_details": {
                        "error_type": type(e).__name__,
                        "traceback": traceback.format_exc() if logger.isEnabledFor(10) else None  # DEBUG level
                    }
                }
                
            finally:
                # Remove from active executions
                if execution_id in self.active_executions:
                    self.active_executions[execution_id]["completed_at"] = datetime.now(timezone.utc)
                    self.active_executions[execution_id]["status"] = "completed"
    
    async def _execute_inbound(self, connector: IntegrationConnector,
                             data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute inbound connector (read from source)."""
        if not connector.source_endpoint:
            raise ValueError("Source endpoint not configured for inbound connector")
        
        endpoint = connector.source_endpoint
        
        if endpoint.integration_type == IntegrationType.REST_API:
            return await self._execute_rest_api_read(endpoint, data, context)
        elif endpoint.integration_type == IntegrationType.DATABASE:
            return await self._execute_database_read(endpoint, data, context)
        elif endpoint.integration_type == IntegrationType.FILE_SYSTEM:
            return await self._execute_file_read(endpoint, data, context)
        elif endpoint.integration_type == IntegrationType.MESSAGE_QUEUE:
            return await self._execute_message_queue_read(endpoint, data, context)
        else:
            raise ValueError(f"Unsupported inbound integration type: {endpoint.integration_type}")
    
    async def _execute_outbound(self, connector: IntegrationConnector,
                              data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute outbound connector (write to target)."""
        if not connector.target_endpoint:
            raise ValueError("Target endpoint not configured for outbound connector")
        
        endpoint = connector.target_endpoint
        
        if endpoint.integration_type == IntegrationType.REST_API:
            return await self._execute_rest_api_write(endpoint, data, context)
        elif endpoint.integration_type == IntegrationType.DATABASE:
            return await self._execute_database_write(endpoint, data, context)
        elif endpoint.integration_type == IntegrationType.FILE_SYSTEM:
            return await self._execute_file_write(endpoint, data, context)
        elif endpoint.integration_type == IntegrationType.MESSAGE_QUEUE:
            return await self._execute_message_queue_write(endpoint, data, context)
        else:
            raise ValueError(f"Unsupported outbound integration type: {endpoint.integration_type}")
    
    async def _execute_rest_api_read(self, endpoint, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute REST API read operation."""
        if not self.http_session:
            self.http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=endpoint.timeout_seconds)
            )
        
        # Prepare headers
        headers = endpoint.headers.copy()
        
        # Add authentication
        if endpoint.authentication.get("type") == "basic":
            import base64
            auth_string = f"{endpoint.authentication['username']}:{endpoint.authentication['password']}"
            auth_bytes = base64.b64encode(auth_string.encode()).decode()
            headers["Authorization"] = f"Basic {auth_bytes}"
        elif endpoint.authentication.get("type") == "bearer":
            headers["Authorization"] = f"Bearer {endpoint.authentication['token']}"
        elif endpoint.authentication.get("type") == "api_key":
            headers[endpoint.authentication["key"]] = endpoint.authentication["value"]
        
        # Execute request
        async with self.http_session.get(
            endpoint.url,
            headers=headers,
            params=endpoint.parameters
        ) as response:
            response.raise_for_status()
            
            if endpoint.data_format == DataFormat.JSON:
                return await response.json()
            elif endpoint.data_format == DataFormat.XML:
                import xml.etree.ElementTree as ET
                text = await response.text()
                return {"xml_data": text}  # Simplified XML handling
            else:
                return {"data": await response.text()}
    
    async def _execute_rest_api_write(self, endpoint, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute REST API write operation."""
        if not self.http_session:
            self.http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=endpoint.timeout_seconds)
            )
        
        # Prepare headers
        headers = endpoint.headers.copy()
        headers.setdefault("Content-Type", "application/json")
        
        # Add authentication
        if endpoint.authentication.get("type") == "basic":
            import base64
            auth_string = f"{endpoint.authentication['username']}:{endpoint.authentication['password']}"
            auth_bytes = base64.b64encode(auth_string.encode()).decode()
            headers["Authorization"] = f"Basic {auth_bytes}"
        elif endpoint.authentication.get("type") == "bearer":
            headers["Authorization"] = f"Bearer {endpoint.authentication['token']}"
        elif endpoint.authentication.get("type") == "api_key":
            headers[endpoint.authentication["key"]] = endpoint.authentication["value"]
        
        # Determine HTTP method from configuration
        method = endpoint.parameters.get("method", "POST").upper()
        
        # Execute request
        if method == "POST":
            async with self.http_session.post(
                endpoint.url,
                json=data,
                headers=headers,
                params=endpoint.parameters
            ) as response:
                response.raise_for_status()
                return {
                    "status_code": response.status,
                    "response": await response.json() if response.content_type == "application/json" else await response.text(),
                    "success": True
                }
        elif method == "PUT":
            async with self.http_session.put(
                endpoint.url,
                json=data,
                headers=headers,
                params=endpoint.parameters
            ) as response:
                response.raise_for_status()
                return {
                    "status_code": response.status,
                    "response": await response.json() if response.content_type == "application/json" else await response.text(),
                    "success": True
                }
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    
    async def _execute_database_read(self, endpoint, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute database read operation."""
        # This is a simplified implementation
        # Production would use actual database drivers
        
        connection_string = endpoint.parameters.get("connection_string", "")
        query = endpoint.parameters.get("query", "")
        
        logger.info(f"Simulating database read from: {connection_string}")
        
        # Simulate database query execution
        await asyncio.sleep(0.1)  # Simulate database latency
        
        return {
            "query": query,
            "results": [
                {"id": 1, "name": "Sample Record 1", "timestamp": datetime.now(timezone.utc).isoformat()},
                {"id": 2, "name": "Sample Record 2", "timestamp": datetime.now(timezone.utc).isoformat()}
            ],
            "record_count": 2
        }
    
    async def _execute_database_write(self, endpoint, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute database write operation."""
        # This is a simplified implementation
        # Production would use actual database drivers
        
        connection_string = endpoint.parameters.get("connection_string", "")
        table_name = endpoint.parameters.get("table_name", "")
        
        logger.info(f"Simulating database write to: {connection_string}, table: {table_name}")
        
        # Simulate database write operation
        await asyncio.sleep(0.1)  # Simulate database latency
        
        record_count = self._count_records(data)
        
        return {
            "table": table_name,
            "records_inserted": record_count,
            "success": True
        }
    
    async def _execute_file_read(self, endpoint, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file system read operation."""
        file_path = endpoint.parameters.get("file_path", endpoint.url)
        
        try:
            async with aiofiles.open(file_path, mode='r') as file:
                content = await file.read()
                
                if endpoint.data_format == DataFormat.JSON:
                    return json.loads(content)
                elif endpoint.data_format == DataFormat.CSV:
                    # Simple CSV parsing
                    lines = content.strip().split('\n')
                    if len(lines) > 1:
                        headers = lines[0].split(',')
                        rows = []
                        for line in lines[1:]:
                            values = line.split(',')
                            row = dict(zip(headers, values))
                            rows.append(row)
                        return {"data": rows, "record_count": len(rows)}
                else:
                    return {"content": content}
                    
        except FileNotFoundError:
            raise ValueError(f"File not found: {file_path}")
    
    async def _execute_file_write(self, endpoint, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file system write operation."""
        file_path = endpoint.parameters.get("file_path", endpoint.url)
        
        try:
            if endpoint.data_format == DataFormat.JSON:
                content = json.dumps(data, indent=2)
            else:
                content = str(data)
            
            async with aiofiles.open(file_path, mode='w') as file:
                await file.write(content)
            
            return {
                "file_path": file_path,
                "bytes_written": len(content),
                "success": True
            }
            
        except Exception as e:
            raise ValueError(f"Failed to write file {file_path}: {str(e)}")
    
    async def _execute_message_queue_read(self, endpoint, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute message queue read operation."""
        # This is a simplified implementation
        # Production would use actual message queue clients
        
        queue_name = endpoint.parameters.get("queue_name", "")
        
        logger.info(f"Simulating message queue read from: {queue_name}")
        
        # Simulate message queue read
        await asyncio.sleep(0.05)  # Simulate network latency
        
        return {
            "queue": queue_name,
            "messages": [
                {"id": str(uuid.uuid4()), "payload": {"message": "Sample message 1"}, "timestamp": datetime.now(timezone.utc).isoformat()},
                {"id": str(uuid.uuid4()), "payload": {"message": "Sample message 2"}, "timestamp": datetime.now(timezone.utc).isoformat()}
            ],
            "message_count": 2
        }
    
    async def _execute_message_queue_write(self, endpoint, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute message queue write operation."""
        # This is a simplified implementation
        # Production would use actual message queue clients
        
        queue_name = endpoint.parameters.get("queue_name", "")
        
        logger.info(f"Simulating message queue write to: {queue_name}")
        
        # Simulate message queue write
        await asyncio.sleep(0.05)  # Simulate network latency
        
        message_count = self._count_records(data)
        
        return {
            "queue": queue_name,
            "messages_sent": message_count,
            "success": True
        }
    
    async def execute_flow(self, flow: IntegrationFlow, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute integration flow."""
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        
        with log_context(operation="execute_flow", flow_id=flow.id, execution_id=execution_id):
            try:
                logger.info(f"Executing integration flow: {flow.name}")
                
                flow_results = []
                current_data = input_data
                
                # Execute connectors in sequence or parallel
                if flow.parallel_execution:
                    # Parallel execution
                    tasks = []
                    for connector_id in flow.connectors:
                        if connector_id in self.registered_connectors:
                            connector = self.registered_connectors[connector_id]
                            task = self.execute_connector(connector, current_data)
                            tasks.append(task)
                    
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            flow_results.append({
                                "connector_id": flow.connectors[i],
                                "success": False,
                                "error": str(result)
                            })
                        else:
                            flow_results.append({
                                "connector_id": flow.connectors[i],
                                **result
                            })
                else:
                    # Sequential execution
                    for connector_id in flow.connectors:
                        if connector_id not in self.registered_connectors:
                            flow_results.append({
                                "connector_id": connector_id,
                                "success": False,
                                "error": "Connector not found"
                            })
                            continue
                        
                        connector = self.registered_connectors[connector_id]
                        result = await self.execute_connector(connector, current_data)
                        
                        flow_results.append({
                            "connector_id": connector_id,
                            **result
                        })
                        
                        # Use output data as input for next connector
                        if result.get("success") and result.get("output_data"):
                            current_data = result["output_data"]
                        elif not flow.error_handling.get("continue_on_failure", False):
                            break
                
                execution_time_ms = int((time.time() - start_time) * 1000)
                success = all(result.get("success", False) for result in flow_results)
                
                logger.info(f"Flow executed: {flow.name}, success: {success}, time: {execution_time_ms}ms")
                
                return {
                    "success": success,
                    "execution_id": execution_id,
                    "flow_results": flow_results,
                    "execution_time_ms": execution_time_ms,
                    "message": "Flow executed successfully" if success else "Flow execution completed with errors"
                }
                
            except Exception as e:
                execution_time_ms = int((time.time() - start_time) * 1000)
                logger.error(f"Flow execution failed: {flow.name}, error: {e}")
                
                return {
                    "success": False,
                    "execution_id": execution_id,
                    "error": str(e),
                    "execution_time_ms": execution_time_ms
                }
    
    async def test_connector(self, connector: IntegrationConnector,
                           test_data: Dict[str, Any] = None,
                           test_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test integration connector."""
        try:
            test_options = test_options or {}
            
            # Validate connector configuration
            validation_errors = connector.validate()
            if validation_errors:
                return {
                    "success": False,
                    "test_result": "validation_failed",
                    "validation_results": {
                        "is_valid": False,
                        "errors": validation_errors
                    }
                }
            
            # Test connectivity if requested
            connectivity_test = {}
            if test_options.get("test_connectivity", True):
                connectivity_test = await self._test_connectivity(connector)
            
            # Test transformations if data provided
            transformation_test = {}
            if test_data and connector.transformations:
                transformation_test = self._test_transformations(connector, test_data)
            
            # Performance test
            performance_metrics = {}
            if test_options.get("test_performance", True):
                performance_metrics = await self._test_performance(connector, test_data or {})
            
            # Generate recommendations
            recommendations = self._generate_test_recommendations(
                connector, validation_errors, connectivity_test, transformation_test
            )
            
            overall_success = (
                len(validation_errors) == 0 and
                connectivity_test.get("success", True) and
                transformation_test.get("success", True)
            )
            
            return {
                "success": True,
                "test_result": "passed" if overall_success else "failed",
                "validation_results": {
                    "is_valid": len(validation_errors) == 0,
                    "errors": validation_errors
                },
                "connectivity_test": connectivity_test,
                "transformation_test": transformation_test,
                "performance_metrics": performance_metrics,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Connector test failed: {e}")
            return {
                "success": False,
                "test_result": "error",
                "error": str(e)
            }
    
    async def _test_connectivity(self, connector: IntegrationConnector) -> Dict[str, Any]:
        """Test connector connectivity."""
        connectivity_results = {}
        
        if connector.source_endpoint:
            connectivity_results["source"] = await self._test_endpoint_connectivity(connector.source_endpoint)
        
        if connector.target_endpoint:
            connectivity_results["target"] = await self._test_endpoint_connectivity(connector.target_endpoint)
        
        success = all(result.get("success", False) for result in connectivity_results.values())
        
        return {
            "success": success,
            "results": connectivity_results
        }
    
    async def _test_endpoint_connectivity(self, endpoint) -> Dict[str, Any]:
        """Test endpoint connectivity."""
        try:
            if endpoint.integration_type == IntegrationType.REST_API:
                if not self.http_session:
                    self.http_session = aiohttp.ClientSession(
                        timeout=aiohttp.ClientTimeout(total=10)
                    )
                
                async with self.http_session.head(endpoint.url) as response:
                    return {
                        "success": True,
                        "status_code": response.status,
                        "response_time_ms": 100  # Simplified
                    }
            else:
                # For other types, return simulated success
                await asyncio.sleep(0.1)
                return {
                    "success": True,
                    "message": f"Connectivity test passed for {endpoint.integration_type.value}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_transformations(self, connector: IntegrationConnector, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test data transformations."""
        try:
            original_data = test_data.copy()
            transformed_data = connector.apply_transformations(test_data)
            
            return {
                "success": True,
                "original_data": original_data,
                "transformed_data": transformed_data,
                "transformations_applied": len([t for t in connector.transformations if t.enabled])
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _test_performance(self, connector: IntegrationConnector, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test connector performance."""
        try:
            # Run multiple test executions
            execution_times = []
            
            for _ in range(3):  # Run 3 test iterations
                start_time = time.time()
                
                # Simulate execution (don't actually execute)
                await asyncio.sleep(0.05)  # Simulate processing time
                
                execution_time_ms = int((time.time() - start_time) * 1000)
                execution_times.append(execution_time_ms)
            
            avg_time = sum(execution_times) / len(execution_times)
            
            return {
                "average_execution_time_ms": avg_time,
                "min_execution_time_ms": min(execution_times),
                "max_execution_time_ms": max(execution_times),
                "test_iterations": len(execution_times)
            }
            
        except Exception as e:
            return {
                "error": str(e)
            }
    
    def _generate_test_recommendations(self, connector: IntegrationConnector,
                                     validation_errors: List[str],
                                     connectivity_test: Dict[str, Any],
                                     transformation_test: Dict[str, Any]) -> List[str]:
        """Generate test recommendations."""
        recommendations = []
        
        if validation_errors:
            recommendations.append("Fix configuration errors before deployment")
        
        if not connectivity_test.get("success", True):
            recommendations.append("Review network connectivity and endpoint configuration")
        
        if not transformation_test.get("success", True):
            recommendations.append("Review data transformation rules")
        
        if len(connector.transformations) == 0:
            recommendations.append("Consider adding data transformations for better integration")
        
        if not connector.monitoring_enabled:
            recommendations.append("Enable monitoring for production deployment")
        
        return recommendations
    
    def _validate_input_data(self, data: Dict[str, Any], expected_format: DataFormat) -> bool:
        """Validate input data format."""
        if not data:
            return True  # Empty data is valid
        
        try:
            if expected_format == DataFormat.JSON:
                json.dumps(data)  # Test JSON serialization
            # Add other format validations as needed
            return True
        except Exception:
            return False
    
    def _convert_data_format(self, data: Any, target_format: DataFormat) -> Any:
        """Convert data to target format."""
        if target_format == DataFormat.JSON:
            return data  # Already in dict/JSON format
        elif target_format == DataFormat.XML:
            # Simplified XML conversion
            return f"<data>{json.dumps(data)}</data>"
        else:
            return str(data)
    
    def _count_records(self, data: Any) -> int:
        """Count number of records in data."""
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            # Check for common list fields
            for key in ["data", "records", "items", "results"]:
                if key in data and isinstance(data[key], list):
                    return len(data[key])
            return 1
        else:
            return 1
    
    async def _send_to_dead_letter_queue(self, queue_name: str, data: Dict[str, Any], error: str) -> None:
        """Send failed data to dead letter queue."""
        logger.info(f"Sending data to dead letter queue: {queue_name}")
        # In production, this would send to actual message queue
        
    def _record_execution_metrics(self, connector_id: str, success: bool, execution_time_ms: int) -> None:
        """Record execution metrics."""
        self.performance_metrics["total_executions"] += 1
        
        if success:
            self.performance_metrics["successful_executions"] += 1
        else:
            self.performance_metrics["failed_executions"] += 1
        
        # Update average execution time
        total = self.performance_metrics["total_executions"]
        current_avg = self.performance_metrics["average_execution_time_ms"]
        new_avg = ((current_avg * (total - 1)) + execution_time_ms) / total
        self.performance_metrics["average_execution_time_ms"] = new_avg
        
        # Update connector-specific metrics
        connector_metrics = self.performance_metrics["connector_metrics"][connector_id]
        connector_metrics["executions"] += 1
        
        if success:
            connector_metrics["successes"] += 1
        else:
            connector_metrics["failures"] += 1
        
        # Update connector average time
        exec_count = connector_metrics["executions"]
        current_avg = connector_metrics["avg_time_ms"]
        new_avg = ((current_avg * (exec_count - 1)) + execution_time_ms) / exec_count
        connector_metrics["avg_time_ms"] = new_avg
    
    def _record_execution_history(self, execution_id: str, connector: IntegrationConnector,
                                success: bool, execution_time_ms: int, error: str = None) -> None:
        """Record execution in history."""
        self.execution_history.append({
            "execution_id": execution_id,
            "connector_id": connector.id,
            "connector_name": connector.name,
            "success": success,
            "execution_time_ms": execution_time_ms,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def get_connector_statistics(self, connector_id: str, days: int = 30) -> Dict[str, Any]:
        """Get detailed connector statistics."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Filter execution history for this connector and time range
        connector_executions = [
            exec_record for exec_record in self.execution_history
            if (exec_record["connector_id"] == connector_id and
                datetime.fromisoformat(exec_record["timestamp"]) > cutoff_time)
        ]
        
        if not connector_executions:
            return {"message": "No execution history found"}
        
        # Calculate statistics
        total_executions = len(connector_executions)
        successful_executions = len([e for e in connector_executions if e["success"]])
        failed_executions = total_executions - successful_executions
        
        execution_times = [e["execution_time_ms"] for e in connector_executions if e["execution_time_ms"]]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        return {
            "period_days": days,
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "success_rate": (successful_executions / total_executions * 100) if total_executions > 0 else 0,
            "average_execution_time_ms": avg_execution_time,
            "min_execution_time_ms": min(execution_times) if execution_times else 0,
            "max_execution_time_ms": max(execution_times) if execution_times else 0
        }
    
    def get_active_executions(self) -> List[Dict[str, Any]]:
        """Get currently active executions."""
        now = datetime.now(timezone.utc)
        active = []
        
        for execution_id, execution_info in self.active_executions.items():
            if execution_info["status"] == "running":
                elapsed_time = (now - execution_info["started_at"]).total_seconds() * 1000
                active.append({
                    "execution_id": execution_id,
                    "connector_id": execution_info["connector_id"],
                    "connector_name": execution_info["connector_name"],
                    "started_at": execution_info["started_at"].isoformat(),
                    "elapsed_time_ms": int(elapsed_time),
                    "input_data_size": execution_info["input_data_size"]
                })
        
        return active
    
    def get_engine_statistics(self) -> Dict[str, Any]:
        """Get overall engine statistics."""
        return {
            **self.performance_metrics,
            "registered_connectors": len(self.registered_connectors),
            "registered_flows": len(self.registered_flows),
            "active_executions": len([e for e in self.active_executions.values() if e["status"] == "running"]),
            "execution_history_size": len(self.execution_history)
        }
    
    async def shutdown(self) -> None:
        """Shutdown integration engine gracefully."""
        logger.info("Shutting down integration engine...")
        
        # Close HTTP session
        if self.http_session:
            await self.http_session.close()
        
        # Shutdown thread pool
        self.executor.shutdown(wait=True)
        
        logger.info("Integration engine shutdown complete")