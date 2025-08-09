"""
Comprehensive Tests for Enterprise Resilience Service

This module tests all enterprise resilience patterns including:
- Circuit Breaker Pattern
- Retry Mechanisms with Exponential Backoff
- Graceful Degradation
- Health Checks and Monitoring
- Error Categorization and Severity Levels
- Automated Error Recovery Procedures
- Error Reporting and Alerting Systems

Author: Arxos Engineering Team
Date: December 2024
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from svgx_engine.services.enterprise_resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    RetryHandler,
    RetryConfig,
    HealthChecker,
    HealthCheckConfig,
    GracefulDegradation,
    ErrorCategorizer,
    ErrorSeverity,
    EnterpriseResilienceService,
    CircuitBreakerOpenError,
    resilient
)


class TestCircuitBreaker:
    """Test Circuit Breaker Pattern Implementation"""

    @pytest.fixture
def circuit_breaker_config(self):
        """Create circuit breaker configuration for testing"""
        return CircuitBreakerConfig(
            name="test_service",
            failure_threshold=3,
            timeout=1.0,
            reset_timeout=2.0,
            monitor_interval=0.1,
            enabled=False  # Disable monitoring for tests
        )

    @pytest.fixture
def circuit_breaker(self, circuit_breaker_config):
        """Create circuit breaker instance for testing"""
        return CircuitBreaker(circuit_breaker_config)

    @pytest.mark.asyncio
    async def test_circuit_breaker_initial_state(self, circuit_breaker):
        """Test circuit breaker initial state"""
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.failures == 0
        assert circuit_breaker.last_failure is None
        assert circuit_breaker.last_success is None

    @pytest.mark.asyncio
    async def test_circuit_breaker_successful_execution(self, circuit_breaker):
        """Test successful execution through circuit breaker"""
        async def successful_func():
            return "success"

        result = await circuit_breaker.execute(successful_func)
        assert result == "success"
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.failures == 0
        assert circuit_breaker.last_success is not None

    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_tracking(self, circuit_breaker):
        """Test failure tracking in circuit breaker"""
        async def failing_func():
            raise Exception("Test failure")

        with pytest.raises(Exception, match="Test failure"):
            await circuit_breaker.execute(failing_func)

        assert circuit_breaker.failures == 1
        assert circuit_breaker.last_failure is not None
        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_opening(self, circuit_breaker):
        """Test circuit breaker opening after threshold failures"""
        async def failing_func():
            raise Exception("Test failure")

        # Execute failing function multiple times to trigger circuit opening
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.execute(failing_func)

        assert circuit_breaker.state == CircuitState.OPEN
        assert circuit_breaker.failures >= 3

    @pytest.mark.asyncio
    async def test_circuit_breaker_open_state_rejection(self, circuit_breaker):
        """Test that circuit breaker rejects requests when open"""
        # First, open the circuit
        async def failing_func():
            raise Exception("Test failure")

        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.execute(failing_func)

        # Now try to execute a successful function
        async def successful_func():
            return "success"

        with pytest.raises(CircuitBreakerOpenError):
            await circuit_breaker.execute(successful_func)

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_state(self, circuit_breaker):
        """Test circuit breaker half-open state behavior"""
        # Open the circuit
        async def failing_func():
            raise Exception("Test failure")

        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.execute(failing_func)

        # Manually set to half-open state
        circuit_breaker.state = CircuitState.HALF_OPEN

        # Test that some requests are allowed in half-open state
        async def successful_func():
            return "success"

        # The half-open state allows 10% of requests
        # We'll test multiple times to ensure some pass'
        results = []
        for _ in range(20):
            try:
                result = await circuit_breaker.execute(successful_func)
                results.append(result)
            except CircuitBreakerOpenError:
                pass

        # Should have some successful executions
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_timeout(self, circuit_breaker):
        """Test circuit breaker timeout handling"""
        async def slow_func():
            await asyncio.sleep(2.0)  # Longer than timeout
            return "success"

        with pytest.raises(asyncio.TimeoutError):
            await circuit_breaker.execute(slow_func)

        assert circuit_breaker.failures == 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_status(self, circuit_breaker):
        """Test circuit breaker status reporting"""
        status = circuit_breaker.get_status()

        assert "name" in status
        assert "state" in status
        assert "failures" in status
        assert "last_failure" in status
        assert "last_success" in status
        assert "next_attempt" in status


class TestRetryHandler:
    """Test Retry Mechanism Implementation"""

    @pytest.fixture
def retry_config(self):
        """Create retry configuration for testing"""
        return RetryConfig(
            max_retries=3,
            base_delay=0.1,
            max_delay=1.0,
            backoff_multiplier=2.0
        )

    @pytest.fixture
def retry_handler(self, retry_config):
        """Create retry handler instance for testing"""
        return RetryHandler(retry_config)

    @pytest.mark.asyncio
    async def test_retry_handler_successful_execution(self, retry_handler):
        """Test successful execution without retries"""
        async def successful_func():
            return "success"

        result = await retry_handler.execute(successful_func)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_handler_with_retries(self, retry_handler):
        """Test retry mechanism with eventual success"""
        call_count = 0

        async def failing_then_successful_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"

        result = await retry_handler.execute(failing_then_successful_func)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_handler_max_retries_exceeded(self, retry_handler):
        """Test retry mechanism when max retries are exceeded"""
        call_count = 0

        async def always_failing_func():
            nonlocal call_count
            call_count += 1
            raise Exception("Persistent failure")

        with pytest.raises(Exception, match="Persistent failure"):
            await retry_handler.execute(always_failing_func)

        assert call_count == 4  # Initial call + 3 retries

    @pytest.mark.asyncio
    async def test_retry_handler_exponential_backoff(self, retry_handler):
        """Test exponential backoff timing"""
        start_time = time.time()
        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            raise Exception("Failure")

        with pytest.raises(Exception):
            await retry_handler.execute(failing_func)

        end_time = time.time()
        duration = end_time - start_time

        # Should have delays: 0.1s, 0.2s, 0.4s = 0.7s minimum
        assert duration >= 0.7
        assert call_count == 4

    @pytest.mark.asyncio
    async def test_retry_handler_non_retryable_error(self, retry_handler):
        """Test that non-retryable errors are not retried"""
        call_count = 0

        async def non_retryable_error_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Non-retryable error")

        with pytest.raises(ValueError, match="Non-retryable error"):
            await retry_handler.execute(non_retryable_error_func)

        assert call_count == 1  # No retries for non-retryable errors


class TestHealthChecker:
    """Test Health Check Implementation"""

    @pytest.fixture
def health_checker(self):
        """Create health checker instance for testing"""
        return HealthChecker()

    @pytest.fixture
def health_config(self):
        """Create health check configuration for testing"""
        return HealthCheckConfig(
            endpoint="http://localhost:8080/health",
            timeout=1.0,
            interval=0.1,
            failure_threshold=2,
            success_threshold=2
        )

    @pytest.mark.asyncio
    async def test_health_checker_add_check(self, health_checker, health_config):
        """Test adding health checks"""
        health_checker.add_check("test_service", health_config)

        assert "test_service" in health_checker.checks
        assert "test_service" in health_checker.status

        status = health_checker.status["test_service"]
        assert status["healthy"] is False
        assert status["consecutive_failures"] == 0
        assert status["consecutive_successes"] == 0

    @pytest.mark.asyncio
    async def test_health_checker_status(self, health_checker):
        """Test health checker status reporting"""
        status = health_checker.get_status()

        assert "checks" in status
        assert "overall_healthy" in status
        assert isinstance(status["checks"], dict)
        assert isinstance(status["overall_healthy"], bool)


class TestGracefulDegradation:
    """Test Graceful Degradation Implementation"""

    @pytest.fixture
def graceful_degradation(self):
        """Create graceful degradation instance for testing"""
        return GracefulDegradation()

    @pytest.mark.asyncio
    async def test_graceful_degradation_with_fallback(self, graceful_degradation):
        """Test graceful degradation with fallback function"""
        call_count = {"primary": 0, "fallback": 0}

        async def primary_func():
            call_count["primary"] += 1
            raise Exception("Primary function failed")

        async def fallback_func():
            call_count["fallback"] += 1
            return "fallback_result"

        graceful_degradation.add_fallback("test_operation", fallback_func)

        result = await graceful_degradation.execute_with_graceful_degradation(
            "test_operation", primary_func
        )

        assert result == "fallback_result"
        assert call_count["primary"] == 1
        assert call_count["fallback"] == 1

    @pytest.mark.asyncio
    async def test_graceful_degradation_with_levels(self, graceful_degradation):
        """Test graceful degradation with multiple levels"""
        call_count = {"primary": 0, "level1": 0, "level2": 0}

        async def primary_func():
            call_count["primary"] += 1
            raise Exception("Primary function failed")

        async def level1_func():
            call_count["level1"] += 1
            raise Exception("Level 1 failed")

        async def level2_func():
            call_count["level2"] += 1
            return "level2_result"

        graceful_degradation.add_degradation_level("test_operation", 0, level1_func)
        graceful_degradation.add_degradation_level("test_operation", 1, level2_func)

        result = await graceful_degradation.execute_with_graceful_degradation(
            "test_operation", primary_func
        )

        assert result == "level2_result"
        assert call_count["primary"] == 1
        assert call_count["level1"] == 1
        assert call_count["level2"] == 1


class TestErrorCategorizer:
    """Test Error Categorization Implementation"""

    @pytest.fixture
def error_categorizer(self):
        """Create error categorizer instance for testing"""
        return ErrorCategorizer()

    def test_error_categorization(self, error_categorizer):
        """Test error categorization by severity"""
        # Test timeout error
        timeout_error = Exception("Request timeout after 30 seconds")
        severity = error_categorizer.categorize_error(timeout_error)
        assert severity == ErrorSeverity.MEDIUM

        # Test authentication error
        auth_error = Exception("Authentication failed")
        severity = error_categorizer.categorize_error(auth_error)
        assert severity == ErrorSeverity.HIGH

        # Test validation error
        validation_error = Exception("Invalid input validation")
        severity = error_categorizer.categorize_error(validation_error)
        assert severity == ErrorSeverity.LOW

        # Test system error
        system_error = Exception("System crash detected")
        severity = error_categorizer.categorize_error(system_error)
        assert severity == ErrorSeverity.CRITICAL

    def test_alert_determination(self, error_categorizer):
        """Test alert determination based on error severity"""
        # High severity should trigger alert
        high_error = Exception("Authentication failed")
        assert error_categorizer.should_alert(high_error) is True

        # Critical severity should trigger alert
        critical_error = Exception("System crash detected")
        assert error_categorizer.should_alert(critical_error) is True

        # Low severity should not trigger alert
        low_error = Exception("Invalid input validation")
        assert error_categorizer.should_alert(low_error) is False

        # Medium severity should not trigger alert
        medium_error = Exception("Request timeout")
        assert error_categorizer.should_alert(medium_error) is False


class TestEnterpriseResilienceService:
    """Test Main Enterprise Resilience Service"""

    @pytest.fixture
def resilience_service(self):
        """Create enterprise resilience service instance for testing"""
        return EnterpriseResilienceService()

    @pytest.mark.asyncio
    async def test_resilience_service_initialization(self, resilience_service):
        """Test resilience service initialization"""
        assert resilience_service.circuit_breakers == {}
        assert resilience_service.retry_handlers == {}
        assert isinstance(resilience_service.health_checker, HealthChecker)
        assert isinstance(resilience_service.graceful_degradation, GracefulDegradation)
        assert isinstance(resilience_service.error_categorizer, ErrorCategorizer)

    @pytest.mark.asyncio
    async def test_add_circuit_breaker(self, resilience_service):
        """Test adding circuit breakers to resilience service"""
        config = CircuitBreakerConfig(name="test_service")
        resilience_service.add_circuit_breaker("test_service", config)

        assert "test_service" in resilience_service.circuit_breakers
        assert isinstance(resilience_service.circuit_breakers["test_service"], CircuitBreaker)

    @pytest.mark.asyncio
    async def test_add_retry_handler(self, resilience_service):
        """Test adding retry handlers to resilience service"""
        config = RetryConfig(max_retries=3)
        resilience_service.add_retry_handler("test_operation", config)

        assert "test_operation" in resilience_service.retry_handlers
        assert isinstance(resilience_service.retry_handlers["test_operation"], RetryHandler)

    @pytest.mark.asyncio
    async def test_add_health_check(self, resilience_service):
        """Test adding health checks to resilience service"""
        config = HealthCheckConfig(endpoint="http://localhost:8080/health")
        resilience_service.add_health_check("test_service", config)

        assert "test_service" in resilience_service.health_checker.checks

    @pytest.mark.asyncio
    async def test_execute_with_resilience_success(self, resilience_service):
        """Test successful execution with resilience patterns"""
        async def successful_func():
            return "success"

        result = await resilience_service.execute_with_resilience(
            "test_operation", successful_func
        )

        assert result == "success"

    @pytest.mark.asyncio
    async def test_execute_with_resilience_with_circuit_breaker(self, resilience_service):
        """Test execution with circuit breaker protection"""
        config = CircuitBreakerConfig(
            name="test_service",
            failure_threshold=5,
            timeout=1.0,
            enabled=False
        )
        resilience_service.add_circuit_breaker("test_service", config)

        async def successful_func():
            return "success"

        result = await resilience_service.execute_with_resilience(
            "test_service", successful_func
        )

        assert result == "success"

    @pytest.mark.asyncio
    async def test_execute_with_resilience_with_retry(self, resilience_service):
        """Test execution with retry mechanism"""
        config = RetryConfig(max_retries=2, base_delay=0.1)
        resilience_service.add_retry_handler("test_operation", config)

        call_count = 0

        async def failing_then_successful_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "success"

        result = await resilience_service.execute_with_resilience(
            "test_operation", failing_then_successful_func
        )

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_resilience_with_both_patterns(self, resilience_service):
        """Test execution with both circuit breaker and retry patterns"""
        circuit_config = CircuitBreakerConfig(
            name="test_service",
            failure_threshold=5,
            timeout=1.0,
            enabled=False
        )
        retry_config = RetryConfig(max_retries=2, base_delay=0.1)

        resilience_service.add_circuit_breaker("test_service", circuit_config)
        resilience_service.add_retry_handler("test_service", retry_config)

        call_count = 0

        async def failing_then_successful_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "success"

        result = await resilience_service.execute_with_resilience(
            "test_service", failing_then_successful_func
        )

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_get_status(self, resilience_service):
        """Test resilience service status reporting"""
        # Add some components
        circuit_config = CircuitBreakerConfig(name="test_service")
        resilience_service.add_circuit_breaker("test_service", circuit_config)

        retry_config = RetryConfig(max_retries=3)
        resilience_service.add_retry_handler("test_operation", retry_config)

        health_config = HealthCheckConfig(endpoint="http://localhost:8080/health")
        resilience_service.add_health_check("test_service", health_config)

        status = resilience_service.get_status()

        assert "circuit_breakers" in status
        assert "health_checks" in status
        assert "overall_healthy" in status
        assert "test_service" in status["circuit_breakers"]


class TestResilientDecorator:
    """Test Resilient Decorator"""

    @pytest.mark.asyncio
    async def test_resilient_decorator(self):
        """Test resilient decorator functionality"""
        call_count = 0

        @resilient("test_operation")
        async def test_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 1


class TestIntegration:
    """Integration Tests for Enterprise Resilience"""

    @pytest.mark.asyncio
    async def test_full_resilience_workflow(self):
        """Test complete resilience workflow"""
        resilience_service = EnterpriseResilienceService()

        # Add circuit breaker
        circuit_config = CircuitBreakerConfig(
            name="database",
            failure_threshold=3,
            timeout=1.0,
            enabled=False
        )
        resilience_service.add_circuit_breaker("database", circuit_config)

        # Add retry handler
        retry_config = RetryConfig(max_retries=2, base_delay=0.1)
        resilience_service.add_retry_handler("database_operation", retry_config)

        # Add health check
        health_config = HealthCheckConfig(
            endpoint="http://localhost:5432/health",
            timeout=1.0
        )
        resilience_service.add_health_check("database", health_config)

        # Test successful operation
        async def database_query():
            return {"result": "success"}

        result = await resilience_service.execute_with_resilience(
            "database", database_query
        )

        assert result == {"result": "success"}

        # Test status reporting
        status = resilience_service.get_status()
        assert "database" in status["circuit_breakers"]
        assert "overall_healthy" in status

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms"""
        resilience_service = EnterpriseResilienceService()

        # Add retry handler
        retry_config = RetryConfig(max_retries=3, base_delay=0.1)
        resilience_service.add_retry_handler("unreliable_operation", retry_config)

        call_count = 0

        async def unreliable_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "recovered"

        result = await resilience_service.execute_with_resilience(
            "unreliable_operation", unreliable_operation
        )

        assert result == "recovered"
        assert call_count == 3


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
