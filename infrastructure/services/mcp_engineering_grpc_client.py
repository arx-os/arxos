"""
MCP-Engineering gRPC Client

This module provides gRPC client functionality for real-time communication
with external MCP-Engineering services. It implements best practices for:
- Async gRPC communication
- Streaming for real-time updates
- Error handling and reconnection logic
- Service discovery
- Load balancing
- Type safety
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

import grpc
import grpc.aio
from grpc import aio as grpc_aio


# Note: These would be generated from .proto files in a real implementation
# For now, we'll create mock protobuf classes
class MockValidationUpdate:
    """Mock validation update protobuf message."""

    def __init__(self, session_id: str, status: str, progress: float, message: str):
        self.session_id = session_id
        self.status = status
        self.progress = progress
        self.message = message


class MockValidationRequest:
    """Mock validation request protobuf message."""

    def __init__(self, building_data: Dict[str, Any], validation_type: str):
        self.building_data = building_data
        self.validation_type = validation_type


class MockMCPEngineeringServiceStub:
    """Mock gRPC service stub."""

    def __init__(self, channel):
        self.channel = channel

    async def validate_building_stream(
        self, request
    ) -> AsyncGenerator[MockValidationUpdate, None]:
        """Mock streaming validation updates."""
        # Simulate streaming updates
        updates = [
            MockValidationUpdate(
                request.session_id, "started", 0.0, "Validation started"
            ),
            MockValidationUpdate(
                request.session_id, "processing", 0.25, "Analyzing building data"
            ),
            MockValidationUpdate(
                request.session_id, "processing", 0.5, "Checking compliance"
            ),
            MockValidationUpdate(
                request.session_id, "processing", 0.75, "Generating recommendations"
            ),
            MockValidationUpdate(
                request.session_id, "completed", 1.0, "Validation completed"
            ),
        ]

        for update in updates:
            yield update
            await asyncio.sleep(0.5)  # Simulate processing time

    async def health_check(self, request) -> MockValidationUpdate:
        """Mock health check response."""
        return MockValidationUpdate("health", "healthy", 1.0, "Service is healthy")


@dataclass
class GRPCConfig:
    """Configuration for MCP-Engineering gRPC client."""

    server_address: str
    timeout: int = 30
    max_reconnect_attempts: int = 5
    reconnect_delay: float = 1.0
    keepalive_time: int = 30
    keepalive_timeout: int = 10


class ServiceDiscovery:
    """Service discovery implementation for gRPC endpoints."""

    def __init__(self, consul_client=None):
        self.consul_client = consul_client
        self.cached_endpoints = []
        self.last_refresh = None

    async def get_service_endpoints(self, service_name: str) -> List[str]:
        """
        Get available service endpoints.

        Args:
            service_name: Name of the service to discover

        Returns:
            List of service endpoint addresses
        """
        # In a real implementation, this would query Consul or similar
        # For now, return mock endpoints
        return [
            "grpc://mcp-engineering-1:50051",
            "grpc://mcp-engineering-2:50051",
            "grpc://mcp-engineering-3:50051",
        ]

    async def refresh_endpoints(self, service_name: str):
        """Refresh cached service endpoints."""
        self.cached_endpoints = await self.get_service_endpoints(service_name)
        self.last_refresh = datetime.now()


class LoadBalancer:
    """Simple round-robin load balancer for gRPC connections."""

    def __init__(self, endpoints: List[str]):
        self.endpoints = endpoints
        self.current_index = 0
        self.healthy_endpoints = endpoints.copy()

    def get_next_endpoint(self) -> str:
        """Get the next endpoint in round-robin fashion."""
        if not self.healthy_endpoints:
            return None

        endpoint = self.healthy_endpoints[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.healthy_endpoints)
        return endpoint

    def mark_endpoint_unhealthy(self, endpoint: str):
        """Mark an endpoint as unhealthy."""
        if endpoint in self.healthy_endpoints:
            self.healthy_endpoints.remove(endpoint)

    def mark_endpoint_healthy(self, endpoint: str):
        """Mark an endpoint as healthy."""
        if endpoint not in self.healthy_endpoints:
            self.healthy_endpoints.append(endpoint)


class MCPEngineeringGRPCClient:
    """
    gRPC client for MCP-Engineering external services.

    Implements best practices for:
    - Async gRPC communication
    - Streaming for real-time updates
    - Error handling and reconnection logic
    - Service discovery
    - Load balancing
    - Type safety
    """

    def __init__(self, config: GRPCConfig, service_discovery: ServiceDiscovery = None):
        """Initialize the gRPC client."""
        self.config = config
        self.service_discovery = service_discovery or ServiceDiscovery()
        self.load_balancer = LoadBalancer([])
        self.channel: Optional[grpc.aio.Channel] = None
        self.stub: Optional[MockMCPEngineeringServiceStub] = None
        self.logger = logging.getLogger(__name__)
        self.connection_attempts = 0
        self.is_connected = False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self):
        """Establish gRPC connection with retry logic."""
        while self.connection_attempts < self.config.max_reconnect_attempts:
            try:
                # Get service endpoints
                endpoints = await self.service_discovery.get_service_endpoints(
                    "mcp-engineering"
                )
                self.load_balancer = LoadBalancer(endpoints)

                # Try to connect to an endpoint
                endpoint = self.load_balancer.get_next_endpoint()
                if not endpoint:
                    raise ConnectionError("No healthy endpoints available")

                # Parse endpoint (remove grpc:// prefix)
                server_address = endpoint.replace("grpc://", "")

                # Create gRPC channel with keepalive settings
                channel_options = [
                    ("grpc.keepalive_time_ms", self.config.keepalive_time * 1000),
                    ("grpc.keepalive_timeout_ms", self.config.keepalive_timeout * 1000),
                    ("grpc.keepalive_permit_without_calls", True),
                    ("grpc.http2.max_pings_without_data", 0),
                    ("grpc.http2.min_time_between_pings_ms", 10000),
                    ("grpc.http2.min_ping_interval_without_data_ms", 300000),
                ]

                self.channel = grpc.aio.insecure_channel(
                    server_address, options=channel_options
                )

                # Create service stub
                self.stub = MockMCPEngineeringServiceStub(self.channel)

                # Test connection with health check
                await self.health_check()

                self.is_connected = True
                self.connection_attempts = 0
                self.logger.info(f"Successfully connected to {server_address}")
                break

            except Exception as e:
                self.connection_attempts += 1
                self.logger.error(
                    f"Connection attempt {self.connection_attempts} failed: {e}"
                )

                if self.connection_attempts >= self.config.max_reconnect_attempts:
                    raise ConnectionError(
                        f"Failed to connect after {self.config.max_reconnect_attempts} attempts"
                    )

                # Wait before retrying
                await asyncio.sleep(
                    self.config.reconnect_delay * (2**self.connection_attempts)
                )

    async def disconnect(self):
        """Close gRPC connection."""
        if self.channel:
            await self.channel.close()
            self.channel = None
            self.stub = None
            self.is_connected = False
            self.logger.info("gRPC connection closed")

    async def health_check(self) -> bool:
        """
        Check the health of the gRPC service.

        Returns:
            True if service is healthy, False otherwise
        """
        if not self.stub:
            return False

        try:
            # Create mock health check request
            request = MockValidationRequest({}, "health")
            response = await self.stub.health_check(request)
            return response.status == "healthy"
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    async def stream_validation_updates(
        self, session_id: str, building_data: Dict[str, Any], validation_type: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream real-time validation updates.

        Args:
            session_id: Validation session ID
            building_data: Building data to validate
            validation_type: Type of validation to perform

        Yields:
            Validation update dictionaries
        """
        if not self.stub:
            raise RuntimeError("gRPC client not connected")

        try:
            # Create validation request
            request = MockValidationRequest(building_data, validation_type)
            request.session_id = session_id

            # Stream validation updates
            async for update in self.stub.validate_building_stream(request):
                yield {
                    "session_id": update.session_id,
                    "status": update.status,
                    "progress": update.progress,
                    "message": update.message,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            self.logger.error(f"Streaming validation updates failed: {e}")
            # Mark endpoint as unhealthy
            if hasattr(self, "current_endpoint"):
                self.load_balancer.mark_endpoint_unhealthy(self.current_endpoint)
            raise

    async def validate_building_realtime(
        self, building_data: Dict[str, Any], validation_type: str, session_id: str
    ) -> Dict[str, Any]:
        """
        Perform real-time building validation with streaming updates.

        Args:
            building_data: Building data to validate
            validation_type: Type of validation to perform
            session_id: Validation session ID

        Returns:
            Final validation result
        """
        updates = []

        async for update in self.stream_validation_updates(
            session_id, building_data, validation_type
        ):
            updates.append(update)

            # Log progress
            self.logger.info(
                f"Validation progress: {update['progress']:.1%} - {update['message']}"
            )

        # Return final result
        final_update = updates[-1] if updates else {}
        return {
            "session_id": session_id,
            "status": final_update.get("status", "error"),
            "progress": final_update.get("progress", 0.0),
            "message": final_update.get("message", "Validation failed"),
            "updates": updates,
            "timestamp": datetime.now().isoformat(),
        }

    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get connection status and metrics.

        Returns:
            Dictionary with connection status
        """
        return {
            "is_connected": self.is_connected,
            "connection_attempts": self.connection_attempts,
            "healthy_endpoints": len(self.load_balancer.healthy_endpoints),
            "total_endpoints": len(self.load_balancer.endpoints),
            "current_endpoint": self.load_balancer.get_next_endpoint(),
        }


class MCPEngineeringGRPCManager:
    """
    Manager for multiple gRPC client instances with load balancing.

    This class manages multiple gRPC connections and provides
    load balancing and failover capabilities.
    """

    def __init__(self, configs: List[GRPCConfig]):
        """Initialize the gRPC manager."""
        self.configs = configs
        self.clients: List[MCPEngineeringGRPCClient] = []
        self.current_client_index = 0
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """Initialize all gRPC clients."""
        for config in self.configs:
            client = MCPEngineeringGRPCClient(config)
            try:
                await client.connect()
                self.clients.append(client)
                self.logger.info(f"Initialized gRPC client for {config.server_address}")
            except Exception as e:
                self.logger.error(f"Failed to initialize gRPC client: {e}")

    async def cleanup(self):
        """Clean up all gRPC clients."""
        for client in self.clients:
            try:
                await client.disconnect()
            except Exception as e:
                self.logger.error(f"Error disconnecting client: {e}")
        self.clients.clear()

    def get_next_client(self) -> Optional[MCPEngineeringGRPCClient]:
        """Get the next available client using round-robin."""
        if not self.clients:
            return None

        client = self.clients[self.current_client_index]
        self.current_client_index = (self.current_client_index + 1) % len(self.clients)
        return client

    async def stream_validation_updates(
        self, session_id: str, building_data: Dict[str, Any], validation_type: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream validation updates using load-balanced clients.

        Args:
            session_id: Validation session ID
            building_data: Building data to validate
            validation_type: Type of validation to perform

        Yields:
            Validation update dictionaries
        """
        client = self.get_next_client()
        if not client:
            raise RuntimeError("No available gRPC clients")

        async for update in client.stream_validation_updates(
            session_id, building_data, validation_type
        ):
            yield update

    def get_manager_status(self) -> Dict[str, Any]:
        """
        Get manager status and metrics.

        Returns:
            Dictionary with manager status
        """
        client_statuses = []
        for i, client in enumerate(self.clients):
            status = client.get_connection_status()
            status["client_index"] = i
            client_statuses.append(status)

        return {
            "total_clients": len(self.clients),
            "active_clients": len([c for c in self.clients if c.is_connected]),
            "current_client_index": self.current_client_index,
            "client_statuses": client_statuses,
        }
