"""
Enterprise Resilience Service

This module implements comprehensive enterprise-grade resilience patterns including:
- Circuit Breaker Pattern
- Retry Mechanisms with Exponential Backoff
- Graceful Degradation
- Fault Tolerance and Recovery
- Health Checks and Monitoring
- Error Categorization and Severity Levels
- Automated Error Recovery Procedures
- Error Reporting and Alerting Systems

Author: Arxos Engineering Team
Date: December 2024
"""

import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from functools import wraps

import aiohttp
import prometheus_client
from pydantic import BaseModel

# Type variables for generic functions
T = TypeVar('T')
F = TypeVar('F', bound=Callable)

# Configure logging
logger = logging.getLogger(__name__)

# Prometheus metrics
circuit_breaker_state = prometheus_client.Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=half-open, 2=open)',
    ['service_name']
)

circuit_breaker_failures = prometheus_client.Counter(
    'circuit_breaker_failures_total',
    'Total circuit breaker failures',
    ['service_name']
)

circuit_breaker_successes = prometheus_client.Counter(
    'circuit_breaker_successes_total',
    'Total circuit breaker successes',
    ['service_name']
)

retry_attempts = prometheus_client.Counter(
    'retry_attempts_total',
    'Total retry attempts',
    ['service_name', 'operation']
)

retry_failures = prometheus_client.Counter(
    'retry_failures_total',
    'Total retry failures',
    ['service_name', 'operation']
)

health_check_status = prometheus_client.Gauge(
    'health_check_status',
    'Health check status (0=unhealthy, 1=healthy)',
    ['service_name', 'endpoint']
)

response_time_histogram = prometheus_client.Histogram(
    'response_time_seconds',
    'Response time in seconds',
    ['service_name', 'operation'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half-open"


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProcessingStatus(Enum):
    """Processing status for operations"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    name: str
    failure_threshold: int = 5
    timeout: float = 30.0
    reset_timeout: float = 60.0
    monitor_interval: float = 10.0
    enabled: bool = True


@dataclass
class RetryConfig:
    """Configuration for retry mechanism"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    retryable_status_codes: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])


@dataclass
class HealthCheckConfig:
    """Configuration for health checks"""
    endpoint: str
    timeout: float = 5.0
    interval: float = 30.0
    failure_threshold: int = 3
    success_threshold: int = 2


class CircuitBreaker:
    """Circuit Breaker Pattern Implementation"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.last_failure = None
        self.last_success = None
        self.next_attempt = None
        self._lock = asyncio.Lock()
        
        # Start monitoring if enabled
        if config.enabled:
            asyncio.create_task(self._monitor())
    
    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self.next_attempt and time.time() < self.next_attempt:
                    raise CircuitBreakerOpenError(f"Circuit breaker is open for {self.config.name}")
                else:
                    self.state = CircuitState.HALF_OPEN
            
            elif self.state == CircuitState.HALF_OPEN:
                # Allow limited requests in half-open state
                if not self._should_allow_request():
                    raise CircuitBreakerOpenError(f"Circuit breaker is half-open for {self.config.name}")
        
        # Execute with timeout
        try:
            start_time = time.time()
            result = await asyncio.wait_for(
                func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs),
                timeout=self.config.timeout
            )
            duration = time.time() - start_time
            
            await self._record_success(duration)
            return result
            
        except Exception as e:
            await self._record_failure(str(e))
            raise
    
    async def _record_success(self, duration: float):
        """Record successful operation"""
        async with self._lock:
            self.failures = 0
            self.last_success = time.time()
            self.state = CircuitState.CLOSED
            self.next_attempt = None
            
            circuit_breaker_successes.labels(service_name=self.config.name).inc()
            response_time_histogram.labels(
                service_name=self.config.name, 
                operation="circuit_breaker_success"
            ).observe(duration)
            
            logger.info(f"Circuit breaker success for {self.config.name} (duration: {duration:.3f}s)")
    
    async def _record_failure(self, error: str):
        """Record failed operation"""
        async with self._lock:
            self.failures += 1
            self.last_failure = time.time()
            
            circuit_breaker_failures.labels(service_name=self.config.name).inc()
            
            logger.warning(f"Circuit breaker failure for {self.config.name}: {error} (failures: {self.failures})")
            
            if self.failures >= self.config.failure_threshold:
                await self._open_circuit()
    
    async def _open_circuit(self):
        """Open the circuit breaker"""
        self.state = CircuitState.OPEN
        self.next_attempt = time.time() + self.config.reset_timeout
        
        circuit_breaker_state.labels(service_name=self.config.name).set(2.0)  # Open state
        
        logger.error(f"Circuit breaker opened for {self.config.name}")
    
    def _should_allow_request(self) -> bool:
        """Determine if request should be allowed in half-open state"""
        # Allow 10% of requests in half-open state
        return time.time() % 10 < 1
    
    async def _monitor(self):
        """Monitor circuit breaker state"""
        while True:
            try:
                await asyncio.sleep(self.config.monitor_interval)
                
                if self.state == CircuitState.OPEN and self.next_attempt and time.time() >= self.next_attempt:
                    async with self._lock:
                        self.state = CircuitState.HALF_OPEN
                        circuit_breaker_state.labels(service_name=self.config.name).set(1.0)  # Half-open state
                        logger.info(f"Circuit breaker transitioned to half-open for {self.config.name}")
                        
            except Exception as e:
                logger.error(f"Error in circuit breaker monitor for {self.config.name}: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return {
            "name": self.config.name,
            "state": self.state.value,
            "failures": self.failures,
            "last_failure": self.last_failure,
            "last_success": self.last_success,
            "next_attempt": self.next_attempt
        }


class RetryHandler:
    """Retry Mechanism with Exponential Backoff"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
    
    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with retry logic"""
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                start_time = time.time()
                result = await asyncio.wait_for(
                    func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs),
                    timeout=self.config.timeout if hasattr(self.config, 'timeout') else 30.0
                )
                duration = time.time() - start_time
                
                response_time_histogram.labels(
                    service_name=getattr(func, '__name__', 'unknown'),
                    operation="retry_success"
                ).observe(duration)
                
                return result
                
            except Exception as e:
                last_error = e
                retry_attempts.labels(
                    service_name=getattr(func, '__name__', 'unknown'),
                    operation="retry_attempt"
                ).inc()
                
                if attempt == self.config.max_retries:
                    retry_failures.labels(
                        service_name=getattr(func, '__name__', 'unknown'),
                        operation="retry_failure"
                    ).inc()
                    break
                
                # Check if error is retryable
                if not self._is_retryable_error(e):
                    break
                
                # Calculate delay with exponential backoff
                delay = min(
                    self.config.base_delay * (self.config.backoff_multiplier ** attempt),
                    self.config.max_delay
                )
                
                logger.warning(f"Retry attempt {attempt + 1}/{self.config.max_retries + 1} failed, retrying in {delay}s: {e}")
                await asyncio.sleep(delay)
        
        raise last_error
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Determine if error is retryable"""
        if hasattr(error, 'status_code'):
            return error.status_code in self.config.retryable_status_codes
        
        # Default retryable errors
        retryable_errors = (
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
            aiohttp.ClientError
        )
        
        return isinstance(error, retryable_errors)


class HealthChecker:
    """Health Check and Monitoring"""
    
    def __init__(self):
        self.checks: Dict[str, HealthCheckConfig] = {}
        self.status: Dict[str, Dict[str, Any]] = {}
        self._monitoring_task = None
    
    def add_check(self, name: str, config: HealthCheckConfig):
        """Add health check"""
        self.checks[name] = config
        self.status[name] = {
            "healthy": False,
            "last_check": None,
            "consecutive_failures": 0,
            "consecutive_successes": 0,
            "last_error": None
        }
    
    async def start_monitoring(self):
        """Start health check monitoring"""
        if self._monitoring_task:
            return
        
        self._monitoring_task = asyncio.create_task(self._monitor_loop())
        logger.info("Health check monitoring started")
    
    async def stop_monitoring(self):
        """Stop health check monitoring"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
            logger.info("Health check monitoring stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                await asyncio.gather(*[
                    self._check_health(name, config)
                    for name, config in self.checks.items()
                ])
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in health check monitoring: {e}")
                await asyncio.sleep(5)
    
    async def _check_health(self, name: str, config: HealthCheckConfig):
        """Perform health check"""
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(config.endpoint, timeout=config.timeout) as response:
                    duration = time.time() - start_time
                    
                    if response.status == 200:
                        await self._record_success(name, duration)
                    else:
                        await self._record_failure(name, f"HTTP {response.status}")
                        
        except Exception as e:
            await self._record_failure(name, str(e))
    
    async def _record_success(self, name: str, duration: float):
        """Record successful health check"""
        status = self.status[name]
        status["consecutive_successes"] += 1
        status["consecutive_failures"] = 0
        status["last_check"] = time.time()
        status["last_error"] = None
        
        if status["consecutive_successes"] >= self.checks[name].success_threshold:
            if not status["healthy"]:
                status["healthy"] = True
                logger.info(f"Health check {name} became healthy")
        
        health_check_status.labels(service_name=name, endpoint=self.checks[name].endpoint).set(1.0)
        response_time_histogram.labels(service_name=name, operation="health_check").observe(duration)
    
    async def _record_failure(self, name: str, error: str):
        """Record failed health check"""
        status = self.status[name]
        status["consecutive_failures"] += 1
        status["consecutive_successes"] = 0
        status["last_check"] = time.time()
        status["last_error"] = error
        
        if status["consecutive_failures"] >= self.checks[name].failure_threshold:
            if status["healthy"]:
                status["healthy"] = False
                logger.error(f"Health check {name} became unhealthy: {error}")
        
        health_check_status.labels(service_name=name, endpoint=self.checks[name].endpoint).set(0.0)
    
    def get_status(self) -> Dict[str, Any]:
        """Get health check status"""
        return {
            "checks": self.status,
            "overall_healthy": all(status["healthy"] for status in self.status.values())
        }


class GracefulDegradation:
    """Graceful Degradation Implementation"""
    
    def __init__(self):
        self.fallbacks: Dict[str, Callable] = {}
        self.degradation_levels: Dict[str, List[Callable]] = {}
    
    def add_fallback(self, operation: str, fallback_func: Callable):
        """Add fallback function for operation"""
        self.fallbacks[operation] = fallback_func
    
    def add_degradation_level(self, operation: str, level: int, func: Callable):
        """Add degradation level function"""
        if operation not in self.degradation_levels:
            self.degradation_levels[operation] = []
        
        while len(self.degradation_levels[operation]) <= level:
            self.degradation_levels[operation].append(None)
        
        self.degradation_levels[operation][level] = func
    
    async def execute_with_graceful_degradation(
        self, 
        operation: str, 
        primary_func: Callable, 
        *args, 
        **kwargs
    ) -> Any:
        """Execute with graceful degradation"""
        try:
            return await primary_func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Primary operation {operation} failed, attempting graceful degradation: {e}")
            
            # Try degradation levels
            if operation in self.degradation_levels:
                for level, func in enumerate(self.degradation_levels[operation]):
                    if func is not None:
                        try:
                            logger.info(f"Trying degradation level {level} for {operation}")
                            return await func(*args, **kwargs)
                        except Exception as level_error:
                            logger.warning(f"Degradation level {level} failed for {operation}: {level_error}")
            
            # Try fallback
            if operation in self.fallbacks:
                try:
                    logger.info(f"Using fallback for {operation}")
                    return await self.fallbacks[operation](*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"Fallback failed for {operation}: {fallback_error}")
            
            raise e


class ErrorCategorizer:
    """Error Categorization and Severity Levels"""
    
    def __init__(self):
        self.error_patterns: Dict[str, ErrorSeverity] = {
            "timeout": ErrorSeverity.MEDIUM,
            "connection": ErrorSeverity.MEDIUM,
            "authentication": ErrorSeverity.HIGH,
            "authorization": ErrorSeverity.HIGH,
            "validation": ErrorSeverity.LOW,
            "database": ErrorSeverity.HIGH,
            "network": ErrorSeverity.MEDIUM,
            "resource": ErrorSeverity.MEDIUM,
            "system": ErrorSeverity.CRITICAL
        }
    
    def categorize_error(self, error: Exception) -> ErrorSeverity:
        """Categorize error by severity"""
        error_str = str(error).lower()
        
        for pattern, severity in self.error_patterns.items():
            if pattern in error_str:
                return severity
        
        return ErrorSeverity.MEDIUM
    
    def should_alert(self, error: Exception) -> bool:
        """Determine if error should trigger alert"""
        severity = self.categorize_error(error)
        return severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]


class EnterpriseResilienceService:
    """Main Enterprise Resilience Service"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_handlers: Dict[str, RetryHandler] = {}
        self.health_checker = HealthChecker()
        self.graceful_degradation = GracefulDegradation()
        self.error_categorizer = ErrorCategorizer()
        
        # Start health monitoring
        asyncio.create_task(self.health_checker.start_monitoring())
    
    def add_circuit_breaker(self, name: str, config: CircuitBreakerConfig):
        """Add circuit breaker"""
        self.circuit_breakers[name] = CircuitBreaker(config)
        logger.info(f"Added circuit breaker: {name}")
    
    def add_retry_handler(self, name: str, config: RetryConfig):
        """Add retry handler"""
        self.retry_handlers[name] = RetryHandler(config)
        logger.info(f"Added retry handler: {name}")
    
    def add_health_check(self, name: str, config: HealthCheckConfig):
        """Add health check"""
        self.health_checker.add_check(name, config)
        logger.info(f"Added health check: {name}")
    
    async def execute_with_resilience(
        self,
        operation_name: str,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """Execute function with full resilience patterns"""
        operation_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Apply circuit breaker if available
            if operation_name in self.circuit_breakers:
                circuit_breaker = self.circuit_breakers[operation_name]
                
                # Apply retry if available
                if operation_name in self.retry_handlers:
                    retry_handler = self.retry_handlers[operation_name]
                    
                    async def retryable_func():
                        return await retry_handler.execute(func, *args, **kwargs)
                    
                    result = await circuit_breaker.execute(retryable_func)
                else:
                    result = await circuit_breaker.execute(func, *args, **kwargs)
            else:
                # Apply retry if available
                if operation_name in self.retry_handlers:
                    retry_handler = self.retry_handlers[operation_name]
                    result = await retry_handler.execute(func, *args, **kwargs)
                else:
                    result = await func(*args, **kwargs)
            
            duration = time.time() - start_time
            logger.info(f"Operation {operation_name} completed successfully in {duration:.3f}s")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            severity = self.error_categorizer.categorize_error(e)
            
            logger.error(
                f"Operation {operation_name} failed after {duration:.3f}s: {e} (severity: {severity.value})"
            )
            
            if self.error_categorizer.should_alert(e):
                await self._send_alert(operation_name, e, severity, duration)
            
            raise
    
    async def _send_alert(self, operation: str, error: Exception, severity: ErrorSeverity, duration: float):
        """Send alert for critical errors"""
        alert_data = {
            "operation": operation,
            "error": str(error),
            "severity": severity.value,
            "duration": duration,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # TODO: Implement actual alerting (Slack, email, etc.)
        logger.critical(f"ALERT: {alert_data}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive resilience status"""
        return {
            "circuit_breakers": {
                name: cb.get_status() for name, cb in self.circuit_breakers.items()
            },
            "health_checks": self.health_checker.get_status(),
            "overall_healthy": self.health_checker.get_status()["overall_healthy"]
        }


# Decorators for easy integration
def resilient(operation_name: str, circuit_breaker: Optional[str] = None, retry: Optional[str] = None):
    """Decorator for resilient operations"""
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get resilience service instance
            # This would typically be injected or retrieved from a service locator
            resilience_service = EnterpriseResilienceService()
            
            return await resilience_service.execute_with_resilience(
                operation_name, func, *args, **kwargs
            )
        
        return wrapper
    return decorator


# Custom exceptions
class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class ResilienceError(Exception):
    """Base exception for resilience errors"""
    pass


# Example usage and configuration
async def setup_enterprise_resilience():
    """Setup enterprise resilience patterns"""
    resilience_service = EnterpriseResilienceService()
    
    # Add circuit breakers
    resilience_service.add_circuit_breaker(
        "database",
        CircuitBreakerConfig(
            name="database",
            failure_threshold=5,
            timeout=30.0,
            reset_timeout=60.0
        )
    )
    
    resilience_service.add_circuit_breaker(
        "external_api",
        CircuitBreakerConfig(
            name="external_api",
            failure_threshold=3,
            timeout=10.0,
            reset_timeout=30.0
        )
    )
    
    # Add retry handlers
    resilience_service.add_retry_handler(
        "database_operations",
        RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=10.0
        )
    )
    
    # Add health checks
    resilience_service.add_health_check(
        "database",
        HealthCheckConfig(
            endpoint="http://localhost:5432/health",
            timeout=5.0,
            interval=30.0
        )
    )
    
    resilience_service.add_health_check(
        "external_api",
        HealthCheckConfig(
            endpoint="http://api.external.com/health",
            timeout=10.0,
            interval=60.0
        )
    )
    
    return resilience_service


if __name__ == "__main__":
    # Example usage
    async def main():
        resilience_service = await setup_enterprise_resilience()
        
        # Example resilient operation
        @resilient("database_query", circuit_breaker="database", retry="database_operations")
        async def query_database():
            # Simulate database query
            await asyncio.sleep(0.1)
            return {"result": "success"}
        
        try:
            result = await query_database()
            print(f"Query result: {result}")
        except Exception as e:
            print(f"Query failed: {e}")
        
        # Get status
        status = resilience_service.get_status()
        print(f"Resilience status: {status}")
    
    asyncio.run(main()) 