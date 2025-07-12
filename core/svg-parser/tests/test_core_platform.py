"""
Comprehensive Test Suite for Core Platform Service

This test suite covers all aspects of the core platform functionality including:
- Service registration and management
- Health monitoring and status tracking
- Configuration management
- Caching operations and performance
- System metrics collection
- Error handling and recovery
- Performance monitoring and analytics
"""

import pytest
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock
import time
import threading
import os
import yaml

from services.core_platform import (
    CorePlatformService,
    ServiceStatus,
    ServiceType,
    HealthStatus,
    ServiceInfo,
    SystemMetrics,
    Configuration
)


class TestCorePlatformService:
    """Test suite for the CorePlatformService."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary configuration file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'environment': 'test',
                'debug_mode': True,
                'log_level': 'DEBUG',
                'database_url': 'sqlite:///test_platform.db',
                'redis_url': 'redis://localhost:6379',
                'api_host': 'localhost',
                'api_port': 8000,
                'max_workers': 5,
                'cache_ttl': 1800,
                'health_check_interval': 10,
                'backup_interval': 1800,
                'security_settings': {
                    'enable_auth': True,
                    'session_timeout': 3600
                },
                'feature_flags': {
                    'advanced_caching': True,
                    'health_monitoring': True
                }
            }
            yaml.dump(config_data, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        try:
            os.unlink(temp_path)
        except OSError:
            pass
    
    @pytest.fixture
    def platform_service(self, temp_config_file):
        """Create a core platform service instance for testing."""
        return CorePlatformService(config_path=temp_config_file)
    
    @pytest.fixture
    def sample_service_info(self):
        """Sample service information for testing."""
        return ServiceInfo(
            service_id="test_service_001",
            name="Test Service",
            service_type=ServiceType.API,
            status=ServiceStatus.RUNNING,
            version="1.0.0",
            host="localhost",
            port=8080,
            health_endpoint="/health",
            metadata={"environment": "test", "region": "us-east-1"},
            last_heartbeat=datetime.now(),
            created_at=datetime.now()
        )
    
    def test_service_initialization(self, platform_service):
        """Test service initialization and configuration loading."""
        assert platform_service is not None
        assert platform_service.config is not None
        assert platform_service.config.environment == 'test'
        assert platform_service.config.debug_mode is True
        assert platform_service.config.log_level == 'DEBUG'
        assert len(platform_service.services) > 0  # Core services registered
        assert platform_service.running is True
    
    def test_configuration_loading(self, temp_config_file):
        """Test configuration loading from file."""
        service = CorePlatformService(config_path=temp_config_file)
        
        config = service.get_configuration()
        assert config.environment == 'test'
        assert config.debug_mode is True
        assert config.log_level == 'DEBUG'
        assert config.api_host == 'localhost'
        assert config.api_port == 8000
        assert config.max_workers == 5
        assert config.cache_ttl == 1800
        assert config.security_settings['enable_auth'] is True
        assert config.feature_flags['advanced_caching'] is True
    
    def test_default_configuration(self):
        """Test default configuration when no config file exists."""
        service = CorePlatformService(config_path="nonexistent.yaml")
        
        config = service.get_configuration()
        assert config.environment == 'development'
        assert config.debug_mode is False
        assert config.log_level == 'INFO'
        assert config.api_host == 'localhost'
        assert config.api_port == 8000
    
    def test_service_registration(self, platform_service, sample_service_info):
        """Test service registration functionality."""
        # Register service
        success = platform_service.register_service(sample_service_info)
        assert success is True
        
        # Verify service is registered
        registered_service = platform_service.get_service_info(sample_service_info.service_id)
        assert registered_service is not None
        assert registered_service.service_id == sample_service_info.service_id
        assert registered_service.name == sample_service_info.name
        assert registered_service.service_type == sample_service_info.service_type
        assert registered_service.status == sample_service_info.status
    
    def test_service_unregistration(self, platform_service, sample_service_info):
        """Test service unregistration functionality."""
        # Register service first
        platform_service.register_service(sample_service_info)
        
        # Verify service is registered
        assert platform_service.get_service_info(sample_service_info.service_id) is not None
        
        # Unregister service
        success = platform_service.unregister_service(sample_service_info.service_id)
        assert success is True
        
        # Verify service is unregistered
        assert platform_service.get_service_info(sample_service_info.service_id) is None
    
    def test_service_listing(self, platform_service):
        """Test service listing functionality."""
        # Get all services
        all_services = platform_service.list_services()
        assert len(all_services) > 0
        
        # Get services by type
        core_services = platform_service.list_services(ServiceType.CORE)
        assert len(core_services) > 0
        assert all(service.service_type == ServiceType.CORE for service in core_services)
        
        api_services = platform_service.list_services(ServiceType.API)
        assert len(api_services) >= 0  # May be empty initially
    
    def test_health_status(self, platform_service):
        """Test health status functionality."""
        health_status = platform_service.get_health_status()
        
        assert 'status' in health_status
        assert 'healthy_services' in health_status
        assert 'total_services' in health_status
        assert 'health_percentage' in health_status
        assert 'last_check' in health_status
        assert 'uptime' in health_status
        
        assert health_status['total_services'] > 0
        assert health_status['healthy_services'] >= 0
        assert health_status['health_percentage'] >= 0
        assert health_status['uptime'] >= 0
    
    def test_cache_operations(self, platform_service):
        """Test cache operations."""
        # Test cache set
        success = platform_service.cache_set("test_key", "test_value", 60)
        assert success is True
        
        # Test cache get
        value = platform_service.cache_get("test_key")
        assert value == "test_value"
        
        # Test cache get with non-existent key
        value = platform_service.cache_get("nonexistent_key")
        assert value is None
        
        # Test cache delete
        success = platform_service.cache_delete("test_key")
        assert success is True
        
        # Verify deletion
        value = platform_service.cache_get("test_key")
        assert value is None
    
    def test_cache_with_complex_data(self, platform_service):
        """Test cache operations with complex data structures."""
        complex_data = {
            "string": "test",
            "number": 42,
            "boolean": True,
            "list": [1, 2, 3],
            "dict": {"key": "value"},
            "null": None
        }
        
        # Set complex data
        success = platform_service.cache_set("complex_key", complex_data, 60)
        assert success is True
        
        # Get complex data
        retrieved_data = platform_service.cache_get("complex_key")
        assert retrieved_data == complex_data
    
    def test_cache_statistics(self, platform_service):
        """Test cache statistics."""
        # Perform some cache operations
        platform_service.cache_set("key1", "value1", 60)
        platform_service.cache_set("key2", "value2", 60)
        platform_service.cache_get("key1")  # Hit
        platform_service.cache_get("key2")  # Hit
        platform_service.cache_get("nonexistent")  # Miss
        platform_service.cache_delete("key1")
        
        stats = platform_service.get_cache_stats()
        
        assert 'hits' in stats
        assert 'misses' in stats
        assert 'sets' in stats
        assert 'deletes' in stats
        assert 'hit_rate' in stats
        assert 'memory_cache_size' in stats
        assert 'redis_available' in stats
        
        assert stats['sets'] >= 2
        assert stats['hits'] >= 2
        assert stats['misses'] >= 1
        assert stats['deletes'] >= 1
        assert stats['hit_rate'] >= 0
    
    def test_configuration_update(self, platform_service):
        """Test configuration update functionality."""
        # Get current configuration
        original_config = platform_service.get_configuration()
        
        # Update configuration
        updates = {
            'log_level': 'ERROR',
            'cache_ttl': 7200,
            'debug_mode': False
        }
        
        success = platform_service.update_configuration(updates)
        assert success is True
        
        # Get updated configuration
        updated_config = platform_service.get_configuration()
        
        # Verify updates
        assert updated_config.log_level == 'ERROR'
        assert updated_config.cache_ttl == 7200
        assert updated_config.debug_mode is False
        
        # Verify unchanged values
        assert updated_config.environment == original_config.environment
        assert updated_config.api_host == original_config.api_host
    
    def test_system_metrics_collection(self, platform_service):
        """Test system metrics collection."""
        # Trigger metrics collection
        platform_service._collect_system_metrics()
        
        # Get metrics
        metrics = platform_service.get_system_metrics(limit=10)
        
        assert len(metrics) > 0
        
        # Check metric structure
        metric = metrics[-1]  # Latest metric
        assert hasattr(metric, 'cpu_usage')
        assert hasattr(metric, 'memory_usage')
        assert hasattr(metric, 'disk_usage')
        assert hasattr(metric, 'network_io')
        assert hasattr(metric, 'active_connections')
        assert hasattr(metric, 'response_time')
        assert hasattr(metric, 'error_rate')
        assert hasattr(metric, 'timestamp')
        
        # Check metric values
        assert 0 <= metric.cpu_usage <= 100
        assert 0 <= metric.memory_usage <= 100
        assert 0 <= metric.disk_usage <= 100
        assert metric.active_connections >= 0
        assert metric.response_time >= 0
        assert 0 <= metric.error_rate <= 100
    
    def test_performance_metrics(self, platform_service):
        """Test performance metrics functionality."""
        # Simulate some requests
        platform_service.total_requests = 100
        platform_service.successful_requests = 95
        platform_service.failed_requests = 5
        platform_service.average_response_time = 0.15
        
        metrics = platform_service.get_performance_metrics()
        
        assert 'uptime_seconds' in metrics
        assert 'total_requests' in metrics
        assert 'successful_requests' in metrics
        assert 'failed_requests' in metrics
        assert 'success_rate' in metrics
        assert 'average_response_time' in metrics
        assert 'registered_services' in metrics
        assert 'health_status' in metrics
        assert 'cache_stats' in metrics
        assert 'system_metrics' in metrics
        
        assert metrics['total_requests'] == 100
        assert metrics['successful_requests'] == 95
        assert metrics['failed_requests'] == 5
        assert metrics['success_rate'] == 95.0
        assert metrics['average_response_time'] == 0.15
        assert metrics['uptime_seconds'] >= 0
    
    def test_service_health_check(self, platform_service):
        """Test service health checking."""
        # Create a test service
        service_info = ServiceInfo(
            service_id="health_test_service",
            name="Health Test Service",
            service_type=ServiceType.CORE,
            status=ServiceStatus.RUNNING,
            version="1.0.0",
            host="localhost",
            port=8080,
            health_endpoint="/health",
            metadata={},
            last_heartbeat=datetime.now(),
            created_at=datetime.now()
        )
        
        # Register service
        platform_service.register_service(service_info)
        
        # Perform health check
        health_status = platform_service._check_service_health(service_info)
        
        # Should be healthy for core service
        assert health_status in [HealthStatus.HEALTHY, HealthStatus.UNKNOWN]
    
    def test_health_monitoring_worker(self, platform_service):
        """Test health monitoring background worker."""
        # Start health monitoring
        platform_service._perform_health_checks()
        
        # Check that health status is updated
        health_status = platform_service.get_health_status()
        assert 'status' in health_status
        assert 'last_check' in health_status
    
    def test_metrics_collection_worker(self, platform_service):
        """Test metrics collection background worker."""
        # Trigger metrics collection
        platform_service._collect_system_metrics()
        
        # Check that metrics are collected
        metrics = platform_service.get_system_metrics(limit=5)
        assert len(metrics) > 0
    
    def test_cache_cleanup_worker(self, platform_service):
        """Test cache cleanup background worker."""
        # Set some cache entries with short TTL
        platform_service.cache_set("temp_key1", "value1", 1)
        platform_service.cache_set("temp_key2", "value2", 1)
        
        # Wait for expiration
        time.sleep(2)
        
        # Trigger cleanup
        platform_service._cleanup_expired_cache()
        
        # Check that expired entries are cleaned up
        value1 = platform_service.cache_get("temp_key1")
        value2 = platform_service.cache_get("temp_key2")
        
        # Values should be None or cleaned up
        assert value1 is None or value1 != "value1"
        assert value2 is None or value2 != "value2"
    
    def test_service_persistence(self, temp_config_file):
        """Test that service data persists across service instances."""
        service_id = "persistence_test_service"
        
        # Create first service instance and register service
        service1 = CorePlatformService(config_path=temp_config_file)
        service_info = ServiceInfo(
            service_id=service_id,
            name="Persistence Test Service",
            service_type=ServiceType.API,
            status=ServiceStatus.RUNNING,
            version="1.0.0",
            host="localhost",
            port=8080,
            health_endpoint="/health",
            metadata={},
            last_heartbeat=datetime.now(),
            created_at=datetime.now()
        )
        
        service1.register_service(service_info)
        
        # Create second service instance and check service exists
        service2 = CorePlatformService(config_path=temp_config_file)
        registered_service = service2.get_service_info(service_id)
        
        assert registered_service is not None
        assert registered_service.service_id == service_id
        assert registered_service.name == "Persistence Test Service"
    
    def test_error_handling(self, platform_service):
        """Test error handling and recovery."""
        # Test service registration with invalid data
        invalid_service = ServiceInfo(
            service_id="",  # Invalid empty ID
            name="Invalid Service",
            service_type=ServiceType.API,
            status=ServiceStatus.RUNNING,
            version="1.0.0",
            host="localhost",
            port=8080,
            health_endpoint="/health",
            metadata={},
            last_heartbeat=datetime.now(),
            created_at=datetime.now()
        )
        
        # Should handle gracefully
        success = platform_service.register_service(invalid_service)
        # May succeed or fail gracefully, but shouldn't crash
    
    def test_concurrent_operations(self, platform_service):
        """Test concurrent operations."""
        import threading
        import time
        
        results = []
        errors = []
        
        def register_service_worker(service_id):
            try:
                service_info = ServiceInfo(
                    service_id=f"concurrent_service_{service_id}",
                    name=f"Concurrent Service {service_id}",
                    service_type=ServiceType.API,
                    status=ServiceStatus.RUNNING,
                    version="1.0.0",
                    host="localhost",
                    port=8080 + service_id,
                    health_endpoint="/health",
                    metadata={},
                    last_heartbeat=datetime.now(),
                    created_at=datetime.now()
                )
                
                success = platform_service.register_service(service_info)
                results.append(success)
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=register_service_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Concurrent operations failed: {errors}"
        assert len(results) == 5
        assert all(results), "All service registrations should succeed"
    
    def test_performance_targets(self, platform_service):
        """Test that service meets performance targets."""
        # Test startup time
        start_time = time.time()
        service = CorePlatformService(config_path="nonexistent.yaml")
        startup_time = time.time() - start_time
        
        # Should start within 30 seconds
        assert startup_time < 30, f"Startup time {startup_time}s exceeds 30s target"
        
        # Test cache performance
        cache_start = time.time()
        for i in range(100):
            platform_service.cache_set(f"perf_key_{i}", f"value_{i}", 60)
        cache_time = time.time() - cache_start
        
        # Should complete cache operations quickly
        assert cache_time < 5, f"Cache operations took {cache_time}s, should be < 5s"
        
        # Test service registration performance
        reg_start = time.time()
        for i in range(50):
            service_info = ServiceInfo(
                service_id=f"perf_service_{i}",
                name=f"Performance Service {i}",
                service_type=ServiceType.API,
                status=ServiceStatus.RUNNING,
                version="1.0.0",
                host="localhost",
                port=8080 + i,
                health_endpoint="/health",
                metadata={},
                last_heartbeat=datetime.now(),
                created_at=datetime.now()
            )
            platform_service.register_service(service_info)
        reg_time = time.time() - reg_start
        
        # Should complete registrations quickly
        assert reg_time < 10, f"Service registrations took {reg_time}s, should be < 10s"
    
    def test_edge_cases(self, platform_service):
        """Test various edge cases."""
        # Test with very large service ID
        large_id = "x" * 1000
        service_info = ServiceInfo(
            service_id=large_id,
            name="Large ID Service",
            service_type=ServiceType.API,
            status=ServiceStatus.RUNNING,
            version="1.0.0",
            host="localhost",
            port=8080,
            health_endpoint="/health",
            metadata={},
            last_heartbeat=datetime.now(),
            created_at=datetime.now()
        )
        
        success = platform_service.register_service(service_info)
        assert success is True
        
        # Test with special characters in service ID
        special_id = "service-with-special-chars!@#$%^&*()"
        service_info.service_id = special_id
        success = platform_service.register_service(service_info)
        assert success is True
        
        # Test with empty cache key
        success = platform_service.cache_set("", "value", 60)
        assert success is True
        
        # Test with None values
        success = platform_service.cache_set("none_key", None, 60)
        assert success is True
        
        value = platform_service.cache_get("none_key")
        assert value is None


class TestCorePlatformIntegration:
    """Integration tests for core platform functionality."""
    
    @pytest.fixture
    def platform_service(self):
        """Create a platform service for integration testing."""
        return CorePlatformService()
    
    def test_full_service_lifecycle(self, platform_service):
        """Test complete service lifecycle."""
        # 1. Register service
        service_info = ServiceInfo(
            service_id="lifecycle_test_service",
            name="Lifecycle Test Service",
            service_type=ServiceType.API,
            status=ServiceStatus.RUNNING,
            version="1.0.0",
            host="localhost",
            port=8080,
            health_endpoint="/health",
            metadata={"test": True},
            last_heartbeat=datetime.now(),
            created_at=datetime.now()
        )
        
        success = platform_service.register_service(service_info)
        assert success is True
        
        # 2. Verify service is registered
        registered_service = platform_service.get_service_info(service_info.service_id)
        assert registered_service is not None
        
        # 3. Check health status
        health_status = platform_service.get_health_status()
        assert health_status['total_services'] > 0
        
        # 4. Use cache
        platform_service.cache_set("lifecycle_key", "lifecycle_value", 60)
        cached_value = platform_service.cache_get("lifecycle_key")
        assert cached_value == "lifecycle_value"
        
        # 5. Get metrics
        metrics = platform_service.get_performance_metrics()
        assert metrics['registered_services'] > 0
        
        # 6. Unregister service
        success = platform_service.unregister_service(service_info.service_id)
        assert success is True
        
        # 7. Verify service is unregistered
        registered_service = platform_service.get_service_info(service_info.service_id)
        assert registered_service is None
    
    def test_configuration_workflow(self, platform_service):
        """Test configuration management workflow."""
        # 1. Get initial configuration
        initial_config = platform_service.get_configuration()
        
        # 2. Update configuration
        updates = {
            'log_level': 'WARNING',
            'cache_ttl': 3600,
            'debug_mode': False
        }
        
        success = platform_service.update_configuration(updates)
        assert success is True
        
        # 3. Verify configuration changes
        updated_config = platform_service.get_configuration()
        assert updated_config.log_level == 'WARNING'
        assert updated_config.cache_ttl == 3600
        assert updated_config.debug_mode is False
        
        # 4. Verify unchanged values
        assert updated_config.environment == initial_config.environment
        assert updated_config.api_host == initial_config.api_host
    
    def test_health_monitoring_workflow(self, platform_service):
        """Test health monitoring workflow."""
        # 1. Register multiple services
        services = []
        for i in range(3):
            service_info = ServiceInfo(
                service_id=f"health_test_service_{i}",
                name=f"Health Test Service {i}",
                service_type=ServiceType.API,
                status=ServiceStatus.RUNNING,
                version="1.0.0",
                host="localhost",
                port=8080 + i,
                health_endpoint="/health",
                metadata={},
                last_heartbeat=datetime.now(),
                created_at=datetime.now()
            )
            platform_service.register_service(service_info)
            services.append(service_info)
        
        # 2. Perform health checks
        platform_service._perform_health_checks()
        
        # 3. Check health status
        health_status = platform_service.get_health_status()
        assert health_status['total_services'] >= 3
        
        # 4. Unregister services
        for service in services:
            platform_service.unregister_service(service.service_id)
    
    def test_cache_performance_workflow(self, platform_service):
        """Test cache performance workflow."""
        # 1. Set multiple cache entries
        for i in range(100):
            platform_service.cache_set(f"perf_key_{i}", f"value_{i}", 60)
        
        # 2. Get cache statistics
        stats = platform_service.get_cache_stats()
        assert stats['sets'] >= 100
        
        # 3. Retrieve cache entries
        hits = 0
        for i in range(100):
            value = platform_service.cache_get(f"perf_key_{i}")
            if value == f"value_{i}":
                hits += 1
        
        # 4. Check hit rate
        updated_stats = platform_service.get_cache_stats()
        assert updated_stats['hits'] >= hits
        
        # 5. Clean up
        for i in range(100):
            platform_service.cache_delete(f"perf_key_{i}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 