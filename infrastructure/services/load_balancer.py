"""
Load Balancer for MCP Engineering

This module provides application-level load balancing for the MCP Engineering API,
including health checks, circuit breakers, and performance optimization.
"""

import asyncio
import time
import random
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import aiohttp
import httpx

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """Load balancing strategies."""

    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    IP_HASH = "ip_hash"
    LEAST_RESPONSE_TIME = "least_response_time"


class HealthStatus(Enum):
    """Health status of a backend server."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class BackendServer:
    """Backend server configuration."""

    id: str
    url: str
    weight: int = 1
    max_connections: int = 100
    timeout: float = 30.0
    health_check_path: str = "/health"
    health_check_interval: int = 30
    health_check_timeout: float = 5.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60


class CircuitBreaker:
    """Circuit breaker pattern implementation."""

    def __init__(self, threshold: int = 5, timeout: int = 60):
        """
        Initialize circuit breaker.

        Args:
            threshold: Number of failures before opening circuit
            timeout: Timeout in seconds before attempting to close circuit
        """
        self.threshold = threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def record_success(self):
        """Record a successful request."""
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_failure_time = None

    def record_failure(self):
        """Record a failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.threshold:
            self.state = "OPEN"

    def can_execute(self) -> bool:
        """
        Check if request can be executed.

        Returns:
            True if circuit is closed or half-open
        """
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        elif self.state == "HALF_OPEN":
            return True
        return False

    def get_status(self) -> Dict[str, Any]:
        """
        Get circuit breaker status.

        Returns:
            Circuit breaker status
        """
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "threshold": self.threshold,
            "last_failure_time": self.last_failure_time,
            "timeout": self.timeout,
        }


class HealthChecker:
    """Health checker for backend servers."""

    def __init__(self, check_interval: int = 30):
        """
        Initialize health checker.

        Args:
            check_interval: Health check interval in seconds
        """
        self.check_interval = check_interval
        self.health_status: Dict[str, HealthStatus] = {}
        self.response_times: Dict[str, List[float]] = {}
        self.last_check: Dict[str, datetime] = {}

    async def check_health(self, server: BackendServer) -> HealthStatus:
        """
        Check health of a backend server.

        Args:
            server: Backend server to check

        Returns:
            Health status
        """
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(
                    f"{server.url}{server.health_check_path}",
                    timeout=aiohttp.ClientTimeout(total=server.health_check_timeout),
                ) as response:
                    response_time = time.time() - start_time

                    if response.status == 200:
                        self.health_status[server.id] = HealthStatus.HEALTHY
                        if server.id not in self.response_times:
                            self.response_times[server.id] = []
                        self.response_times[server.id].append(response_time)

                        # Keep only last 10 response times
                        if len(self.response_times[server.id]) > 10:
                            self.response_times[server.id] = self.response_times[
                                server.id
                            ][-10:]

                        self.last_check[server.id] = datetime.utcnow()
                        return HealthStatus.HEALTHY
                    else:
                        self.health_status[server.id] = HealthStatus.UNHEALTHY
                        return HealthStatus.UNHEALTHY

        except Exception as e:
            logger.warning(f"Health check failed for {server.url}: {e}")
            self.health_status[server.id] = HealthStatus.UNHEALTHY
            return HealthStatus.UNHEALTHY

    def get_average_response_time(self, server_id: str) -> float:
        """
        Get average response time for a server.

        Args:
            server_id: Server identifier

        Returns:
            Average response time in seconds
        """
        if server_id in self.response_times and self.response_times[server_id]:
            return sum(self.response_times[server_id]) / len(
                self.response_times[server_id]
            )
        return float("inf")

    def get_health_status(self, server_id: str) -> HealthStatus:
        """
        Get health status for a server.

        Args:
            server_id: Server identifier

        Returns:
            Health status
        """
        return self.health_status.get(server_id, HealthStatus.UNKNOWN)


class LoadBalancer:
    """Application-level load balancer."""

    def __init__(
        self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    ):
        """
        Initialize load balancer.

        Args:
            strategy: Load balancing strategy
        """
        self.strategy = strategy
        self.servers: List[BackendServer] = []
        self.current_index = 0
        self.connection_counts: Dict[str, int] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.health_checker = HealthChecker()
        self._lock = asyncio.Lock()

        # Start health check loop
        asyncio.create_task(self._health_check_loop())

    def add_server(self, server: BackendServer):
        """
        Add a backend server.

        Args:
            server: Backend server to add
        """
        self.servers.append(server)
        self.connection_counts[server.id] = 0
        self.circuit_breakers[server.id] = CircuitBreaker(
            server.circuit_breaker_threshold, server.circuit_breaker_timeout
        )
        logger.info(f"Backend server added: {server.url}")

    def remove_server(self, server_id: str):
        """
        Remove a backend server.

        Args:
            server_id: Server identifier to remove
        """
        self.servers = [s for s in self.servers if s.id != server_id]
        if server_id in self.connection_counts:
            del self.connection_counts[server_id]
        if server_id in self.circuit_breakers:
            del self.circuit_breakers[server_id]
        logger.info(f"Backend server removed: {server_id}")

    async def get_server(
        self, client_ip: Optional[str] = None
    ) -> Optional[BackendServer]:
        """
        Get a backend server based on load balancing strategy.

        Args:
            client_ip: Client IP address for IP hash strategy

        Returns:
            Selected backend server or None if no healthy servers
        """
        async with self._lock:
            healthy_servers = []

            for server in self.servers:
                health_status = self.health_checker.get_health_status(server.id)
                circuit_breaker = self.circuit_breakers[server.id]

                if (
                    health_status == HealthStatus.HEALTHY
                    and circuit_breaker.can_execute()
                ):
                    healthy_servers.append(server)

            if not healthy_servers:
                logger.warning("No healthy backend servers available")
                return None

            if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
                return self._round_robin_select(healthy_servers)
            elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                return self._least_connections_select(healthy_servers)
            elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
                return self._weighted_round_robin_select(healthy_servers)
            elif self.strategy == LoadBalancingStrategy.IP_HASH:
                return self._ip_hash_select(healthy_servers, client_ip)
            elif self.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
                return self._least_response_time_select(healthy_servers)
            else:
                return self._round_robin_select(healthy_servers)

    def _round_robin_select(self, servers: List[BackendServer]) -> BackendServer:
        """Round-robin server selection."""
        server = servers[self.current_index % len(servers)]
        self.current_index = (self.current_index + 1) % len(servers)
        return server

    def _least_connections_select(self, servers: List[BackendServer]) -> BackendServer:
        """Least connections server selection."""
        return min(servers, key=lambda s: self.connection_counts.get(s.id, 0))

    def _weighted_round_robin_select(
        self, servers: List[BackendServer]
    ) -> BackendServer:
        """Weighted round-robin server selection."""
        total_weight = sum(server.weight for server in servers)
        random_value = random.randint(1, total_weight)

        current_weight = 0
        for server in servers:
            current_weight += server.weight
            if random_value <= current_weight:
                return server

        return servers[0]  # Fallback

    def _ip_hash_select(
        self, servers: List[BackendServer], client_ip: Optional[str]
    ) -> BackendServer:
        """IP hash server selection."""
        if not client_ip:
            return self._round_robin_select(servers)

        hash_value = hash(client_ip)
        return servers[hash_value % len(servers)]

    def _least_response_time_select(
        self, servers: List[BackendServer]
    ) -> BackendServer:
        """Least response time server selection."""
        return min(
            servers, key=lambda s: self.health_checker.get_average_response_time(s.id)
        )

    def increment_connection(self, server_id: str):
        """Increment connection count for a server."""
        self.connection_counts[server_id] = self.connection_counts.get(server_id, 0) + 1

    def decrement_connection(self, server_id: str):
        """Decrement connection count for a server."""
        if server_id in self.connection_counts:
            self.connection_counts[server_id] = max(
                0, self.connection_counts[server_id] - 1
            )

    def record_success(self, server_id: str):
        """Record successful request for circuit breaker."""
        if server_id in self.circuit_breakers:
            self.circuit_breakers[server_id].record_success()

    def record_failure(self, server_id: str):
        """Record failed request for circuit breaker."""
        if server_id in self.circuit_breakers:
            self.circuit_breakers[server_id].record_failure()

    async def _health_check_loop(self):
        """Background health check loop."""
        while True:
            try:
                for server in self.servers:
                    await self.health_checker.check_health(server)

                await asyncio.sleep(self.health_checker.check_interval)
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(5)  # Short delay on error

    def get_status(self) -> Dict[str, Any]:
        """
        Get load balancer status.

        Returns:
            Load balancer status
        """
        return {
            "strategy": self.strategy.value,
            "total_servers": len(self.servers),
            "healthy_servers": len(
                [
                    s
                    for s in self.servers
                    if self.health_checker.get_health_status(s.id)
                    == HealthStatus.HEALTHY
                ]
            ),
            "connection_counts": self.connection_counts.copy(),
            "circuit_breakers": {
                server_id: cb.get_status()
                for server_id, cb in self.circuit_breakers.items()
            },
            "health_status": {
                server_id: status.value
                for server_id, status in self.health_checker.health_status.items()
            },
        }


class LoadBalancedClient:
    """HTTP client with load balancing."""

    def __init__(self, load_balancer: LoadBalancer):
        """
        Initialize load balanced client.

        Args:
            load_balancer: Load balancer instance
        """
        self.load_balancer = load_balancer
        self.session = aiohttp.ClientSession()

    async def request(
        self, method: str, path: str, client_ip: Optional[str] = None, **kwargs
    ) -> Optional[aiohttp.ClientResponse]:
        """
        Make a load-balanced HTTP request.

        Args:
            method: HTTP method
            path: Request path
            client_ip: Client IP address
            **kwargs: Additional request parameters

        Returns:
            HTTP response or None if no healthy servers
        """
        server = await self.load_balancer.get_server(client_ip)
        if not server:
            return None

        try:
            self.load_balancer.increment_connection(server.id)

            url = f"{server.url.rstrip('/')}/{path.lstrip('/')}"
            async with self.session.request(method, url, **kwargs) as response:
                self.load_balancer.record_success(server.id)
                return response

        except Exception as e:
            self.load_balancer.record_failure(server.id)
            logger.error(f"Request failed for {server.url}: {e}")
            raise
        finally:
            self.load_balancer.decrement_connection(server.id)

    async def close(self):
        """Close the client session."""
        await self.session.close()


# Global load balancer instance
load_balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
