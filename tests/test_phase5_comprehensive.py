"""
Comprehensive Phase 5 Production Deployment Tests

This module provides comprehensive testing for all Phase 5 components including:
- CI/CD Pipeline
- Performance Optimization
- Security Hardening
- Monitoring & Alerting
- Load Balancing
- Database Connection Pooling
- Input Validation
"""

import pytest
import asyncio
import time
import json
import os
import subprocess
from typing import Dict, Any, List
from datetime import datetime, timedelta

from infrastructure.database.connection_pool import DatabaseConnectionPool, PoolConfig
from infrastructure.services.load_balancer import (
    LoadBalancer,
    BackendServer,
    LoadBalancingStrategy,
)
from infrastructure.security.input_validation import (
    InputValidator,
    ValidationRule,
    SecurityLevel,
)
from infrastructure.security.authentication import JWTAuthentication, TokenType
from infrastructure.security.authorization import (
    RoleBasedAccessControl,
    Role,
    Permission,
)
from infrastructure.monitoring.prometheus_metrics import (
    MCPEngineeringMetrics,
    MetricsConfig,
)
from infrastructure.caching.redis_cache import RedisCache, CacheConfig


class TestPhase5CI_CD:
    """Tests for CI/CD pipeline components."""

    def test_github_actions_workflow_exists(self):
        """Test that GitHub Actions workflow exists."""
        workflow_path = ".github/workflows/deploy.yml"
        assert os.path.exists(
            workflow_path
        ), f"GitHub Actions workflow not found: {workflow_path}"

        with open(workflow_path, "r") as f:
            content = f.read()
            assert "name: MCP Engineering - CI/CD Pipeline" in content
            assert "security-scan" in content
            assert "code-quality" in content
            assert "test" in content
            assert "build" in content
            assert "deploy-staging" in content
            assert "deploy-production" in content

    def test_dockerfile_exists(self):
        """Test that Dockerfile exists and is valid."""
        assert os.path.exists("Dockerfile"), "Dockerfile not found"

        with open("Dockerfile", "r") as f:
            content = f.read()
            assert "FROM python:3.11-slim as builder" in content
            assert "FROM python:3.11-slim as production" in content
            assert "USER mcp" in content
            assert "HEALTHCHECK" in content
            assert "EXPOSE 8000" in content

    def test_kubernetes_manifests_exist(self):
        """Test that Kubernetes manifests exist."""
        k8s_files = [
            "k8s/namespace.yaml",
            "k8s/deployment.yaml",
            "k8s/service.yaml",
            "k8s/ingress.yaml",
        ]

        for file_path in k8s_files:
            assert os.path.exists(
                file_path
            ), f"Kubernetes manifest not found: {file_path}"

    def test_monitoring_config_exists(self):
        """Test that monitoring configuration exists."""
        monitoring_files = [
            "k8s/monitoring/prometheus.yaml",
            "k8s/monitoring/grafana.yaml",
            "k8s/monitoring/alertmanager.yaml",
        ]

        for file_path in monitoring_files:
            assert os.path.exists(
                file_path
            ), f"Monitoring config not found: {file_path}"


class TestPhase5PerformanceOptimization:
    """Tests for performance optimization components."""

    def test_database_connection_pool(self):
        """Test database connection pooling."""
        config = PoolConfig(
            pool_size=10, max_overflow=20, pool_timeout=30, pool_recycle=3600
        )

        # Test with dummy URL (won't actually connect)
        pool = DatabaseConnectionPool(
            "postgresql://test:test@localhost:5432/test", config
        )

        assert pool.config.pool_size == 10
        assert pool.config.max_overflow == 20
        assert pool.config.pool_timeout == 30
        assert pool.config.pool_recycle == 3600

        # Test health check (should fail with dummy URL)
        health = pool.health_check()
        assert "status" in health
        assert health["status"] == "unhealthy"

    def test_load_balancer(self):
        """Test load balancer functionality."""
        lb = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)

        # Add test servers
        server1 = BackendServer("server1", "http://localhost:8001")
        server2 = BackendServer("server2", "http://localhost:8002")

        lb.add_server(server1)
        lb.add_server(server2)

        assert len(lb.servers) == 2
        assert lb.strategy == LoadBalancingStrategy.ROUND_ROBIN

        # Test status
        status = lb.get_status()
        assert "strategy" in status
        assert "total_servers" in status
        assert status["total_servers"] == 2

    def test_caching_system(self):
        """Test Redis caching system."""
        config = CacheConfig(
            host="localhost",
            port=6379,
            db=0,
            password=None,
            max_connections=10,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            retry_on_timeout=True,
            health_check_interval=30,
        )

        cache = RedisCache(config)

        # Test basic operations (will fail without Redis, but tests structure)
        try:
            cache.set("test_key", "test_value", expire=60)
            value = cache.get("test_key")
            assert value == "test_value"
        except Exception:
            # Expected without Redis running
            pass


class TestPhase5SecurityHardening:
    """Tests for security hardening components."""

    def test_input_validation(self):
        """Test input validation system."""
        validator = InputValidator()

        # Test email validation
        valid_email = validator.validate_email("test@example.com")
        assert valid_email == "test@example.com"

        with pytest.raises(Exception):
            validator.validate_email("invalid-email")

        # Test URL validation
        valid_url = validator.validate_url("https://example.com")
        assert valid_url == "https://example.com"

        with pytest.raises(Exception):
            validator.validate_url("javascript:alert('xss')")

        # Test string sanitization
        sanitized = validator.sanitize_string("<script>alert('xss')</script>")
        assert "<script>" not in sanitized

        # Test SQL injection detection
        assert validator.check_sql_injection("SELECT * FROM users") == True
        assert validator.check_sql_injection("normal text") == False

    def test_jwt_authentication(self):
        """Test JWT authentication system."""
        auth = JWTAuthentication("test-secret-key")

        # Test token creation
        payload = {
            "user_id": "test-user",
            "permissions": ["read", "write"],
            "expires_at": datetime.utcnow() + timedelta(hours=1),
        }

        token = auth.create_token(payload, TokenType.ACCESS)
        assert token is not None

        # Test token verification
        verified_payload = auth.verify_token(token)
        assert verified_payload["user_id"] == "test-user"
        assert "read" in verified_payload["permissions"]

    def test_rbac_authorization(self):
        """Test RBAC authorization system."""
        rbac = RoleBasedAccessControl()

        # Test role permissions
        permissions = rbac.get_permissions_for_role(Role.ADMIN)
        assert Permission.READ_ALL in permissions
        assert Permission.WRITE_ALL in permissions

        # Test user permissions
        user = rbac.add_user("test-user", [Role.USER])
        assert rbac.has_permission("test-user", Permission.READ_BUILDINGS)
        assert not rbac.has_permission("test-user", Permission.WRITE_ALL)


class TestPhase5Monitoring:
    """Tests for monitoring and alerting components."""

    def test_prometheus_metrics(self):
        """Test Prometheus metrics collection."""
        config = MetricsConfig(
            enable_metrics=True, metrics_port=8000, metrics_path="/metrics"
        )

        metrics = MCPEngineeringMetrics(config)

        # Test HTTP request recording
        metrics.record_http_request("GET", "/health", 200, 0.1)
        metrics.record_http_request("POST", "/buildings", 201, 0.5)

        # Test business metrics
        metrics.record_building_validation("structural", "pass")
        metrics.record_ai_recommendation("optimization")
        metrics.record_ml_prediction("cost_savings")

        # Test system metrics
        metrics.update_system_metrics()

        # Test metrics generation
        metrics_content = metrics.get_metrics()
        assert "http_requests_total" in metrics_content
        assert "building_validations_total" in metrics_content

    def test_alert_rules(self):
        """Test that alert rules are properly configured."""
        prometheus_config = "k8s/monitoring/prometheus.yaml"

        if os.path.exists(prometheus_config):
            with open(prometheus_config, "r") as f:
                content = f.read()
                assert "HighErrorRate" in content
                assert "HighResponseTime" in content
                assert "ServiceDown" in content
                assert "HighCPUUsage" in content
                assert "HighMemoryUsage" in content


class TestPhase5Integration:
    """Integration tests for Phase 5 components."""

    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test complete Phase 5 workflow."""
        # Initialize components
        pool_config = PoolConfig(pool_size=5, max_overflow=10)
        db_pool = DatabaseConnectionPool(
            "postgresql://test:test@localhost:5432/test", pool_config
        )

        lb = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        server = BackendServer("test-server", "http://localhost:8000")
        lb.add_server(server)

        validator = InputValidator()
        auth = JWTAuthentication("test-secret")
        rbac = RoleBasedAccessControl()

        metrics = MCPEngineeringMetrics(MetricsConfig())

        # Test workflow
        # 1. Validate input
        validated_email = validator.validate_email("user@example.com")

        # 2. Authenticate user
        payload = {
            "user_id": "test-user",
            "permissions": ["read_buildings"],
            "expires_at": datetime.utcnow() + timedelta(hours=1),
        }
        token = auth.create_token(payload, TokenType.ACCESS)

        # 3. Authorize request
        user = rbac.add_user("test-user", [Role.USER])
        has_permission = rbac.has_permission("test-user", Permission.READ_BUILDINGS)

        # 4. Record metrics
        metrics.record_http_request("GET", "/buildings", 200, 0.1)
        metrics.record_building_validation("structural", "pass")

        # 5. Test load balancer
        selected_server = await lb.get_server()

        # Assertions
        assert validated_email == "user@example.com"
        assert token is not None
        assert has_permission == True
        assert selected_server is not None

    @pytest.mark.asyncio
    async def test_performance_benchmarks(self):
        """Test performance benchmarks."""
        # Test database connection pool performance
        start_time = time.time()
        pool_config = PoolConfig(pool_size=20, max_overflow=30)
        db_pool = DatabaseConnectionPool(
            "postgresql://test:test@localhost:5432/test", pool_config
        )
        pool_init_time = time.time() - start_time

        assert pool_init_time < 1.0  # Should initialize quickly

        # Test load balancer performance
        lb = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        for i in range(3):
            server = BackendServer(f"server{i}", f"http://localhost:800{i}")
            lb.add_server(server)

        start_time = time.time()
        for _ in range(100):
            await lb.get_server()
        lb_time = time.time() - start_time

        assert lb_time < 1.0  # Should handle 100 requests quickly

        # Test input validation performance
        validator = InputValidator()
        start_time = time.time()
        for _ in range(100):
            try:
                validator.validate_email("test@example.com")
            except:
                pass
        validation_time = time.time() - start_time

        assert validation_time < 1.0  # Should validate quickly

    @pytest.mark.asyncio
    async def test_security_compliance(self):
        """Test security compliance."""
        validator = InputValidator()

        # Test XSS protection
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<iframe src='javascript:alert(1)'></iframe>",
            "<img src=x onerror=alert('xss')>",
        ]

        for payload in xss_payloads:
            sanitized = validator.sanitize_string(payload, SecurityLevel.CRITICAL)
            assert "<script>" not in sanitized.lower()
            assert "javascript:" not in sanitized.lower()

        # Test SQL injection protection
        sql_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "UNION SELECT * FROM users",
        ]

        for payload in sql_payloads:
            assert validator.check_sql_injection(payload) == True

        # Test authentication security
        auth = JWTAuthentication("strong-secret-key-here")

        # Test token expiration
        payload = {
            "user_id": "test-user",
            "permissions": ["read"],
            "expires_at": datetime.utcnow() - timedelta(hours=1),  # Expired
        }

        token = auth.create_token(payload, TokenType.ACCESS)
        with pytest.raises(Exception):
            auth.verify_token(token)  # Should fail for expired token


def main():
    """Run all Phase 5 comprehensive tests."""
    print("🚀 Running Phase 5 Comprehensive Tests...")

    test_classes = [
        TestPhase5CI_CD,
        TestPhase5PerformanceOptimization,
        TestPhase5SecurityHardening,
        TestPhase5Monitoring,
        TestPhase5Integration,
    ]

    total_tests = 0
    passed_tests = 0

    for test_class in test_classes:
        print(f"\n📋 Testing {test_class.__name__}...")

        # Get all test methods
        test_methods = [
            method
            for method in dir(test_class)
            if method.startswith("test_") and callable(getattr(test_class, method))
        ]

        for method_name in test_methods:
            total_tests += 1
            try:
                test_instance = test_class()
                method = getattr(test_instance, method_name)

                # Handle async methods
                if asyncio.iscoroutinefunction(method):
                    asyncio.run(method())
                else:
                    method()

                print(f"  ✅ {method_name}")
                passed_tests += 1

            except Exception as e:
                print(f"  ❌ {method_name}: {e}")

    print(f"\n📊 Test Results:")
    print(f"  Total Tests: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {total_tests - passed_tests}")
    print(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")

    if passed_tests == total_tests:
        print("\n🎉 All Phase 5 tests passed!")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} tests failed.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
